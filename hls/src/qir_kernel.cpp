// Üst seviye çekirdek — QAOA'ya özel statevector emülatörü.
//
// Onaylanan mimari: ADR 0008 (A1 + B4 + C1).
// Sözleşmeler: specs/002-fpga-statevector-cekirdegi/contracts/
//
// İKİ AYRI YÜZEY vardır ve bu bilinçlidir (NFR-02 çelişkisinin çözümü):
//   qir_kernel        -> dağıtılan IP. Tek skaler döndürür, genlik göstermez.
//                        BU DOSYA yalnızca onu içerir ve sentezlenen tek yoldur.
//   qir_kernel_debug  -> yalnızca doğrulama. `hls/tb/qir_kernel_debug.cpp`.
//
// Doğrulama yüzeyi bilinçli olarak AYRI DOSYADADIR. Önceden `#ifdef
// QIR_VERIFICATION` ile burada duruyordu; ama csim, csynth ve cosim aynı Vitis
// çözümünü paylaştığı için o bayrak sentez yolunda da tanımlı kalırdı ve
// `sv_out` bir m_axi portu doğurarak K-1'i (DDR'a taşma yasağı) ihlal edebilirdi.
// Dosya ayrımı bunu `#ifdef` disiplinine güvenmeden garanti eder: Tcl akışı
// debug dosyasını `add_files -tb` ile ekler, sentez onu hiç görmez.
#include "qir_kernel.hpp"


namespace qir {

/// <psi|H_C|psi>, ölçeklenmiş birimde. Konak `* olcek` ile geri çevirir.
///
/// Offset DAHİL DEĞİL — referansın `cost_after` alanı da böyledir. QUBO
/// enerjisine çevirmek konak tarafının işidir; offset (bu problemde ~35.303)
/// çekirdeğin sabit-nokta aralığına sığmaz ve taşınmasının bir faydası yoktur.
float expectation_scaled(const amp_t sv[N_AMP], const cost_scaled_t& cs) {
    // apply_cost_layer ile AYNI iki seviyeli ayristirma. Kubitler L = {0..7} ve
    // H = {8..15} diye bolunur:
    //
    //   E(i) = EL[dusuk] + EH[yuksek] + sum_{a in L} s_a * G_a[yuksek]
    //
    // Capraz terimler carpanlara ayrilabiliyor:
    //   sum_{a in L, b in H} s_a s_b J[a][b] = sum_{a in L} s_a * (sum_{b in H} s_b J[a][b])
    // ve ictekinin yalnizca YUKSEK bitlere bagli olmasi onu onceden
    // hesaplanabilir kiliyor. Genlik basina 136 terim yerine ~10 terim kaliyor.
    //
    // OLCULDU: acilmis 136 terimli hali 38.338.624 cevrim ve 38.012 LUT
    // tutuyordu (docs/measurements/faz2-sentez.md).
    constexpr int YARIM = N_QUBITS / 2;
    constexpr int TABLO = 1 << YARIM;

    sum_t EL[TABLO], EH[TABLO], G[YARIM][TABLO];
#pragma HLS ARRAY_PARTITION variable = G complete dim = 1

    // Tablolar BIR KEZ kurulur. Bilincli olarak ACILMAZ ve boru hattina
    // alinmaz: yalnizca 256 kez calisiyorlar ve acilirlarsa genlik basina
    // calismayan bir yola yuzlerce toplayici orneklenir.
exp_tablo_dusuk:
    for (int lo = 0; lo < TABLO; ++lo) {
        sum_t a = 0.0;
        for (int k = 0; k < YARIM; ++k) {
            if ((lo >> k) & 1) a -= sum_t(cs.h[k]);
            else               a += sum_t(cs.h[k]);
        }
        for (int x = 0; x < YARIM; ++x) {
            for (int y = x + 1; y < YARIM; ++y) {
                if (((lo >> x) ^ (lo >> y)) & 1) a -= sum_t(cs.J[x][y]);
                else                             a += sum_t(cs.J[x][y]);
            }
        }
        EL[lo] = a;
    }

exp_tablo_yuksek:
    for (int hi = 0; hi < TABLO; ++hi) {
        sum_t a = 0.0;
        for (int k = 0; k < YARIM; ++k) {
            if ((hi >> k) & 1) a -= sum_t(cs.h[YARIM + k]);
            else               a += sum_t(cs.h[YARIM + k]);
        }
        for (int x = 0; x < YARIM; ++x) {
            for (int y = x + 1; y < YARIM; ++y) {
                if (((hi >> x) ^ (hi >> y)) & 1) a -= sum_t(cs.J[YARIM + x][YARIM + y]);
                else                             a += sum_t(cs.J[YARIM + x][YARIM + y]);
            }
        }
        EH[hi] = a;

        for (int aa = 0; aa < YARIM; ++aa) {
            sum_t g = 0.0;
            for (int b = 0; b < YARIM; ++b) {
                if ((hi >> b) & 1) g -= sum_t(cs.J[aa][YARIM + b]);
                else               g += sum_t(cs.J[aa][YARIM + b]);
            }
            G[aa][hi] = g;
        }
    }

    sum_t pay = 0.0;
    sum_t payda = 0.0;

exp_amp_loop:
    for (int i = 0; i < N_AMP; ++i) {
#pragma HLS PIPELINE II = 1
        const real_t re = sv[i].re;
        const real_t im = sv[i].im;
        const acc_t olasilik = re * re + im * im;

        const int lo = i & (TABLO - 1);
        const int hi = i >> YARIM;

        sum_t E = EL[lo];
        E += EH[hi];
    exp_capraz:
        for (int aa = 0; aa < YARIM; ++aa) {
#pragma HLS UNROLL
            if ((lo >> aa) & 1) E -= G[aa][hi];
            else                E += G[aa][hi];
        }

        pay += olasilik * E;
        payda += olasilik;
    }
    return float(double(pay) / double(payda));
}

}  // namespace qir

// ---------------------------------------------------------------------------
// Dağıtım arayüzü (FR-015) — contracts/kernel-interface.md
// ---------------------------------------------------------------------------
void qir_kernel(const qir::cost_phases_t phases[qir::P_MAX],
                const qir::real_t cos_beta[qir::P_MAX],
                const qir::real_t sin_beta[qir::P_MAX],
                const qir::cost_scaled_t& cost,
                int p,
                float& beklenen_deger) {
#pragma HLS INTERFACE mode = s_axilite port = phases
#pragma HLS INTERFACE mode = s_axilite port = cos_beta
#pragma HLS INTERFACE mode = s_axilite port = sin_beta
#pragma HLS INTERFACE mode = s_axilite port = cost
#pragma HLS INTERFACE mode = s_axilite port = p
#pragma HLS INTERFACE mode = s_axilite port = beklenen_deger
#pragma HLS INTERFACE mode = s_axilite port = return

    // Madde K-2: geçersiz p -> çekirdek çalışmaz, çıkış değişmez.
    if (p < 1 || p > qir::P_MAX) return;

    // Statevector: çip-içi, m_axi YOK (madde K-1, Anayasa Prensip III).
    static qir::amp_t sv[qir::N_AMP];
#pragma HLS ARRAY_PARTITION variable = sv cyclic factor = 16 dim = 1
#pragma HLS BIND_STORAGE variable = sv type = RAM_2P impl = BRAM

    // Madde K-4: çekirdek durumsuzdur — run_circuit her çağrıda init_uniform
    // ile başlar, önceki çağrının kalıntısı taşınmaz.
    qir::run_circuit(sv, phases, cos_beta, sin_beta, p);
    beklenen_deger = qir::expectation_scaled(sv, cost);
}



