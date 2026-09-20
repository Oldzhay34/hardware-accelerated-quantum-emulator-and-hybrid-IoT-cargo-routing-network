"""Konak kodlayıcı testleri — G2 kapısının ilk yarısı (görev T024).

**Kart gerekmez** (Anayasa Prensip V, madde H-5). Bu testler geçmeden
kodlayıcı kart yoluna bağlanmaz; bağlanırsa kartta çıkan her uyuşmazlık
"donanım mı, kodlayıcı mı" belirsizliğinde kalır.

Referans: `hls/tb/tb_kernel.cpp` (`tura_cevir`, `real_t` atamaları) ve
`specs/003-zynq-ps-kartta-kosum/contracts/`.
"""
import math

import pytest

from agent import cost_vectors
from agent.encoder import (
    AralikDisi, BETA_WORD, COST_H, COST_WORD, MASKE_18, N_QUBITS, P_MAX,
    PHASES_WORD, PHASE_SCALE, REAL_Q_MAX, REAL_Q_MIN, REAL_SCALE,
    TOPLAM_YAZMA, beta_dizileri, cost_dizisi, faz_worda, kosum_kodla,
    olcek_bul, olcekle, phases_dizisi, real_worda, word_reale,
)


# =========================================================================
# Q1.17 paketleme — sınır değerleri
# =========================================================================
@pytest.mark.parametrize("x, beklenen", [
    (0.0, 0),
    (0.5, 65536),
    (0.25, 32768),
    (-0.5, 0x30000),                      # -65536 ikiye tümleyen, 18 bit
    (-1.0, 0x20000),                      # REAL_Q_MIN, en küçük değer
    (REAL_Q_MAX / REAL_SCALE, 0x1FFFF),   # +1 - 2^-17, en büyük değer
])
def test_real_worda_sinirlar(x, beklenen):
    assert real_worda(x) == beklenen


def test_real_worda_isaret_genisletmesi_yok():
    """Üst 14 bit sıfırlanır — maskeleme tek belirlenimci davranıştır."""
    w = real_worda(-0.5)
    assert w == w & MASKE_18
    assert w < (1 << 18)


def test_real_worda_gidis_donus():
    for x in (0.0, 0.1, -0.1, 0.9, -0.9, 0.123456, -0.987654):
        assert word_reale(real_worda(x)) == pytest.approx(x, abs=1.0 / REAL_SCALE)


def test_real_worda_yakinsak_yuvarlama():
    """`AP_RND_CONV` = yarıyı çifte yuvarlar; `floor(x+0.5)` DEĞİL.

    Python'un `round`'u da yarıyı çifte yuvarlar, bu yüzden eşleşirler.
    `floor(x+0.5)` kullanılsaydı 0,5 → 1 olurdu ve C'den ayrışırdı.
    """
    assert real_worda(0.5 / REAL_SCALE) == 0      # 0,5 -> 0 (çift)
    assert real_worda(1.5 / REAL_SCALE) == 2      # 1,5 -> 2 (çift)
    assert real_worda(2.5 / REAL_SCALE) == 2      # 2,5 -> 2 (çift)


# =========================================================================
# Madde H-3 — kırpma sessiz olamaz
# =========================================================================
@pytest.mark.parametrize("x", [1.0, 1.5, -1.001, 12345.0, -9999.9])
def test_h3_aralik_disi_istisna(x):
    with pytest.raises(AralikDisi):
        real_worda(x, ad="test")


def test_h3_tam_ust_sinirin_bir_ustu_de_atar():
    """`1 - 2^-18` yuvarlanınca `REAL_Q_MAX`'ı aşar → istisna."""
    with pytest.raises(AralikDisi):
        real_worda(1.0 - 2.0 ** -19)


def test_h3_sonsuz_ve_nan():
    for x in (float("inf"), float("-inf"), float("nan")):
        with pytest.raises(AralikDisi):
            real_worda(x)


def test_h3_cost_dizisinde_de_gecerli():
    h = [0.0] * N_QUBITS
    h[3] = 2.0                                   # ölçeklenmemiş
    J = [[0.0] * N_QUBITS for _ in range(N_QUBITS)]
    with pytest.raises(AralikDisi) as e:
        cost_dizisi(h, J)
    assert "h[3]" in str(e.value)


# =========================================================================
# TUR paketleme (phase_t) — sarma HATA DEĞİL (madde H-4)
# =========================================================================
TAU = 2.0 * math.pi


@pytest.mark.parametrize("aci, beklenen", [
    (0.0, 0),
    (TAU / 2, PHASE_SCALE // 2),
    (TAU / 4, PHASE_SCALE // 4),
    (-TAU / 4, 3 * PHASE_SCALE // 4),      # negatif -> +1 kaydırılır
    (TAU, 0),                              # tam tur -> 0
    (-TAU, 0),
])
def test_faz_worda_sinirlar(aci, beklenen):
    assert faz_worda(aci) == beklenen


def test_faz_worda_buyuk_aci_sarar_istisna_atmaz():
    """Madde H-4: `|gamma*h| ~ 1e4` burada **beklenen** durumdur."""
    for aci in (TAU * 1e4, -TAU * 1e4 + TAU / 8, 12345.6789):
        w = faz_worda(aci)
        assert 0 <= w < PHASE_SCALE


def test_faz_worda_hep_18_bit():
    for aci in (0.1, -0.1, 1e3, -1e3, TAU - 1e-12):
        assert faz_worda(aci) == faz_worda(aci) & MASKE_18


# =========================================================================
# Ölçekleme protokolü (H-1, H-2, H-6)
# =========================================================================
def _ornek_katsayilar(buyukluk=1.0):
    h = [buyukluk * (0.5 - (k % 7) / 10.0) for k in range(N_QUBITS)]
    J = [[0.0] * N_QUBITS for _ in range(N_QUBITS)]
    for a in range(N_QUBITS):
        for b in range(a + 1, N_QUBITS):
            J[a][b] = buyukluk * (((a * 3 + b * 5) % 11) / 11.0 - 0.5)
    return h, J


def test_h2_olcek_sonrasi_mutlak_deger_birden_kucuk():
    """Kenar payı olmasaydı en büyük katsayı tam 1,0'a oturur ve AP_SAT kırpardı."""
    h, J = _ornek_katsayilar(buyukluk=1e4)
    S = olcek_bul(h, J)
    ho, Jo = olcekle(h, J, S)
    enb = max(max(abs(v) for v in ho),
              max(abs(Jo[a][b]) for a in range(N_QUBITS)
                  for b in range(a + 1, N_QUBITS)))
    assert enb < 1.0
    assert enb == pytest.approx(1.0 / 1.001, rel=1e-9)


def test_olcek_hepsi_sifirken_bire_duser():
    h = [0.0] * N_QUBITS
    J = [[0.0] * N_QUBITS for _ in range(N_QUBITS)]
    assert olcek_bul(h, J) == 1.0


def test_h6_ham_beklenen_geri_donusu():
    h, J = _ornek_katsayilar(buyukluk=1e4)
    k = kosum_kodla(h, J, [0.7], [0.3], p=1)
    assert k.ham_bekleneni_coz(2.5) == pytest.approx(2.5 * k.olcek)
    assert k.olcek > 1.0                       # gerçekten ölçeklendi
    assert k.h_ham == h                        # ham ayrı saklanıyor


def test_h1_olcek_kaydediliyor():
    h, J = _ornek_katsayilar(buyukluk=1e4)
    k = kosum_kodla(h, J, [0.7], [0.3], p=1)
    assert k.olcek == pytest.approx(olcek_bul(h, J))


def test_buyuk_katsayilar_istisna_atmaz_olcekleme_hallediyor():
    """1e4 mertebesi tam da sözleşmenin uyardığı durum — geçmeli."""
    h, J = _ornek_katsayilar(buyukluk=1e4)
    kosum_kodla(h, J, [0.7, 1.1], [0.3, 0.9], p=2)


# =========================================================================
# Dizi yerleşimi (contracts/axi-register-map.md)
# =========================================================================
def test_word_sayilari():
    assert COST_WORD == 272
    assert PHASES_WORD == 816 == P_MAX * COST_WORD
    assert TOPLAM_YAZMA == 1095


def test_cost_dizisi_yerlesimi():
    h = [0.0] * N_QUBITS
    J = [[0.0] * N_QUBITS for _ in range(N_QUBITS)]
    h[5] = 0.25
    J[2][7] = -0.5
    w = cost_dizisi(h, J)
    assert len(w) == COST_WORD
    assert w[5] == real_worda(0.25)
    assert w[COST_H + N_QUBITS * 2 + 7] == real_worda(-0.5)


def test_cost_alt_ucgen_sifir_kalir():
    """`a >= b` okunmaz ama 256 word'ün tamamı yazılır — sıfır olmalı."""
    h, J = _ornek_katsayilar(0.5)
    for a in range(N_QUBITS):
        for b in range(a + 1):
            J[a][b] = 0.9              # üretici doldurmasa da kodlayıcı okumamalı
    w = cost_dizisi(h, J)
    for a in range(N_QUBITS):
        for b in range(a + 1):
            assert w[COST_H + N_QUBITS * a + b] == 0


def test_phases_dizisi_yerlesimi_ve_katman_ofseti():
    h = [0.0] * N_QUBITS
    J = [[0.0] * N_QUBITS for _ in range(N_QUBITS)]
    h[1] = 1000.0                      # ham — ölçeklenmeyecek
    gammalar = [0.3, 0.6]
    w = phases_dizisi(h, J, gammalar)
    assert len(w) == PHASES_WORD
    for r, g in enumerate(gammalar):
        assert w[r * COST_WORD + 1] == faz_worda(-g * 1000.0)
    # kullanılmayan 3. katman sıfır
    assert all(v == 0 for v in w[2 * COST_WORD:])


def test_phases_ham_kullanir_olcekli_degil():
    """Fazlar ölçeklenseydi devrenin hazırladığı durum değişirdi."""
    h, J = _ornek_katsayilar(buyukluk=1e4)
    k = kosum_kodla(h, J, [0.7], [0.3], p=1)
    beklenen = faz_worda(-0.7 * h[0])          # HAM h ile
    assert k.phases[0] == beklenen
    olcekli = faz_worda(-0.7 * h[0] / k.olcek)
    assert beklenen != olcekli                 # ayrım gerçekten görünür


def test_yazma_sayisi_1095():
    h, J = _ornek_katsayilar(0.5)
    k = kosum_kodla(h, J, [0.7], [0.3], p=1)
    assert k.yazma_sayisi == 1095


# =========================================================================
# beta — C referansıyla aynı doyurma, ama sessiz değil
# =========================================================================
def test_beta_cos_sifir_doyar_ve_uyarir():
    """`cos(0) = 1,0` Q1.17'ye sığmaz; C referansı da doyurur (tb:176)."""
    c, s, uyarilar = beta_dizileri([0.0])
    assert c[0] == REAL_Q_MAX & MASKE_18
    assert s[0] == 0
    assert len(uyarilar) == 1 and "cos_beta[0]" in uyarilar[0]


def test_beta_normal_deger_uyarmaz():
    c, s, uyarilar = beta_dizileri([0.3, 1.1])
    assert uyarilar == []
    assert c[0] == real_worda(math.cos(0.3))
    assert s[1] == real_worda(math.sin(1.1))
    assert len(c) == len(s) == BETA_WORD


def test_beta_uyarisi_kosuma_tasiniyor():
    h, J = _ornek_katsayilar(0.5)
    k = kosum_kodla(h, J, [0.7], [0.0], p=1)
    assert k.doyma_uyarilari, "doyma sessiz kalmamalı"


# =========================================================================
# p doğrulaması (madde A-3)
# =========================================================================
@pytest.mark.parametrize("p", [0, 4, -1])
def test_a3_gecersiz_p(p):
    h, J = _ornek_katsayilar(0.5)
    with pytest.raises(AralikDisi):
        kosum_kodla(h, J, [0.7] * max(p, 1), [0.3] * max(p, 1), p=p)


def test_p_ile_parametre_sayisi_tutarsizsa_atar():
    h, J = _ornek_katsayilar(0.5)
    with pytest.raises(AralikDisi):
        kosum_kodla(h, J, [0.7], [0.3], p=2)


# =========================================================================
# İzdüşüm vektörleri (madde H-7)
# =========================================================================
def test_h7_yirmi_vektor_uretilir():
    seri = cost_vectors.uret(20)
    assert len(seri) == 20
    assert seri.tohum == 20260920


def test_h7_ayni_tohum_ayni_vektorler():
    a = cost_vectors.uret(5, tohum=42)
    b = cost_vectors.uret(5, tohum=42)
    assert a.vektorler == b.vektorler


def test_h7_farkli_tohum_farkli_vektorler():
    a = cost_vectors.uret(5, tohum=1)
    b = cost_vectors.uret(5, tohum=2)
    assert a.vektorler != b.vektorler


def test_h7_vektorler_bagimsiz():
    """Asıl mesele bu: bağımlı vektörler bağımsız kısıt üretmez."""
    seri = cost_vectors.uret(20)
    duz = [cost_vectors._duzlestir(v["h"], v["J"]) for v in seri.vektorler]
    for i in range(len(duz)):
        for j in range(i + 1, len(duz)):
            c = abs(cost_vectors._kosinus(duz[i], duz[j]))
            assert c <= cost_vectors.BAGIMLILIK_ESIGI, \
                "vektör {} ve {} bağımlı: |cos|={:.3f}".format(i, j, c)


def test_h7_katlar_elenir():
    """Bir vektörün katı, kosinüs ölçütüne takılmalı (|cos| = 1)."""
    seri = cost_vectors.uret(3, tohum=7)
    v = cost_vectors._duzlestir(seri.vektorler[0]["h"], seri.vektorler[0]["J"])
    kat = [3.5 * x for x in v]
    assert abs(cost_vectors._kosinus(v, kat)) == pytest.approx(1.0)
    assert abs(cost_vectors._kosinus(v, kat)) > cost_vectors.BAGIMLILIK_ESIGI


def test_h7_sifir_vektor_bagimli_sayilir():
    sifir = [0.0] * 136
    v = [1.0] * 136
    assert cost_vectors._kosinus(sifir, v) == 1.0


def test_h7_vektorler_aralik_icinde_ve_ust_ucgen():
    seri = cost_vectors.uret(5)
    for v in seri.vektorler:
        assert len(v["h"]) == N_QUBITS
        assert all(-1.0 <= x < 1.0 for x in v["h"])
        for a in range(N_QUBITS):
            for b in range(a + 1):
                assert v["J"][a][b] == 0.0        # alt üçgen ve köşegen sıfır


def test_h7_uretilen_vektorler_kodlanabiliyor():
    """Uçtan uca: üretici → ölçekleme → paketleme, istisna olmadan."""
    seri = cost_vectors.uret(3)
    for v in seri.vektorler:
        k = kosum_kodla(v["h"], v["J"], [0.7], [0.3], p=1)
        assert len(k.cost) == COST_WORD
        assert len(k.phases) == PHASES_WORD
