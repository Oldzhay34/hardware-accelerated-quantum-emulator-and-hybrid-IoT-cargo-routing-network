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
# Başarı = rapor VAR, çıkış kodu değil. 27 Eyl'de W=14 koşusunda vitis-run
# hiçbir şey yazmadan 0 döndü, proje dizini hiç oluşmadı ve döngü "TAMAM"
# dedi. Tek başına yeniden koşunca normal çalıştı; nedeni bulunamadı.
for W in $GENISLIKLER; do
    echo "=== W=$W basladi $(date '+%H:%M:%S') ==="
    RAPOR="qir_hls_prj_W$W/solution1/syn/report/qir_kernel_csynth.xml"
    rm -f "$RAPOR"
    if QIR_REAL_BITS=$W bash hls/run.sh csynth > "hls/build/csynth_W$W.log" 2>&1 \
       && [ -s "$RAPOR" ]; then
        echo "=== W=$W TAMAM $(date '+%H:%M:%S') ==="
    else
        echo "=== W=$W BASARISIZ $(date '+%H:%M:%S') — rapor yok ya da hata, hls/build/csynth_W$W.log ==="
    fi
done
echo "=== HEPSI BITTI $(date '+%H:%M:%S') ==="
