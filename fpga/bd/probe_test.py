#!/usr/bin/env python3
"""G0 uyumluluk denemesi -- KARTTA kosar (PYNQ 2.5, Python 3.6).

PYNQ 2.5'in (Glasgow, 2019) Vivado 2025.2 .hwh'sini ayristirip
ayristiramadigini olcer. Cevap uc olabilir:

  A yolu   -- ip_dict dolu VE register haritalari okundu
              -> Overlay("qir.bit") kullanilabilir
  KISMI    -- ip_dict dolu ama register haritalari bos
              -> taban adres .hwh'den, erisim MMIO ile
  B yolu   -- ayristirici hata verdi
              -> Bitstream(...).download() + MMIO(taban, 0x3000)

Bkz. research.md §R1. Bu betik ASLA yigin iziyle olmez: hata da bir sonuctur
ve raporlanmasi gerekir.

Kullanim:  python3 probe_test.py probe.hwh
"""
from __future__ import print_function

import os
import sys
import traceback


def parser_bul():
    """HWH ayristiricisini bul. Modul yolu PYNQ surumune gore degisir."""
    denenen = []
    adaylar = [
        ("pynq.pl_server.hwh_parser", "HWH"),
        ("pynq.pl_server.hwh_parser", "_HWHABC"),
        ("pynq.pl", "HWH"),
        ("pynq.overlay", "HWH"),
    ]
    for modul_adi, sinif_adi in adaylar:
        etiket = "{}.{}".format(modul_adi, sinif_adi)
        try:
            modul = __import__(modul_adi, fromlist=[sinif_adi])
            sinif = getattr(modul, sinif_adi)
            print("  [BULUNDU] {}".format(etiket))
            return sinif, etiket
        except Exception as e:
            denenen.append("{} -> {}: {}".format(etiket, type(e).__name__, e))
    print("  HICBIRI BULUNAMADI:")
    for d in denenen:
        print("    " + d)
    try:
        import pynq
        print("  pynq modul dizini: {}".format(os.path.dirname(pynq.__file__)))
        print("  pynq surumu      : {}".format(getattr(pynq, "__version__", "?")))
    except Exception as e:
        print("  pynq hic yuklenemedi: {}".format(e))
    return None, None


def main():
    if len(sys.argv) < 2:
        print("kullanim: python3 probe_test.py <yol>.hwh")
        return 2
    hwh = sys.argv[1]
    if not os.path.isfile(hwh):
        print("HATA: dosya yok: {}".format(hwh))
        return 2

    print("=" * 62)
    print("G0 -- .hwh uyumluluk denemesi")
    print("=" * 62)
    print("dosya  : {} ({} bayt)".format(hwh, os.path.getsize(hwh)))
    print("python : {}".format(sys.version.split()[0]))
    print()

    print("[1] ayristirici araniyor")
    HWH, etiket = parser_bul()
    if HWH is None:
        print()
        print("SONUC: B YOLU -- ayristirici sinifi hic bulunamadi.")
        return 1
    print()

    print("[2] .hwh ayristiriliyor")
    try:
        h = HWH(hwh)
    except Exception:
        print("  AYRISTIRMA COKTU:")
        traceback.print_exc(file=sys.stdout)
        print()
        print("SONUC: B YOLU -- Overlay kullanilamaz.")
        print("       Konak kodu Bitstream(...).download() + MMIO ile yazilacak.")
        return 1
    print("  ayristirma gecti")
    print()

    print("[3] ip_dict inceleniyor")
    try:
        ip_dict = h.ip_dict
    except Exception:
        print("  ip_dict ERISILEMEDI:")
        traceback.print_exc(file=sys.stdout)
        print()
        print("SONUC: B YOLU")
        return 1

    print("  IP sayisi: {}".format(len(ip_dict)))
    toplam_reg = 0
    qir_var = False
    for ad in sorted(ip_dict):
        bilgi = ip_dict[ad] or {}
        taban = bilgi.get("phys_addr")
        uzunluk = bilgi.get("addr_range")
        regs = bilgi.get("registers") or {}
        tip = bilgi.get("type", "?")
        toplam_reg += len(regs)
        if "qir" in ad.lower() or "qir" in str(tip).lower():
            qir_var = True
        taban_s = "0x{:08X}".format(taban) if isinstance(taban, int) else str(taban)
        uz_s = "0x{:X}".format(uzunluk) if isinstance(uzunluk, int) else str(uzunluk)
        print("    {:<24} taban={}  uzunluk={}  register={}".format(
            ad, taban_s, uz_s, len(regs)))
        print("      tip: {}".format(tip))
        for rad in sorted(regs)[:6]:
            r = regs[rad] or {}
            print("        - {:<20} +0x{:03X}".format(rad, r.get("address_offset", -1)))
        if len(regs) > 6:
            print("        ... {} register daha".format(len(regs) - 6))
    print()

    # --- Hukum ---
    print("=" * 62)
    if len(ip_dict) == 0:
        print("SONUC: BELIRSIZ -- ip_dict BOS.")
        print("       Bu BASARI SAYILMAZ. Ya .hwh'de ozel IP yok (kukla BD")
        print("       PS-only uretilmis -- research.md §R1'deki tuzak), ya da")
        print("       ayristirici IP bolumunu sessizce atladi. Once .hwh'nin")
        print("       qir_kernel icerdigini dogrulayin.")
        return 1

    if not qir_var:
        print("SONUC: BELIRSIZ -- ip_dict dolu ama qir_kernel YOK.")
        print("       Yanlis .hwh kopyalanmis olabilir.")
        return 1

    if toplam_reg > 0:
        print("SONUC: A YOLU ACIK")
        print("       ip_dict dolu ve register haritalari okundu.")
        print("       Overlay(\"qir.bit\") kullanilabilir.")
        print("       Ayristirici: {}".format(etiket))
        return 0

    print("SONUC: KISMI BASARI")
    print("       ip_dict dolu (taban adresler var) ama register haritasi BOS.")
    print("       Taban adres .hwh'den alinir, erisim MMIO ile yapilir.")
    print("       Register ofsetleri IP paketindeki xqir_kernel_hw.h'den gelir.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
