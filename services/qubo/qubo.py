"""One-hot TSP QUBO formülasyonu. Faz 1 T013-T015.

Hem altın referans (Faz 1) hem klasik çözücü (Faz 10) bu modülü AYNEN kullanır —
kıyasın adil olması buna bağlı (spec FR-011). İki çözücü farklı formülasyonla
çalışırsa aradaki fark algoritma farkı değil formülasyon farkı olur.

Değişken sayısı (N-1)^2: başlangıç şehri sabitlenir. N=5 -> 16 kübit, Anayasa
Prensip III tavanına birebir oturur.
"""
from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np


@dataclass(frozen=True)
class QUBOProblem:
    Q: np.ndarray              # (V, V) float64, simetrik
    penalty_A: float
    n_stops: int
    var_map: dict[tuple[int, int], int]  # (sehir, zaman) -> degisken indeksi

    @property
    def n_vars(self) -> int:
        return self.Q.shape[0]


def _dogrula(durations: np.ndarray) -> None:
    if durations.ndim != 2 or durations.shape[0] != durations.shape[1]:
        raise ValueError(f"Matris kare olmali, verilen: {durations.shape}")
    if not np.all(np.isfinite(durations)):
        # Prensip II: tanimsiz deger uydurulmaz, hata verilir (spec FR-007)
        raise ValueError("Matris inf/nan iceriyor — ulasilamayan cift sessizce doldurulamaz")
    if not np.allclose(np.diag(durations), 0.0):
        raise ValueError("Kosegen 0 olmali")
    if durations.shape[0] < 2:
        raise ValueError("En az 2 durak gerekli")


def matrix_to_qubo(durations: np.ndarray, *, epsilon: float = 0.1) -> QUBOProblem:
    """Mesafe matrisini one-hot TSP QUBO'suna çevirir.

    Ceza katsayısı A = (1+epsilon) * max(durations) olarak matristen TÜRETİLİR
    (spec FR-009 — sabit gömülü değer yasak). Bu, bir kısıt ihlalinin cezasının
    en kötü geçerli turdan pahalı olmasını garantiler.
    """
    durations = np.asarray(durations, dtype=np.float64)
    _dogrula(durations)

    n = durations.shape[0]
    m = n - 1                      # baslangic sehri sabit
    V = m * m
    A = float((1.0 + epsilon) * durations.max())

    # degisken haritasi: (sehir, zaman) -> indeks. sehir 1..n-1, zaman 0..m-1
    var_map: dict[tuple[int, int], int] = {}
    for sehir in range(1, n):
        for zaman in range(m):
            var_map[(sehir, zaman)] = (sehir - 1) * m + zaman

    Q = np.zeros((V, V), dtype=np.float64)

    # --- Kisit 1: her sehir tam bir zamanda ---
    # A * (sum_t x[c,t] - 1)^2  -> koselerde -A, ciftlerde +2A
    for sehir in range(1, n):
        idx = [var_map[(sehir, t)] for t in range(m)]
        for i in idx:
            Q[i, i] -= A
        for a in range(len(idx)):
            for b in range(a + 1, len(idx)):
                Q[idx[a], idx[b]] += A
                Q[idx[b], idx[a]] += A

    # --- Kisit 2: her zamanda tam bir sehir ---
    for zaman in range(m):
        idx = [var_map[(c, zaman)] for c in range(1, n)]
        for i in idx:
            Q[i, i] -= A
        for a in range(len(idx)):
            for b in range(a + 1, len(idx)):
                Q[idx[a], idx[b]] += A
                Q[idx[b], idx[a]] += A

    # --- Maliyet: ardisik duraklar arasi sure ---
    # baslangic (0) -> ilk sehir
    for sehir in range(1, n):
        Q[var_map[(sehir, 0)], var_map[(sehir, 0)]] += durations[0][sehir]
    # son sehir -> baslangic (0)
    for sehir in range(1, n):
        Q[var_map[(sehir, m - 1)], var_map[(sehir, m - 1)]] += durations[sehir][0]
    # ara gecisler
    for t in range(m - 1):
        for c1 in range(1, n):
            for c2 in range(1, n):
                if c1 == c2:
                    continue
                i, j = var_map[(c1, t)], var_map[(c2, t + 1)]
                # simetrik yerlestirme: toplam katki durations[c1][c2] olsun
                Q[i, j] += durations[c1][c2] / 2.0
                Q[j, i] += durations[c1][c2] / 2.0

    return QUBOProblem(Q=Q, penalty_A=A, n_stops=n, var_map=var_map)


def energy(problem: QUBOProblem, assignment: np.ndarray) -> float:
    """x^T Q x — atamanın QUBO enerjisi."""
    x = np.asarray(assignment, dtype=np.float64).ravel()
    if x.size != problem.n_vars:
        raise ValueError(f"Atama {problem.n_vars} uzunlugunda olmali, verilen {x.size}")
    return float(x @ problem.Q @ x)


def assignment_to_tour(problem: QUBOProblem, assignment: np.ndarray) -> list[int] | None:
    """Atamayı tura çevirir. Kısıt ihlali varsa None — 'en yakın tur' uydurulmaz."""
    x = np.asarray(assignment).ravel()
    if x.size != problem.n_vars:
        raise ValueError(f"Atama {problem.n_vars} uzunlugunda olmali")

    n = problem.n_stops
    m = n - 1
    grid = np.zeros((m, m), dtype=int)  # [sehir-1][zaman]
    for (sehir, zaman), idx in problem.var_map.items():
        grid[sehir - 1][zaman] = int(x[idx])

    if not (grid.sum(axis=0) == 1).all():   # her zamanda tam bir sehir
        return None
    if not (grid.sum(axis=1) == 1).all():   # her sehir tam bir zamanda
        return None

    tour = [0]
    for zaman in range(m):
        tour.append(int(np.argmax(grid[:, zaman])) + 1)
    return tour
