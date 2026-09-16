// EŞLEMELİ kapılar — `(i, i XOR 2^k)` çiftleri. SK-02 yalnızca burada geçerli.
//
// p=2'de 232 kapının yalnızca 32'si (%13,8) buradadır (research.md R-4).
//
// ⚠️ `K` ŞABLON PARAMETRESİDİR, çalışma zamanı değişkeni DEĞİL. Bu tesadüf
// değil, tasarımın kendisidir (research.md R-7): HLS `ARRAY_PARTITION`'lı bir
// diziye hangi parçadan erişildiğini derleme zamanında çözemezse BÜTÜN
// erişimleri seri hale getirir ve plandaki II aritmetiğinin tamamı geçersiz
// olur. `K` sabit olduğu sürece bu risk oluşmaz.
//
// Beklenen II (HESAPLANAN, doğrulanmamış):
//   k = 0..3  -> II = 1   (çiftin iki üyesi farklı bankalara düşer)
//   k = 4..15 -> II = 2   (düşük 4 bit aynı -> aynı banka, 4 erişim)
// SC-003 II <= 4'e izin verdiği için ikisi de kabul sınırları içinde.
#pragma once

#include "qir_types.hpp"
#include "statevector.hpp"

namespace qir {

/// RX(theta) kübit K'ye.  cos_half = cos(theta/2), sin_half = sin(theta/2).
///
///   yeni[i0] = c*a - i*s*b
///   yeni[i1] = -i*s*a + c*b
template <int K>
inline void apply_rx(amp_t sv[N_AMP], real_t cos_half, real_t sin_half) {
    static_assert(K >= 0 && K < N_QUBITS, "kubit indeksi araligi disinda");
    constexpr int STRIDE = 1 << K;

rx_pair_loop:
    for (int j = 0; j < N_PAIR; ++j) {
#pragma HLS PIPELINE II = 1
        const int i0 = pair_index(j, K);
        const int i1 = i0 | STRIDE;

        const real_t ar = sv[i0].re, ai = sv[i0].im;
        const real_t br = sv[i1].re, bi = sv[i1].im;

        // -i*s*(br + i*bi) = s*bi - i*s*br
        sv[i0].re = cos_half * ar + sin_half * bi;
        sv[i0].im = cos_half * ai - sin_half * br;
        sv[i1].re = cos_half * br + sin_half * ai;
        sv[i1].im = cos_half * bi - sin_half * ar;
    }
}

/// Hadamard kübit K'ye (FR-002). QAOA'da kullanılmaz — başlangıç durumu
/// doğrudan düzgün süperpozisyon olarak kurulur — ama kapı kümesi gereği var.
template <int K>
inline void apply_h(amp_t sv[N_AMP]) {
    static_assert(K >= 0 && K < N_QUBITS, "kubit indeksi araligi disinda");
    constexpr int STRIDE = 1 << K;
    const real_t inv_sqrt2 = 0.70710678118654752440;

h_pair_loop:
    for (int j = 0; j < N_PAIR; ++j) {
#pragma HLS PIPELINE II = 1
        const int i0 = pair_index(j, K);
        const int i1 = i0 | STRIDE;
        const real_t ar = sv[i0].re, ai = sv[i0].im;
        const real_t br = sv[i1].re, bi = sv[i1].im;
        sv[i0].re = inv_sqrt2 * (ar + br);
        sv[i0].im = inv_sqrt2 * (ai + bi);
        sv[i1].re = inv_sqrt2 * (ar - br);
        sv[i1].im = inv_sqrt2 * (ai - bi);
    }
}

/// X (NOT) kübit K'ye (FR-002) — çiftin iki üyesini takas eder.
template <int K>
inline void apply_x(amp_t sv[N_AMP]) {
    static_assert(K >= 0 && K < N_QUBITS, "kubit indeksi araligi disinda");
    constexpr int STRIDE = 1 << K;

x_pair_loop:
    for (int j = 0; j < N_PAIR; ++j) {
#pragma HLS PIPELINE II = 1
        const int i0 = pair_index(j, K);
        const int i1 = i0 | STRIDE;
        const amp_t t = sv[i0];
        sv[i0] = sv[i1];
        sv[i1] = t;
    }
}

/// CNOT: kontrol C, hedef T (FR-002).
///
/// Kontrol biti 1 olan indekslerde hedef biti takas edilir. Her çift YALNIZCA
/// BİR KEZ ziyaret edilir — `i`'nin hedef biti 0 olan yarısı taranır.
template <int C, int T>
inline void apply_cnot(amp_t sv[N_AMP]) {
    static_assert(C >= 0 && C < N_QUBITS, "kontrol kubiti araligi disinda");
    static_assert(T >= 0 && T < N_QUBITS, "hedef kubiti araligi disinda");
    static_assert(C != T, "kontrol ve hedef ayni olamaz");
    constexpr int T_STRIDE = 1 << T;

cnot_pair_loop:
    for (int j = 0; j < N_PAIR; ++j) {
#pragma HLS PIPELINE II = 1
        const int i0 = pair_index(j, T);   // hedef biti 0
        if ((i0 >> C) & 1) {
            const int i1 = i0 | T_STRIDE;
            const amp_t t = sv[i0];
            sv[i0] = sv[i1];
            sv[i1] = t;
        }
    }
}

/// PAYLAŞILAN RX birimi — `k` ÇALIŞMA ZAMANI parametresi.
///
/// ⚠️ Bu, R-7'nin bilinçli olarak kaçındığı şeydir. Gerekçesi şuydu: HLS
/// `ARRAY_PARTITION`'lı diziye hangi parçadan erişildiğini derleme zamanında
/// çözemezse bütün erişimleri seri hale getirir. O gerekçe bir HİPOTEZDİ ve
/// hiç sınanmamıştı.
///
/// Sınanmasının nedeni ölçüm: `template <int K>` sürümü 16 ayrı örnek
/// doğuruyor ve bunlar **45.114 LUT** tutuyor — kalan bütçenin %57'si. Tek
/// birim ~3k olmalı. Karşılığında II bozulabilir; RX toplam gecikmenin ~%19'u
/// olduğu için 16× bozulma toplamı ~3× kötüleştirir.
///
/// Geri dönüş tek satır: `apply_mixer_layer` içinde `mixer_unroll<0>::run`
/// çağrısına dönmek yeterli — şablon sürümü aşağıda duruyor.
inline void apply_rx_dyn(amp_t sv[N_AMP], int k, real_t cos_half, real_t sin_half) {
    const int stride = 1 << k;
rx_dyn_pair_loop:
    for (int j = 0; j < N_PAIR; ++j) {
#pragma HLS PIPELINE II = 1
        // Farkli j degerleri FARKLI ciftlere dokunur; yinelemeler arasinda
        // gercek bir bagimlilik YOKTUR. HLS bunu kanitlayamadigi icin
        // oku-degistir-yaz zincirini tek kombinasyonel parcada tutuyordu:
        //   "Cannot meet target clock period from 'load' ... to 'store'
        //    (combination delay: 24.0859 ns) to honor II or Latency constraint"
        // Bu pragma bagimsizligi BILDIRIR, boylece HLS load ile store arasina
        // kayit koyabilir.
#pragma HLS DEPENDENCE variable = sv type = inter dependent = false
        const int dusuk = j & (stride - 1);
        const int yuksek = j >> k;
        const int i0 = (yuksek << (k + 1)) | dusuk;
        const int i1 = i0 | stride;

        const real_t ar = sv[i0].re, ai = sv[i0].im;
        const real_t br = sv[i1].re, bi = sv[i1].im;

        sv[i0].re = cos_half * ar + sin_half * bi;
        sv[i0].im = cos_half * ai - sin_half * br;
        sv[i1].re = cos_half * br + sin_half * ai;
        sv[i1].im = cos_half * bi - sin_half * ar;
    }
}

// --- Şablon sürümü: 16 ayrı örnek (ölçüm için saklanıyor) -------------------
// `k` derleme zamanı sabiti olur, HLS partition'ı çözebilir; bedeli 16 kopya.
template <int K>
struct mixer_unroll {
    static void run(amp_t sv[N_AMP], real_t c, real_t s) {
        apply_rx<K>(sv, c, s);
        mixer_unroll<K + 1>::run(sv, c, s);
    }
};

template <>
struct mixer_unroll<N_QUBITS> {
    static void run(amp_t*, real_t, real_t) {}
};

/// Karıştırıcı: her kübite RX(2*beta).  exp(-i*beta*X) = RX(2*beta).
///
/// ŞU AN: paylaşılan birim (tek örnek, çalışma zamanı k).
/// Geri dönmek için: `mixer_unroll<0>::run(sv, cos_beta, sin_beta);`
inline void apply_mixer_layer(amp_t sv[N_AMP], real_t cos_beta, real_t sin_beta) {
mixer_loop:
    for (int k = 0; k < N_QUBITS; ++k) {
        apply_rx_dyn(sv, k, cos_beta, sin_beta);
    }
}

}  // namespace qir
