"""6C / T073 — genişlik Pareto figürü (SVG), genislik-pareto_*.json'dan.

Bağımlılık yok (matplotlib kurulu değil ve bir figür için eklenmedi): SVG
elle üretilir, çıktı belirlenimcidir ve git'te okunabilir fark verir.

İki panel:
  (a) doğruluk–maliyet: x = BRAM_18K (csynth), y = 1 − fidelity (log).
      Çekirdek (C-sim, Qiskit'e karşı) ve Faz 2'nin sayısal modeli aynı x'te.
  (b) BRAM genişlikle: ölçülen toplam ve statevector, Faz 2'nin el hesabı
      (re+im tek 36-bit kelimede → 19. bitte ikiye katlanma) kesikli çizgiyle.

⛔ Rakam elle yazılmaz: her değer JSON'dan gelir. Yalnız Faz 2 hesabının
kuralı (memory-budget.md §3b) burada formül olarak durur — o bir ölçüm değil,
yanlışlanan bir öngörüdür ve öyle etiketlenir.

Kullanım:
    .venv\\Scripts\\python.exe scripts\\genislik_figur.py docs\\measurements\\genislik-pareto_<damga>.json
Çıktı: docs/figures/genislik-pareto_<json damgası>.svg
"""
from __future__ import annotations

import glob
import json
import math
import sys
from pathlib import Path

KOK = Path(__file__).resolve().parents[1]
BRAM_KAPASITE = 280          # XC7Z020 RAMB18 sayısı (olculen-degerler.md §3)
H_ESIGI, M_ESIGI = 0.999, 0.99
BITSTREAM_W = 18             # kartta koşan genişlik

# Renkler: ölçülen = mavi aile, öngörü/model = gri/turuncu kesikli
MUREKKEP, IKINCIL, IZGARA = "#1f2937", "#6b7280", "#e5e7eb"
OLCULEN, OLCULEN_ACIK = "#1d4ed8", "#60a5fa"
MODEL, ONGORU, ESIK = "#6b7280", "#c2410c", "#9ca3af"
FONT = "Helvetica, Arial, sans-serif"

GEN, YUK = 960, 470
PA = dict(x0=80, x1=450, y0=60, y1=360)     # panel a çizim alanı
PB = dict(x0=570, x1=930, y0=60, y1=360)    # panel b çizim alanı


def _ust(n: int) -> str:
    return "10" + str(n).translate(str.maketrans("-0123456789", "⁻⁰¹²³⁴⁵⁶⁷⁸⁹"))


def _metin(x, y, s, boy=12, renk=MUREKKEP, hiza="start", kalin=False, ek=""):
    k = ' font-weight="600"' if kalin else ""
    return (f'<text x="{x:.1f}" y="{y:.1f}" font-size="{boy}" fill="{renk}" '
            f'text-anchor="{hiza}"{k}{ek}>{s}</text>')


def _cizgi(x1, y1, x2, y2, renk, kalinlik=1.0, kesik=""):
    d = f' stroke-dasharray="{kesik}"' if kesik else ""
    return (f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" '
            f'stroke="{renk}" stroke-width="{kalinlik}"{d}/>')


def _yol(noktalar, renk, kalinlik=2.0, kesik=""):
    d = f' stroke-dasharray="{kesik}"' if kesik else ""
    p = " ".join(f"{'M' if i == 0 else 'L'}{x:.1f},{y:.1f}" for i, (x, y) in enumerate(noktalar))
    return f'<path d="{p}" fill="none" stroke="{renk}" stroke-width="{kalinlik}"{d}/>'


def _daire(x, y, renk, dolu=True, r=4.5):
    dolgu = renk if dolu else "#ffffff"
    return (f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{r}" fill="{dolgu}" '
            f'stroke="{renk}" stroke-width="1.8"/>')


def _kare(x, y, renk, a=8):
    return (f'<rect x="{x - a / 2:.1f}" y="{y - a / 2:.1f}" width="{a}" height="{a}" '
            f'fill="{renk}" stroke="{renk}" stroke-width="1"/>')


def panel_a(s: list[dict]) -> list[str]:
    x0, x1, y0, y1 = PA["x0"], PA["x1"], PA["y0"], PA["y1"]
    bx0, bx1, ly0, ly1 = 130, 250, -8, -1
    X = lambda b: x0 + (b - bx0) / (bx1 - bx0) * (x1 - x0)
    Y = lambda v: y1 - (math.log10(v) - ly0) / (ly1 - ly0) * (y1 - y0)
    o = [_metin(x0, 36, "(a) Doğruluk–maliyet: her nokta bir genlik genişliği", 14, kalin=True)]
    for d in range(ly0, ly1 + 1):
        o.append(_cizgi(x0, Y(10 ** d), x1, Y(10 ** d), IZGARA))
        o.append(_metin(x0 - 8, Y(10 ** d) + 4, _ust(d), 11, IKINCIL, "end"))
    for b in range(150, bx1 + 1, 25):
        o.append(_cizgi(X(b), y1, X(b), y1 + 5, IKINCIL))
        o.append(_metin(X(b), y1 + 19, b, 11, IKINCIL, "middle"))
    o.append(_cizgi(x0, y1, x1, y1, MUREKKEP))
    o.append(_cizgi(x0, y0, x0, y1, MUREKKEP))
    # eşikler
    for esik, ad in ((M_ESIGI, "M: F ≥ 0,99"), (H_ESIGI, "H: F ≥ 0,999")):
        o.append(_cizgi(x0, Y(1 - esik), x1, Y(1 - esik), ESIK, 1.2, "5,4"))
        o.append(_metin(x1 - 4, Y(1 - esik) - 5, ad, 11, IKINCIL, "end"))
    # model (kesikli, içi boş) ve çekirdek (dolu)
    m = [(X(r["BRAM_18K"]), Y(1 - r["model_fidelity_p2"])) for r in s]
    k = [(X(r["BRAM_18K"]), Y(1 - r["fidelity_p2"])) for r in s]
    o.append(_yol(m, MODEL, 1.6, "6,4"))
    o.extend(_daire(x, y, MODEL, dolu=False) for x, y in m)
    o.append(_yol(k, OLCULEN, 2.2))
    # etiketler noktanın SOLUNDA: çizgiler sağa-aşağı iniyor, sol taraf boş.
    # Son nokta hariç — orada model çizgisi soldan kesiyor, sağ taraf boş.
    for i, (r, (x, y)) in enumerate(zip(s, k)):
        o.append(_daire(x, y, OLCULEN))
        son = i == len(s) - 1
        o.append(_metin(x + 12 if son else x - 12, y + 4, f"{r['genislik_bit']} bit", 11.5,
                        OLCULEN, "start" if son else "end", kalin=True))
        if r["genislik_bit"] == BITSTREAM_W:
            o.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="9" fill="none" '
                     f'stroke="{OLCULEN}" stroke-width="1.2"/>')
            o.append(_metin(x - 12, y + 19, "(kartta koşan)", 10.5, OLCULEN, "end"))
    # eksen adları
    o.append(_metin((x0 + x1) / 2, y1 + 42, "BRAM_18K (Vitis HLS csynth; kapasite 280)",
                    12, MUREKKEP, "middle"))
    o.append(_metin(22, (y0 + y1) / 2, "1 − fidelity  (n=16, p=2; log)", 12, MUREKKEP,
                    "middle", ek=f' transform="rotate(-90 22 {(y0 + y1) / 2:.1f})"'))
    # açıklama kutusu (sol alt boş bölge)
    lx, ly = x0 + 14, y1 - 58
    o.append(f'<rect x="{lx - 8}" y="{ly - 16}" width="232" height="52" fill="#ffffff" '
             f'stroke="{IZGARA}"/>')
    o.append(_cizgi(lx, ly - 4, lx + 26, ly - 4, OLCULEN, 2.2))
    o.append(_daire(lx + 13, ly - 4, OLCULEN, r=3.5))
    o.append(_metin(lx + 34, ly, "çekirdek — C-sim, Qiskit'e karşı", 11))
    o.append(_cizgi(lx, ly + 20, lx + 26, ly + 20, MODEL, 1.6, "6,4"))
    o.append(_daire(lx + 13, ly + 20, MODEL, dolu=False, r=3.5))
    o.append(_metin(lx + 34, ly + 24, "Faz 2 sayısal modeli (format seçimi)", 11))
    return o


def panel_b(s: list[dict]) -> list[str]:
    x0, x1, y0, y1 = PB["x0"], PB["x1"], PB["y0"], PB["y1"]
    wx0, wx1, by0, by1 = 12, 26, 0, 320
    X = lambda w: x0 + (w - wx0) / (wx1 - wx0) * (x1 - x0)
    Y = lambda b: y1 - (b - by0) / (by1 - by0) * (y1 - y0)
    o = [_metin(x0, 36, "(b) BRAM genişlikle doğrusal — 19. bitte uçurum yok", 14, kalin=True)]
    for b in range(0, by1 + 1, 50):
        o.append(_cizgi(x0, Y(b), x1, Y(b), IZGARA))
        o.append(_metin(x0 - 8, Y(b) + 4, b, 11, IKINCIL, "end"))
    for w in range(14, wx1 + 1, 2):
        o.append(_cizgi(X(w), y1, X(w), y1 + 5, IKINCIL))
        o.append(_metin(X(w), y1 + 19, w, 11, IKINCIL, "middle"))
    o.append(_cizgi(x0, y1, x1, y1, MUREKKEP))
    o.append(_cizgi(x0, y0, x0, y1, MUREKKEP))
    # kapasite
    o.append(_cizgi(x0, Y(BRAM_KAPASITE), x1, Y(BRAM_KAPASITE), MUREKKEP, 1.2, "2,3"))
    o.append(_metin(x0 + 6, Y(BRAM_KAPASITE) - 6, f"XC7Z020 kapasitesi: {BRAM_KAPASITE}",
                    11, MUREKKEP))
    # Faz 2 el hesabı: re+im tek 36-bit kelime → 2W ≤ 36 ise 64 BRAM36, değilse 128
    # (memory-budget.md §3b), RAMB18 cinsinden 128 / 256. ÖNGÖRÜ, ölçüm değil.
    ongoru = lambda w: 128 if 2 * w <= 36 else 256
    o.append(_yol([(X(13), Y(ongoru(13))), (X(18.5), Y(128)), (X(18.5), Y(256)),
                   (X(25.5), Y(256))], ONGORU, 1.8, "7,4"))
    o.append(_metin(X(19.2), Y(256) - 7, "Faz 2 hesabı: 19. bitte ×2", 11, ONGORU))
    # ölçülen
    top = [(X(r["genislik_bit"]), Y(r["BRAM_18K"])) for r in s]
    sv = [(X(r["genislik_bit"]), Y(r["BRAM_statevector"])) for r in s]
    o.append(_yol(top, OLCULEN, 2.2))
    o.extend(_daire(x, y, OLCULEN) for x, y in top)
    o.append(_yol(sv, OLCULEN_ACIK, 2.0))
    o.extend(_kare(x, y, OLCULEN_ACIK) for x, y in sv)

    # Sayı etiketi noktanın üstünde; yalnız kesikli öngörü çizgisi noktanın
    # hemen üstünden geçiyorsa (30 bloktan yakın) altına alınır.
    def etiket(w, b, x, y, renk):
        alta = 0 < ongoru(w) - b < 30
        o.append(_metin(x, y + 18 if alta else y - 10, b, 10.5, renk, "middle"))

    for r, (x, y) in zip(s, top):
        etiket(r["genislik_bit"], r["BRAM_18K"], x, y, OLCULEN)
    for r, (x, y) in zip(s, sv):
        etiket(r["genislik_bit"], r["BRAM_statevector"], x, y, "#2563eb")
    o.append(_metin((x0 + x1) / 2, y1 + 42, "genlik genişliği W (bit; Q1.W−1)", 12,
                    MUREKKEP, "middle"))
    o.append(_metin(PB["x0"] - 50, (y0 + y1) / 2, "BRAM_18K", 12, MUREKKEP, "middle",
                    ek=f' transform="rotate(-90 {PB["x0"] - 50} {(y0 + y1) / 2:.1f})"'))
    # açıklama kutusu (sağ alt boş bölge)
    lx, ly = X(19.0), Y(78)
    o.append(f'<rect x="{lx - 8:.1f}" y="{ly - 16:.1f}" width="196" height="70" '
             f'fill="#ffffff" stroke="{IZGARA}"/>')
    o.append(_cizgi(lx, ly - 4, lx + 24, ly - 4, OLCULEN, 2.2))
    o.append(_daire(lx + 12, ly - 4, OLCULEN, r=3.5))
    o.append(_metin(lx + 32, ly, "toplam (ölçülen)", 11))
    o.append(_cizgi(lx, ly + 16, lx + 24, ly + 16, OLCULEN_ACIK, 2.0))
    o.append(_kare(lx + 12, ly + 16, OLCULEN_ACIK, 7))
    o.append(_metin(lx + 32, ly + 20, "statevector = 8W (ölçülen)", 11))
    o.append(_cizgi(lx, ly + 36, lx + 24, ly + 36, ONGORU, 1.8, "7,4"))
    o.append(_metin(lx + 32, ly + 40, "Faz 2 el hesabı (yanlışlandı)", 11))
    return o


def svg(veri: dict, kaynak: str) -> str:
    s = sorted(veri["satirlar"], key=lambda r: r["genislik_bit"])
    eksik = [r["genislik_bit"] for r in s if r.get("BRAM_statevector") is None
             or r.get("fidelity_p2") is None or r.get("model_fidelity_p2") is None]
    if eksik:
        raise SystemExit(f"eksik alan, W={eksik} — genislik_pareto.py ile yeniden üret")
    alt1 = (f"Kaynak: docs/measurements/{kaynak} (git {veri['git_hash']}, {veri['tarih']}) · "
            f"sabit: n=16, faz 18 bit, trig indeksi 13 bit")
    alt2 = ("Fidelity: C-sim, Qiskit Aer altın referansına karşı · BRAM: Vitis HLS csynth, "
            "xc7z020clg400-1; 18 bitte Vivado P&amp;R ile aynı (187)")
    o = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{GEN}" height="{YUK}" '
         f'viewBox="0 0 {GEN} {YUK}" font-family="{FONT}">',
         f'<rect width="{GEN}" height="{YUK}" fill="#ffffff"/>']
    o += panel_a(s) + panel_b(s)
    o.append(_metin(GEN / 2, YUK - 26, alt1, 10, IKINCIL, "middle"))
    o.append(_metin(GEN / 2, YUK - 11, alt2, 10, IKINCIL, "middle"))
    o.append("</svg>")
    return "\n".join(o) + "\n"


def main(argv: list[str]) -> int:
    # Dosya AÇIKÇA verilir: damgadaki git hash'i sıralanabilir değil, "en
    # yenisi"ni adla seçmek yanlış dosyayı çizebilir.
    if len(argv) != 2:
        adaylar = sorted(glob.glob(str(KOK / "docs" / "measurements" / "genislik-pareto_*.json")))
        raise SystemExit("kullanim: genislik_figur.py <genislik-pareto_*.json>\n  "
                         + "\n  ".join(Path(a).name for a in adaylar))
    yol = Path(argv[1])
    veri = json.loads(yol.read_text(encoding="utf-8"))
    damga = yol.stem.removeprefix("genislik-pareto_")
    cikti = KOK / "docs" / "figures" / f"genislik-pareto_{damga}.svg"
    cikti.parent.mkdir(exist_ok=True)
    cikti.write_text(svg(veri, yol.name), encoding="utf-8")
    print("yazildi:", cikti)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
