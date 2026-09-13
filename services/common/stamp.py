"""Ölçüm çıktılarını damgalar. Faz 1 T007.

Risk VR-03: "Ölçüm verisi karışıyor — hangi koşum hangi konfigürasyona ait
belirsiz." Damgasız koşum GEÇERSİZ sayılır ve yeniden koşulur; bu da donanım
zamanının iki kez harcanması demektir. Bu yüzden damgalama, ölçümü yazan her
yolun üzerinde durur.
"""
from __future__ import annotations

import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def git_hash(short: bool = True) -> str:
    """Mevcut commit hash'i. Git yoksa veya depo değilse 'nogit'."""
    cmd = ["git", "rev-parse", "--short" if short else "HEAD", "HEAD"]
    if not short:
        cmd = ["git", "rev-parse", "HEAD"]
    try:
        out = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
        return out.stdout.strip() if out.returncode == 0 else "nogit"
    except (OSError, subprocess.SubprocessError):
        return "nogit"


def is_dirty() -> bool:
    """Çalışma ağacında commit'lenmemiş değişiklik var mı.

    Kirli bir ağaçtan alınan ölçüm, git hash'iyle tam olarak eşleşmez —
    metadata'ya yazılır ki sonradan fark edilsin.
    """
    try:
        out = subprocess.run(
            ["git", "status", "--porcelain"], capture_output=True, text=True, timeout=10
        )
        return out.returncode == 0 and bool(out.stdout.strip())
    except (OSError, subprocess.SubprocessError):
        return False


def stamp(**config: Any) -> dict[str, Any]:
    """Ölçüm metadata damgası. Verilen konfigürasyon anahtarları da eklenir."""
    return {
        "stamped_at": datetime.now(timezone.utc).isoformat(),
        "git_hash": git_hash(),
        "git_dirty": is_dirty(),
        "config": config,
    }


def stamped_name(prefix: str, **parts: Any) -> str:
    """Damgalı dosya adı: <prefix>_<tarih>_<githash>[_k=v...]"""
    tarih = datetime.now(timezone.utc).strftime("%Y%m%d")
    ek = "".join(f"_{k}{v}" for k, v in parts.items())
    return f"{prefix}_{tarih}_{git_hash()}{ek}"


def measurements_dir(repo_root: Path | None = None) -> Path:
    """docs/measurements/ — ölçümlerin kalıcı yeri (backup.md §1: yeniden üretilemez)."""
    root = repo_root or Path(__file__).resolve().parents[2]
    d = root / "docs" / "measurements"
    d.mkdir(parents=True, exist_ok=True)
    return d
