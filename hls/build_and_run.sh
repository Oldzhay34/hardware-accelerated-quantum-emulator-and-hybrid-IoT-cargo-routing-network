#!/usr/bin/env bash
# C-simülasyonu WSL/Linux altında derler ve koşar.
#
# NEDEN WSL: bu makinede Windows Smart App Control açık ve YENİ ÜRETİLEN her
# imzasız .exe'yi dosya özetine göre engelliyor. SAC'ı kapatmak geri alınamaz
# bir sistem güvenlik değişikliğidir; bunun yerine derleme Linux tarafına
# alındı. Ne güvenlik ayarı değişiyor ne de sonuç etkileniyor — aynı kaynak,
# aynı standart C++17.
#
# Kullanım (Windows PowerShell'den):
#   wsl -e bash /mnt/c/Users/olcay/IdeaProjects/qir-engine/hls/build_and_run.sh
set -euo pipefail

KOK="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$KOK"

BUILD="hls/build"
mkdir -p "$BUILD"
GIT_HASH="$(git rev-parse --short HEAD 2>/dev/null || echo unknown)"

derle_ve_kos() {
    local n="$1" ref="$2" etiket="$3"
    local exe="$BUILD/tb_kernel_n$n"
    echo "=== n=$n  ($etiket) ==="
    g++ -std=c++17 -O2 -DQIR_NO_VITIS "-DQIR_N_QUBITS=$n" \
        -Ihls/src -Ihls/tb hls/tb/tb_kernel.cpp hls/tb/qir_kernel_debug.cpp \
        hls/src/qir_kernel.cpp -o "$exe"
    "$exe" --reference "$ref" --git-hash "$GIT_HASH" --n "$n" \
           --dump "$BUILD/csim_n${n}.npy"
    echo
}

son() { ls -1t $1 2>/dev/null | head -1; }

# n=16: gerçek TSP altın referansı (Faz 1), p=1 ve p=2
derle_ve_kos 16 "$(son 'docs/measurements/reference_*_p2_n5.npy')" "TSP, p=2"
R1="$(son 'docs/measurements/reference_*_p1_n5.npy')"
"$BUILD/tb_kernel_n16" --reference "$R1" --git-hash "$GIT_HASH" --n 16 \
    --dump "$BUILD/csim_n16_p1.npy"
echo

# n=8, 12: sentetik referanslar — kübit sayısının parametrik olduğunu kanıtlar
derle_ve_kos 8  "$(son 'docs/measurements/synthref_*_p2_n8.npy')"  "sentetik, p=2"
derle_ve_kos 12 "$(son 'docs/measurements/synthref_*_p2_n12.npy')" "sentetik, p=2"

echo "TAMAM — ciktilar docs/measurements/csim-fidelity_*.json"
