"""`hls/src/trig_lut.hpp` uretir — sabit-nokta sinus tablosu.

NEDEN: ilk sentez raporu (docs/measurements/faz2-sentez.md) `trig.hpp`'nin
`std::cos/sin` cagrilarini tam bir CIFT DUYARLIKLI transandantal birim olarak
sentezledigini gosterdi: tek ornek 85 DSP + 6.364 LUT. DSP %153 ve LUT %185'in
ana kaynagi buydu.

Tablo DERLEME ZAMANINDA sabittir; HLS onu ROM olarak yerlestirir ve hicbir
aritmetik birim sentezlemez.

Tasarim:
  - TEK sinus tablosu. cos(x) = sin(x + ceyrek periyot) oldugu icin kosinus
    ayni tablodan indeks kaydirmayla okunur -> tablo yariya iner ve simetri/
    isaret mantiginin ince hatalari hic dogmaz.
  - 13 bit indeks = 8192 girdi x 18 bit = 147.456 bit ~ 8 BRAM_18K.
    (Cift duyarlikli birim de 8 BRAM_18K kullaniyordu; BRAM acisindan bedava.)
  - Faz cozunurlugu 2^-13 tur. Olculen etki: 12 bit -> 0,999950,
    14 bit -> 0,999998 (docs/measurements/faz-bit-genisligi_*.json).

Kullanim:
    .venv/Scripts/python.exe scripts/gen_trig_lut.py
"""
from __future__ import annotations

import io
import math
from pathlib import Path

LUT_BITS = 13
N = 1 << LUT_BITS
FRAC_BITS = 17                      # Q1.17
OLCEK = 1 << FRAC_BITS
UST = 1.0 - 1.0 / OLCEK             # ap_fixed<18,1> ust siniri (AP_SAT)


def q1_17(x: float) -> float:
    """real_t ile AYNI kuantalama: yakina yuvarla (yarim ise cifte) + doyur."""
    q = round(x * OLCEK)            # Python round = yarim ise cifte = AP_RND_CONV
    v = q / OLCEK
    return min(max(v, -1.0), UST)


def main() -> None:
    kok = Path(__file__).resolve().parents[1]
    yol = kok / "hls" / "src" / "trig_lut.hpp"

    degerler = [q1_17(math.sin(2.0 * math.pi * i / N)) for i in range(N)]
    azami_hata = max(abs(d - math.sin(2.0 * math.pi * i / N))
                     for i, d in enumerate(degerler))

    satirlar = []
    for i in range(0, N, 8):
        parca = ", ".join(f"{d: .8f}" for d in degerler[i:i + 8])
        satirlar.append(f"    {parca},")

    icerik = f"""// URETILMIS DOSYA -- ELLE DUZENLEME. Uretici: scripts/gen_trig_lut.py
//
// Sabit-nokta sinus tablosu. {N} girdi (13 bit indeks), Q1.17.
//
// Ilk sentez raporu `std::cos/sin`'in cift duyarlikli bir transandantal birim
// olarak sentezlendigini gosterdi (tek ornek 85 DSP + 6.364 LUT) ve tasarim
// cipe sigmadi. Bu tablo derleme zamaninda sabittir; HLS onu ROM olarak
// yerlestirir, hicbir aritmetik birim sentezlemez.
//
// TEK tablo: cos(x) = sin(x + ceyrek periyot) oldugu icin kosinus ayni
// tablodan indeks kaydirmayla okunur.
//
// Tablo kuantalama hatasi (azami): {azami_hata:.3e}  (1 LSB = {1.0/OLCEK:.3e})
#pragma once

#include "qir_types.hpp"

namespace qir {{

constexpr int TRIG_LUT_BITS = {LUT_BITS};
constexpr int TRIG_LUT_N    = 1 << TRIG_LUT_BITS;   // {N}

static const real_t TRIG_SIN[TRIG_LUT_N] = {{
{chr(10).join(satirlar)}
}};

}}  // namespace qir
"""
    io.open(yol, "w", encoding="ascii", newline="\n").write(icerik)
    print(f"Yazildi: {yol}")
    print(f"  girdi        : {N} ({LUT_BITS} bit indeks)")
    print(f"  bit/girdi    : 18 (Q1.17)")
    print(f"  toplam       : {N * 18:,} bit = {N * 18 / 18432:.0f} BRAM_18K")
    print(f"  azami hata   : {azami_hata:.3e}  (1 LSB = {1.0 / OLCEK:.3e})")
    print(f"  dosya boyutu : {yol.stat().st_size / 1024:.0f} KB")


if __name__ == "__main__":
    main()
