"""T029-T031 — Matris HTTP API sözleşmesi (contracts/matrix-api.md)."""
import os
import tempfile

import pytest
from fastapi.testclient import TestClient

os.environ.setdefault("OSRM_URL", "http://localhost:5000")
os.environ.setdefault("OSM_MD5", "cb101d9243c3c605907e94f4266159c2")
# Gerçek data/matrices/ EĞİL — üretim önbelleği test artefaktlarıyla kirlenmesin.
# (Prensip: data/matrices commit edilir çünkü ölçüm girdisidir; test verisi değil.)
os.environ["MATRIX_CACHE_DIR"] = tempfile.mkdtemp(prefix="qir_matrix_test_cache_")

from services.matrix.app.main import app

client = TestClient(app)


def test_iki_noktadan_az_reddedilir():
    r = client.post("/matrix", json={"points": [[41.0, 29.0]]})
    assert r.status_code == 400
    assert r.json()["error"] == "stop_count_out_of_range"


def test_otuzdan_fazla_reddedilir():
    pts = [[41.0 + i * 0.001, 29.0] for i in range(31)]
    r = client.post("/matrix", json={"points": pts})
    assert r.status_code == 400
    assert r.json()["error"] == "stop_count_out_of_range"


def test_gecersiz_koordinat_reddedilir():
    r = client.post("/matrix", json={"points": [[999.0, 29.0], [41.0, 29.0]]})
    assert r.status_code == 400
    assert r.json()["error"] == "invalid_coordinate"


@pytest.mark.integration
def test_osrm_entegrasyon_otuz_durak():
    """OSRM ayaktayken: 30x30, 900/900 hucre dolu, yuksek asimetri orani (spec FR-002)."""
    import csv
    from pathlib import Path

    kok = Path(__file__).resolve().parents[3]
    satirlar = list(csv.DictReader((kok / "data/synthetic/deliveries.csv").open(encoding="utf-8")))[:30]
    pts = [[float(r["lat"]), float(r["lon"])] for r in satirlar]

    r = client.post("/matrix", json={"points": pts})
    assert r.status_code == 200
    body = r.json()

    assert body["n"] == 30
    d = body["durations"]
    dolu = sum(1 for row in d for v in row if v is not None)
    assert dolu == 900

    n = len(d)
    asim = sum(1 for i in range(n) for j in range(i + 1, n) if d[i][j] != d[j][i])
    assert asim / (n * (n - 1) / 2) > 0.5, "gercek yol agi asimetri kaniti (FR-002)"


@pytest.mark.integration
def test_ayni_istek_ikinci_kez_onbellekten():
    pts = [[41.01, 28.97], [41.03, 29.02], [41.02, 29.00]]
    r1 = client.post("/matrix", json={"points": pts})
    r2 = client.post("/matrix", json={"points": pts})

    assert r1.json()["durations"] == r2.json()["durations"]
    assert r2.json()["cache_hit"] is True


def test_health_ucu_var():
    r = client.get("/health")
    assert r.status_code in (200, 503)
    assert "status" in r.json()
