#!/usr/bin/env bash
# 6B / T065b + T067 — GPU tabanı protokolü v1.1 (🔒), katman 2 (aynı algoritma).
# docs/measurements/gpu-taban-olcum-protokolu.md §6: aer_serileri.sh'tan SONRA,
# sıra SABİT: G32-2, G64-2, G32-1, G64-1; her seri 300 sn; her serinin
# öncesinde ≥ 5 dk soğuma (B-GPU ile G32-2 arası dahil).
#
# Önce dört yapılandırmanın T066 (katman 2) doğrulama kaydı yazılır
# (gpu-ayni-algoritma-dogrulama_*.json) — her seri de başında ayrıca doğrular.
#
# Kullanım (WSL, temiz ağaçta; ~45 dk — makineye DOKUNMA, prizde):
#   bash scripts/aer_serileri.sh && bash scripts/g_serileri.sh
set -uo pipefail
export GIT_CONFIG_COUNT=1 GIT_CONFIG_KEY_0=core.autocrlf GIT_CONFIG_VALUE_0=true
KOK="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$KOK"
PY="${QIR_GPU_PY:-/root/qir-gpu-venv/bin/python}"
SOGUMA_S=300
SERILER=("G32-2 32 2" "G64-2 64 2" "G32-1 32 1" "G64-1 64 1")

if git status --porcelain | grep -v '^?? "\{0,1\}docs/measurements/' | grep -q .; then
    echo "⛔ commit'lenmemis kod var — protokol §4: seriler temiz agacta"; exit 1
fi
echo "=== katman 2 basladi $(date '+%F %T'), git $(git rev-parse --short HEAD)"

echo "=== T066 katman 2: dogrulama kayitlari"
for s in "${SERILER[@]}"; do
    read -r ad h p <<< "$s"
    if ! "$PY" scripts/gpu_ayni_algoritma.py --hassasiyet "$h" --p "$p" --yalniz-dogrula; then
        echo "⛔ $ad dogrulamasi gecmedi — seriler KOSULMADI"; exit 1
    fi
done

for s in "${SERILER[@]}"; do
    read -r ad h p <<< "$s"
    echo "--- soguma ${SOGUMA_S} sn ($(date '+%T'))"
    sleep "$SOGUMA_S"
    echo "=== $ad (FP$h, p=$p) basladi $(date '+%T')"
    if ! "$PY" scripts/gpu_ayni_algoritma.py --hassasiyet "$h" --p "$p" --saniye 300 \
            --etiket "seri${ad}"; then
        echo "⛔ $ad basarisiz ya da gecersiz — sonraki seriler KOSULMADI ($(date '+%T'))"
        exit 1
    fi
    echo "=== $ad bitti $(date '+%T')"
done
echo "=== KATMAN 2 BITTI $(date '+%F %T')"
