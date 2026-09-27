"""Koşum boyunca XADC besleme gerilimlerini sürekli örnekler.

# PYTHON 3.6 UYUMU ZORUNLU — KARTTA koşar (PYNQ 2.5 / Python 3.6.5). sudo ile.

Kullanım (kartta, koşumla eşzamanlı):
    sudo python3 -m agent.xadc_izle 50 xadc.json &
    sudo python3 -m agent.run_board ...

Amaç: kart USB'den beslenirken (JP5) çekirdek yükü gerilimi düşürüyor mu?
Düşürürse sonuç *sessiz yanlış* olabilir ve mantık hatası sanılır
(SIRADAKI.md, JP5 notu). Bu bir güç ÖLÇÜMÜ değildir — yalnız ray gerilimi.

⚠️ XADC PL'dedir: bitstream yüklenirken bütün kanallar birden 0 okur. Bu
örnekler çökme değil yeniden programlama penceresidir; ayrı sayılır ve
en-düşük değere katılmaz. (2026-09-27: ilk sürüm onları katıyordu ve dört
rayın hepsi "0,0 V" görünüyordu — PS rayı gerçekten 0 olsaydı Linux çökerdi.)
"""
# PYTHON 3.6 UYUMU ZORUNLU (yukarı bakın)
import json
import sys
import time

XADC = "/sys/bus/iio/devices/iio:device0/"
KANAL = ("voltage0_vccint", "voltage2_vccbram", "voltage1_vccaux", "voltage3_vccpint")
YENIDEN_PROGRAMLAMA_ESIGI_V = 0.5


def _olcek(ch):
    with open(XADC + "in_%s_scale" % ch) as f:
        return float(f.read()) / 1000.0


def izle(sure):
    sk = dict((ch, _olcek(ch)) for ch in KANAL)
    dosya = dict((ch, open(XADC + "in_%s_raw" % ch)) for ch in KANAL)
    en_az = dict((ch, 9.0) for ch in KANAL)
    en_cok = dict((ch, 0.0) for ch in KANAL)
    toplam = dict((ch, 0.0) for ch in KANAL)
    n = 0
    yeniden_programlama = 0
    t0 = time.time()
    while time.time() - t0 < sure:
        oku = {}
        for ch in KANAL:
            f = dosya[ch]
            f.seek(0)
            oku[ch] = float(f.read()) * sk[ch]
        if min(oku.values()) < YENIDEN_PROGRAMLAMA_ESIGI_V:
            yeniden_programlama += 1
            continue
        for ch, v in oku.items():
            en_az[ch] = min(en_az[ch], v)
            en_cok[ch] = max(en_cok[ch], v)
            toplam[ch] += v
        n += 1
    sonuc = {"ornek": n, "yeniden_programlama_ornegi": yeniden_programlama,
             "sure_s": round(time.time() - t0, 2)}
    for ch in KANAL:
        sonuc[ch.split("_")[1]] = {
            "min": round(en_az[ch], 4), "max": round(en_cok[ch], 4),
            "ort": round(toplam[ch] / n, 4) if n else None}
    return sonuc


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    sure, cikti = float(argv[0]), argv[1]
    with open(cikti, "w") as f:
        json.dump(izle(sure), f, indent=1)
    return 0


if __name__ == "__main__":
    sys.exit(main())
