"""Referans genliklerini diske yazar/okur. Faz 1 T025.

Faz 2 bu .npy dosyasini DOGRUDAN okuyacak. JSON metadata'si olmadan hangi
tohum/konvansiyonla uretildigi bilinemez -> risk VR-03 (olcum karisikligi) ve
DG-02 (endian karisikligi).
"""
from __future__ import annotations

import json
import math
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

    def _json_sayi(x: float):
        """NaN/Inf JSON standardında YOKTUR; json.dumps bunları `NaN` diye yazar
        ve standart ayrıştırıcılar (Faz 2'nin C++ testbench'i dahil) çuvallar.
        Tanımsız değer `null` olarak yazılır — 0.0 yazmak, olmayan bir sonucu
        varmış gibi göstermek olurdu."""
        return x if math.isfinite(x) else None

    meta = stamp.stamp(p=result.p, seed=result.seed, n_qubits=result.n_qubits)
    meta.update(
        {
            "best_tour": result.best_tour,
            "best_energy": _json_sayi(result.best_energy),
            "optimal_probability": _json_sayi(result.optimal_probability),
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
            # Faz 2 (2026-09-15): referansin YENIDEN URETILEBILIR olmasi icin
            # zorunlu alanlar. Bunlar olmadan donanim cekirdegi ayni devreyi
            # kosamaz, dolayisiyla genlik kiyasi yapilamaz (FR-006).
            "params": result.params,
            "ising_h": result.ising_h,
            "ising_J": result.ising_J,
            "ising_offset": result.ising_offset,
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
        # null (tanimsiz) -> nan. Sentetik referanslarda "en iyi tur" yoktur.
        best_energy=float(meta["best_energy"]) if meta.get("best_energy") is not None else float("nan"),
        optimal_probability=(float(meta["optimal_probability"])
                             if meta.get("optimal_probability") is not None else float("nan")),
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
        # Faz 2 oncesi uretilmis dosyalarda bu alanlar yok. Bos donerler ve
        # tuketen taraf (testbench) bunu ACIKCA hata olarak bildirmelidir —
        # sessizce sifir kabul edip yanlis devre kosmak en kotu sonuctur.
        params=dict(meta.get("params", {})),
        ising_h=list(meta.get("ising_h", [])),
        ising_J=[list(r) for r in meta.get("ising_J", [])],
        ising_offset=float(meta.get("ising_offset", 0.0)),
    )

