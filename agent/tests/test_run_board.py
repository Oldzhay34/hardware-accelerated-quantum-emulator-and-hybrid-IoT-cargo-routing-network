"""`agent/run_board.py` testleri — **kart gerekmez**.

En değerli test `test_devreyi_kodla_c_dokumuyle_ayni`: koşucunun ürettiği
`phases`/`cos_beta`/`sin_beta` dizilerini, G2 kapısında C tarafının döktüğü
word'lerle **bit bit** karşılaştırır. Koşucu farklı bir devre kurarsa kartta
çıkan sapma "donanım mı kodlayıcı mı" belirsizliğinde kalırdı.
"""
import json
import os
import struct

import pytest

from agent import run_board

KOK = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
REFERANS = os.path.join(KOK, "docs", "measurements",
                        "reference_20260915_c6ad872_p2_n5.json")
C_WORDS = os.path.join(KOK, "hls", "build", "c_words.json")
VEKTORLER = os.path.join(KOK, "artifacts", "izdusum_vektorleri.json")
BEKLENEN = os.path.join(KOK, "artifacts", "izdusum_beklenen.json")


def _yukle(yol):
    if not os.path.isfile(yol):
        pytest.skip("dosya yok: {}".format(yol))
    with open(yol, encoding="utf-8") as f:
        return json.load(f)


def test_devreyi_kodla_c_dokumuyle_ayni():
    """Koşucunun kurduğu devre, C-sim'in kurduğuyla **bit bit** aynı olmalı."""
    ref = _yukle(REFERANS)
    c = _yukle(C_WORDS)
    phases, cb, sb, p, _ = run_board.devreyi_kodla(ref)
    assert p == c["p"]
    assert phases == c["phases"], "phases ayrisiyor"
    assert cb == c["cos_beta"]
    assert sb == c["sin_beta"]


def test_bits_donusumu():
    assert run_board._bits(-0.442401439) == 0xBEE28271


def test_param_bul_ada_bakar_siraya_degil():
    params = {u"\u03b2[1]": 1.5, u"\u03b3[0]": 0.3, u"\u03b2[0]": 0.7,
              u"\u03b3[1]": 0.9}
    assert run_board._param_bul(params, u"\u03b3", 0) == 0.3
    assert run_board._param_bul(params, u"\u03b2", 1) == 1.5
    with pytest.raises(KeyError):
        run_board._param_bul(params, u"\u03b3", 5)


# =========================================================================
# İzdüşüm dosyalarının tutarlılığı
# =========================================================================
def test_vektor_ve_beklenen_ayni_tohumdan():
    v, b = _yukle(VEKTORLER), _yukle(BEKLENEN)
    assert v["tohum"] == b["tohum"], "farkli tohumdan uretilmis dosyalar"
    assert len(v["kodlu"]) == len(b["beklenen"])


def test_en_az_20_izdusum():
    """Karar K1: 20'nin altı seriyi geçersiz kılar."""
    v = _yukle(VEKTORLER)
    assert len(v["kodlu"]) >= 20


def test_vektorler_bagimsiz():
    v = _yukle(VEKTORLER)
    assert v["en_buyuk_benzerlik"] <= v["bagimlilik_esigi"]


def test_her_izdusum_272_word():
    v = _yukle(VEKTORLER)
    for i, k in enumerate(v["kodlu"]):
        assert len(k["words"]) == 272, "izdusum {}".format(i)
        assert all(0 <= w <= 0x3FFFF for w in k["words"])


def test_beklenen_degerler_farkli():
    """Hepsi aynı çıksaydı izdüşümler bağımsız kısıt üretmiyor demekti."""
    b = _yukle(BEKLENEN)
    bitler = [x["bits"] for x in b["beklenen"]]
    assert len(set(bitler)) == len(bitler), "ayni beklenen deger tekrar ediyor"


def test_beklenen_bits_degerle_tutarli():
    """`bits` alanı `beklenen_deger` ile aynı sayıyı göstermeli."""
    b = _yukle(BEKLENEN)
    for x in b["beklenen"]:
        geri = struct.unpack("<f", struct.pack("<I", x["bits"]))[0]
        assert abs(geri - x["beklenen_deger"]) < 1e-6 * max(1.0, abs(geri))
