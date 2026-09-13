"""T018 — Aynı tohum aynı sonucu veriyor mu (spec FR-018, Anayasa Prensip II).

Tekrarlanabilirlik olmadan olcum durustlugu saglanamaz: Faz 2'nin kiyas yaptigi
referans, aylar sonra yeniden uretildiginde ayni cikmali.
"""
import numpy as np

from services.qubo import qubo
from services.reference import qaoa_reference


def test_ayni_tohum_bit_birebir_ayni(fixture_matrix_5x5):
    problem = qubo.matrix_to_qubo(fixture_matrix_5x5)

    a = qaoa_reference.run(problem, p=1, seed=42)
    b = qaoa_reference.run(problem, p=1, seed=42)

    assert np.array_equal(a.amplitudes, b.amplitudes), "genlikler bit-birebir ayni olmali"
    assert a.best_tour == b.best_tour
    assert a.best_energy == b.best_energy


def test_farkli_tohum_farkli_sonuc(fixture_matrix_5x5):
    """Tohum gercekten etkili mi — sabit bir devre kosulmuyor olsun."""
    problem = qubo.matrix_to_qubo(fixture_matrix_5x5)

    a = qaoa_reference.run(problem, p=1, seed=1)
    b = qaoa_reference.run(problem, p=1, seed=2)

    assert not np.array_equal(a.amplitudes, b.amplitudes)


def test_tohum_sonuca_kaydediliyor(fixture_matrix_5x5):
    problem = qubo.matrix_to_qubo(fixture_matrix_5x5)
    ref = qaoa_reference.run(problem, p=2, seed=123)
    assert ref.seed == 123
    assert ref.p == 2
