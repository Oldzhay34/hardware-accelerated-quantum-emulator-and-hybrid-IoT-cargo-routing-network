"""Iki donanim davranisini OLCER — C++ yazmadan once karari verdirir.

1. Kuantalama kipi: Vitis varsayilani AP_TRN (asagi kirpma) mi, AP_RND_CONV
   (yakina yuvarlama) mi? Yuvarlama daha pahalidir; bedelini hak ediyor mu?
2. Kapi basina yeniden normalizasyon: format_fidelity.py her kapidan sonra
   normalize ediyordu. Gercek donanim bunu yapmaz (tam gecis + ters karekok).
   Yapmazsak fidelity ne oluyor?
"""
import sys, json, time
from pathlib import Path
import numpy as np
from qiskit.circuit.library import QAOAAnsatz
from qiskit.quantum_info import Statevector
sys.path.insert(0, '.')
from services.common import stamp
from services.qubo import qubo as qubo_mod
from services.reference import qaoa_reference
from services.reference.cli import ornek_matris

FRAC = 17
OLCEK = 1 << FRAC
UST = 1.0 - 1.0 / OLCEK

def q_rnd_sat(v):
    """AP_RND_CONV + AP_SAT — numpy round = yakina, yarim ise cifte."""
    re = np.clip(np.round(v.real * OLCEK) / OLCEK, -1.0, UST)
    im = np.clip(np.round(v.imag * OLCEK) / OLCEK, -1.0, UST)
    return re + 1j * im

def q_trn_sat(v):
    """AP_TRN + AP_SAT — eksi sonsuza kirpma (Vitis varsayilani kuantalama)."""
    re = np.clip(np.floor(v.real * OLCEK) / OLCEK, -1.0, UST)
    im = np.clip(np.floor(v.imag * OLCEK) / OLCEK, -1.0, UST)
    return re + 1j * im

def q_rnd_wrap(v):
    """AP_RND_CONV + AP_WRAP — Vitis varsayilani tasma kipi."""
    def w(x):
        q = np.round(x * OLCEK).astype(np.int64)
        q = ((q + OLCEK) % (2 * OLCEK)) - OLCEK      # 18-bit iki'ye tumleyen sarma
        return q / OLCEK
    return w(v.real) + 1j * w(v.imag)

def evrimle(qc, kuantize, normalize):
    sv = Statevector.from_int(0, 2 ** qc.num_qubits)
    for k in qc.data:
        sv = sv.evolve(k.operation, [qc.find_bit(q).index for q in k.qubits])
        v = kuantize(np.asarray(sv.data))
        if normalize:
            n = np.linalg.norm(v)
            if n > 0: v = v / n
        sv = Statevector(v)
    return np.asarray(sv.data)

def fid(a, b):
    a = a / np.linalg.norm(a); b = b / np.linalg.norm(b)
    return float(abs(np.vdot(a, b)) ** 2)

problem = qubo_mod.matrix_to_qubo(ornek_matris(5))
cost_op, _ = qaoa_reference._qubo_to_ising(problem)
a = QAOAAnsatz(cost_operator=cost_op, reps=2)
qc = a.decompose(reps=3).assign_parameters(
    np.random.default_rng(42).uniform(0, np.pi, a.num_parameters))
print(f"Devre: {len(qc.data)} kapi, 16 kubit, Q1.{FRAC}\n")

ref = evrimle(qc, lambda v: v, True)
sonuc = {}
print(f"  {'kuantalama':<28} {'normalizasyon':<16} {'fidelity':>14}  {'H(.999)':>8}")
for ad, fn in [("AP_RND_CONV + AP_SAT", q_rnd_sat),
               ("AP_TRN + AP_SAT (Vitis vars.)", q_trn_sat),
               ("AP_RND_CONV + AP_WRAP (vars.)", q_rnd_wrap)]:
    for nrm_ad, nrm in [("her kapida", True), ("YOK", False)]:
        t0 = time.perf_counter()
        f = fid(ref, evrimle(qc, fn, nrm))
        print(f"  {ad:<28} {nrm_ad:<16} {f:>14.9f}  {'GECTI' if f>=0.999 else 'KALDI':>8}"
              f"   ({time.perf_counter()-t0:.0f} sn)")
        sonuc[f"{ad} | {nrm_ad}"] = {"fidelity": f, "H_gecti": f >= 0.999}

meta = stamp.stamp(problem="5-durak-16-kubit", format="Q1.17", seed=42,
                   not_="ap_fixed kip secimi icin OLCUM")
meta["sonuclar"] = sonuc
yol = stamp.measurements_dir(Path('.')) / f"{stamp.stamped_name('apfixed-kip')}.json"
yol.write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")
print(f"\nYazildi: {yol.name}")
