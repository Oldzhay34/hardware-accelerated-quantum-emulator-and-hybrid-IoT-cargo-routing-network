"""n = 8 ve 12 için SENTETİK altın referans üretir. T021 / SC-001.

Neden gerekli: SC-001 fidelity'nin n = 8, 12, 16 için AYRI AYRI ölçülmesini
istiyor (FR-003: kübit sayısı parametrik olmalı). Ama tek-sıcak TSP
formülasyonunda kübit sayısı (N-1)² olduğu için yalnızca 4, 9, 16 mümkün —
8 ve 12'nin problem karşılığı YOKTUR.

Çözüm: aynı YAPIDA (köşegen maliyet + RX karıştırıcı) ama rastgele katsayılı
bir QAOA devresi. Amaç TSP çözmek değil, çekirdeğin kübit sayısına göre
parametrik çalıştığını kanıtlamak. Altın referans yine Qiskit/Aer'dir
(Anayasa Prensip IV) — çekirdeğin kendi çıktısı referans olarak kullanılmaz.

Kullanım:
    .venv/Scripts/python.exe scripts/make_synthetic_reference.py --n 8 --p 2
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
import qiskit_aer
from qiskit import transpile
from qiskit.circuit.library import QAOAAnsatz
from qiskit.quantum_info import SparsePauliOp
from qiskit_aer import AerSimulator

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from services.common import stamp
from services.reference import amplitudes
from services.reference.qaoa_reference import ReferenceResult, _olc_qubit_order


def rastgele_ising(n: int, seed: int) -> tuple[np.ndarray, np.ndarray]:
    """Rastgele ama GERÇEKÇİ ölçekli Ising katsayıları.

    Ölçek, 5 duraklı TSP QUBO'sundakine yakın tutulur (~1e3) ki faz
    akümülatörünün tur temsili gerçek koşuldaki gibi sınansın — küçük
    katsayılarla test etmek, asıl zorlanan yolu atlamak olurdu.
    """
    rng = np.random.default_rng(seed)
    h = rng.uniform(-1500.0, 1500.0, n)
    J = np.zeros((n, n))
    for i in range(n):
        for j in range(i + 1, n):
            J[i, j] = rng.uniform(-1500.0, 1500.0)
    return h, J


def ising_to_pauli(h: np.ndarray, J: np.ndarray, n: int) -> SparsePauliOp:
    """`_qubo_to_ising` ile AYNI Pauli dizgi sırasını kullanır (ters çevrilmiş)."""
    terimler = []
    for i in range(n):
        if h[i] != 0.0:
            p = ["I"] * n
            p[i] = "Z"
            terimler.append(("".join(reversed(p)), h[i]))
    for i in range(n):
        for j in range(i + 1, n):
            if J[i, j] != 0.0:
                p = ["I"] * n
                p[i] = p[j] = "Z"
                terimler.append(("".join(reversed(p)), J[i, j]))
    return SparsePauliOp.from_list(terimler)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, required=True)
    ap.add_argument("--p", type=int, default=2)
    ap.add_argument("--seed", type=int, default=42)
    a = ap.parse_args()

    if a.n % 2 != 0 or not (2 <= a.n <= 16):
        raise SystemExit("n cift ve 2..16 araliginda olmali")

    kok = Path(__file__).resolve().parents[1]
    h, J = rastgele_ising(a.n, a.seed)
    cost_op = ising_to_pauli(h, J, a.n)

    ansatz = QAOAAnsatz(cost_operator=cost_op, reps=a.p)
    qc_sablon = ansatz.decompose(reps=3)
    rng = np.random.default_rng(a.seed)
    params = rng.uniform(0, np.pi, ansatz.num_parameters)
    qc = qc_sablon.assign_parameters(params)
    qc.save_statevector()

    sim = AerSimulator(method="statevector", seed_simulator=a.seed)
    sv = np.asarray(sim.run(transpile(qc, sim)).result().get_statevector(),
                    dtype=np.complex128)

    # Sentetik problemin "en iyi turu" yok — bu alanlar anlamsız, dürüstçe
    # boş bırakılıyor. Testbench yalnızca params/ising_*/qubit_order kullanır.
    sonuc = ReferenceResult(
        amplitudes=sv,
        probabilities=np.abs(sv) ** 2,
        best_tour=[],
        best_energy=float("nan"),
        optimal_probability=float("nan"),
        p=a.p,
        seed=a.seed,
        qubit_order=_olc_qubit_order(),
        backend=f"aer_simulator_statevector/{qiskit_aer.__version__}",
        n_qubits=a.n,
        optimizer="none (sentetik — optimizasyon yok)",
        optimizer_iterations=0,
        params={pr.name: float(v) for pr, v in zip(qc_sablon.parameters, params)},
        ising_h=[float(x) for x in h],
        ising_J=[[float(x) for x in satir] for satir in J],
        ising_offset=0.0,
    )
    ad = f"{stamp.stamped_name('synthref')}_p{a.p}_n{a.n}"
    npy, js = amplitudes.save(sonuc, stamp.measurements_dir(kok) / ad)
    print(f"n={a.n}, p={a.p}, {len(qc.data)} kapi, norm={np.linalg.norm(sv):.12f}")
    print(f"  {npy.name}")
    print(f"  {js.name}")


if __name__ == "__main__":
    main()
