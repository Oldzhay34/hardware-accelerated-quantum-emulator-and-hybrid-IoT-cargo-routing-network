"""T019/T020 — Ham genlikler Faz 2'nin kıyasına hazır mı (spec SC-008, FR-014/017)."""
import numpy as np
import pytest

from services.qubo import qubo
from services.reference import amplitudes, qaoa_reference


@pytest.fixture
def ref5(fixture_matrix_5x5):
    problem = qubo.matrix_to_qubo(fixture_matrix_5x5)
    return qaoa_reference.run(problem, p=1, seed=42)


def test_genlikler_complex128_ve_16_kubit(ref5):
    """Faz 2 bu diziyi dogrudan okuyacak."""
    assert ref5.amplitudes.dtype == np.complex128
    assert ref5.amplitudes.shape == (2**16,)
    assert len(ref5.amplitudes) == 65536


def test_norm_bir(ref5):
    """SC-008: tolerans 1e-9."""
    assert abs(np.linalg.norm(ref5.amplitudes) - 1.0) < 1e-9


def test_olasiliklar_tutarli(ref5):
    assert np.allclose(ref5.probabilities, np.abs(ref5.amplitudes) ** 2)
    assert abs(ref5.probabilities.sum() - 1.0) < 1e-9


def test_qubit_order_acikca_dolu(ref5):
    """DG-02 riski: endian karisikligi. Varsayilmaz, YAZILIR."""
    assert ref5.qubit_order in ("little", "big")


def test_kaydet_yukle_kayipsiz(ref5, tmp_path):
    yol = tmp_path / "ref_test"
    amplitudes.save(ref5, yol)

    assert yol.with_suffix(".npy").exists()
    assert yol.with_suffix(".json").exists()

    geri = amplitudes.load(yol)
    assert np.array_equal(geri.amplitudes, ref5.amplitudes)
    assert geri.best_tour == ref5.best_tour
    assert geri.seed == ref5.seed
    assert geri.p == ref5.p
    assert geri.qubit_order == ref5.qubit_order
    assert geri.backend == ref5.backend


def test_metadata_damgali(ref5, tmp_path):
    """VR-03: damgasiz olcum gecersiz."""
    import json

    yol = tmp_path / "ref_damga"
    amplitudes.save(ref5, yol)
    meta = json.loads(yol.with_suffix(".json").read_text(encoding="utf-8"))

    assert "stamped_at" in meta
    assert "git_hash" in meta
    assert meta["qubit_order"] in ("little", "big")
