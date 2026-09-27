"""`agent/board.py` testleri — **kart gerekmez** (Anayasa Prensip V).

En değerli test `test_register_haritasi_baslikla_ayni`: sabitleri IP paketinin
kendi `xqir_kernel_hw.h` dosyasına karşı doğrular. Elle yazılmış bir register
haritası sessizce kayar; bu test kaymayı yakalar.
"""
import os
import re
import struct

import pytest

from agent import board

KOK = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
BASLIK = os.path.join(KOK, "artifacts", "ip", "repo", "qir_kernel_v0_1",
                      "drivers", "qir_kernel_v0_1", "src", "xqir_kernel_hw.h")


# =========================================================================
# T026 — register haritası
# =========================================================================
def test_register_haritasi_baslikla_ayni():
    """Sabitler IP paketindeki başlıkla **birebir** olmalı."""
    if not os.path.isfile(BASLIK):
        pytest.skip("IP başlığı yok ({}); T001 koşulmamış".format(BASLIK))
    with open(BASLIK, encoding="utf-8", errors="replace") as f:
        metin = f.read()

    def define(ad):
        m = re.search(r"#define\s+XQIR_KERNEL_CONTROL_" + ad + r"\s+(\S+)", metin)
        assert m, "başlıkta yok: " + ad
        return int(m.group(1), 0)

    assert board.ADDR_AP_CTRL             == define("ADDR_AP_CTRL")
    assert board.ADDR_GIE                 == define("ADDR_GIE")
    assert board.ADDR_IER                 == define("ADDR_IER")
    assert board.ADDR_ISR                 == define("ADDR_ISR")
    assert board.ADDR_P                   == define("ADDR_P_DATA")
    assert board.ADDR_BEKLENEN_DEGER      == define("ADDR_BEKLENEN_DEGER_DATA")
    assert board.ADDR_BEKLENEN_DEGER_CTRL == define("ADDR_BEKLENEN_DEGER_CTRL")
    assert board.ADDR_COS_BETA            == define("ADDR_COS_BETA_BASE")
    assert board.ADDR_SIN_BETA            == define("ADDR_SIN_BETA_BASE")
    assert board.ADDR_PHASES              == define("ADDR_PHASES_BASE")
    assert board.ADDR_COST                == define("ADDR_COST_BASE")
    assert board.DEPTH_COS_BETA           == define("DEPTH_COS_BETA")
    assert board.DEPTH_SIN_BETA           == define("DEPTH_SIN_BETA")
    assert board.DEPTH_PHASES             == define("DEPTH_PHASES")
    assert board.DEPTH_COST               == define("DEPTH_COST")


def test_dizi_siniri_pencereyi_asmiyor():
    """Son elemanın adresi MMIO penceresine sığmalı."""
    for taban, derinlik in ((board.ADDR_PHASES, board.DEPTH_PHASES),
                            (board.ADDR_COST, board.DEPTH_COST),
                            (board.ADDR_COS_BETA, board.DEPTH_COS_BETA),
                            (board.ADDR_SIN_BETA, board.DEPTH_SIN_BETA)):
        son = taban + 4 * (derinlik - 1)
        assert son < board.MMIO_UZUNLUK


def test_diziler_cakismiyor():
    araliklar = sorted([
        (board.ADDR_COS_BETA, board.DEPTH_COS_BETA),
        (board.ADDR_SIN_BETA, board.DEPTH_SIN_BETA),
        (board.ADDR_PHASES,   board.DEPTH_PHASES),
        (board.ADDR_COST,     board.DEPTH_COST),
    ])
    for (t1, d1), (t2, _) in zip(araliklar, araliklar[1:]):
        assert t1 + 4 * d1 <= t2, "cakisma: 0x{:04X} ve 0x{:04X}".format(t1, t2)


def test_toplam_yazma_1095():
    """Sözleşmedeki sayı — `T_yazma` kapsamının tanımı."""
    assert board.TOPLAM_YAZMA == 1095
    assert board.TOPLAM_YAZMA == (816 + 272 + 3 + 3 + 1)


def test_taban_adres_sozlesmeyle_ayni():
    assert board.AXI_TABAN == 0x43C00000


def test_kontrol_bitleri():
    assert (board.BIT_AP_START, board.BIT_AP_DONE,
            board.BIT_AP_IDLE, board.BIT_AP_READY) == (1, 2, 4, 8)


# =========================================================================
# Kart olmadan davranış
# =========================================================================
def test_gecersiz_yol_reddedilir():
    with pytest.raises(ValueError):
        board.Kart("x.bit", yol="C")


def test_pynq_yoksa_anlamli_hata():
    """Konakta `pynq` yok — hata mesajı **root** ipucunu vermeli."""
    k = board.Kart("yok.bit")
    with pytest.raises(board.KartHatasi) as e:
        k.yukle()
    assert "sudo" in str(e.value).lower() or "root" in str(e.value).lower()


def test_kosum_gecersizse_deger_tasimaz():
    k = board.Kosum(hata="test")
    assert k.gecerli is False
    assert k.beklenen_deger_ham is None
    assert "GECERSIZ" in repr(k)


def test_beklenen_deger_bit_deseni_korunur():
    """Madde A-6: ham 32 bit `struct.unpack` ile yorumlanır, cast edilmez."""
    ham = 0xBEE28271                      # cosim'de olculen deger
    deger = struct.unpack("<f", struct.pack("<I", ham))[0]
    assert abs(deger - (-0.442401439)) < 1e-9


# =========================================================================
# FCLK ayarı — 2026-09-27 T032'de kartta yaşanan 62,5 MHz durumu
# =========================================================================
class _SahteSaatler(object):
    """`pynq.ps.Clocks` yerine: yalnız `fclk0_mhz` özniteliğini tutar."""
    fclk0_mhz = None


@pytest.fixture
def sahte_pynq(monkeypatch):
    import sys
    import types

    def _hazirla(baslangic_mhz):
        _SahteSaatler.fclk0_mhz = baslangic_mhz
        ps = types.ModuleType("pynq.ps")
        ps.Clocks = _SahteSaatler
        paket = types.ModuleType("pynq")
        paket.ps = ps
        monkeypatch.setitem(sys.modules, "pynq", paket)
        monkeypatch.setitem(sys.modules, "pynq.ps", ps)
        return _SahteSaatler
    return _hazirla


def test_fclk_sapmissa_ayarlanir_ve_kaydedilir(sahte_pynq):
    """Kartta ölçülen durum: yüklemeden sonra 62,5 MHz → 100'e getirilmeli."""
    saat = sahte_pynq(62.5)
    k = board.Kart("x.bit")
    k.fclk_ayarla()
    assert k.fclk_yukleme_sonrasi == 62.5          # ayar ÖNCESİ değer kayıtta
    assert k.fclk_ayarlandi is True
    assert saat.fclk0_mhz == board.FCLK_HEDEF_MHZ
    assert k.fclk_dogrula() == board.FCLK_HEDEF_MHZ


def test_fclk_dogruysa_yazilmaz(sahte_pynq):
    """Tolerans içindeyse saate dokunulmaz — gereksiz yazma bölenleri oynatır.

    100,5 seçildi: kod yazsaydı değer 100,0'a dönerdi ve test yakalardı.
    """
    saat = sahte_pynq(100.5)
    k = board.Kart("x.bit")
    k.fclk_ayarla()
    assert k.fclk_ayarlandi is False
    assert saat.fclk0_mhz == 100.5


def test_fclk_ayar_tutmazsa_hata(sahte_pynq):
    """Ayardan sonra da sapma varsa sessiz geçilmez."""
    sahte_pynq(62.5)
    k = board.Kart("x.bit")
    k.fclk_ayarla()
    _SahteSaatler.fclk0_mhz = 62.5                 # PLL hedefi veremedi
    with pytest.raises(board.KartHatasi) as e:
        k.fclk_dogrula()
    assert "tutmadi" in str(e.value)
