"""`agent/measure_latency.py` testleri — **kart gerekmez** (Anayasa Prensip V).

En değerli test `test_sabitler_dondurulmus_protokolle_ayni`: kod ile 🔒 v1.0
protokol belgesi ayrışırsa kırılır. Protokol sonuca bakıp değiştirilemez
(FR-011); kodun sessizce değişmesi aynı ihlalin başka bir yoludur.
"""
import os
import re

import pytest

from agent import measure_latency as ml

KOK = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
PROTOKOL = os.path.join(KOK, "docs", "measurements", "kart-olcum-protokolu.md")


def _protokol():
    with open(PROTOKOL, encoding="utf-8") as f:
        return f.read()


def test_sabitler_dondurulmus_protokolle_ayni():
    metin = _protokol()
    assert "DONDURULDU" in metin, "protokol dondurulmamis — olcum alinamaz"
    assert "**v1.0**" in metin and ml.PROTOKOL_SURUMU.endswith("v1.0")
    assert "ilk **3** koşumu atılır" in metin and ml.ISINMA == 3
    assert "**300 sn**" in metin and ml.SERI_SURE_S == 300.0
    assert "≥ 30 koşum" in metin and ml.KONTROL_ADET == 30
    assert "10 sn'lik pencerelere" in metin and ml.PENCERE_S == 10.0
    assert "son 6 pencere" in metin and ml.PLATO_PENCERE == 6
    assert "**±%0,5**" in metin and ml.PLATO_TOLERANS == 0.005
    assert "İlk 50 koşum ile son 60 sn" in metin
    assert ml.ILK_N == 50 and ml.SON_S == 60.0
    assert "10.000 kez" in metin and ml.YOKLAMA_OLCUM_N == 10000
    assert re.search(r"`kosum_sayisi < 10`", metin) and ml.MIN_KOSUM == 10


# ------------------------------------------------------------------ SC-004
def test_on_kosumdan_az_seri_uretilmez():
    with pytest.raises(ValueError, match="SC-004"):
        ml.olcum_serisi("k", "cekirdek", [0.03] * 9)


def test_tek_kosum_hic_uretilmez():
    with pytest.raises(ValueError):
        ml.olcum_serisi("k", "cekirdek", [0.0365])


def test_bilinmeyen_kapsam_reddedilir():
    with pytest.raises(ValueError, match="kapsam"):
        ml.olcum_serisi("k", "toplam", [0.03] * 10)


def test_ozet_alanlari_ve_degerleri():
    veri = [float(i) for i in range(1, 12)]            # 1..11
    s = ml.olcum_serisi("n16_p2", "cekirdek", veri)
    assert s["kosum_sayisi"] == 11
    assert s["medyan_s"] == 6.0
    assert s["p25_s"] == 3.5 and s["p75_s"] == 8.5     # dogrusal ara degerleme
    assert s["yayilim_s"] == 5.0                       # IQR
    assert s["min_s"] == 1.0 and s["max_s"] == 11.0 and s["jitter_s"] == 10.0
    assert s["protokol_surumu"] == ml.PROTOKOL_SURUMU


def test_aykiri_deger_atilmaz():
    """§7: zaman değerine bakarak koşum atılmaz — kuyruk maks'ta görünür."""
    veri = [0.0365] * 20 + [0.5]
    s = ml.olcum_serisi("k", "cekirdek", veri)
    assert s["kosum_sayisi"] == 21 and s["max_s"] == 0.5


# ---------------------------------------------------------------- pencere
def test_pencereler_baslangic_zamanina_gore_boler():
    zaman = [0.0, 5.0, 9.99, 10.0, 25.0]
    deger = [1.0, 2.0, 3.0, 4.0, 5.0]
    p = ml.pencereler(zaman, deger)
    assert [x["bas_s"] for x in p] == [0.0, 10.0, 20.0]
    assert [x["n"] for x in p] == [3, 1, 1]
    assert p[0]["medyan_s"] == 2.0


def _pen(medyanlar):
    return [{"bas_s": 10.0 * i, "n": 5, "medyan_s": m} for i, m in enumerate(medyanlar)]


def test_plato_sabitse_oturur():
    assert ml.plato(_pen([0.0370, 0.0365] + [0.03650] * 6))["oturdu"] is True


def test_plato_kayiyorsa_oturmaz():
    """Son 6 pencerede %2'lik kayma → uçlar ortalamadan ±%1 → ±%0,5 dışı."""
    kayan = [0.0365 * (1 + 0.004 * i) for i in range(6)]
    assert ml.plato(_pen(kayan))["oturdu"] is False


@pytest.mark.parametrize("sapma, beklenen", [(0.0049, True), (0.0051, False)])
def test_plato_siniri(sapma, beklenen):
    """§8 "±%0,5 içinde": ortalamaya simetrik ±sapma — sınırın iki yanı."""
    m = 0.0365
    medyanlar = [m * (1 - sapma), m * (1 + sapma), m, m, m, m]   # ortalama = m
    assert ml.plato(_pen(medyanlar))["oturdu"] is beklenen


def test_plato_pencere_yetmezse_hukum_yok():
    sonuc = ml.plato(_pen([0.0365] * 5))
    assert sonuc["oturdu"] is None and "yetersiz" in sonuc["neden"]


def test_ilk_ve_son_ayri_raporlanir():
    zaman = [0.5 * i for i in range(400)]              # 0..199.5 sn
    deger = [0.04] * 50 + [0.0365] * 350
    s = ml.ilk_ve_son("k", "cekirdek", zaman, deger)
    assert s["ilk_50_kosum"]["medyan_s"] == 0.04
    assert s["son_60_sn"]["medyan_s"] == 0.0365
