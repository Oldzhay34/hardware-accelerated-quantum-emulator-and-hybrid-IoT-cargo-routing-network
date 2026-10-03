"""Prizde/pilde kontrol ölçümünün özeti (priz-pil-kontrol-protokolu v1.0 §4–§6).

`priz_pil_kontrol.ps1` dört blok bitince çağırır. Karar kuralları (`karar`)
ve beklentiler (`beklentiler`) protokolle birlikte donar.

Kullanım:
    .venv\\Scripts\\python.exe scripts\\priz_pil_kontrol_ozet.py --dizin docs\\measurements --tarih 20261003 --git abc1234
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

KOK = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(KOK))
from services.common import stamp                              # noqa: E402

PROTOKOL = "priz-pil-kontrol-protokolu v1.0"
BLOKLAR = (("AC1", True), ("DC1", False), ("AC2", True), ("DC2", False))
TABAN = {"G": 0.997, "K": 3.273}          # T067 G32-2 (30 Eyl), adil-cpu-tabani (21 Eyl), ms
ESIK_KAYNAK = (0.90, 1.10)
ESIK_TABAN = (0.85, 1.15)


def _ms(s: float | None) -> float | None:
    return None if s is None else s * 1000.0


def g_oku(dizin: Path, tarih: str, git: str, ad: str) -> dict:
    yol = dizin / f"gpu-ayni-algoritma_{tarih}_{git}_kontrol{ad}_fp32_p2.json"
    d = json.loads(yol.read_text(encoding="utf-8"))
    s, ilk, son = d["seri"], d["ilk_ve_son"]["ilk_50_kosum"], d["ilk_ve_son"]["son_60_sn"]
    return {
        "dosya": yol.name, "gecerli": bool(d["gecerli"]), "kosum": s["kosum_sayisi"],
        "medyan_ms": _ms(s["medyan_s"]), "p25_ms": _ms(s["p25_s"]), "p75_ms": _ms(s["p75_s"]),
        "p99_ms": _ms(s["p99_s"]), "maks_ms": _ms(s["max_s"]),
        "ilk50_ms": _ms(ilk["medyan_s"]), "son60_ms": _ms(son["medyan_s"]),
        "son60_ilk50": son["medyan_s"] / ilk["medyan_s"],
        "plato_oturdu": bool(d["plato"]["oturdu"]),
        "sebekede_bas": d["kosullar_bas"]["guc"].get("sebekede"),
        "sebekede_son": d["kosullar_son"]["guc"].get("sebekede"),
        "gpu_bas": d["kosullar_bas"].get("gpu"), "gpu_son": d["kosullar_son"].get("gpu"),
    }


def k_oku(dizin: Path, tarih: str, git: str, ad: str) -> dict:
    yol = dizin / f"bench-kontrol_{tarih}_{git}_{ad}.txt"
    t = yol.read_text(encoding="utf-8-sig")

    def sayi(desen: str) -> float:
        m = re.search(desen, t)
        if not m:
            raise ValueError(f"{yol.name}: '{desen}' bulunamadi")
        return float(m.group(1))

    return {"dosya": yol.name, "kosum": int(sayi(r"kosum_sayisi\s*:\s*(\d+)")),
            "beklenen_deger": sayi(r"beklenen_deger\s*:\s*(\S+)"),
            "medyan_ms": sayi(r"medyan\s*:\s*([\d.]+)"),
            "p25_ms": sayi(r"p25=([\d.]+)"), "p75_ms": sayi(r"p75=([\d.]+)")}


def karar(ac: list[float], dc: list[float], taban: float) -> dict:
    """Protokol §5. ac/dc: [çift1, çift2] medyanları (ms)."""
    oran = [d / a for a, d in zip(ac, dc)]
    lo, hi = ESIK_KAYNAK
    if all(o < lo for o in oran) or all(o > hi for o in oran):
        kaynak = "VAR"
    elif all(lo <= o <= hi for o in oran):
        kaynak = "yok"
    else:
        kaynak = "belirsiz"
    rt = [a / taban for a in ac]
    tlo, thi = ESIK_TABAN
    if all(tlo <= r <= thi for r in rt):
        tab = "yeniden_uretildi"
    elif all(r < tlo for r in rt):
        tab = "yeniden_uretilemedi_bugun_hizli"
    else:
        tab = "belirsiz"
    return {"DC_AC": oran, "AC2_AC1": ac[1] / ac[0], "AC_taban": rt,
            "guc_kaynagi_etkisi": kaynak, "taban": tab}


def beklentiler(g: dict, k: dict, kg: dict, kk: dict) -> dict:
    """Protokol §6 (K1–K5)."""
    g_ac = [g["AC1"]["medyan_ms"], g["AC2"]["medyan_ms"]]
    k_ac = [k["AC1"]["medyan_ms"], k["AC2"]["medyan_ms"]]
    oranlar = [g[a]["son60_ilk50"] for a, _ in BLOKLAR]
    return {
        "K1": {"olcut": "G guc kaynagi etkisi yok (iki cift 0,90-1,10)",
               "deger": kg["DC_AC"], "tuttu": kg["guc_kaynagi_etkisi"] == "yok"},
        "K2": {"olcut": "G iki AC medyani <= 0,75 ms", "deger": g_ac,
               "tuttu": all(x <= 0.75 for x in g_ac)},
        "K3": {"olcut": "dort G serisinde son60/ilk50 < 1,3", "deger": oranlar,
               "tuttu": all(x < 1.3 for x in oranlar)},
        "K4": {"olcut": "K guc kaynagi etkisi yok", "deger": kk["DC_AC"],
               "tuttu": kk["guc_kaynagi_etkisi"] == "yok"},
        "K5": {"olcut": "K iki AC medyani <= 3,0 ms", "deger": k_ac,
               "tuttu": all(x <= 3.0 for x in k_ac)},
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dizin", required=True)
    ap.add_argument("--tarih", required=True)
    ap.add_argument("--git", required=True)
    ap.add_argument("--deneme", action="store_true", help="guc durumu denetlenmez")
    args = ap.parse_args()
    dizin = Path(args.dizin)

    g = {ad: g_oku(dizin, args.tarih, args.git, ad) for ad, _ in BLOKLAR}
    k = {ad: k_oku(dizin, args.tarih, args.git, ad) for ad, _ in BLOKLAR}
    sorunlar = []
    for ad, priz in BLOKLAR:
        if not g[ad]["gecerli"]:
            sorunlar.append(f"{ad}: G gecersiz")
        if abs(k[ad]["beklenen_deger"] - (-3950.989990234)) > 1e-9:
            sorunlar.append(f"{ad}: K beklenen_deger")
        if not args.deneme and (g[ad]["sebekede_bas"], g[ad]["sebekede_son"]) != (priz, priz):
            sorunlar.append(f"{ad}: G sirasinda guc durumu {g[ad]['sebekede_bas']}/{g[ad]['sebekede_son']}")

    kg = karar([g["AC1"]["medyan_ms"], g["AC2"]["medyan_ms"]],
               [g["DC1"]["medyan_ms"], g["DC2"]["medyan_ms"]], TABAN["G"])
    kk = karar([k["AC1"]["medyan_ms"], k["AC2"]["medyan_ms"]],
               [k["DC1"]["medyan_ms"], k["DC2"]["medyan_ms"]], TABAN["K"])
    bek = beklentiler(g, k, kg, kk)

    kayit = {"protokol": PROTOKOL, "deneme": bool(args.deneme), **stamp.stamp(),
             "gecerli": not sorunlar, "sorunlar": sorunlar, "taban_ms": TABAN,
             "G": g, "K": k, "karar_G": kg, "karar_K": kk, "beklentiler": bek}
    yol = dizin / f"priz-pil-kontrol_{args.tarih}_{args.git}.json"
    yol.write_text(json.dumps(kayit, ensure_ascii=False, indent=1), encoding="utf-8")

    print(f"{'blok':5s} {'G medyan':>9s} {'ilk50':>7s} {'son60':>7s} {'p99':>7s}  {'K medyan':>9s}")
    for ad, _ in BLOKLAR:
        print(f"{ad:5s} {g[ad]['medyan_ms']:9.4f} {g[ad]['ilk50_ms']:7.4f} {g[ad]['son60_ms']:7.4f} "
              f"{g[ad]['p99_ms']:7.3f}  {k[ad]['medyan_ms']:9.3f}")
    for ad, kr in (("G", kg), ("K", kk)):
        print(f"{ad}: DC/AC {[round(x, 3) for x in kr['DC_AC']]}  AC2/AC1 {kr['AC2_AC1']:.3f}  "
              f"AC/taban {[round(x, 3) for x in kr['AC_taban']]}  -> kaynak etkisi {kr['guc_kaynagi_etkisi']}, "
              f"taban {kr['taban']}")
    for h, v in bek.items():
        print(f"{h} {'TUTTU' if v['tuttu'] else 'TUTMADI'}: {v['olcut']}")
    print(f"gecerli: {not sorunlar} {sorunlar if sorunlar else ''}")
    print(f"yazildi: {yol}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
