"""Servis konfigürasyonu. Faz 1 T032.

repo-conventions.md §7: eksik değişkenle servis SESSİZCE kalkmaz, çalışmayı
REDDEDER. Sessiz varsayılan, yanlış OSRM'e veya yanlış veri sürümüne karşı
sessizce ölçüm yapmak demektir (Prensip II ihlali).
"""
from __future__ import annotations

import os
from dataclasses import dataclass


class MissingConfigError(RuntimeError):
    pass


@dataclass(frozen=True)
class Settings:
    osrm_url: str
    osm_md5: str
    cache_dir: str


def load_settings() -> Settings:
    eksik = [k for k in ("OSRM_URL", "OSM_MD5", "MATRIX_CACHE_DIR") if not os.environ.get(k)]
    if eksik:
        raise MissingConfigError(
            f"Zorunlu ortam değişkenleri eksik: {', '.join(eksik)}. "
            "Servis varsayılanla kalkmaz — bkz. docs/repo-conventions.md §7."
        )
    return Settings(
        osrm_url=os.environ["OSRM_URL"],
        osm_md5=os.environ["OSM_MD5"],
        cache_dir=os.environ["MATRIX_CACHE_DIR"],
    )
