"""Sayı formatının fidelity'ye etkisini ÖLÇER. Faz 2 araştırma adımı (b şıkkı).

Faz 2 promptu soruyor: "float32 vs Q1.15 için 16 qubit ve p=2 QAOA derinliğinde
birikimli hata (Qiskit'e karşı state fidelity)".

Bu tahmin edilmez, ölçülür (Anayasa Prensip II). Donanım GEREKMEZ (Prensip V):
sabit-nokta aritmetiği CPU'da taklit edilir — her kapıdan sonra genlikler hedef
formata yuvarlanır, tıpkı donanımın yapacağı gibi.

Kullanım:
    .venv/Scripts/python.exe scripts/format_fidelity.py
"""
from __future__ import annotations

import json
import time
from pathlib import Path

import numpy as np
from qiskit.circuit.library import QAOAAnsatz
from qiskit.quantum_info import Statevector

import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from services.common import stamp
from services.qubo import qubo as qubo_mod
from services.reference import qaoa_reference


# ----------------------------------------------------------------- formatlar
def q_fixed(v: np.ndarray, frac_bits: int) -> np.ndarray:
    """Qm.f sabit-nokta yuvarlaması. Q1.15 -> frac_bits=15.

    Donanımın yapacağı şey: her genliğin reel ve sanal kısmı ayrı ayrı
    2^-frac_bits çözünürlüğüne yuvarlanır ve [-1, 1) aralığına kırpılır.
    """
    olcek = 1 << frac_bits
    ust = 1.0 - 1.0 / olcek
    re = np.clip(np.round(v.real * olcek) / olcek, -1.0, ust)
    im = np.clip(np.round(v.imag * olcek) / olcek, -1.0, ust)
    return re + 1j * im


FORMATLAR = {
    "complex128 (referans)": lambda v: v,
    "float32 (complex64)": lambda v: v.astype(np.complex64).astype(np.complex128),
    "Q1.15": lambda v: q_fixed(v, 15),
    "Q1.23": lambda v: q_fixed(v, 23),   # ara secenek: 24-bit sabit nokta
}


def fidelity(a: np.ndarray, b: np.ndarray) -> float:
    """|<a|b>|^2, ikisi de normalize edilerek."""
    a = a / np.linalg.norm(a)
    b = b / np.linalg.norm(b)
    return float(abs(np.vdot(a, b)) ** 2)


def kapi_kapi_evrimle(qc, kuantize) -> np.ndarray:
    """Devreyi kapı kapı uygular; HER KAPIDAN SONRA kuantize eder.

    Donanımın davranışını taklit eden kısım burası: gerçek bir sabit-nokta
    çekirdek her kapı sonrası sonucu kendi formatında saklar, hata birikir.
    """
    n = qc.num_qubits
    sv = Statevector.from_int(0, 2**n)
    for komut in qc.data:
        sv = sv.evolve(komut.operation, list(qc.find_bit(q).index for q in komut.qubits))
        v = kuantize(np.asarray(sv.data))
        nrm = np.linalg.norm(v)
        if nrm > 0:
            v = v / nrm          # donanim da periyodik normalize eder
        sv = Statevector(v)
    return np.asarray(sv.data)


def main() -> None:
    kok = Path(__file__).resolve().parents[1]

    # Faz 1'in referans problemini aynen kullan (5 durak -> 16 kubit)
    sys.path.insert(0, str(kok))
    from services.reference.cli import ornek_matris

    d = ornek_matris(5)
    problem = qubo_mod.matrix_to_qubo(d)
    print(f"Problem: {problem.n_stops} durak -> {problem.n_vars} kubit")

    cost_op, _ = qaoa_reference._qubo_to_ising(problem)
    sonuclar = {}

    for p in (1, 2):
        ansatz = QAOAAnsatz(cost_operator=cost_op, reps=p)
        qc_sablon = ansatz.decompose(reps=3)
        rng = np.random.default_rng(42)
        params = rng.uniform(0, np.pi, ansatz.num_parameters)
        qc = qc_sablon.assign_parameters(params)

        kapi_sayisi = len(qc.data)
        print(f"\n=== p={p} | devre {kapi_sayisi} kapi ===")

        # Referans: tam duyarlik
        t0 = time.perf_counter()
        ref = kapi_kapi_evrimle(qc, FORMATLAR["complex128 (referans)"])
        print(f"  referans evrimi: {time.perf_counter()-t0:.1f} sn")

        sonuclar[f"p={p}"] = {"kapi_sayisi": kapi_sayisi, "formatlar": {}}
        for ad, fn in FORMATLAR.items():
            if ad.startswith("complex128"):
                continue
            t0 = time.perf_counter()
            v = kapi_kapi_evrimle(qc, fn)
            f = fidelity(ref, v)
            sure = time.perf_counter() - t0
            print(f"  {ad:22s} fidelity = {f:.9f}   ({sure:.1f} sn)")
            sonuclar[f"p={p}"]["formatlar"][ad] = {"fidelity": f, "sure_sn": round(sure, 1)}

    # --- Bit genisligi taramasi: esigi gecen EN UCUZ format hangisi? ---
    print("\n=== Bit genisligi taramasi (p=2, en zorlu durum) ===")
    ansatz = QAOAAnsatz(cost_operator=cost_op, reps=2)
    qc = ansatz.decompose(reps=3).assign_parameters(
        np.random.default_rng(42).uniform(0, np.pi, ansatz.num_parameters)
    )
    ref2 = kapi_kapi_evrimle(qc, lambda v: v)

    tarama = {}
    print(f"  {'toplam bit':>10} {'Qm.f':>8} {'fidelity':>14} {'M(.99)':>8} {'H(.999)':>9} {'bayt/genlik':>12}")
    for frac in (11, 13, 15, 17, 19, 21, 23):
        toplam_bit = frac + 1                      # 1 isaret biti
        v = kapi_kapi_evrimle(qc, lambda a, f=frac: q_fixed(a, f))
        f_deg = fidelity(ref2, v)
        bayt = 2 * toplam_bit / 8                  # reel + sanal
        print(f"  {toplam_bit:>10} {'Q1.'+str(frac):>8} {f_deg:>14.9f} "
              f"{'GECTI' if f_deg>=0.99 else 'KALDI':>8} {'GECTI' if f_deg>=0.999 else 'KALDI':>9} "
              f"{bayt:>12.1f}")
        tarama[f"Q1.{frac}"] = {
            "toplam_bit": toplam_bit, "fidelity": f_deg,
            "M_gecti": f_deg >= 0.99, "H_gecti": f_deg >= 0.999,
            "bayt_per_genlik": bayt,
            "statevector_KB": round(65536 * bayt / 1024, 1),
        }
    sonuclar["bit_taramasi_p2"] = tarama

    # Kaydet
    meta = stamp.stamp(problem="5-durak-16-kubit", seed=42)
    meta["sonuclar"] = sonuclar
    meta["esikler"] = {"M": 0.99, "H": 0.999}
    yol = stamp.measurements_dir(kok) / f"{stamp.stamped_name('format-fidelity')}.json"
    yol.write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\nYazildi: {yol.name}")


if __name__ == "__main__":
    main()
