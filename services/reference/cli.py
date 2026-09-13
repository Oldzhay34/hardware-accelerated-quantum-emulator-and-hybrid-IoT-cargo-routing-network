"""Altın referans üretici CLI. Faz 1 T026-T027.

Gerçek süre ve bellek ÖLÇÜLÜR ve raporlanır (Anayasa Prensip II — tahmini
rakam yazılmaz). Çıktı docs/measurements/ altına damgalı yazılır (VR-03).
"""
from __future__ import annotations

import argparse
import time
import tracemalloc
from pathlib import Path

import numpy as np

from services.common import stamp
from services.qubo import brute_force, qubo
from services.reference import amplitudes, qaoa_reference


def ornek_matris(n: int) -> np.ndarray:
    """Sentetik İstanbul verisinden ilk n durakla matris kurar.

    Gerçek OSRM matrisi henüz yoksa (Phase 5 bitmemişse) bu, deterministik ve
    gerçekçi bir vekildir. Koordinatlar Faz 0.4'ün sentetik üreticisinden gelir.
    """
    import csv

    kok = Path(__file__).resolve().parents[2]
    csv_yolu = kok / "data" / "synthetic" / "deliveries.csv"
    satirlar = list(csv.DictReader(csv_yolu.open(encoding="utf-8")))[:n]
    pts = np.array([[float(r["lat"]), float(r["lon"])] for r in satirlar])

    # Haversine yaklasimi + yone bagli asimetri (gercek yol agini taklit eder).
    # NOT: Bu GERCEK surus suresi DEGILDIR; Phase 5'te OSRM matrisiyle degisir.
    R = 6371.0
    lat = np.radians(pts[:, 0])[:, None]
    lon = np.radians(pts[:, 1])[:, None]
    dlat = lat - lat.T
    dlon = lon - lon.T
    a = np.sin(dlat / 2) ** 2 + np.cos(lat) * np.cos(lat.T) * np.sin(dlon / 2) ** 2
    km = 2 * R * np.arcsin(np.sqrt(np.clip(a, 0, 1)))
    sn = km * 90.0  # ~40 km/s ortalama sehir ici hiz
    asimetri = 1.0 + 0.08 * np.sign(np.arange(n)[:, None] - np.arange(n)[None, :])
    m = sn * asimetri
    np.fill_diagonal(m, 0.0)
    return np.round(m, 1)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--stops", type=int, default=5)
    ap.add_argument("--p", type=int, required=True, choices=[1, 2])
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--matrix", type=Path, default=None, help="Gercek .npy matris (varsa)")
    args = ap.parse_args()

    if args.matrix and args.matrix.exists():
        d = np.load(args.matrix)[: args.stops, : args.stops]
        kaynak = str(args.matrix)
    else:
        d = ornek_matris(args.stops)
        kaynak = "sentetik-vekil (Faz 0.4 koordinatlari; OSRM DEGIL)"

    problem = qubo.matrix_to_qubo(d)
    print(f"Matris kaynagi : {kaynak}")
    print(f"Durak / kubit  : {args.stops} / {problem.n_vars}")
    print(f"Ceza katsayisi : {problem.penalty_A:.1f}  (max mesafe {d.max():.1f})")

    tracemalloc.start()
    t0 = time.perf_counter()
    ref = qaoa_reference.run(problem, p=args.p, seed=args.seed)
    sure = time.perf_counter() - t0
    tepe = tracemalloc.get_traced_memory()[1] / 1024**2
    tracemalloc.stop()

    bf = brute_force.solve(d)
    eslesme = ref.best_tour == bf.optimal_tour

    print(f"\n--- OLCULEN (tahmin degil) ---")
    print(f"QAOA suresi        : {sure*1000:.1f} ms  (optimizasyon dahil)")
    print(f"Tepe bellek        : {tepe:.2f} MB")
    print(f"Optimizer          : {ref.optimizer}, {ref.optimizer_iterations} degerlendirme")
    print(f"Beklenti (once/sonra): {ref.cost_before:.1f} -> {ref.cost_after:.1f}")
    print(f"Genlik sayisi      : {ref.amplitudes.size} ({ref.amplitudes.dtype})")
    print(f"Norm               : {np.linalg.norm(ref.amplitudes):.12f}")
    print(f"Kubit sirasi       : {ref.qubit_order}")
    print(f"\n--- DOGRULAMA ---")
    print(f"QAOA en iyi tur    : {ref.best_tour}  (enerji {ref.best_energy:.1f})")
    print(f"Kaba kuvvet optimal: {bf.optimal_tour}  (uzunluk {bf.optimal_length:.1f})")
    print(f"Taranan tur sayisi : {len(bf.all_tours)}  ((N-1)! = {args.stops-1}!)")
    print(f"ESLESME            : {'EVET' if eslesme else 'HAYIR'}")
    print(f"Optimali olcme olasiligi (p={args.p}): {ref.optimal_probability:.6f}")

    ad = stamp.stamped_name("reference", p=args.p, n=args.stops)
    yol = stamp.measurements_dir() / ad
    npy, js = amplitudes.save(ref, yol)
    print(f"\nYazildi: {npy.name} + {js.name}")

    if not eslesme:
        raise SystemExit("DOGRULAMA BASARISIZ: QAOA en iyi turu kaba kuvvet optimaliyle eslesmedi")


if __name__ == "__main__":
    main()
