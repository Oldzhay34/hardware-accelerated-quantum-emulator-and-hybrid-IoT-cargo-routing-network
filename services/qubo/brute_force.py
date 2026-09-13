"""Kaba kuvvet TSP çözücü — mutlak gerçek. Faz 1 T016.

Tur sayısı (N-1)!, N! DEĞİL. Başlangıç şehri sabitlendiğinde aynı çevrimsel tur
N kez tekrar sayılmaz. N=5 -> 24 tur. Bkz. data-model.md §5.

Bu modül altın referansın doğruluğunu bağımsız olarak ölçer (spec FR-015).
"""
from __future__ import annotations

import itertools
from dataclasses import dataclass
from typing import Iterator

import numpy as np

MAX_N = 8  # 8 durak -> 5040 tur; ustu pratik degil


@dataclass(frozen=True)
class BruteForceResult:
    all_tours: list[list[int]]
    optimal_tour: list[int]
    optimal_length: float


def all_tours(n: int) -> Iterator[list[int]]:
    """Başlangıç şehri 0'da sabit, kalan (n-1) şehrin tüm permütasyonları."""
    if n < 2:
        raise ValueError("En az 2 durak gerekli")
    for perm in itertools.permutations(range(1, n)):
        yield [0, *perm]


def tour_length(durations: np.ndarray, tour: list[int]) -> float:
    """Kapalı turun toplam süresi (son duraktan başlangıca dönüş dahil)."""
    return float(
        sum(durations[tour[i]][tour[(i + 1) % len(tour)]] for i in range(len(tour)))
    )


def solve(durations: np.ndarray) -> BruteForceResult:
    """Tüm turları sayarak mutlak optimali bulur."""
    durations = np.asarray(durations, dtype=np.float64)
    n = durations.shape[0]
    if durations.ndim != 2 or durations.shape[0] != durations.shape[1]:
        raise ValueError("Matris kare olmali")
    if n > MAX_N:
        raise ValueError(f"Kaba kuvvet en fazla {MAX_N} durak icin; verilen {n}")

    turlar = list(all_tours(n))
    uzunluklar = [tour_length(durations, t) for t in turlar]
    en_iyi = int(np.argmin(uzunluklar))

    return BruteForceResult(
        all_tours=turlar,
        optimal_tour=turlar[en_iyi],
        optimal_length=uzunluklar[en_iyi],
    )
