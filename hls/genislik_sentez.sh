#!/usr/bin/env bash
# 6C / T072 — her genlik genişliği için csynth. Asıl proje (qir_hls_prj)
# DOKUNULMAZ: her genişlik qir_hls_prj_W<n> dizinine yazar (common.tcl).
#
# Kullanım (WSL, uzun sürer — nohup önerilir):
#   nohup bash hls/genislik_sentez.sh > /root/genislik_sentez.log 2>&1 &
# Sonra rakamlar: .venv\Scripts\python.exe scripts\genislik_pareto.py
set -uo pipefail
KOK="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$KOK"
GENISLIKLER="${QIR_GENISLIKLER:-14 16 18 20 24}"
for W in $GENISLIKLER; do
    echo "=== W=$W basladi $(date '+%H:%M:%S') ==="
    if QIR_REAL_BITS=$W bash hls/run.sh csynth > "hls/build/csynth_W$W.log" 2>&1; then
        echo "=== W=$W TAMAM $(date '+%H:%M:%S') ==="
    else
        echo "=== W=$W BASARISIZ $(date '+%H:%M:%S') — hls/build/csynth_W$W.log ==="
    fi
done
echo "=== HEPSI BITTI $(date '+%H:%M:%S') ==="
