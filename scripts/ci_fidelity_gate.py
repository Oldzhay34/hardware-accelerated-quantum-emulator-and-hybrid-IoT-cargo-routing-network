"""CI regresyon kapisi — olculen fidelity referans degerlerden saptiysa BASARISIZ olur.

NEDEN AYRI BIR KAPI: testbench `return gecti_M ? 0 : 1` yapar, yani yalnizca
M esiginde (0,99) basarisiz olur. Olculen degerlerimiz 0,99997 mertebesinde;
fidelity 0,995'e cokse testbench yine "gecti" derdi ve regresyon fark
edilmezdi. Bu kapi referans degerlerle karsilastirir.

Cekirdek sabit-nokta (tamsayi) aritmetigi kullandigi icin cikti platformdan
bagimsiz olarak BIREBIR ayni olmalidir; tolerans yalnizca fidelity hesabindaki
double aritmetigi icindir.

Kullanim:
    python scripts/ci_fidelity_gate.py docs/measurements/csim-fidelity_*.json
"""
from __future__ import annotations

import glob
import json
import sys
from pathlib import Path

KOK = Path(__file__).resolve().parents[1]
REFERANS = KOK / "docs" / "measurements" / "baseline-fidelity.json"


def main(argv: list[str]) -> int:
    ref = json.loads(REFERANS.read_text(encoding="utf-8"))
    tol = float(ref["_tolerans"])
    beklenen = {(d["n"], d["p"]): float(d["fidelity"]) for d in ref["durumlar"]}

    yollar: list[str] = []
    for a in argv:
        yollar.extend(sorted(glob.glob(a)))
    if not yollar:
        print("HATA: hic olcum dosyasi bulunamadi", file=sys.stderr)
        return 2

    olculen: dict[tuple[int, int], tuple[float, str]] = {}
    for y in yollar:
        d = json.loads(Path(y).read_text(encoding="utf-8"))
        anahtar = (int(d["n_qubits"]), int(d["p"]))
        # Ayni durum birden fazla dosyada varsa en yenisi kazanir (glob sirali)
        olculen[anahtar] = (float(d["fidelity"]), Path(y).name)

    hata = 0
    print(f"{'durum':>10} {'beklenen':>14} {'olculen':>14} {'fark':>11}   sonuc")
    for anahtar in sorted(beklenen, reverse=True):
        n, p = anahtar
        ad = f"n={n} p={p}"
        if anahtar not in olculen:
            print(f"{ad:>10} {beklenen[anahtar]:14.9f} {'YOK':>14} {'-':>11}   EKSIK")
            hata += 1
            continue
        deger, dosya = olculen[anahtar]
        fark = deger - beklenen[anahtar]
        tamam = abs(fark) <= tol
        if not tamam:
            hata += 1
        print(f"{ad:>10} {beklenen[anahtar]:14.9f} {deger:14.9f} {fark:+11.2e}   "
              f"{'TAMAM' if tamam else 'SAPMA'}  ({dosya})")

    print()
    if hata:
        print(f"KAPI BASARISIZ: {hata} durum referanstan sapti veya eksik.")
        print(f"Tolerans: {tol:.1e}")
        print()
        print("Bu bir REGRESYONDUR. Sapma kasitliysa once NEDEN degistigini")
        print("docs/measurements/ altina yaz, sonra baseline-fidelity.json'u")
        print("guncelle. Once dosyayi guncelleyip sonra aciklama yazma.")
        return 1

    print(f"KAPI GECTI: {len(beklenen)} durumun {len(beklenen)}'i referansla uyusuyor.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
