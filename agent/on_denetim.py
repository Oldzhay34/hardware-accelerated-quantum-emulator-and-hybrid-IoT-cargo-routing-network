"""Kör ön denetim — kart-enerji-protokolu v1.3 §13 (T046).

# PYTHON 3.6 UYUMU ZORUNLU — KARTTA koşar. ⛔ `sudo` ile koşulmalı.

INA219 kartın güç yoluna (JP5) girdikten sonra, ölçümden ÖNCE bir kez koşar:
bitstream yüklenir (EMIO I2C için; ölçümün boş durumuyla aynı), INA219
yapılandırılır ve geri okunur, ON_DENETIM_S saniye örneklenir. Yazdığı:
yalnız gerilim ve EVET/HAYIR. **Akım ve güç sayı olarak yazılmaz, örnekler
diske yazılmaz** — ön kayıtlı B1–B3 ölçümden önce görülmesin.

Kullanım (kartta):
    sudo python3 -m agent.on_denetim --bit qir_20260920_d350605.bit
"""
# PYTHON 3.6 UYUMU ZORUNLU (yukarı bakın)
import argparse
import sys
import time

from agent import ina219 as ina
from agent import measure_energy as me


def _ev(b):
    return "EVET" if b else "HAYIR"


def main(argv=None):
    ap = argparse.ArgumentParser(description="Kor on denetim (" + me.PROTOKOL_SURUMU + " §13)")
    ap.add_argument("--bit", required=True)
    a = ap.parse_args(argv)

    from agent import board as bd
    bd.Kart(a.bit).yukle()
    i2c = ina.INA219()
    yap = i2c.yapilandir()
    time.sleep(0.5)
    ornekler = []
    bitis = time.monotonic() + me.ON_DENETIM_S
    while time.monotonic() < bitis:
        s, b = i2c.ornek()
        ornekler.append((time.monotonic(), s, b))
        time.sleep(me.PERIYOT_S)
    i2c.kapat()

    k = me.on_denetim_karari(ornekler)
    print("yapilandirma geri okundu : 0x{:04X}".format(yap))
    print("ornek sayisi             : {}".format(k["ornek_sayisi"]))
    if k["ornek_sayisi"]:
        print("kart girisi (V)          : min {:.3f}, ort {:.3f}".format(
            k["min_gerilim_v"], k["ort_gerilim_v"]))
        print("gerilim >= {} V         : {}".format(me.MIN_GERILIM_V, _ev(k["gerilim_yeterli"])))
        print("akim yonu dogru          : {}".format(_ev(k["akim_yonu_dogru"])))
        print("akim olcum araliginda    : {}".format(_ev(k["akim_aralikta"])))
        print("bara tasmasi (OVF) yok   : {}".format(_ev(k["ovf_yok"])))
    print("ON DENETIM: {}".format("GECTI" if k["gecti"] else "KALDI"))
    return 0 if k["gecti"] else 1


if __name__ == "__main__":
    sys.exit(main())
