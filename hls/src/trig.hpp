// Tur (turn) -> (cos, sin) donusumu — SABIT NOKTA LUT.
//
// ⚠️ TARIHCE — bu dosya bir sentez raporundan sonra yeniden yazildi.
//
// Ilk surum `std::cos`/`std::sin` kullaniyordu ve argumani `double`'di.
// Uzerine "SENTEZ BORCU" notu dusulmustu ama bedeli TAHMIN EDILMEMISTI.
// Ilk sentez raporu olctu (docs/measurements/faz2-sentez.md):
//
//   sin_or_cos_double tek ornek : 85 DSP, 6.364 LUT, 5.562 FF, 8 BRAM_18K
//   ust seviye sonucu           : DSP %153, LUT %185 -> TASARIM SIGMADI
//
// Yani borc bir dipnot degil, tasarimin cipe sigmamasinin BIRINCI sebebiydi.
//
// Simdiki surum tablo okumasidir: hicbir aritmetik birim sentezlenmez.
#pragma once

#include <cstdint>

#include "qir_types.hpp"
#include "trig_lut.hpp"

namespace qir {

/// `turn` tur cinsinden faz (0 .. 2^PHASE_BITS-1  <->  0 .. 2*pi).
///
/// TEK tablo kullanilir: cos(x) = sin(x + ceyrek periyot). Kosinus, sinus
/// tablosundan indeks kaydirmayla okunur. Boylece tablo yariya iner VE
/// kadran/isaret mantiginin ince hatalari hic dogmaz — iki okuma da ayni
/// tablodan, ayni bicimde.
///
/// Faz akumulatoru PHASE_BITS (18) bit; tablo indeksi TRIG_LUT_BITS (13) bit.
/// Aradaki 5 bit atilir. Bu, faz cozunurlugunu 2^-13 tura dusurur ve fidelity'ye
/// etkisi OLCULMUSTUR: 12 bit -> 0,999950, 14 bit -> 0,999998
/// (docs/measurements/faz-bit-genisligi_*.json). 13 bit ikisinin arasinda ve
/// H esigini (>=0,999) rahat gecer.
inline void turn_to_cos_sin(phase_t turn, real_t& c, real_t& s) {
#pragma HLS INLINE
    constexpr int KAYDIR = PHASE_BITS - TRIG_LUT_BITS;      // 18 - 13 = 5
    constexpr unsigned MASKE = TRIG_LUT_N - 1;
    constexpr unsigned CEYREK = TRIG_LUT_N >> 2;            // +pi/2

    const unsigned idx_s = static_cast<unsigned>(
                               static_cast<uint64_t>(turn) >> KAYDIR) & MASKE;
    const unsigned idx_c = (idx_s + CEYREK) & MASKE;

    s = TRIG_SIN[idx_s];
    c = TRIG_SIN[idx_c];
}

}  // namespace qir

