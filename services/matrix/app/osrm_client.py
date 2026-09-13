"""OSRM /table çağrısı. Faz 1 T033."""
from __future__ import annotations

import httpx
import numpy as np


class UnreachablePairError(Exception):
    def __init__(self, pairs: list[tuple[int, int]]):
        self.pairs = pairs
        super().__init__(f"{len(pairs)} durak çifti ulaşılamaz")


class OSRMUnavailableError(Exception):
    pass


def fetch_matrix(osrm_url: str, points: list[tuple[float, float]]) -> np.ndarray:
    """points: [(lat, lon), ...] — OSRM lon,lat sırası ister, burada çeviriliyor."""
    coords = ";".join(f"{lon},{lat}" for lat, lon in points)
    url = f"{osrm_url}/table/v1/driving/{coords}"

    try:
        r = httpx.get(url, timeout=30.0)
    except httpx.RequestError as e:
        raise OSRMUnavailableError(str(e)) from e

    if r.status_code != 200:
        raise OSRMUnavailableError(f"OSRM {r.status_code}: {r.text[:200]}")

    body = r.json()
    if body.get("code") != "Ok":
        raise OSRMUnavailableError(f"OSRM code={body.get('code')}")

    durations = body["durations"]
    n = len(durations)
    ulasilmaz = [
        (i, j) for i in range(n) for j in range(n) if i != j and durations[i][j] is None
    ]
    if ulasilmaz:
        # Prensip II: tanimsiz deger uydurulmaz. Matris uretilmez, hata firlatilir.
        raise UnreachablePairError(ulasilmaz)

    m = np.array(durations, dtype=np.float64)
    np.fill_diagonal(m, 0.0)
    return m
