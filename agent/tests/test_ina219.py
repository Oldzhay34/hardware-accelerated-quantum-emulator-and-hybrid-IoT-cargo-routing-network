"""`agent/ina219.py` ve `agent/measure_energy.py` testleri — **kart gerekmez**
(Anayasa Prensip V).

`test_sabitler_protokolle_ayni`: kod ile kart-enerji-protokolu ayrışırsa
kırılır (FR-011). Protokol dondurulunca `test_protokol_dondurulmus` da devreye
girer.
"""
import os

import pytest

from agent import ina219 as ina
from agent import measure_energy as me

KOK = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
PROTOKOL = os.path.join(KOK, "docs", "measurements", "kart-enerji-protokolu.md")


def _protokol():
    with open(PROTOKOL, encoding="utf-8") as f:
        return f.read()


# --- protokol bağı --------------------------------------------------------
def test_sabitler_protokolle_ayni():
    m = _protokol()
    assert me.PROTOKOL_SURUMU == "kart-enerji-protokolu v1.1" and "v1.1" in m
    assert "`0x17FF`" in m and ina.YAPILANDIRMA == 0x17FF
    assert "**0,1 Ω**" in m and ina.R_SONT_OHM == 0.1
    assert "**5 Hz** (0,2 sn)" in m and me.PERIYOT_S == 0.2
    assert "[ boş 170 sn ] -> [ yük 170 sn ]" in m and me.BOS_S == 170.0 and me.YUK_S == 170.0
    assert "F2, P2, F2, P2" in m and me.SIRA == ("F2", "P2", "F2", "P2")
    assert "beklenenin %90'ı" in m and me.MIN_ORNEK_ORANI == 0.9
    assert "--isinma 3" in m and me.ARM_ISINMA == 3
    assert "**30 sn**" in m


def test_protokol_dondurulmus():
    durum = next(s for s in _protokol().splitlines() if s.startswith("| **Durum** |"))
    if "TASLAK" in durum:
        pytest.skip("protokol henuz taslak — dondurulunca bu test zorunlu")
    assert "DONDURULDU" in durum


def test_kalibrasyon_ayni_ornekleyici():
    from agent import calibrate_ina219 as ki
    assert ki.SURE_S == 30.0 and ki.PERIYOT_S == me.PERIYOT_S


# --- dönüşümler -----------------------------------------------------------
def test_yapilandirma_kelimesi_veri_sayfasi():
    # BRNG=16V(0), PG=/4(10), BADC=SADC=128 ornek(1111), MODE=surekli(111)
    assert ina.yapilandirma_kelimesi() == 0b0_0_0_10_1111_1111_111 == 0x17FF
    # acilis degeri 0x399F = BRNG 32V, PG /8, 12 bit tek, surekli
    assert ina.yapilandirma_kelimesi(brng=1, pga=3, badc=0x3, sadc=0x3) == 0x399F


def test_sont_isaretli():
    assert ina.sont_uv(0xFFFC) == -40.0          # T047'de okunan bos deger
    assert ina.sont_uv(0x0FA0) == 40000.0
    assert ina.sont_uv(0x8000) == -327680.0


def test_bara_ve_bayraklar():
    mv, cnvr, ovf = ina.bara(0x06F2)             # T047: 888 mV
    assert (mv, cnvr, ovf) == (888.0, True, False)
    assert ina.bara(0x5DC1) == (12000.0, False, True)              # 3000 << 3 | OVF


def test_guc():
    assert ina.akim_a(30000.0) == pytest.approx(0.3)                 # 30 mV / 0,1 ohm
    assert ina.guc_w(12000.0, 30000.0) == pytest.approx(3.6)
    assert ina.guc_w(12000.0, -30000.0) == pytest.approx(-3.6)


def test_doyma_pga4():
    assert ina.doygun(159300.0) and ina.doygun(-160000.0)
    assert not ina.doygun(100000.0)


# --- pencere ve enerji ----------------------------------------------------
def _ornek(t, akim_a, gerilim_v=12.0):
    sont = int(round(akim_a * ina.R_SONT_OHM / 10e-6)) & 0xFFFF
    bara = (int(round(gerilim_v * 1000 / 4.0)) << 3) | 0x2
    return (t, sont, bara)


def test_pencere_ozeti_yalniz_aralik():
    orn = [_ornek(t * 0.2, 0.25) for t in range(50)] + [_ornek(10 + t * 0.2, 0.30) for t in range(50)]
    bos = ina.pencere_ozeti(orn, 0.0, 10.0)
    yuk = ina.pencere_ozeti(orn, 10.0, 20.0)
    assert bos["n"] == 50 and yuk["n"] == 50
    assert bos["ort_guc_w"] == pytest.approx(3.0, rel=1e-3)
    assert yuk["ort_guc_w"] == pytest.approx(3.6, rel=1e-3)
    assert bos["doygun_ornek"] == 0 and bos["ovf_ornek"] == 0


def test_pencere_bos_aralik_denetimde_kalir():
    oz = ina.pencere_ozeti([], 0.0, 10.0)
    assert oz["n"] == 0 and oz["sure_s"] == 10.0
    with pytest.raises(me.SeriGecersiz):
        me.pencere_denetle(oz, "bos")


def test_enerji_hesabi_data_model_formulu():
    e = ina.enerji_hesabi({"ort_guc_w": 3.0, "se_guc_w": 0.003},
                          {"ort_guc_w": 3.5, "se_guc_w": 0.004}, 170.0, 4000)
    assert e["guc_farki_w"] == pytest.approx(0.5)
    assert e["enerji_j_kosum"] == pytest.approx(0.5 * 170.0 / 4000)
    assert e["guc_farki_se_w"] == pytest.approx(0.005)
    with pytest.raises(ValueError):
        ina.enerji_hesabi({"ort_guc_w": 3.0}, {"ort_guc_w": 3.5}, 170.0, 0)


def test_seri_sonucu_yuk_bostan_buyuk_olmali():
    orn = [_ornek(t * 0.2, 0.30) for t in range(850)] + \
          [_ornek(170 + t * 0.2, 0.25) for t in range(850)]
    with pytest.raises(me.SeriGecersiz):
        me.seri_sonucu(orn, (0.0, 170.0), (170.0, 340.0), 4000)


def test_seri_sonucu_eksik_ornek_gecersiz():
    orn = [_ornek(t * 0.2, 0.25) for t in range(850)] + \
          [_ornek(170 + t * 0.4, 0.30) for t in range(425)]     # yuk'te yarisi
    with pytest.raises(me.SeriGecersiz):
        me.seri_sonucu(orn, (0.0, 170.0), (170.0, 340.0), 4000)


# --- kalibrasyon ----------------------------------------------------------
def test_kalibrasyon_esigi():
    k = ina.kalibrasyon_kaydi(0.25, 0.2575, "t")
    assert k["sapma_yuzde"] == pytest.approx(3.0) and k["gecti"]
    assert not ina.kalibrasyon_kaydi(0.25, 0.2625, "t")["gecti"]       # %5 -> kalir


def test_kalibrasyon_once_ve_gecmis_olmali():
    iyi = {"gecti": True, "sapma_yuzde": 1.2, "zaman_damgasi_unix": 100.0}
    assert me.kalibrasyonlari_denetle([iyi], 200.0) == 1.2
    with pytest.raises(me.SeriGecersiz):
        me.kalibrasyonlari_denetle([], 200.0)
    with pytest.raises(me.SeriGecersiz):
        me.kalibrasyonlari_denetle([dict(iyi, zaman_damgasi_unix=300.0)], 200.0)
    with pytest.raises(me.SeriGecersiz):
        me.kalibrasyonlari_denetle([dict(iyi, gecti=False, sapma_yuzde=6.0)], 200.0)


def test_bench_ciktisi():
    metin = ("varyant   : float\nkosum_sayisi   : 2019  (isinma 3 haric)\n"
             "beklenen_deger : -3950.990722656  (dogruluk kontrolu)\n"
             "medyan  :     84.132 ms\n")
    c = me.bench_ciktisi_coz(metin)
    assert c == {"kosum_sayisi": 2019, "isinma": 3,
                 "beklenen_deger": "-3950.990722656", "medyan_ms": 84.132}
