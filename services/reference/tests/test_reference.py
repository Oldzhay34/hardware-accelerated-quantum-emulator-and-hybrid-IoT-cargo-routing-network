"""T017/T021 — Altın referans kaba kuvvetle doğrulanıyor mu (spec SC-002, FR-015)."""
import numpy as np
import pytest

from services.qubo import brute_force, qubo
from services.reference import qaoa_reference


@pytest.mark.parametrize("p", [1, 2])
def test_en_iyi_tur_kaba_kuvvet_optimaliyle_ayni(fixture_matrix_5x5, p):
    """SC-002: %100 eşleşme.

    QAOA'nin OLASILIK DAGILIMI optimali bulmayabilir (p yetersizse) — bu bir
    hata degil, olculecek bir ozelliktir. Ama referansin RAPORLADIGI en iyi tur,
    tarattigi durumlar icinden en dusuk enerjilisidir ve bu kaba kuvvet
    optimaliyle eslesmek ZORUNDADIR: tam statevector tum durumlari kapsiyor.
    """
    problem = qubo.matrix_to_qubo(fixture_matrix_5x5)
    ref = qaoa_reference.run(problem, p=p, seed=42)
    bf = brute_force.solve(fixture_matrix_5x5)

    assert ref.best_tour == bf.optimal_tour


def test_optimali_bulma_orani_olculebiliyor(fixture_matrix_5x5):
    """FR-016: oran ölçülür ve raporlanır; hedef değer dayatılmaz."""
    problem = qubo.matrix_to_qubo(fixture_matrix_5x5)
    ref = qaoa_reference.run(problem, p=1, seed=42)

    assert 0.0 <= ref.optimal_probability <= 1.0
    assert isinstance(ref.optimal_probability, float)


def test_alti_durak_reddedilir():
    """Anayasa Prensip III: 16 kübit tavanı. 6 durak 25 kübit ister."""
    d = np.array(
        [[0, 1, 2, 3, 4, 5],
         [1, 0, 1, 2, 3, 4],
         [2, 1, 0, 1, 2, 3],
         [3, 2, 1, 0, 1, 2],
         [4, 3, 2, 1, 0, 1],
         [5, 4, 3, 2, 1, 0]],
        dtype=np.float64,
    )
    problem = qubo.matrix_to_qubo(d)
    assert problem.n_vars == 25

    with pytest.raises(ValueError, match="16"):
        qaoa_reference.run(problem, p=1, seed=1)


def test_dort_durak_calisir(fixture_matrix_4x4):
    """4 durak -> 9 kübit, tavanın altında."""
    problem = qubo.matrix_to_qubo(fixture_matrix_4x4)
    ref = qaoa_reference.run(problem, p=1, seed=7)
    bf = brute_force.solve(fixture_matrix_4x4)
    assert ref.best_tour == bf.optimal_tour
