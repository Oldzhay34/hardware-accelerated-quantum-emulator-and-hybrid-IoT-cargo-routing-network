"""INA219 kalibrasyonu — görev T048 (kart-enerji-protokolu §4, SC-005, FR-010).

# PYTHON 3.6 UYUMU ZORUNLU — KARTTA koşar. ⛔ `sudo` (bitstream yüklenir).

Bilinen bir yükte INA219'un okuduğu güç, multimetreyle bağımsız ölçülen
güçle karşılaştırılır. Sapma **< %5** olmalı; değilse o aletle alınan hiçbir
enerji ölçümü geçerli sayılmaz (data-model §3b).

Referans (multimetre değerleri komut satırından verilir, ölçümden ÖNCE okunur):
  --direnc-ohm R --gerilim-v V   →  bilinen = V² / R   (R kart kapalıyken, V yük altında)
  --akim-ma I    --gerilim-v V   →  bilinen = V × I

Kullanım (kartta):
    sudo python3 -m agent.calibrate_ina219 --bit qir_20260920_d350605.bit \\
        --direnc-ohm 99.6 --gerilim-v 4.981 \\
        --duzen "3.3V (VCC sutunu) -> VIN+ ; VIN- -> 200 ohm || 220 ohm -> GND" \\
        --multimetre "model, kademeler" --cikti kalibrasyon-1.json
"""
# PYTHON 3.6 UYUMU ZORUNLU (yukarı bakın)
import argparse
import json
import sys
import time

from agent import ina219 as ina

SURE_S = 30.0                   # protokol §4: 30 sn ortalama
PERIYOT_S = 0.2                 # protokol §3: 5 Hz (ölçümle aynı örnekleyici)


def me_surum():
    """Protokol sürümü TEK yerde: measure_energy.PROTOKOL_SURUMU."""
    from agent import measure_energy as me
    return me.PROTOKOL_SURUMU


def bilinen_yuk(a):
    if a.akim_ma is not None:
        return a.gerilim_v * a.akim_ma * 1e-3, "V x I (multimetre, ardisik)"
    return a.gerilim_v ** 2 / a.direnc_ohm, "V^2 / R (multimetre; R kart kapaliyken)"


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

    if not a.yuklu:
        from agent import board as bd
        bd.Kart(a.bit).yukle()

    i2c = ina.INA219()
    geri = i2c.yapilandir()
    i2c.kapat()
    time.sleep(0.5)                                  # ilk dönüşümler tamamlansın

    ornek_dosyasi = a.cikti.rsplit(".", 1)[0] + ".ornekler.csv"
    orn = ina.Ornekleyici(ornek_dosyasi, PERIYOT_S).basla()
    t0 = time.monotonic()
    time.sleep(a.sure)
    t1 = time.monotonic()
    orn.durdur()
    ozet = ina.pencere_ozeti(ina.Ornekleyici.oku(ornek_dosyasi), t0, t1)

    bilinen, yontem = bilinen_yuk(a)
    ref_akim = (a.akim_ma * 1e-3) if a.akim_ma is not None else a.gerilim_v / a.direnc_ohm
    kayit = ina.kalibrasyon_kaydi(
        bilinen, ozet["ort_guc_w"], time.strftime("%Y-%m-%dT%H:%M:%S%z"),
        zaman_damgasi_unix=time.time(), boot_id=_boot_id(),
        yontem=yontem, duzen=a.duzen, multimetre=a.multimetre,
        referans={"gerilim_v": a.gerilim_v, "direnc_ohm": a.direnc_ohm,
                  "akim_ma": a.akim_ma, "akim_a_turetilen": ref_akim},
        okunan={"gerilim_v": ozet["ort_gerilim_v"], "akim_a": ozet["ort_akim_a"]},
        gerilim_sapma_yuzde=(ozet["ort_gerilim_v"] - a.gerilim_v) / a.gerilim_v * 100.0,
        akim_sapma_yuzde=(ozet["ort_akim_a"] - ref_akim) / ref_akim * 100.0,
        r_sont_nominal_ohm=ina.R_SONT_OHM,
        ina219_yapilandirma="0x{:04X}".format(geri),
        pencere=ozet, ornek_dosyasi=ornek_dosyasi,
        protokol_surumu=me_surum())
    with open(a.cikti, "w") as f:
        json.dump(kayit, f, indent=1)
    print("bilinen {:.4f} W, okunan {:.4f} W -> sapma %{:.2f} ({}); "
          "gerilim %{:+.2f}, akim %{:+.2f}; {} ornek -> {}".format(
              bilinen, ozet["ort_guc_w"], kayit["sapma_yuzde"],
              "GECTI" if kayit["gecti"] else "KALDI",
              kayit["gerilim_sapma_yuzde"], kayit["akim_sapma_yuzde"], ozet["n"], a.cikti))
    return 0 if kayit["gecti"] else 1


if __name__ == "__main__":
    sys.exit(main())
