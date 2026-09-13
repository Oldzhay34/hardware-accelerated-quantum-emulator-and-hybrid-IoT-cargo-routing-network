#!/usr/bin/env bash
# Faz 1 T037 — OSRM MLD boru hattı: extract -> partition -> customize.
#
# ⚠️ Git Bash'ten çağırıyorsan MSYS_NO_PATHCONV=1 ŞART. Aksi halde Git Bash
# konteyner İÇİNDEKİ /opt/car.lua yolunu Windows yoluna çevirir ve şu hatayı
# alırsın: "the argument ('C:/Program Files/Git/opt/car.lua') ... is invalid"
# (bkz. specs/001-veri-hatti-altin-referans/research.md R-4)
set -euo pipefail

DATA=/data
PBF="$DATA/Istanbul.osm.pbf"

echo "=== osrm-extract ==="
osrm-extract -p /opt/car.lua "$PBF"

echo "=== osrm-partition ==="
osrm-partition "$DATA/Istanbul.osrm"

echo "=== osrm-customize ==="
osrm-customize "$DATA/Istanbul.osrm"

echo "TAMAM"
