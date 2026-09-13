"""Referans genliklerini diske yazar/okur. Faz 1 T025.

Faz 2 bu .npy dosyasini DOGRUDAN okuyacak. JSON metadata'si olmadan hangi
tohum/konvansiyonla uretildigi bilinemez -> risk VR-03 (olcum karisikligi) ve
DG-02 (endian karisikligi).
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np

from services.common import stamp
from services.reference.qaoa_reference import ReferenceResult


def save(result: ReferenceResult, path: str | Path) -> tuple[Path, Path]:
    """<path>.npy (complex128 genlikler) + <path>.json (metadata) yazar."""
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    npy = p.with_suffix(".npy")
    js = p.with_suffix(".json")

    np.save(npy, result.amplitudes)

    meta = stamp.stamp(p=result.p, seed=result.seed, n_qubits=result.n_qubits)
    meta.update(
        {
            "best_tour": result.best_tour,
            "best_energy": result.best_energy,
            "optimal_probability": result.optimal_probability,
            "p": result.p,
            "seed": result.seed,
            "qubit_order": result.qubit_order,
            "backend": result.backend,
            "n_qubits": result.n_qubits,
            "optimizer": result.optimizer,
            "optimizer_iterations": result.optimizer_iterations,
            "cost_before": result.cost_before,
            "cost_after": result.cost_after,
            "amplitudes_file": npy.name,
            "dtype": str(result.amplitudes.dtype),
            "length": int(result.amplitudes.size),
        }
    )
    js.write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")
    return npy, js


def load(path: str | Path) -> ReferenceResult:
    p = Path(path)
    amps = np.load(p.with_suffix(".npy"))
    meta = json.loads(p.with_suffix(".json").read_text(encoding="utf-8"))

    return ReferenceResult(
        amplitudes=amps,
        probabilities=np.abs(amps) ** 2,
        best_tour=list(meta["best_tour"]),
        best_energy=float(meta["best_energy"]),
        optimal_probability=float(meta["optimal_probability"]),
        p=int(meta["p"]),
        seed=int(meta["seed"]),
        qubit_order=meta["qubit_order"],
        backend=meta["backend"],
        n_qubits=int(meta["n_qubits"]),
        # eski dosyalarda (optimizasyon eklenmeden once) bu alanlar yok — geriye uyumlu varsayilan
        optimizer=meta.get("optimizer", "unassigned"),
        optimizer_iterations=int(meta.get("optimizer_iterations", 0)),
        cost_before=float(meta.get("cost_before", 0.0)),
        cost_after=float(meta.get("cost_after", 0.0)),
    )
