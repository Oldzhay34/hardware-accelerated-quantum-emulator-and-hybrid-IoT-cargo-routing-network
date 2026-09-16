#!/usr/bin/env bash
# Vitis HLS akisini uctan uca kosar: csim -> csynth -> cosim -> export (FR-017, SC-005).
#
# NEDEN POWERSHELL DEGIL: hls/run.ps1 Windows PATH'inde `vitis-run` arar. Vitis
# Windows'ta Device Guard tarafindan engellendigi icin (SK-05) kurulum WSL'e
# tasindi ve Windows tarafinda arayacak bir ikili KALMADI. run.ps1 calismaz.
#
# Kullanim (Windows PowerShell'den):
#   wsl -d Ubuntu -e bash /mnt/c/.../qir-engine/hls/run.sh            # csim + csynth
#   wsl -d Ubuntu -e bash /mnt/c/.../qir-engine/hls/run.sh csynth     # yalniz sentez
#   QIR_N=8 wsl -d Ubuntu -e bash .../hls/run.sh cosim                # cosim (kucuk n)
#
# COSIM VARSAYILAN OLARAK ATLANIR: n=16'da 11,5 saat suruyor (olculdu).
# QIR_N=8 ile 4,5 dakika. SC-002/SC-003 csynth'ten geldigi icin bu kayip degil.
set -uo pipefail

KOK="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$KOK"

VITIS=/opt/Xilinx/2025.2/Vitis
if [ ! -x "$VITIS/bin/vitis-run" ]; then
    echo "HATA: $VITIS/bin/vitis-run bulunamadi." >&2
    echo "      Kurulum: docs/runbooks/vitis-hls-kurulum.md" >&2
    exit 1
fi

# LC_ALL SART: yoksa vitis-run core dump eder
#   locale::facet::_S_create_c_locale name not valid
export LC_ALL=en_US.UTF-8 LANG=en_US.UTF-8
# shellcheck disable=SC1091
source "$VITIS/settings64.sh"

ADIMLAR=("${@:-}")
if [ -z "${ADIMLAR[0]}" ]; then ADIMLAR=(csim csynth); fi

for adim in "${ADIMLAR[@]}"; do
    case "$adim" in
        csim|csynth|cosim|export|impl) ;;
        *) echo "HATA: bilinmeyen adim '$adim' (csim|csynth|cosim|export|impl)" >&2; exit 2 ;;
    esac
    echo "=== $adim  (n=${QIR_N:-16})  $(date '+%H:%M:%S') ==="
    if ! vitis-run --mode hls --tcl "hls/tcl/$adim.tcl"; then
        echo "=== $adim BASARISIZ ===" >&2
        exit 1
    fi
done
echo "=== TAMAM: ${ADIMLAR[*]} ==="
