"""T028 — Önbellek anahtarı doğru mu (spec edge case: sıra hassasiyeti)."""
import numpy as np
import pytest

from services.matrix.app import cache


def test_ayni_girdi_ayni_anahtar():
    p = [(41.01, 28.97), (41.03, 29.02)]
    assert cache.cache_key(p, "abc123") == cache.cache_key(p, "abc123")


def test_farkli_sira_farkli_anahtar():
    """Spec edge case: aynı noktalar farklı sırayla -> yanlış önbellek isabeti olmamalı."""
    p1 = [(41.01, 28.97), (41.03, 29.02)]
    p2 = [(41.03, 29.02), (41.01, 28.97)]
    assert cache.cache_key(p1, "abc123") != cache.cache_key(p2, "abc123")


def test_farkli_osm_surumu_farkli_anahtar():
    p = [(41.01, 28.97), (41.03, 29.02)]
    assert cache.cache_key(p, "abc123") != cache.cache_key(p, "def456")


def test_yaz_oku_gidis_donus(tmp_path):
    d = np.array([[0.0, 100.0], [110.0, 0.0]])
    meta = {"osm_md5": "abc123", "engine": "osrm/5.x"}
    key = "test-anahtar"

    cache.write(tmp_path, key, d, meta)
    okunan_d, okunan_meta = cache.read(tmp_path, key)

    assert np.array_equal(okunan_d, d)
    assert okunan_meta["osm_md5"] == "abc123"


def test_olmayan_anahtar_none_doner(tmp_path):
    assert cache.read(tmp_path, "hic-yok") is None
