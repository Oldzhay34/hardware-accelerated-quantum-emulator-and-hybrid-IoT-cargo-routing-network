#!/usr/bin/env bash
# 6B / T067 — GPU tabanı protokolü v1.0 (🔒), katman 1: dört Aer serisi.
# docs/measurements/gpu-taban-olcum-protokolu.md §6: sıra SABİT, her seri
# 300 sn, seriler arasında ≥ 5 dk boşta bekleme (soğuma).
#
# Kullanım (WSL, temiz ağaçta; ~40 dk — makineye DOKUNMA, prizde):
#   nohup bash scripts/aer_serileri.sh > /root/aer-serileri.log 2>&1 &
#   tail -f /root/aer-serileri.log
#
# Bir seri geçersiz ya da hatalı biterse sonrakiler KOŞMAZ (protokol §7:
# geçersiz seri baştan koşulur, sıra bozulmaz).
set -uo pipefail
KOK="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$KOK"
PY="${QIR_GPU_PY:-/root/qir-gpu-venv/bin/python}"
SOGUMA_S=300
SERILER=("A-CPU CPU 2" "A-GPU GPU 2" "B-CPU CPU 1" "B-GPU GPU 1")

if [ -n "$(git status --porcelain)" ]; then
    echo "⛔ calisma agaci kirli — protokol §4: seriler temiz agacta"; exit 1
fi
echo "=== protokol serileri basladi $(date '+%F %T'), git $(git rev-parse --short HEAD)"
ilk=1
for s in "${SERILER[@]}"; do
    read -r ad cihaz p <<< "$s"
    if [ $ilk -eq 0 ]; then
        echo "--- soguma ${SOGUMA_S} sn ($(date '+%T'))"
        sleep "$SOGUMA_S"
    fi
    ilk=0
    echo "=== $ad ($cihaz, p=$p) basladi $(date '+%T')"
    if ! "$PY" scripts/cpu_load_loop.py --device "$cihaz" --p "$p" --saniye 300 \
            --etiket "seri${ad}"; then
        echo "⛔ $ad basarisiz ya da gecersiz — sonraki seriler KOSULMADI ($(date '+%T'))"
        exit 1
    fi
    echo "=== $ad bitti $(date '+%T')"
done
echo "=== HEPSI BITTI $(date '+%F %T')"
