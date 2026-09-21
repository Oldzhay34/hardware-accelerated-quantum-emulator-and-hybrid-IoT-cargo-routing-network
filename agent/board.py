"""Kart sürücüsü — AXI-Lite üzerinden `qir_kernel`. Görevler T026–T030.

Sözleşme: `specs/003-zynq-ps-kartta-kosum/contracts/axi-register-map.md`
Register kaynağı: IP paketindeki `drivers/qir_kernel_v0_1/src/xqir_kernel_hw.h`
(değerler o başlıkla birebir doğrulandı, 2026-09-20).

# PYTHON 3.6 UYUMU ZORUNLU — bu modül KARTTA koşar (PYNQ 2.5 / Python 3.6.5).
# `dataclasses` ve `from __future__ import annotations` KULLANILMAZ.

--------------------------------------------------------------------------
İKİ TUZAK — ikisi de sessiz
--------------------------------------------------------------------------
1. **`import pynq` root ister.** `RuntimeError: Root permission needed by the
   library` (`pynq/xlnk.py:133`). Konak kodu `sudo` ile koşar. Bu yüzden
   `pynq` **tembel** içe aktarılır: modül, kart olmadan da (testler için)
   içe aktarılabilir olmak zorunda.

2. **FCLK doğrulanmadan koşulmaz.** Blok tasarımdaki 100 MHz bir
   *implementasyon zamanı* kısıtıdır; çalışma zamanında PL saatini kartın
   boot'taki `ps7_init`'i belirler ve PYNQ `.bit` indirirken PS'i yeniden
   yapılandırmaz. Yanlış saatte koşan çekirdek **doğru sonuç verir ama
   gecikme ölçümleri sessizce yanlış çıkar** — ve "makul" göründüğü için
   fark edilmez.
"""
# PYTHON 3.6 UYUMU ZORUNLU (yukarı bakın)
import struct
import time

# ==========================================================================
# T026 — Register haritası (xqir_kernel_hw.h ile birebir)
# ==========================================================================
ADDR_AP_CTRL              = 0x0000   # bit0 ap_start, bit1 ap_done,
                                     # bit2 ap_idle, bit3 ap_ready, bit7 auto_restart
ADDR_GIE                  = 0x0004
ADDR_IER                  = 0x0008
ADDR_ISR                  = 0x000C
ADDR_COS_BETA             = 0x0020   # 3 word, word başına bit[17:0]
ADDR_SIN_BETA             = 0x0030   # 3 word
ADDR_P                    = 0x0048   # bit[31:0]
ADDR_BEKLENEN_DEGER       = 0x0050   # R, IEEE-754 float bit deseni
ADDR_BEKLENEN_DEGER_CTRL  = 0x0054   # bit0 ap_vld (R/COR)
ADDR_PHASES               = 0x1000   # 816 word
ADDR_COST                 = 0x2000   # 272 word

DEPTH_COS_BETA = 3
DEPTH_SIN_BETA = 3
DEPTH_PHASES   = 816
DEPTH_COST     = 272

BIT_AP_START = 0x1
BIT_AP_DONE  = 0x2
BIT_AP_IDLE  = 0x4
BIT_AP_READY = 0x8

MMIO_UZUNLUK = 0x10000    # 0x2800 kullanılıyor, sayfa hizası için 64K eşlenir

# Blok tasarımda SABİTLENDİ (`fpga/bd/qir_bd.tcl`) ve `.hwh`'de doğrulandı:
# BASEVALUE="0x43C00000". B yolunun tek doğruluk kaynağı budur.
AXI_TABAN = 0x43C00000

# Toplam yazma sayısı — `T_yazma` kapsamının tanımı (FR-007).
TOPLAM_YAZMA = DEPTH_PHASES + DEPTH_COST + DEPTH_COS_BETA + DEPTH_SIN_BETA + 1  # 1095

ZAMAN_ASIMI_SN = 5.0      # madde A-4
FCLK_HEDEF_MHZ = 100.0
FCLK_TOLERANS  = 0.01     # %1


class KartHatasi(RuntimeError):
    """Kart yolunda beklenmeyen durum. Sessiz geçilmez."""


class Kosum(object):
    """Tek bir çekirdek çağrısının sonucu.

    ⚠️ `gecerli=False` olan koşum **hiçbir seride sayılmaz** (madde A-4).
    Kısmî sonuç ölçüm değildir.
    """

    __slots__ = ("beklenen_deger_ham", "gecerli", "t_cekirdek", "t_yazma",
                 "t_uctan_uca", "yazma_sayisi", "yoklama_sayisi", "hata")

    def __init__(self, beklenen_deger_ham=None, gecerli=False, t_cekirdek=None,
                 t_yazma=None, t_uctan_uca=None, yazma_sayisi=0,
                 yoklama_sayisi=0, hata=None):
        self.beklenen_deger_ham = beklenen_deger_ham
        self.gecerli = gecerli
        self.t_cekirdek = t_cekirdek      # ap_start -> ap_done (sn)
        self.t_yazma = t_yazma            # register yazımı (sn)
        self.t_uctan_uca = t_uctan_uca    # yazma + koşum + okuma (sn)
        self.yazma_sayisi = yazma_sayisi
        self.yoklama_sayisi = yoklama_sayisi
        self.hata = hata

    def __repr__(self):
        if not self.gecerli:
            return "Kosum(GECERSIZ: {})".format(self.hata)
        return "Kosum(deger={!r}, t_cekirdek={:.6f}s, yazma={})".format(
            self.beklenen_deger_ham, self.t_cekirdek, self.yazma_sayisi)


class Kart(object):
    """`qir_kernel`'e AXI-Lite erişimi. İki yol destekler (T027).

    A yolu (varsayılan) : `Overlay` — G0 denemesinde açık olduğu **ölçüldü**
                          (2026-09-20, research.md §R1)
    B yolu (yedek)      : `Bitstream(...).download()` + `MMIO(taban, 0x10000)`

    ⛔ `sudo` ile koşulmalı — `import pynq` root ister.
    """

    def __init__(self, bit_yolu, hwh_yolu=None, yol="A", taban=AXI_TABAN,
                 fclk_mhz=FCLK_HEDEF_MHZ):
        if yol not in ("A", "B"):
            raise ValueError("yol 'A' veya 'B' olmali, verilen: {!r}".format(yol))
        self.bit_yolu = bit_yolu
        self.hwh_yolu = hwh_yolu
        self.yol = yol
        self.taban = taban
        self.fclk_mhz = fclk_mhz
        self.overlay = None
        self.mmio = None
        self._dizi = None          # numpy uint32 gorunumu (varsa)
        self.olculen_fclk = None

    # ----------------------------------------------------------------- yükleme
    def yukle(self):
        """Bitstream'i indirir ve MMIO'yu kurar. FCLK'yi **doğrular**."""
        try:
            import pynq
        except Exception as e:                      # noqa: BLE001
            raise KartHatasi(
                "pynq içe aktarılamadı ({}). Bu kod KARTTA ve `sudo` ile "
                "koşmalıdır — `import pynq` root ister.".format(e))

        if self.yol == "A":
            self.overlay = pynq.Overlay(self.bit_yolu)
            ip = self._ip_bul(self.overlay)
            kesfedilen = ip.get("phys_addr")
            if kesfedilen is not None and int(kesfedilen) != int(self.taban):
                raise KartHatasi(
                    "Overlay taban adresi 0x{:08X}, beklenen 0x{:08X}. "
                    "contracts/axi-register-map.md ve fpga/bd/qir_bd.tcl ile "
                    "uyuşmuyor.".format(int(kesfedilen), int(self.taban)))
            self.mmio = pynq.MMIO(int(self.taban), MMIO_UZUNLUK)
        else:
            pynq.Bitstream(self.bit_yolu).download()
            self.mmio = pynq.MMIO(int(self.taban), MMIO_UZUNLUK)

        self._dizi = getattr(self.mmio, "array", None)
        self.fclk_dogrula()
        return self

    @staticmethod
    def _ip_bul(overlay):
        for ad, bilgi in (overlay.ip_dict or {}).items():
            if "qir" in ad.lower() or "qir" in str(bilgi.get("type", "")).lower():
                return bilgi
        raise KartHatasi(
            "Overlay'in ip_dict'inde qir_kernel yok: {}".format(
                list((overlay.ip_dict or {}).keys())))

    def fclk_dogrula(self):
        """⚠️ Bu kontrol atlanamaz — modül başlığındaki 2. tuzak.

        Bitstream 100 MHz'e göre zamanlama kapattı; çalışma zamanında PL
        saatini boot yapılandırması belirler. Uyuşmazsa **bütün gecikme
        ölçümleri sessizce yanlış** olur.
        """
        from pynq.ps import Clocks
        self.olculen_fclk = float(Clocks.fclk0_mhz)
        sapma = abs(self.olculen_fclk - self.fclk_mhz) / self.fclk_mhz
        if sapma > FCLK_TOLERANS:
            raise KartHatasi(
                "FCLK0 = {:.3f} MHz, beklenen {:.3f} MHz (sapma %{:.2f}). "
                "Gecikme ölçümleri geçersiz olurdu. Düzeltmek için: "
                "`from pynq.ps import Clocks; Clocks.fclk0_mhz = {}`".format(
                    self.olculen_fclk, self.fclk_mhz, sapma * 100, self.fclk_mhz))
        return self.olculen_fclk

    # ------------------------------------------------------------- alt seviye
    def _oku(self, ofset):
        return int(self.mmio.read(ofset))

    def _yaz(self, ofset, deger):
        self.mmio.write(ofset, int(deger) & 0xFFFFFFFF)

    def _yaz_dizi(self, taban_ofset, kelimeler):
        """Diziyi word word yazar. `adres(dizi[n]) = taban_ofset + 4*n`.

        numpy görünümü varsa dilim ataması kullanılır — yetkin bir
        gerçeklemenin yapacağı şey, ve `T_yazma` onunla ölçülmelidir.
        """
        if self._dizi is not None:
            bas = taban_ofset // 4
            self._dizi[bas:bas + len(kelimeler)] = kelimeler
        else:
            for n, w in enumerate(kelimeler):
                self._yaz(taban_ofset + 4 * n, w)
        return len(kelimeler)

    # ------------------------------------------------------- durum sorguları
    def ap_idle(self):
        """Madde A-1: `ap_start` yazılmadan önce **doğrulanır**."""
        return bool(self._oku(ADDR_AP_CTRL) & BIT_AP_IDLE)

    def ap_done(self):
        return bool(self._oku(ADDR_AP_CTRL) & BIT_AP_DONE)

    # ----------------------------------------------------- T028: çağrı sırası
    def yaz_tam(self, kodlanmis):
        """Adım 2 — **1.095 yazma**. `T_yazma` kapsamının tanımı budur."""
        n = 0
        n += self._yaz_dizi(ADDR_COST, kodlanmis.cost)
        n += self._yaz_dizi(ADDR_PHASES, kodlanmis.phases)
        n += self._yaz_dizi(ADDR_COS_BETA, kodlanmis.cos_beta)
        n += self._yaz_dizi(ADDR_SIN_BETA, kodlanmis.sin_beta)
        self._yaz(ADDR_P, kodlanmis.p)
        n += 1
        if n != TOPLAM_YAZMA:
            raise KartHatasi(
                "yazma sayısı {} != {} — dizi boyutları sözleşmeyle "
                "uyuşmuyor".format(n, TOPLAM_YAZMA))
        return n

    def yaz_cost(self, cost):
        """T030 — izdüşüm kısa yolu: **yalnız `cost`** (272 word).

        `phases`, `cos_beta`, `sin_beta`, `p` yerinde kalır.

        ⛔ **GECİKME ÖLÇÜMÜNDE KULLANILMAZ.** G4 tam çağrı sırasını ölçer;
        bu kısa yol yalnız G3 doğrulamasına aittir. Karıştırılırsa `T_yazma`
        olduğundan küçük raporlanır.
        """
        if len(cost) != DEPTH_COST:
            raise KartHatasi("cost {} word, beklenen {}".format(
                len(cost), DEPTH_COST))
        return self._yaz_dizi(ADDR_COST, cost)

    def basla_ve_bekle(self, zaman_asimi=ZAMAN_ASIMI_SN):
        """Adım 3–4. Döner: `(bitti, sure_sn, yoklama_sayisi)`.

        T029 / madde A-4: `ap_done` zaman aşımına uğrarsa **istisna atılmaz** —
        çağıran koşumu `gecerli=False` işaretler. Kısmî sonuç ölçüm sayılmaz.
        """
        self._yaz(ADDR_AP_CTRL, BIT_AP_START)
        t0 = time.time()
        yoklama = 0
        while True:
            durum = self._oku(ADDR_AP_CTRL)
            yoklama += 1
            if durum & BIT_AP_DONE:
                return True, time.time() - t0, yoklama
            if time.time() - t0 > zaman_asimi:
                return False, time.time() - t0, yoklama

    def beklenen_deger_oku(self):
        """Adım 5 / madde A-6: ham 32 bit okunur, `struct.unpack` ile yorumlanır.

        Float'a **kesme (cast) YAPILMAZ** — bit deseni korunur.
        """
        ham = self._oku(ADDR_BEKLENEN_DEGER) & 0xFFFFFFFF
        return struct.unpack("<f", struct.pack("<I", ham))[0]

    # --------------------------------------------------------- tam çağrı sırası
    def kosum(self, kodlanmis, zaman_asimi=ZAMAN_ASIMI_SN):
        """Sözleşmedeki 1–5 adımlarının tamamı (maddeler A-1…A-6)."""
        t_bas = time.time()
        if not self.ap_idle():
            return Kosum(hata="ap_idle=0: çekirdek meşgul (madde A-1)")

        t0 = time.time()
        n = self.yaz_tam(kodlanmis)
        t_yazma = time.time() - t0

        bitti, t_cek, yoklama = self.basla_ve_bekle(zaman_asimi)
        if not bitti:
            return Kosum(gecerli=False, t_yazma=t_yazma, yazma_sayisi=n,
                         yoklama_sayisi=yoklama, t_cekirdek=t_cek,
                         hata="ap_done {:.1f} sn içinde gelmedi (madde A-4)".format(
                             zaman_asimi))

        deger = self.beklenen_deger_oku()
        return Kosum(beklenen_deger_ham=deger, gecerli=True, t_cekirdek=t_cek,
                     t_yazma=t_yazma, t_uctan_uca=time.time() - t_bas,
                     yazma_sayisi=n, yoklama_sayisi=yoklama)

    def izdusum(self, cost, zaman_asimi=ZAMAN_ASIMI_SN):
        """T030 kısa yolu — yalnız `cost` yeniden yazılır (272 yazma).

        ⛔ Gecikme ölçümünde kullanılmaz; bkz. `yaz_cost`.
        """
        t_bas = time.time()
        if not self.ap_idle():
            return Kosum(hata="ap_idle=0: çekirdek meşgul (madde A-1)")
        t0 = time.time()
        n = self.yaz_cost(cost)
        t_yazma = time.time() - t0
        bitti, t_cek, yoklama = self.basla_ve_bekle(zaman_asimi)
        if not bitti:
            return Kosum(gecerli=False, t_yazma=t_yazma, yazma_sayisi=n,
                         yoklama_sayisi=yoklama, t_cekirdek=t_cek,
                         hata="ap_done zaman aşımı (madde A-4)")
        return Kosum(beklenen_deger_ham=self.beklenen_deger_oku(), gecerli=True,
                     t_cekirdek=t_cek, t_yazma=t_yazma,
                     t_uctan_uca=time.time() - t_bas,
                     yazma_sayisi=n, yoklama_sayisi=yoklama)
