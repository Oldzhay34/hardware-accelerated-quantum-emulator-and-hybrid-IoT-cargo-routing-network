"""T010/T011 — Ceza katsayısı doğru mu (spec SC-003, FR-009)."""
import itertools

import numpy as np

from services.qubo import brute_force, qubo
from services.qubo.tests.test_qubo_energy import tour_length, tour_to_assignment


def test_her_ihlal_her_gecerli_turdan_pahali(fixture_matrix_4x4):
    """SC-003: ihlal sayısı 0 olmalı.

    4 durak -> 9 degisken -> 512 atama. Hepsi tek tek denenir; bu test
    ornekleme yapmaz, TUM uzayi tarar.
    """
    d = fixture_matrix_4x4
    problem = qubo.matrix_to_qubo(d)

    gecerli, gecersiz = [], []
    for bitler in itertools.product([0, 1], repeat=problem.n_vars):
        a = np.array(bitler, dtype=np.int8)
        e = qubo.energy(problem, a)
        (gecerli if qubo.assignment_to_tour(problem, a) is not None else gecersiz).append(e)

    assert gecerli, "en az bir gecerli tur bulunmali"
    assert gecersiz, "en az bir gecersiz atama bulunmali"

    ihlal = [e for e in gecersiz if e <= max(gecerli)]
    assert not ihlal, (
        f"{len(ihlal)} gecersiz atama, en pahali gecerli turdan ucuz: "
        f"max(gecerli)={max(gecerli):.1f}, min(ihlal)={min(ihlal):.1f}"
    )


def test_ceza_matristen_turetiliyor_sabit_degil(fixture_matrix_5x5):
    """FR-009: max(matris) degisince penalty_A da degismeli."""
    p1 = qubo.matrix_to_qubo(fixture_matrix_5x5)
    p2 = qubo.matrix_to_qubo(fixture_matrix_5x5 * 3.0)

    assert p2.penalty_A > p1.penalty_A
    assert np.isclose(p2.penalty_A, p1.penalty_A * 3.0)


def test_ceza_max_mesafeden_buyuk(fixture_matrix_5x5):
    """A > max(mesafe) kurali."""
    problem = qubo.matrix_to_qubo(fixture_matrix_5x5)
    assert problem.penalty_A > fixture_matrix_5x5.max()


def test_epsilon_ceza_katsayisini_etkiler(fixture_matrix_5x5):
    kucuk = qubo.matrix_to_qubo(fixture_matrix_5x5, epsilon=0.1)
    buyuk = qubo.matrix_to_qubo(fixture_matrix_5x5, epsilon=0.5)
    assert buyuk.penalty_A > kucuk.penalty_A
