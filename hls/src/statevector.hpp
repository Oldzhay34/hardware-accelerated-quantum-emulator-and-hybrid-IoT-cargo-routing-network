// Statevector bellek yerleşimi ve başlangıç durumu.
//
// Bellek bütçesi (HESAPLANAN, DS190): 65536 genlik x 36 bit = 64 BRAM36 bloğu
// = %45,7 (140 üzerinden). Vitis HLS 18Kb biriminde raporlar: **128 BRAM_18K**,
// bütçe 280 — 140'a bölmek doluluğu iki kat gösterir.
//
// ⚠️ Bu rakam DOĞRULANMAMIŞTIR. Kesin sayı yalnızca sentez raporundan okunur
// (SC-002, Anayasa Prensip II).
#pragma once

#include "qir_types.hpp"

namespace qir {

// Diziyi bildiren fonksiyonun İÇİNE konması gereken pragma'lar. HLS pragma'ları
// dizinin bildirildiği kapsamda olmak zorunda olduğu için burada makro olarak
// duruyorlar; `qir_kernel.cpp` bunları kullanır.
//
//   #pragma HLS ARRAY_PARTITION variable=sv cyclic factor=16 dim=1
//   #pragma HLS BIND_STORAGE     variable=sv type=RAM_2P impl=BRAM
//
// `m_axi` portu AÇILMAZ — statevector DDR'a taşamaz (Anayasa Prensip III,
// sözleşme maddesi K-1).

/// Başlangıç durumu: düzgün süperpozisyon. H^(x)n katmanının yerine geçer.
///
/// Neden H uygulanmıyor: n çift olduğu için 2^(-n/2) ikinin kuvvetidir ve
/// Q1.17'de tam temsil edilir. Böylece (a) bir kapı geçişi tasarruf edilir,
/// (b) başlangıçta hiç kuantalama hatası oluşmaz, (c) |0...0>'ın 1,0 genliği
/// hiç belleğe yazılmaz — Q1.17 aralığı [-1, 1) olduğu için bu önemlidir.
inline void init_uniform(amp_t sv[N_AMP]) {
init_loop:
    for (int i = 0; i < N_AMP; ++i) {
#pragma HLS PIPELINE II = 1
        sv[i].re = UNIFORM_AMP;
        sv[i].im = 0.0;
    }
}

/// Genlik çiftinin düşük indeksi: j'ye k konumunda 0 biti sokulur.
///
/// `scripts/banking_analysis.py` içindeki `pair_index` ile AYNI olmak
/// ZORUNDADIR — bankalama analizi ile uygulama aynı erişim desenini paylaşır,
/// yoksa analiz başka bir tasarımı ölçmüş olur.
inline int pair_index(int j, int k) {
    const int dusuk = j & ((1 << k) - 1);
    const int yuksek = j >> k;
    return (yuksek << (k + 1)) | dusuk;
}

}  // namespace qir
