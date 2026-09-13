"""T012 — Kaba kuvvet tur sayısı (N-1)! olmalı, N! değil.

Faz 1 promptu "brute-force (5! tur)" diyor. Başlangıç şehri sabitlendiğinde —
ki QUBO'nun 16 kübitte kalması için sabitlenmek ZORUNDA — gerçek sayı 4! = 24'tür.
120 üzerinden dolaşmak aynı turu 5 kez sayardı. Bkz. data-model.md §5.
"""
import math

import pytest

from services.qubo import brute_force


@pytest.mark.parametrize("n,beklenen", [(3, 2), (4, 6), (5, 24), (6, 120)])
def test_tur_sayisi_n_eksi_bir_faktoriyel(n, beklenen):
    turlar = list(brute_force.all_tours(n))
    assert len(turlar) == beklenen == math.factorial(n - 1)


def test_bes_durak_yirmidort_tur_yuzyirmi_degil():
    """Promptdaki '5! = 120' ifadesine karsi acik kontrol."""
    assert len(list(brute_force.all_tours(5))) == 24
    assert len(list(brute_force.all_tours(5))) != 120


def test_tum_turlar_sifirdan_baslar(fixture_matrix_5x5):
    for tour in brute_force.all_tours(5):
        assert tour[0] == 0
        assert sorted(tour) == [0, 1, 2, 3, 4], "her sehir tam bir kez"


def test_optimal_gercekten_en_kisa(fixture_matrix_5x5):
    d = fixture_matrix_5x5
    sonuc = brute_force.solve(d)

    def uzunluk(t):
        return sum(d[t[i]][t[(i + 1) % len(t)]] for i in range(len(t)))

    assert sonuc.optimal_length == pytest.approx(uzunluk(sonuc.optimal_tour))
    assert all(uzunluk(t) >= sonuc.optimal_length for t in brute_force.all_tours(5))
    assert len(sonuc.all_tours) == 24


def test_buyuk_n_reddedilir(fixture_matrix_5x5):
    import numpy as np

    with pytest.raises(ValueError):
        brute_force.solve(np.zeros((9, 9)))
