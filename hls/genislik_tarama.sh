#!/usr/bin/env bash
# 6C / T071 — genlik genişliği taraması: her QIR_REAL_BITS için C-sim fidelity.
#
# Süpürülen TEK şey `real_t` genişliği (tek bir reel sayının biti). Kübit
# sayısı hep 16, faz genişliği (phase_t) hep 18, trig indeksi hep 13 bit.
# Donanım maliyeti (T072) ayrı: hls/run.sh csynth, aynı bayrakla.
#
# Kullanım (WSL):  bash hls/genislik_tarama.sh [cikti_dizini]
# Çıktı: <cikti>/W<n>/csim-fidelity_*_n16_p{1,2}.json  (her genişlik ayrı dizin;
#        dosya adları genişliği taşımadığı için karışmasınlar)
set -euo pipefail

KOK="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$KOK"
CIKTI="${1:-hls/build/genislik}"
GENISLIKLER="${QIR_GENISLIKLER:-14 16 18 20 24}"
GIT_HASH="$(git rev-parse --short HEAD 2>/dev/null || echo unknown)"
son() { ls -1t $1 2>/dev/null | head -1; }
R2="$(son 'docs/measurements/reference_*_p2_n5.npy')"
R1="$(son 'docs/measurements/reference_*_p1_n5.npy')"

for W in $GENISLIKLER; do
    D="$CIKTI/W$W"; mkdir -p "$D"
    exe="hls/build/tb_kernel_n16_W$W"
    g++ -std=c++17 -O2 -DQIR_NO_VITIS -DQIR_N_QUBITS=16 "-DQIR_REAL_BITS=$W" \
        -Ihls/src -Ihls/tb hls/tb/tb_kernel.cpp hls/tb/qir_kernel_debug.cpp \
        hls/src/qir_kernel.cpp -o "$exe"
    for R in "$R2" "$R1"; do
        # Ham statevector de dökülür: fidelity tek sayıdır; uygulama düzeyi
        # ölçütler (optimum rota olasılığı, beklenen enerji) buradan hesaplanır
        # (scripts/genislik_uygulama.py).
        p="$(basename "$R" | grep -o '_p[0-9]*_' | tr -d _)"
        "$exe" --reference "$R" --git-hash "$GIT_HASH" --n 16 --out-dir "$D" \
            --dump "$D/sv_n16_$p.npy" \
            | grep -E 'Format|Kubit|Fidelity' | tr '\n' ' '
        echo
    done
done
echo "TAMAM -> $CIKTI"
