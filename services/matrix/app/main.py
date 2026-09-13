"""Mesafe matrisi FastAPI servisi. Faz 1 T035-T036.

Sözleşme: specs/001-veri-hatti-altin-referans/contracts/matrix-api.md
"""
from __future__ import annotations

import time

import httpx
from fastapi import FastAPI
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from services.matrix.app import cache, osrm_client
from services.matrix.app.config import MissingConfigError, load_settings

app = FastAPI(title="qir-engine matrix service")

try:
    _settings = load_settings()
except MissingConfigError:
    _settings = None  # /health bunu raporlar; /matrix çağrılırsa hata döner


class MatrixRequest(BaseModel):
    points: list[tuple[float, float]] = Field(..., description="[(lat, lon), ...]")
    use_cache: bool = True


@app.post("/matrix")
def post_matrix(req: MatrixRequest):
    if _settings is None:
        return JSONResponse(status_code=503, content={"error": "config_missing"})

    n = len(req.points)
    if not (2 <= n <= 30):
        return JSONResponse(
            status_code=400,
            content={"error": "stop_count_out_of_range", "n": n, "max": 30},
        )

    for i, (lat, lon) in enumerate(req.points):
        if not (-90 <= lat <= 90 and -180 <= lon <= 180):
            return JSONResponse(
                status_code=400, content={"error": "invalid_coordinate", "index": i}
            )

    key = cache.cache_key(req.points, _settings.osm_md5)
    t0 = time.perf_counter()

    if req.use_cache:
        cached = cache.read(_settings.cache_dir, key)
        if cached is not None:
            durations, meta = cached
            return {
                "durations": durations.tolist(),
                "n": n,
                "cache_hit": True,
                "osm_md5": meta["osm_md5"],
                "engine": meta["engine"],
                "cache_key": key,
                "elapsed_ms": round((time.perf_counter() - t0) * 1000, 1),
            }

    try:
        durations = osrm_client.fetch_matrix(_settings.osrm_url, req.points)
    except osrm_client.UnreachablePairError as e:
        return JSONResponse(
            status_code=422, content={"error": "unreachable_pair", "pairs": e.pairs}
        )
    except osrm_client.OSRMUnavailableError:
        return JSONResponse(status_code=503, content={"error": "engine_unavailable"})

    meta = {"osm_md5": _settings.osm_md5, "engine": "osrm/5.x"}
    cache.write(_settings.cache_dir, key, durations, meta)

    return {
        "durations": durations.tolist(),
        "n": n,
        "cache_hit": False,
        "osm_md5": _settings.osm_md5,
        "engine": "osrm/5.x",
        "cache_key": key,
        "elapsed_ms": round((time.perf_counter() - t0) * 1000, 1),
    }


@app.get("/health")
def health():
    if _settings is None:
        return JSONResponse(status_code=503, content={"status": "config_missing"})
    try:
        # osrm-routed'in /health ucu yok; en ucuz gerçek sorgu tek noktalı /route.
        r = httpx.get(f"{_settings.osrm_url}/route/v1/driving/0,0;0.001,0.001", timeout=3.0)
        osrm_ok = r.status_code == 200
    except httpx.RequestError:
        osrm_ok = False

    if not osrm_ok:
        return JSONResponse(
            status_code=503, content={"status": "degraded", "osrm": "unreachable"}
        )
    return {"status": "ok", "osrm": "reachable", "osm_md5": _settings.osm_md5}
