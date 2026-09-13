"""T009 — QUBO enerjisi ile gerçek tur uzunluğu tutarlı mı (spec FR-010)."""
import itertools

import numpy as np
import pytest

from services.qubo import brute_force, qubo


def tour_length(durations: np.ndarray, tour: list[int]) -> float:
    """Kapalı turun gerçek uzunluğu."""
    return sum(durations[tour[i]][tour[(i + 1) % len(tour)]] for i in range(len(tour)))


def tour_to_assignment(problem: qubo.QUBOProblem, tour: list[int]) -> np.ndarray:
    """Turu one-hot atamaya çevirir (başlangıç şehri sabit, değişkeni yok)."""
    a = np.zeros(problem.n_vars, dtype=np.int8)
    for zaman, sehir in enumerate(tour[1:]):  # tour[0] == 0, sabit
        a[problem.var_map[(sehir, zaman)]] = 1
    return a


def test_enerji_siralamasi_tur_uzunlugu_siralamasiyla_ayni(fixture_matrix_5x5):
    """Geçerli turların enerji sıralaması = gerçek tur uzunluğu sıralaması."""
    d = fixture_matrix_5x5
    problem = qubo.matrix_to_qubo(d)

    kayitlar = []
    for tour in brute_force.all_tours(5):
        a = tour_to_assignment(problem, tour)
        kayitlar.append((qubo.energy(problem, a), tour_length(d, tour), tour))

    assert len(kayitlar) == 24, "5 durak icin (5-1)! = 24 tur olmali"

    enerjiye_gore = [k[2] for k in sorted(kayitlar, key=lambda k: k[0])]
    uzunluga_gore = [k[2] for k in sorted(kayitlar, key=lambda k: k[1])]
    assert enerjiye_gore == uzunluga_gore


def test_enerji_tur_uzunlugunu_sabit_farkla_izler(fixture_matrix_5x5):
    """Geçerli turlarda enerji - tur uzunluğu farkı sabit olmalı (ceza terimleri sabit katkı)."""
    d = fixture_matrix_5x5
    problem = qubo.matrix_to_qubo(d)

    farklar = []
    for tour in brute_force.all_tours(5):
        a = tour_to_assignment(problem, tour)
        farklar.append(qubo.energy(problem, a) - tour_length(d, tour))

    assert np.allclose(farklar, farklar[0]), "gecerli turlarda fark sabit olmali"


def test_assignment_to_tour_gidis_donus(fixture_matrix_5x5):
    """Tur -> atama -> tur dönüşümü kayıpsız."""
    problem = qubo.matrix_to_qubo(fixture_matrix_5x5)
    for tour in brute_force.all_tours(5):
        a = tour_to_assignment(problem, tour)
        assert qubo.assignment_to_tour(problem, a) == tour


def test_gecersiz_atama_none_dondurur(fixture_matrix_5x5):
    """Kısıt ihlalinde None döner — 'en yakın gecerli tur' uydurulmaz."""
    problem = qubo.matrix_to_qubo(fixture_matrix_5x5)
    hepsi_bir = np.ones(problem.n_vars, dtype=np.int8)
    assert qubo.assignment_to_tour(problem, hepsi_bir) is None


@pytest.mark.parametrize("bozuk", ["kare_degil", "kosegen", "nan", "inf"])
def test_bozuk_matris_valueerror(fixture_matrix_5x5, bozuk):
    d = fixture_matrix_5x5.copy()
    if bozuk == "kare_degil":
        d = d[:, :3]
    elif bozuk == "kosegen":
        d[2][2] = 5.0
    elif bozuk == "nan":
        d[0][1] = np.nan
    else:
        d[0][1] = np.inf
    with pytest.raises(ValueError):
        qubo.matrix_to_qubo(d)
