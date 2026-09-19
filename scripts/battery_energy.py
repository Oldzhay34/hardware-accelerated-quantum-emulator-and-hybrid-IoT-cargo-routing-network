r"""Batarya kayitlarindan is yukunun enerji maliyetini hesaplar (Faz 5 / US3).

YONTEM -- delta: bos kayit ile yuk kaydinin FARKI alinir. Ekran, diskler ve
boştaki her sey iki olcumde de var oldugu icin sadelesir; geriye yalnizca
"isi yapmanin maliyeti" kalir. Bu, kart tarafinda uygulanan yontemle AYNIDIR,
dolayisiyla iki taraf kiyaslanabilir.

IKI BAGIMSIZ HESAP yapilir ve karsilastirilir:
  A) DischargeRate (mW) zamana gore integral
  B) RemainingCapacity (mWh) bas/son farki
Ikisi %10'dan fazla ayrisiyorsa olcume GUVENILMEZ -- batarya raporlamasi kaba
olabilir veya olcum cok kisa surmustur.

Kullanim:
    python scripts\battery_energy.py --bos bos.csv --yuk yuk.csv --kosum 3200
"""
from __future__ import annotations

import argparse
import csv
import json
import sys
from datetime import datetime
from pathlib import Path

KOK = Path(__file__).resolve().parents[1]


def yukle(yol: str) -> list[dict]:
    with open(yol, encoding="utf-8-sig", newline="") as f:
        satirlar = list(csv.DictReader(f))
    if not satirlar:
        raise SystemExit(f"HATA: {yol} bos")
    for s in satirlar:
        if str(s.get("PrizdeMi", "")).strip().lower() in ("true", "1"):
            raise SystemExit(
                f"HATA: {yol} icinde PRIZE TAKILI ornek var — bu kayit gecersiz.\n"
                "      Olcumu fisten cikmis halde tekrarla.")
    return satirlar


def coz(satirlar: list[dict]) -> dict:
    t = [datetime.fromisoformat(s["Zaman"]) for s in satirlar]
    mw = [float(s["DesarjMw"]) for s in satirlar]
    mwh = [float(s["KalanMwh"]) for s in satirlar]
    sure_sn = (t[-1] - t[0]).total_seconds()
    if sure_sn <= 0:
        raise SystemExit("HATA: kayit suresi sifir")

    # A) anlik gucun integrali -> mWh   (yamuk kurali)
    integral_mwh = 0.0
    for i in range(1, len(t)):
        dt_h = (t[i] - t[i - 1]).total_seconds() / 3600.0
        integral_mwh += (mw[i] + mw[i - 1]) / 2.0 * dt_h

    # B) kapasite farki
    kapasite_mwh = mwh[0] - mwh[-1]

    return {
        "ornek": len(satirlar),
        "sure_sn": round(sure_sn, 1),
        "ortalama_guc_mw": round(sum(mw) / len(mw), 1),
        "enerji_A_integral_mwh": round(integral_mwh, 2),
        "enerji_B_kapasite_mwh": round(kapasite_mwh, 2),
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--bos", required=True, help="bosta alinan kayit (CSV)")
    ap.add_argument("--yuk", required=True, help="yuk altinda alinan kayit (CSV)")
    ap.add_argument("--kosum", type=int, required=True,
                    help="yuk kaydi sirasinda tamamlanan kosum sayisi")
    ap.add_argument("--git-hash", default="unknown")
    a = ap.parse_args()

    bos = coz(yukle(a.bos))
    yuk = coz(yukle(a.yuk))

    print(f"{'':22} {'BOS':>16} {'YUK':>16}")
    for k in ("sure_sn", "ortalama_guc_mw", "enerji_A_integral_mwh", "enerji_B_kapasite_mwh"):
        print(f"{k:22} {bos[k]:>16} {yuk[k]:>16}")
    print()

    # Iki hesap birbirini dogruluyor mu?
    uyari = []
    for ad, d in (("bos", bos), ("yuk", yuk)):
        A, B = d["enerji_A_integral_mwh"], d["enerji_B_kapasite_mwh"]
        if A > 0 and B > 0:
            sapma = abs(A - B) / max(A, B) * 100
            print(f"{ad}: iki hesap arasi sapma %{sapma:.1f}")
            if sapma > 10:
                uyari.append(f"{ad} kaydinda iki enerji hesabi %{sapma:.0f} ayrisiyor")
        else:
            uyari.append(f"{ad} kaydinda hesaplardan biri sifir/negatif (A={A}, B={B})")

    # Sureler esit degilse gucten normalize et
    guc_farki_mw = yuk["ortalama_guc_mw"] - bos["ortalama_guc_mw"]
    yuk_sure_sn = yuk["sure_sn"]
    is_enerjisi_mwh = guc_farki_mw * (yuk_sure_sn / 3600.0)
    joule = is_enerjisi_mwh * 3.6          # 1 mWh = 3.6 J
    kosum_basina_j = joule / a.kosum if a.kosum else float("nan")

    print()
    print(f"yuk - bos guc farki    : {guc_farki_mw:.1f} mW")
    print(f"isin toplam enerjisi   : {is_enerjisi_mwh:.2f} mWh = {joule:.1f} J")
    print(f"kosum sayisi           : {a.kosum}")
    print(f"KOSUM BASINA ENERJI    : {kosum_basina_j:.4f} J")

    if guc_farki_mw <= 0:
        uyari.append("yuk altindaki guc bostakinden YUKSEK DEGIL - olcum gecersiz")

    if uyari:
        print()
        print("UYARILAR:")
        for u in uyari:
            print(f"  - {u}")

    ozet = {
        "bos": bos, "yuk": yuk,
        "guc_farki_mw": round(guc_farki_mw, 1),
        "is_enerjisi_mwh": round(is_enerjisi_mwh, 2),
        "is_enerjisi_j": round(joule, 1),
        "kosum": a.kosum,
        "kosum_basina_j": round(kosum_basina_j, 4),
        "uyarilar": uyari,
        "yontem": "batarya delta (yuk - bos), tum dizustu kapsami",
        "git_hash": a.git_hash,
    }
    yol = KOK / "docs" / "measurements" / f"cpu-enerji-batarya_{a.git_hash}.json"
    yol.write_text(json.dumps(ozet, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"\nyazildi: {yol.name}")
    return 1 if uyari else 0


if __name__ == "__main__":
    raise SystemExit(main())
