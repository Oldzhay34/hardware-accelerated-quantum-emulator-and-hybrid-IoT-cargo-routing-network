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
    assert me.PROTOKOL_SURUMU == "kart-enerji-protokolu v1.3" and "v1.3" in m
    assert "`0x17FF`" in m and ina.YAPILANDIRMA == 0x17FF
    assert "**0,1 Ω**" in m and ina.R_SONT_OHM == 0.1
    assert "**5 Hz** (0,2 sn)" in m and me.PERIYOT_S == 0.2
    assert "[ boş 170 sn ] -> [ yük 170 sn ]" in m and me.BOS_S == 170.0 and me.YUK_S == 170.0
    assert "F2, P2, F2, P2" in m and me.SIRA == ("F2", "P2", "F2", "P2")
    assert "beklenenin %90'ı" in m and me.MIN_ORNEK_ORANI == 0.9
    assert "--isinma 3" in m and me.ARM_ISINMA == 3
    assert "**30 sn**" in m
    from agent import calibrate_ina219 as ki
    assert "art arda **3 × 30 sn**" in m and ki.KATSAYI_PENCERE == 3
    assert "yayılım **< %1**" in m and ki.KATSAYI_YAYILIM_ESIK == 1.0
    assert "akım **≥ 10 mA**" in m and ki.DOGRULAMA_MIN_MA == 10.0
    assert "en az **1,5 kat**" in m and me.DOGRULAMA_AKIM_ORANI == 1.5
    assert "**4,6 V**" in m and me.MIN_GERILIM_V == 4.6
    assert "**10 sn**" in m and me.ON_DENETIM_S == 10.0
    assert "tam ölçeğin **%80**" in m and me.ON_DENETIM_ARALIK == 0.8
    assert "`kart-5v-girisi`" in m and me.KAPSAM.startswith("kart-5v-girisi")


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
        me.seri_sonucu(orn, (0.0, 170.0), (170.0, 340.0), 4000, ina.R_SONT_OHM)


def test_seri_sonucu_eksik_ornek_gecersiz():
    orn = [_ornek(t * 0.2, 0.25) for t in range(850)] + \
          [_ornek(170 + t * 0.4, 0.30) for t in range(425)]     # yuk'te yarisi
    with pytest.raises(me.SeriGecersiz):
        me.seri_sonucu(orn, (0.0, 170.0), (170.0, 340.0), 4000, ina.R_SONT_OHM)


def test_kart_girisi_gerilim_alt_siniri():
    """§13: tek bir örnek bile 4,6 V'un altına inerse seri geçersiz."""
    orn = [_ornek(t * 0.2, 0.50, 5.0) for t in range(850)] + \
          [_ornek(170 + t * 0.2, 0.60, 5.0) for t in range(850)]
    bos, yuk, e, _ = me.seri_sonucu(orn, (0.0, 170.0), (170.0, 340.0), 4000, ina.R_SONT_OHM)
    assert bos["min_gerilim_v"] == pytest.approx(5.0) and e["guc_farki_w"] > 0
    orn[900] = _ornek(orn[900][0], 0.60, 4.5)
    with pytest.raises(me.SeriGecersiz):
        me.seri_sonucu(orn, (0.0, 170.0), (170.0, 340.0), 4000, ina.R_SONT_OHM)


def test_on_denetim_kor_ve_kararlar():
    iyi = [_ornek(t * 0.2, 0.50, 5.0) for t in range(50)]
    k = me.on_denetim_karari(iyi)
    assert k["gecti"] and k["gerilim_yeterli"] and k["akim_yonu_dogru"] and k["akim_aralikta"]
    # kor: akim ya da guc SAYI olarak donmez
    assert not any(("akim" in a or "guc" in a) and not isinstance(v, bool) for a, v in k.items())
    assert not me.on_denetim_karari([_ornek(0.0, 0.50, 4.5)])["gerilim_yeterli"]
    assert not me.on_denetim_karari([_ornek(0.0, -0.50, 5.0)])["akim_yonu_dogru"]
    assert not me.on_denetim_karari([_ornek(0.0, 1.40, 5.0)])["akim_aralikta"]   # 140 mV > 128 mV
    assert not me.on_denetim_karari([])["gecti"]


# --- kalibrasyon ----------------------------------------------------------
def test_kalibrasyon_esigi():
    k = ina.kalibrasyon_kaydi(0.25, 0.2575, "t")
    assert k["sapma_yuzde"] == pytest.approx(3.0) and k["gecti"]
    assert not ina.kalibrasyon_kaydi(0.25, 0.2625, "t")["gecti"]       # %5 -> kalir


def _kat(ts=100.0, r=0.13, kararli=True):
    return {"rol": "katsayi", "kararli": kararli, "r_sont_etkin_ohm": r,
            "yayilim_yuzde": 0.4 if kararli else 2.0, "gecti": kararli,
            "sapma_yuzde": 29.0, "zaman_damgasi_unix": ts}


def _dog(ts, akim_a, r=0.13, sapma=1.2):
    return {"rol": "dogrulama", "gecti": sapma < 5.0, "sapma_yuzde": sapma,
            "r_sont_kullanilan_ohm": r, "zaman_damgasi_unix": ts,
            "referans": {"akim_a_turetilen": akim_a}}


def test_kalibrasyon_v12_kurallari():
    iyi = [_kat(), _dog(110.0, 0.0165), _dog(120.0, 0.0348, sapma=2.0)]
    assert me.kalibrasyonlari_denetle(iyi, 200.0) == (0.13, 2.0)
    kotu = {
        "katsayi yok": iyi[1:],
        "iki katsayi": [_kat(), _kat(105.0)] + iyi[1:],
        "kararsiz": [_kat(kararli=False)] + iyi[1:],
        "tek dogrulama": iyi[:2],
        "dogrulama kaldi": [_kat(), _dog(110.0, 0.0165), _dog(120.0, 0.0348, sapma=6.0)],
        "farkli R": [_kat(), _dog(110.0, 0.0165), _dog(120.0, 0.0348, r=0.1)],
        "katsayidan once": [_kat(), _dog(90.0, 0.0165), _dog(120.0, 0.0348)],
        "akimlar yakin": [_kat(), _dog(110.0, 0.0313), _dog(120.0, 0.0348)],
        "olcumden sonra": [_kat(), _dog(110.0, 0.0165), _dog(250.0, 0.0348)],
    }
    for ad, kayitlar in kotu.items():
        with pytest.raises(me.SeriGecersiz):
            me.kalibrasyonlari_denetle(kayitlar, 200.0)
            pytest.fail(ad)


def test_etkin_sont_ve_katsayi_ozeti():
    from agent import calibrate_ina219 as ki
    # INA219 nominal hesapla 40,4 mA, gerçek 31,0 mA -> 0,1303 ohm
    assert ina.etkin_sont_ohm(0.0404, 0.0310) == pytest.approx(0.130322, rel=1e-5)
    oz = ki.katsayi_ozeti([0.0404, 0.0405, 0.0404], 0.0310)
    assert oz["kararli"] and oz["yayilim_yuzde"] == pytest.approx(0.2475, rel=1e-3)
    assert not ki.katsayi_ozeti([0.0400, 0.0405, 0.0410], 0.0310)["kararli"]
    with pytest.raises(ValueError):
        ina.etkin_sont_ohm(0.04, 0.0)


def test_seri_sonucu_etkin_sont_ve_nominal():
    orn = [_ornek(t * 0.2, 0.25) for t in range(850)] + \
          [_ornek(170 + t * 0.2, 0.30) for t in range(850)]
    bos, yuk, e, e_nom = me.seri_sonucu(orn, (0.0, 170.0), (170.0, 340.0), 4000, 0.13)
    # aynı ham şönt gerilimi, 0,13 ohm ile 0,1'e göre 1/1,3 kat akım
    assert e["guc_farki_w"] == pytest.approx(e_nom["guc_farki_w"] / 1.3, rel=1e-3)
    assert e_nom["guc_farki_w"] == pytest.approx(0.6, rel=1e-3)


def test_bench_ciktisi():
    metin = ("varyant   : float\nkosum_sayisi   : 2019  (isinma 3 haric)\n"
             "beklenen_deger : -3950.990722656  (dogruluk kontrolu)\n"
             "medyan  :     84.132 ms\n")
    c = me.bench_ciktisi_coz(metin)
    assert c == {"kosum_sayisi": 2019, "isinma": 3,
                 "beklenen_deger": "-3950.990722656", "medyan_ms": 84.132}
