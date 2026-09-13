"""Matris önbelleği. Faz 1 T034.

Anahtar sıraya duyarlıdır: aynı noktalar farklı sırada FARKLI bir anahtar
üretir (spec edge case). Matris satır/sütun indeksleri girdi sırasına bağlı
olduğundan, sırayı yok saymak yanlış önbellek isabetine yol açardı.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np


def cache_key(points: list[tuple[float, float]], osm_md5: str) -> str:
    payload = json.dumps({"points": [list(p) for p in points], "osm_md5": osm_md5})
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def write(cache_dir: str | Path, key: str, durations: np.ndarray, meta: dict) -> None:
    d = Path(cache_dir)
    d.mkdir(parents=True, exist_ok=True)
    np.save(d / f"{key}.npy", durations)
    (d / f"{key}.json").write_text(json.dumps(meta, ensure_ascii=False), encoding="utf-8")


def read(cache_dir: str | Path, key: str) -> tuple[np.ndarray, dict] | None:
    d = Path(cache_dir)
    npy, js = d / f"{key}.npy", d / f"{key}.json"
    if not (npy.exists() and js.exists()):
        return None
    return np.load(npy), json.loads(js.read_text(encoding="utf-8"))
