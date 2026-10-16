"""`scripts/build_comparison_matrix.py` testleri — kart ve GPU gerekmez.

Gerçek kayıtlardan kurulan matris (docs/measurements, commit'li) ve saf oran
kuralları sınanır. Koşum: `.venv\\Scripts\\python.exe -m pytest scripts/tests`
"""
import json
import re
import sys
from pathlib import Path

import pytest

KOK = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(KOK / "scripts"))
import build_comparison_matrix as bcm                          # noqa: E402

OLCUM = KOK / "docs" / "measurements"


@pytest.fixture(scope="module")
def m():
    return bcm.matris_kur()


# --- SC-007: hiçbir hücre elle yazılmaz -----------------------------------
def test_betikte_olcum_sayisi_yazili_degil():
    """Ölçülmüş değerler betikte sabit olarak geçmemeli; yalnız kayıtlardan okunur."""
    kaynak = (KOK / "scripts" / "build_comparison_matrix.py").read_text(encoding="utf-8")
    for sayi in ("84.132", "36.57", "3.273", "0.997", "0.0217", "0.0127", "0.01715",
                 "0.01493", "1.446", "32.75", "41.93", "0.644", "2.30", "11.2", "36.7"):
        assert not re.search(r"(?<![\d.])" + re.escape(sayi), kaynak), sayi


def test_her_hucre_kaynagini_tasir(m):
    for katman in (m["ana_tablo"]["hucreler"], m["aer_katmani"]["hucreler"]):
        for pf, h in katman.items():
            for eksen in ("gecikme", "enerji"):
                assert h[eksen] is not None, (pf, eksen, h[f"{eksen}_hatasi"])
                assert (OLCUM / h[eksen]["kaynak"]["dosya"]).exists(), (pf, eksen)


def test_hucreler_kayitlarla_ayni(m):
    h = m["ana_tablo"]["hucreler"]
    kg = json.loads((OLCUM / "kart-gecikme_20260927_201475a_n16_p2.json").read_text(encoding="utf-8"))
    assert h["fpga"]["gecikme"]["medyan_ms"] == kg["seri"]["ozet"]["cekirdek"]["seri"]["medyan_s"] * 1000
    ke = json.loads((OLCUM / "kart-enerji_20261008_47b15b1.json").read_text(encoding="utf-8"))
    f2 = [s["enerji"]["enerji_j_kosum"] for s in ke["seriler"] if s["ad"] == "F2"]
    assert h["fpga"]["enerji"]["tekrarlar_j"] == f2
    e4 = json.loads((OLCUM / "enerji-batarya_20261003_f15dd47_E4.json").read_text(encoding="utf-8"))
    assert h["cpu"]["enerji"]["j_kosum"] == e4["kosum_basina_j"]


# --- FR-012: konfigürasyon kayıttan okunur ----------------------------------
def test_her_hucre_ayni_konfig(m):
    for katman in (m["ana_tablo"]["hucreler"], m["aer_katmani"]["hucreler"]):
        for h in katman.values():
            for eksen in ("gecikme", "enerji"):
                k = h[eksen]["konfig"]
                assert (k["n"], k["p"]) == (16, 2)
                assert k["problem"]["baglanti"]


def test_fpga_bit_parmak_izi_beyan_olarak_isaretli(m):
    k = m["ana_tablo"]["hucreler"]["fpga"]["gecikme"]["konfig"]["problem"]
    assert k["tur"] == "fpga_bits" and k["baglanti"] == "beyan"


def test_parmak_izi_baglantisi_calisma_aninda_dogrulanir():
    k = bcm.problem_kaniti(OLCUM, "arm_float", "-3950.990722656")
    assert k["baglanti"].startswith("dogrulandi")


def test_konfig_uyumsuzlugu_hucre_uretmez():
    with pytest.raises(bcm.KonfigUyumsuz):
        bcm.konfig_denetle(16, 1, {})
    with pytest.raises(bcm.KonfigUyumsuz):
        bcm.problem_kaniti(OLCUM, "ad", "reference_20260915_c6ad872_p1_n5.json")
    with pytest.raises(bcm.KonfigUyumsuz):
        bcm.problem_kaniti(OLCUM, "float", "-9799.875")


# --- SC-008 ve tasarım v1 oran kuralları ---------------------------------------
def _e(j, kapsam="kart-5v-girisi", guvenilir=True, tekrar=None):
    d = {"j_kosum": j, "kapsam_anahtari": kapsam, "gecerli": True, "guvenilir": guvenilir}
    if tekrar:
        d["tekrarlar_j"] = tekrar
    return d


def test_enerji_orani_yalniz_ayni_kapsamda():
    r = bcm.enerji_orani(_e(2.0, "tum-dizustu"), _e(1.0))
    assert r["oran"] is None and "kapsam" in r["not"]
    r = bcm.enerji_orani(_e(2.0), _e(1.0))
    assert r["oran"] == 2.0 and r["ifade"] == "FPGA 2.00x az"


def test_enerji_orani_guvenilmezse_null():
    r = bcm.enerji_orani(_e(2.0, guvenilir=False), _e(1.0))
    assert r["oran"] is None and "guvenilmez" in r["not"]


def test_enerji_orani_tekrar_araligi():
    r = bcm.enerji_orani(_e(0.9, tekrar=[0.8, 1.0]), _e(1.0, tekrar=[0.95, 1.05]))
    assert r["aralik_tekrar"] == pytest.approx([0.8 / 1.05, 1.0 / 0.95])
    assert r["ifade"] == "FPGA %11 fazla"


def _g(medyan, p25=None, p75=None, gecerli=True):
    return {"medyan_ms": medyan, "p25_ms": p25, "p75_ms": p75, "gecerli": gecerli}


def test_gecikme_orani():
    r = bcm.gecikme_orani(_g(80.0, 79.0, 81.0), _g(40.0, 39.0, 41.0), "ARM")
    assert r["oran"] == 2.0 and r["ifade"] == "FPGA 2.00x hizli"
    assert r["aralik_ceyrek"] == pytest.approx([79.0 / 41.0, 81.0 / 39.0])
    r = bcm.gecikme_orani(_g(4.0), _g(40.0, 39.0, 41.0), "CPU")
    assert r["ifade"] == "CPU 10.0x hizli" and r["aralik_ceyrek"] is None and r["not"]
    assert bcm.gecikme_orani(_g(4.0, gecerli=False), _g(40.0), "CPU")["oran"] is None


# --- matrisin kendisi ----------------------------------------------------------
def test_ana_tablo_oranlari(m):
    o = m["ana_tablo"]["fpgaya_gore_oranlar"]
    assert o["arm"]["gecikme"]["oran"] > 1 > o["cpu"]["gecikme"]["oran"] > o["gpu"]["gecikme"]["oran"]
    assert o["arm"]["enerji"]["oran"] is not None                   # aynı kapsam
    assert o["cpu"]["enerji"]["oran"] is None and o["gpu"]["enerji"]["oran"] is None
    assert not m["ana_tablo"]["hucreler"]["gpu"]["enerji"]["guvenilir"]


def test_aer_katmani_fpgayla_kiyaslanmaz(m):
    assert "fpgaya_gore_oranlar" not in m["aer_katmani"]
    assert "KIYASLANMAZ" in m["aer_katmani"]["oranlar"]["not"]
    assert m["aer_katmani"]["oranlar"]["gpu_cpu_enerji"]["oran"] is None    # E2 guvenilmez


def test_faz2_tabani_disarida(m):
    assert m["disarida_birakilan"] and "gecersiz" in m["disarida_birakilan"][0]["neden"]


def test_kontrol_notu_hucreye_eklenir_ama_yerine_gecmez(tmp_path):
    k = {"protokol": "priz-pil-kontrol-protokolu v1.0", "gecerli": True,
         "karar_G": {"guc_kaynagi_etkisi": "yok", "taban": "yeniden_uretilemedi_bugun_hizli"},
         "karar_K": {"guc_kaynagi_etkisi": "yok", "taban": "yeniden_uretildi"}}
    yol = tmp_path / "priz-pil-kontrol_20261016_abc1234.json"
    yol.write_text(json.dumps(k), encoding="utf-8")
    m = bcm.matris_kur(kontrol=yol)
    g = m["ana_tablo"]["hucreler"]["gpu"]["gecikme"]
    assert g["kontrol"]["taban"] == "yeniden_uretilemedi_bugun_hizli" and "GECMEZ" in g["kontrol"]["kural"]
    assert g["medyan_ms"] == bcm.matris_kur()["ana_tablo"]["hucreler"]["gpu"]["gecikme"]["medyan_ms"]
    assert m["ana_tablo"]["hucreler"]["cpu"]["gecikme"]["kontrol"]["taban"] == "yeniden_uretildi"
