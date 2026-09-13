"""Altın referans QAOA çözücü. Faz 1 T022-T024.

Bu modülün çıktısı Faz 2'nin donanım çekirdeğini doğrulayacak referanstır
(Anayasa Prensip IV). En iyi turun yanında HAM GENLİK VEKTÖRÜ de üretilir —
Faz 2'nin genlik-genlik kıyası buna bağlıdır (spec FR-014, FR-017).

Kübit tavanı: problem 16 kübiti aşamaz (Anayasa Prensip III). 5 durak ->
(5-1)^2 = 16 kübit, tam tavanda. 6 durak 25 kübit ister ve reddedilir.
"""
from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
import qiskit
import qiskit_aer
from qiskit import QuantumCircuit
from qiskit.circuit.library import QAOAAnsatz
from qiskit.quantum_info import SparsePauliOp
from qiskit_aer import AerSimulator

from services.qubo import qubo as qubo_mod

MAX_QUBITS = 16  # Anayasa Prensip III


@dataclass(frozen=True)
class ReferenceResult:
    amplitudes: np.ndarray       # complex128, (2^V,)
    probabilities: np.ndarray    # float64, (2^V,)
    best_tour: list[int]
    best_energy: float
    optimal_probability: float   # optimal turu olcme olasiligi (FR-016)
    p: int
    seed: int
    qubit_order: str             # "little" | "big" — DG-02, olculur, varsayilmaz
    backend: str
    n_qubits: int


def _olc_qubit_order() -> str:
    """Qiskit'in kübit sıralama konvansiyonunu ÖLÇEREK belirler.

    DG-02 riski (risk-register.md) bu karisikligi "yuksek olasilikli" isaretliyor
    ve imzasi sinsi: fidelity ~ 0 ama genlik buyuklukleri dogru. Varsaymak yerine
    bilinen bir devreyle olcuyoruz.

    Test: 2 kubitlik devrede yalnizca qubit 0'a X uygula. Sonuc |01> ise
    (indeks 1) Qiskit kubit 0'i EN DUSUK anlamli bit olarak yerlestiriyor
    demektir -> little-endian.
    """
    qc = QuantumCircuit(2)
    qc.x(0)
    qc.save_statevector()
    sim = AerSimulator(method="statevector")
    sv = np.asarray(sim.run(qc).result().get_statevector())
    return "little" if abs(sv[1]) > 0.5 else "big"


def _qubo_to_ising(problem: qubo_mod.QUBOProblem) -> tuple[SparsePauliOp, float]:
    """QUBO'yu Ising Hamiltonian'ına çevirir: x_i = (1 - z_i)/2."""
    Q = problem.Q
    n = problem.n_vars

    h = np.zeros(n)
    J = np.zeros((n, n))
    offset = 0.0

    for i in range(n):
        offset += Q[i, i] / 2.0
        h[i] -= Q[i, i] / 2.0
        for j in range(i + 1, n):
            q = Q[i, j] + Q[j, i]
            if q == 0.0:
                continue
            offset += q / 4.0
            h[i] -= q / 4.0
            h[j] -= q / 4.0
            J[i, j] += q / 4.0

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

    if not terimler:
        terimler = [("I" * n, 0.0)]
    return SparsePauliOp.from_list(terimler), offset


def _tum_enerjiler(problem: qubo_mod.QUBOProblem) -> np.ndarray:
    """Her temel durumun QUBO enerjisi. V<=16 oldugu icin tam tarama yapilabilir."""
    n = problem.n_vars
    boyut = 2**n
    idx = np.arange(boyut, dtype=np.uint32)
    # little-endian: bit i -> degisken i
    bits = ((idx[:, None] >> np.arange(n)) & 1).astype(np.float64)
    return np.einsum("bi,ij,bj->b", bits, problem.Q, bits)


def run(
    problem: qubo_mod.QUBOProblem,
    *,
    p: int,
    seed: int,
    shots: int | None = None,
) -> ReferenceResult:
    """Altın referansı üretir.

    shots=None -> tam statevector (varsayılan ve tercih edilen): tüm durumların
    genlikleri elde edilir, Faz 2 kıyası bunu gerektirir.
    """
    if problem.n_vars > MAX_QUBITS:
        raise ValueError(
            f"Problem {problem.n_vars} kubit istiyor, tavan {MAX_QUBITS} "
            f"(Anayasa Prensip III). {problem.n_stops} durak fazla — en fazla 5."
        )
    if p not in (1, 2):
        raise ValueError(f"p yalnizca 1 veya 2 olabilir, verilen {p}")

    n = problem.n_vars
    cost_op, _offset = _qubo_to_ising(problem)

    ansatz = QAOAAnsatz(cost_operator=cost_op, reps=p)
    rng = np.random.default_rng(seed)
    params = rng.uniform(0, np.pi, ansatz.num_parameters)

    qc = ansatz.assign_parameters(params)
    qc = qc.decompose(reps=3)
    qc.save_statevector()

    sim = AerSimulator(method="statevector", seed_simulator=seed)
    sv = np.asarray(sim.run(qc).result().get_statevector(), dtype=np.complex128)

    probs = np.abs(sv) ** 2
    enerjiler = _tum_enerjiler(problem)

    # Referansin raporladigi en iyi tur: taranan tum durumlar icinden GECERLI
    # olanlarin en dusuk enerjilisi. Tam statevector tum uzayi kapsadigi icin
    # bu kaba kuvvet optimaliyle eslesmek zorundadir.
    en_iyi_enerji = np.inf
    en_iyi_tur: list[int] | None = None
    en_iyi_idx = -1
    for idx in np.argsort(enerjiler):
        bits = np.array([(idx >> k) & 1 for k in range(n)], dtype=np.int8)
        tur = qubo_mod.assignment_to_tour(problem, bits)
        if tur is not None:
            en_iyi_enerji = float(enerjiler[idx])
            en_iyi_tur = tur
            en_iyi_idx = int(idx)
            break

    if en_iyi_tur is None:
        raise RuntimeError("Hicbir gecerli tur bulunamadi — QUBO formulasyonu bozuk")

    return ReferenceResult(
        amplitudes=sv,
        probabilities=probs,
        best_tour=en_iyi_tur,
        best_energy=en_iyi_enerji,
        optimal_probability=float(probs[en_iyi_idx]),
        p=p,
        seed=seed,
        qubit_order=_olc_qubit_order(),
        backend=f"aer_simulator_statevector/{qiskit_aer.__version__}",
        n_qubits=n,
    )
