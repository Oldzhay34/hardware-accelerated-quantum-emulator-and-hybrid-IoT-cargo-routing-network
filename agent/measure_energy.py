"""Kart enerji ölçümü — görevler T049–T050 (kart-enerji-protokolu v1.0).

# PYTHON 3.6 UYUMU ZORUNLU — KARTTA koşar. ⛔ `sudo` ile koşulmalı.

Delta yöntemi (FR-009c/d), dizüstü ölçümüyle AYNI yöntem: her seri
[boş BOS_S] → [yük YUK_S]. Güç INA219'dan, ayrı bir süreçte, PERIYOT_S
aralıkla örneklenir; pencere ortalaması yalnız o pencerenin örneklerinden.

Seriler (protokol §5, sıra SABİT: F2, P2, F2, P2):
  F2 — PL: `qir_kernel`, p=2, TAM çağrı (kodla + 1.095 yazma + koş + oku);
       her koşum C-sim bit deseniyle karşılaştırılır (gecikme protokolünün
       `seri_kos`'u — AYNI kod).
  P2 — PS: aynı algoritma kartın ARM'ında (`bench_kernel`, float, -O3),
       `beklenen_deger` denetlenir.

Kullanım (kartta; bağlantı düşse de sürsün diye nohup):
    sudo nohup python3 -m agent.measure_energy --bit qir_20260920_d350605.bit \\
        --reference reference_20260915_c6ad872_p2_n5 --beklenen-bits 3204875187 \\
        --arm-bench ./bench_float_arm --arm-beklenen -3950.990722656 \\
        --kalibrasyon kalibrasyon-1.json --besleme REG \\
        --cikti kart-enerji.json > kart-enerji.log 2>&1 &
"""
# PYTHON 3.6 UYUMU ZORUNLU (yukarı bakın)
import argparse
import hashlib
import json
import re
import subprocess
import sys
import time

from agent import ina219 as ina

PROTOKOL_SURUMU = "kart-enerji-protokolu v1.0"

# --- protokol v1.0 sabitleri ----------------------------------------------
BOS_S = 170.0                   # §5
YUK_S = 170.0                   # §5 — FR-009d: ≥ 60 sn
PERIYOT_S = 0.2                 # §3 — 5 Hz
MIN_ORNEK_ORANI = 0.9           # §7 — pencere örnek sayısı ≥ beklenenin %90'ı
SIRA = ("F2", "P2", "F2", "P2") # §5
ARM_ISINMA = 3                  # §5 — gecikme protokolüyle aynı
FCLK_TOLERANS = 0.01            # §7


class SeriGecersiz(RuntimeError):
    """§7: seriyi geçersiz kılan durum."""


# =========================================================================
# Saf yardımcılar — kart gerekmez
# =========================================================================
def kalibrasyonlari_denetle(kayitlar, simdi_unix):
    """§4 / FR-010: her kalibrasyon geçmiş (< %5) ve ölçümden ÖNCE alınmış olmalı."""
    if not kayitlar:
        raise SeriGecersiz("kalibrasyon kaydi yok (FR-010)")
    for k in kayitlar:
        if not (k.get("gecti") and k["sapma_yuzde"] < 5.0):
            raise SeriGecersiz("kalibrasyon gecmedi: sapma %{:.2f}".format(k["sapma_yuzde"]))
        if k["zaman_damgasi_unix"] >= simdi_unix:
            raise SeriGecersiz("kalibrasyon olcumden ONCE degil (FR-010)")
    return max(k["sapma_yuzde"] for k in kayitlar)


def bench_ciktisi_coz(metin):
    """`bench_kernel` çıktısı → {kosum_sayisi, isinma, beklenen_deger, medyan_ms}."""
    def bul(desen):
        m = re.search(desen, metin)
        return m.group(1) if m else None
    k = bul(r"kosum_sayisi\s*:\s*(\d+)\s*\(isinma (\d+)")
    return {
        "kosum_sayisi": int(k) if k is not None else None,
        "isinma": int(bul(r"isinma (\d+) haric")) if bul(r"isinma (\d+) haric") else None,
        "beklenen_deger": bul(r"beklenen_deger\s*:\s*(\S+)"),
        "medyan_ms": float(bul(r"medyan\s*:\s*([\d.]+)")) if bul(r"medyan\s*:\s*([\d.]+)") else None,
    }


def pencere_denetle(ozet, ad):
    """§7: yeterli örnek, doyma yok, taşma yok."""
    beklenen = ozet["sure_s"] / PERIYOT_S
    if ozet["n"] == 0 or ozet["n"] < MIN_ORNEK_ORANI * beklenen:
        raise SeriGecersiz("{} penceresinde {} ornek < %{:.0f} x {:.0f}".format(
            ad, ozet["n"], MIN_ORNEK_ORANI * 100, beklenen))
    if ozet["doygun_ornek"]:
        raise SeriGecersiz("{} penceresinde {} doymus ornek".format(ad, ozet["doygun_ornek"]))
    if ozet["ovf_ornek"]:
        raise SeriGecersiz("{} penceresinde {} OVF ornegi".format(ad, ozet["ovf_ornek"]))


def seri_sonucu(ornekler, bos_aralik, yuk_aralik, kosum_sayisi):
    bos = ina.pencere_ozeti(ornekler, *bos_aralik)
    yuk = ina.pencere_ozeti(ornekler, *yuk_aralik)
    pencere_denetle(bos, "bos")
    pencere_denetle(yuk, "yuk")
    if yuk["ort_guc_w"] <= bos["ort_guc_w"]:
        raise SeriGecersiz("P_yuk {:.4f} <= P_bos {:.4f} W".format(
            yuk["ort_guc_w"], bos["ort_guc_w"]))
    e = ina.enerji_hesabi(bos, yuk, yuk_aralik[1] - yuk_aralik[0], kosum_sayisi)
    return bos, yuk, e


# =========================================================================
# Kart tarafı
# =========================================================================
def _sha256(yol):
    h = hashlib.sha256()
    with open(yol, "rb") as f:
        for parca in iter(lambda: f.read(1 << 20), b""):
            h.update(parca)
    return h.hexdigest()


def _oku(yol):
    try:
        with open(yol) as f:
            return f.read().strip()
    except (IOError, OSError):
        return None


def yuk_f2(kart, girdi, beklenen_bits):
    """PL yükü: gecikme protokolünün `seri_kos`'u (ısınma + YUK_S döngü, bit bit)."""
    from agent import measure_latency as ml
    kosumlar, sicaklik, zaman_asimi = ml.seri_kos(kart, girdi, True, beklenen_bits,
                                                  sure_s=YUK_S)
    if zaman_asimi:
        raise SeriGecersiz("{} zaman asimi (§7)".format(zaman_asimi))
    t_cek = [k["t_cekirdek_s"] for k in kosumlar]
    return ml.ISINMA + len(kosumlar), {
        "isinma": ml.ISINMA, "olculen_kosum": len(kosumlar),
        "t_cekirdek": ml.olcum_serisi("n16_p2_fpga_enerji", "cekirdek", t_cek),
        "sicakliklar": sicaklik}


def yuk_p2(bench, reference, arm_beklenen):
    """PS yükü: ARM'da aynı algoritma, YUK_S saniye."""
    p = subprocess.run([bench, "--reference", reference, "--saniye", str(int(YUK_S)),
                        "--isinma", str(ARM_ISINMA)],
                       stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                       universal_newlines=True)
    c = bench_ciktisi_coz(p.stdout)
    if p.returncode != 0 or c["kosum_sayisi"] is None:
        raise SeriGecersiz("bench_kernel basarisiz (kod {})".format(p.returncode))
    if c["beklenen_deger"] != arm_beklenen:
        raise SeriGecersiz("ARM beklenen_deger {} != {}".format(c["beklenen_deger"],
                                                              arm_beklenen))
    return c["kosum_sayisi"] + ARM_ISINMA, {"bench": c, "ham_cikti": p.stdout}


def main(argv=None):
    ap = argparse.ArgumentParser(description="Kart enerji olcumu (kart-enerji-protokolu v1.0)")
    ap.add_argument("--bit", required=True)
    ap.add_argument("--reference", required=True, help="taban ad (.json'suz)")
    ap.add_argument("--beklenen-bits", type=int, required=True)
    ap.add_argument("--arm-bench", required=True, help="kartta derlenmis bench_kernel (float)")
    ap.add_argument("--arm-beklenen", required=True, help="ARM float beklenen_deger metni")
    ap.add_argument("--kalibrasyon", nargs="+", required=True)
    ap.add_argument("--besleme", required=True, help="JP5 duzeni (REG)")
    ap.add_argument("--cikti", required=True)
    a = ap.parse_args(argv)

    from pynq.ps import Clocks
    from agent import board as bd
    from agent import measure_latency as ml
    from agent.run_board import _param_bul

    kal = []
    for y in a.kalibrasyon:
        with open(y) as f:
            kal.append(json.load(f))
    en_buyuk_sapma = kalibrasyonlari_denetle(kal, time.time())

    with open(a.reference + ".json") as f:
        ref = json.load(f)
    p = int(ref["p"])
    girdi = (ref["ising_h"], ref["ising_J"],
             [_param_bul(ref["params"], u"γ", r) for r in range(p)],
             [_param_bul(ref["params"], u"β", r) for r in range(p)], p)

    kart = bd.Kart(a.bit).yukle()
    i2c = ina.INA219()
    yap_bas = i2c.yapilandir()
    i2c.kapat()
    time.sleep(0.5)

    ornek_dosyasi = a.cikti.rsplit(".", 1)[0] + ".ornekler.csv"
    kosul = {"besleme": a.besleme, "bitstream": a.bit, "bitstream_sha256": _sha256(a.bit),
             "arm_bench": a.arm_bench, "arm_bench_sha256": _sha256(a.arm_bench),
             "fclk_bas_mhz": kart.olculen_fclk, "boot_id": _oku("/proc/sys/kernel/random/boot_id"),
             "kart_saati": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
             "ina219_yapilandirma_bas": "0x{:04X}".format(yap_bas),
             "r_sont_nominal_ohm": ina.R_SONT_OHM, "ornek_periyodu_s": PERIYOT_S}
    cikti = {"ne": "Kart enerji olcumu (US3, T049-T050)", "protokol_surumu": PROTOKOL_SURUMU,
             "alet": "INA219-0.1ohm", "kapsam": "tum-kart", "yontem": "delta (FR-009c)",
             "kalibrasyon": kal, "kalibrasyon_en_buyuk_sapma_yuzde": en_buyuk_sapma,
             "kosullar": kosul, "ornek_dosyasi": ornek_dosyasi, "seriler": [],
             "gecerli": False, "gecersizlik_nedeni": None}

    orn = ina.Ornekleyici(ornek_dosyasi, PERIYOT_S).basla()
    araliklar = []
    try:
        for i, ad in enumerate(SIRA):
            kayit = {"sira": i, "ad": ad, "taraf": "fpga" if ad == "F2" else "ps",
                     "sicaklik_bas_C": ml.xadc_sicaklik(), "yuk_bas": ml.yuk_ortalamasi()}
            print("{} {}: bos {} sn".format(i, ad, BOS_S)); sys.stdout.flush()
            b0 = time.monotonic(); time.sleep(BOS_S); b1 = time.monotonic()
            print("{} {}: yuk".format(i, ad)); sys.stdout.flush()
            y0 = time.monotonic()
            if ad == "F2":
                n, is_yuku = yuk_f2(kart, girdi, a.beklenen_bits)
            else:
                n, is_yuku = yuk_p2(a.arm_bench, a.reference, a.arm_beklenen)
            y1 = time.monotonic()
            kayit.update({"bos_aralik": [b0, b1], "yuk_aralik": [y0, y1], "kosum_sayisi": n,
                          "is_yuku": is_yuku, "sicaklik_son_C": ml.xadc_sicaklik()})
            araliklar.append(kayit)
            cikti["seriler"].append(kayit)
        fclk_son = float(Clocks.fclk0_mhz)
        kosul["fclk_son_mhz"] = fclk_son
        if abs(fclk_son - kart.fclk_mhz) / kart.fclk_mhz > FCLK_TOLERANS:
            raise SeriGecersiz("olcum sonunda FCLK0 {:.3f} MHz (§7)".format(fclk_son))
    except (SeriGecersiz, ml.SeriGecersiz) as e:
        cikti["gecersizlik_nedeni"] = str(e)
    finally:
        orn.durdur()

    i2c = ina.INA219()
    yap_son = i2c.oku(ina.YAZMAC_YAPILANDIRMA)
    i2c.kapat()
    kosul["ina219_yapilandirma_son"] = "0x{:04X}".format(yap_son)
    if yap_son != yap_bas and cikti["gecersizlik_nedeni"] is None:
        cikti["gecersizlik_nedeni"] = "INA219 yapilandirmasi olcum sirasinda degisti"

    ornekler = ina.Ornekleyici.oku(ornek_dosyasi)
    for k in araliklar:
        try:
            bos, yuk, e = seri_sonucu(ornekler, k["bos_aralik"], k["yuk_aralik"],
                                      k["kosum_sayisi"])
            k.update({"bos": bos, "yuk": yuk, "enerji": e, "gecerli": True})
        except SeriGecersiz as hata:
            k.update({"gecerli": False, "neden": str(hata)})
            if cikti["gecersizlik_nedeni"] is None:
                cikti["gecersizlik_nedeni"] = "{} {}: {}".format(k["sira"], k["ad"], hata)
    cikti["gecerli"] = (cikti["gecersizlik_nedeni"] is None
                        and len(araliklar) == len(SIRA))
    with open(a.cikti, "w") as f:
        json.dump(cikti, f)
    for k in araliklar:
        if k.get("gecerli"):
            e = k["enerji"]
            print("{} {}: P_bos {:.4f} W, P_yuk {:.4f} W, dP {:.4f} W, N {}, {:.5f} J/kosum".format(
                k["sira"], k["ad"], e["bos_guc_w"], e["yuk_guc_w"], e["guc_farki_w"],
                e["kosum_sayisi"], e["enerji_j_kosum"]))
    print("bitti: gecerli={} neden={} -> {}".format(cikti["gecerli"],
                                                   cikti["gecersizlik_nedeni"], a.cikti))
    return 0 if cikti["gecerli"] else 1


if __name__ == "__main__":
    sys.exit(main())
