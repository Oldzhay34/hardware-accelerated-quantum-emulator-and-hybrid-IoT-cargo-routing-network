"""INA219 kalibrasyonu — görev T048 (kart-enerji-protokolu §4, §11, §12; SC-005, FR-010).

# PYTHON 3.6 UYUMU ZORUNLU — KARTTA koşar. ⛔ `sudo` (bitstream yüklenir).

Bilinen bir yükte INA219'un okuduğu güç, multimetreyle bağımsız ölçülen
güçle karşılaştırılır. Üç rol (v1.2 §12):

  nominal    — şönt 0,1 Ω kabul edilir; sapma < %5 (v1.0/v1.1 yöntemi).
  katsayi    — ETKİN şönt direnci belirlenir: art arda N pencere, her biri
               R_etkin = (INA219'un gördüğü şönt gerilimi) / (bağımsız akım);
               pencereler arası yayılım < %1 olmalı ("kararlı").
  dogrulama  — katsayi'dan gelen R_etkin ile, FARKLI bir yükte; sapma < %5.

Referans (multimetre değerleri komut satırından verilir, ölçümden ÖNCE okunur):
  --direnc-ohm R --gerilim-v V   →  bilinen = V² / R   (R ağ yalıtılmışken, V yük altında)
  --akim-ma I    --gerilim-v V   →  bilinen = V × I

Kullanım (kartta):
    sudo python3 -m agent.calibrate_ina219 --yuklu --rol katsayi \\
        --direnc-ohm 104.7 --gerilim-v 3.28 \\
        --duzen "3.3V (VCC sutunu) -> VIN+ ; VIN- -> 200 ohm || 220 ohm -> GND" \\
        --multimetre "model, kademeler" --cikti kalibrasyon-K4.json
"""
# PYTHON 3.6 UYUMU ZORUNLU (yukarı bakın)
import argparse
import json
import sys
import time

from agent import ina219 as ina

SURE_S = 30.0                   # protokol §4: 30 sn ortalama (pencere başına)
PERIYOT_S = 0.2                 # protokol §3: 5 Hz (ölçümle aynı örnekleyici)
KATSAYI_PENCERE = 3             # §12: katsayı için art arda 3 pencere
KATSAYI_YAYILIM_ESIK = 1.0      # §12: pencereler arası yayılım < %1
DOGRULAMA_MIN_MA = 10.0         # §12: doğrulama yükünde akım ≥ 10 mA


def me_surum():
    """Protokol sürümü TEK yerde: measure_energy.PROTOKOL_SURUMU."""
    from agent import measure_energy as me
    return me.PROTOKOL_SURUMU


def bilinen_yuk(a):
    if a.akim_ma is not None:
        return a.gerilim_v * a.akim_ma * 1e-3, "V x I (multimetre, ardisik)"
    return a.gerilim_v ** 2 / a.direnc_ohm, "V^2 / R (multimetre; R ag yalitilmisken)"


def katsayi_ozeti(pencere_akimlari_nominal_a, ref_akim_a):
    """§12: pencere başına etkin şönt, ortalaması ve yayılımı (saf; testli)."""
    r = [ina.etkin_sont_ohm(i, ref_akim_a) for i in pencere_akimlari_nominal_a]
    ort = sum(r) / len(r)
    yayilim = (max(r) - min(r)) / ort * 100.0
    return {"r_etkin_pencere_ohm": r, "r_sont_etkin_ohm": ort,
            "yayilim_yuzde": yayilim, "kararli": yayilim < KATSAYI_YAYILIM_ESIK}


def _boot_id():
    try:
        with open("/proc/sys/kernel/random/boot_id") as f:
            return f.read().strip()
    except (IOError, OSError):
        return None


def main(argv=None):
    ap = argparse.ArgumentParser(description="INA219 kalibrasyonu (T048)")
    ap.add_argument("--bit", help="bitstream (EMIO I2C icin); --yuklu ile atlanir")
    ap.add_argument("--yuklu", action="store_true", help="bitstream zaten yuklu")
    ap.add_argument("--rol", choices=("nominal", "katsayi", "dogrulama"), default="nominal")
    ap.add_argument("--r-sont-ohm", type=float, default=None,
                    help="dogrulama: katsayi kaydindaki r_sont_etkin_ohm")
    ref = ap.add_mutually_exclusive_group(required=True)
    ref.add_argument("--direnc-ohm", type=float)
    ref.add_argument("--akim-ma", type=float)
    ap.add_argument("--gerilim-v", type=float, required=True)
    ap.add_argument("--duzen", required=True, help="baglanti duzeni (kayit icin)")
    ap.add_argument("--multimetre", required=True, help="model ve kademeler (kayit icin)")
    ap.add_argument("--sure", type=float, default=SURE_S)
    ap.add_argument("--cikti", required=True)
    a = ap.parse_args(argv)
    if not a.yuklu and not a.bit:
        ap.error("--bit ya da --yuklu gerekli (EMIO I2C bitstream ister)")
    if (a.rol == "dogrulama") != (a.r_sont_ohm is not None):
        ap.error("--r-sont-ohm yalniz ve mutlaka --rol dogrulama ile verilir")

    bilinen, yontem = bilinen_yuk(a)
    ref_akim = (a.akim_ma * 1e-3) if a.akim_ma is not None else a.gerilim_v / a.direnc_ohm
    if a.rol == "dogrulama" and ref_akim * 1000.0 < DOGRULAMA_MIN_MA:
        ap.error("dogrulama yukunde akim {:.1f} mA < {} mA (§12)".format(
            ref_akim * 1000.0, DOGRULAMA_MIN_MA))

    if not a.yuklu:
        from agent import board as bd
        bd.Kart(a.bit).yukle()

    i2c = ina.INA219()
    geri = i2c.yapilandir()
    i2c.kapat()
    time.sleep(0.5)                                  # ilk dönüşümler tamamlansın

    n_pencere = KATSAYI_PENCERE if a.rol == "katsayi" else 1
    ornek_dosyasi = a.cikti.rsplit(".", 1)[0] + ".ornekler.csv"
    orn = ina.Ornekleyici(ornek_dosyasi, PERIYOT_S).basla()
    t0 = time.monotonic()
    time.sleep(a.sure * n_pencere)
    orn.durdur()
    ornekler = ina.Ornekleyici.oku(ornek_dosyasi)
    pencereler = [ina.pencere_ozeti(ornekler, t0 + i * a.sure, t0 + (i + 1) * a.sure)
                  for i in range(n_pencere)]
    r_kullanilan = a.r_sont_ohm if a.rol == "dogrulama" else ina.R_SONT_OHM
    tum = ina.pencere_ozeti(ornekler, t0, t0 + a.sure * n_pencere, r_sont=r_kullanilan)
    tum_nominal = ina.pencere_ozeti(ornekler, t0, t0 + a.sure * n_pencere)

    kayit = ina.kalibrasyon_kaydi(
        bilinen, tum["ort_guc_w"], time.strftime("%Y-%m-%dT%H:%M:%S%z"),
        rol=a.rol, zaman_damgasi_unix=time.time(), boot_id=_boot_id(),
        yontem=yontem, duzen=a.duzen, multimetre=a.multimetre,
        referans={"gerilim_v": a.gerilim_v, "direnc_ohm": a.direnc_ohm,
                  "akim_ma": a.akim_ma, "akim_a_turetilen": ref_akim},
        okunan={"gerilim_v": tum["ort_gerilim_v"], "akim_a": tum["ort_akim_a"]},
        gerilim_sapma_yuzde=(tum["ort_gerilim_v"] - a.gerilim_v) / a.gerilim_v * 100.0,
        akim_sapma_yuzde=(tum["ort_akim_a"] - ref_akim) / ref_akim * 100.0,
        r_sont_nominal_ohm=ina.R_SONT_OHM, r_sont_kullanilan_ohm=r_kullanilan,
        nominal_ile={"okunan_w": tum_nominal["ort_guc_w"],
                     "akim_a": tum_nominal["ort_akim_a"]},
        ina219_yapilandirma="0x{:04X}".format(geri),
        pencere=tum, pencereler=pencereler, ornek_dosyasi=ornek_dosyasi,
        protokol_surumu=me_surum())
    if a.rol == "katsayi":
        kayit.update(katsayi_ozeti([p["ort_akim_a"] for p in pencereler], ref_akim))
        kayit["gecti"] = kayit["kararli"]       # katsayı: geçmek = kararlı olmak
    with open(a.cikti, "w") as f:
        json.dump(kayit, f, indent=1)

    if a.rol == "katsayi":
        print("katsayi: R_etkin {:.5f} ohm (pencereler {}), yayilim %{:.3f} -> {}; "
              "nominal ile sapma %{:.2f}; {} ornek -> {}".format(
                  kayit["r_sont_etkin_ohm"],
                  ", ".join("{:.5f}".format(r) for r in kayit["r_etkin_pencere_ohm"]),
                  kayit["yayilim_yuzde"], "KARARLI" if kayit["kararli"] else "KARARSIZ",
                  kayit["sapma_yuzde"], tum["n"], a.cikti))
    else:
        print("{}: R_sont {:.5f} ohm; bilinen {:.4f} W, okunan {:.4f} W -> sapma %{:.2f} ({}); "
              "gerilim %{:+.2f}, akim %{:+.2f}; {} ornek -> {}".format(
                  a.rol, r_kullanilan, bilinen, tum["ort_guc_w"], kayit["sapma_yuzde"],
                  "GECTI" if kayit["gecti"] else "KALDI",
                  kayit["gerilim_sapma_yuzde"], kayit["akim_sapma_yuzde"], tum["n"], a.cikti))
    return 0 if kayit["gecti"] else 1


if __name__ == "__main__":
    sys.exit(main())
