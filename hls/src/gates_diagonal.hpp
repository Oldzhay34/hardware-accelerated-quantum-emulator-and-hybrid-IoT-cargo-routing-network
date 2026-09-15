// KÖŞEGEN kapılar — bankalama sorunu YOK.
//
// Fazın en önemli tasarım bulgusu bu ayrımdır (research.md R-4, ÖLÇÜLEN):
// köşegen kapı genliği yerinde bir sayıyla çarpar, `(i, i XOR 2^k)` eşlemesi
// YOKTUR, erişim `i = 0..N_AMP-1` sıralıdır. QAOA maliyet operatörünün 100
// Pauli teriminin HEPSİ köşegendir.
//
// Qiskit RZZ'yi CX-RZ-CX olarak ayrıştırır ve CX köşegen değildir — ama bu
// Qiskit'in kapı kümesinin kısıtıdır, bizim çekirdeğimizin değil. Yerleşik
// uygulamayla eşlemeli kapı sayısı p=2'de 384 -> 32, yani 12x azalır.
//
// Köşegen matrislerin çarpımı köşegendir: 100 kapı TEK geçişe füzyonlanır ve
// bu füzyon BEDELSİZDİR (çok kübitli füzyondan farkı budur — aritmetik artmaz).
#pragma once

#include "qir_types.hpp"
#include "trig.hpp"

namespace qir {

/// Maliyet katmanının faz sabitleri — bir QAOA katmanı için.
///
/// Konak tarafından hesaplanır: `h[k] = round(mod(-gamma*h_k/(2*pi), 1) * 2^18)`.
/// Neden konakta: E(i) ~ 1e4 mertebesinde olduğu için `gamma*E`'yi sabit
/// noktada tutmak ~44 bitlik akümülatör isterdi. Terim başına faz mod 1'e
/// indirgenince toplama taşması ZATEN mod 2*pi olur ve sorun kaybolur.
/// Konak zaten klasik optimizasyon döngüsünü koşuyor; katman başına 100 sabit
/// hesaplamak ihmal edilebilir bir iştir (genlik başına değil, katman başına).
struct cost_phases_t {
    phase_t h[N_QUBITS];
    phase_t J[N_QUBITS][N_QUBITS];  // yalnızca a < b kullanılır
};

/// exp(-i * gamma * H_C) - fuzyonlanmis kosegen gecis.
///
/// IKI SEVIYELI AYRISTIRMA. Kubitler ikiye bolunur: L = {0..7}, H = {8..15}.
///
///   acc(i) = FL[dusuk] + FH[yuksek] + sum_{a in L} s_a * D_a[yuksek]
///
/// Capraz terimler carpanlara ayrilabiliyor:
///   sum_{a in L, b in H} s_a s_b J[a][b] = sum_{a in L} s_a * (sum_{b in H} s_b J[a][b])
/// ve ictekinin yalnizca YUKSEK bitlere bagli olmasi onu onceden hesaplanabilir
/// kiliyor. Genlik basina 136 terim yerine ~10 terim kaliyor.
///
/// NEDEN BOYLE (docs/measurements/faz2-sentez.md):
///   - Acilmamis hali: 98M cevrim (seri bagimlilik) -- gecikmenin %70'i.
///   - Tam acilmis hali: 4,46M cevrim ama LUT %359 -- cipe sigmiyor.
///   - II gevsetme ISE YARAMIYOR: II=1/4/16 icin LUT 191k/190,7k/190,3k,
///     yani %0,5 degisim; HLS UNROLL'la orneklenen toplayicilari paylastirmiyor.
///     Tek yol terim sayisini dusurmek.
///   - Gray-kod da 136->16 yapardi, ama calisma zamani bit indeksi (16 yollu
///     mux) ve permute edilmis gezinme getirirdi. Bu ayristirma ~10'a indiriyor
///     VE sirali erisimi koruyor.
inline void apply_cost_layer(amp_t sv[N_AMP], const cost_phases_t& ph) {
    constexpr int YARIM = N_QUBITS / 2;
    constexpr int TABLO = 1 << YARIM;

    // Katman basina BIR KEZ kurulur; genlik basina degil.
    phase_t FL[TABLO], FH[TABLO], D[YARIM][TABLO];
#pragma HLS ARRAY_PARTITION variable = D complete dim = 1

    // DIKKAT -- bu iki dongu BILINCLI OLARAK acilmaz ve boru hattina alinmaz.
    //
    // Ilk denemede acmistim ve apply_cost_layer 89.935 LUT + 148 DSP tuttu
    // (toplamin yarisi). Sebep: tablo_yuksek acilinca 100 toplayicilik donanim
    // orneklenıyor -- yalnizca 256 kez calisan bir dongu icin. Tablolar ana
    // gecisin DISINDA, katman basina bir kez kuruluyor; serı hallerinde
    // ~35.000 cevrim tutuyorlar ve bu 65.536'lik ana gecisin yaninda ucuz.
    //
    // Kural: UNROLL yalnizca genlik basina calisan yola uygulanir.
tablo_dusuk:
    for (int lo = 0; lo < TABLO; ++lo) {
#pragma HLS PIPELINE off
        phase_t a(0);
        for (int k = 0; k < YARIM; ++k) {
            if ((lo >> k) & 1) a -= (uint64_t)ph.h[k];
            else               a += (uint64_t)ph.h[k];
        }
        for (int x = 0; x < YARIM; ++x) {
            for (int y = x + 1; y < YARIM; ++y) {
                if (((lo >> x) ^ (lo >> y)) & 1) a -= (uint64_t)ph.J[x][y];
                else                             a += (uint64_t)ph.J[x][y];
            }
        }
        FL[lo] = a;
    }

tablo_yuksek:
    for (int hi = 0; hi < TABLO; ++hi) {
#pragma HLS PIPELINE off
        phase_t a(0);
        for (int k = 0; k < YARIM; ++k) {
            if ((hi >> k) & 1) a -= (uint64_t)ph.h[YARIM + k];
            else               a += (uint64_t)ph.h[YARIM + k];
        }
        for (int x = 0; x < YARIM; ++x) {
            for (int y = x + 1; y < YARIM; ++y) {
                if (((hi >> x) ^ (hi >> y)) & 1) a -= (uint64_t)ph.J[YARIM + x][YARIM + y];
                else                             a += (uint64_t)ph.J[YARIM + x][YARIM + y];
            }
        }
        FH[hi] = a;

        // D_a[hi] = sum_{b in H} s_b * J[a][b]  -- yalnizca yuksek bitlere bagli
        for (int aa = 0; aa < YARIM; ++aa) {
            phase_t d(0);
            for (int b = 0; b < YARIM; ++b) {
                if ((hi >> b) & 1) d -= (uint64_t)ph.J[aa][YARIM + b];
                else               d += (uint64_t)ph.J[aa][YARIM + b];
            }
            D[aa][hi] = d;
        }
    }

cost_amp_loop:
    for (int i = 0; i < N_AMP; ++i) {
#pragma HLS PIPELINE II = 1
        const int lo = i & (TABLO - 1);
        const int hi = i >> YARIM;

        phase_t acc(0);
        acc += (uint64_t)FL[lo];
        acc += (uint64_t)FH[hi];
    capraz:
        for (int aa = 0; aa < YARIM; ++aa) {
#pragma HLS UNROLL
            if ((lo >> aa) & 1) acc -= (uint64_t)D[aa][hi];
            else                acc += (uint64_t)D[aa][hi];
        }

        real_t c, s;
        turn_to_cos_sin(acc, c, s);

        const real_t re = sv[i].re;
        const real_t im = sv[i].im;
        sv[i].re = re * c - im * s;
        sv[i].im = re * s + im * c;
    }
}

}  // namespace qir
