#!/bin/bash
# G0 kukla blok tasarimini kosar ve artifacts/bitstream/probe.hwh uretir.
#
#   wsl -d Ubuntu -e bash fpga/bd/probe_hwh.sh
#
# ⚠️ LC_ALL SART. Yoksa Xilinx araclari sunu der ve cekirdek doker:
#   locale::facet::_S_create_c_locale name not valid
# Bkz. docs/runbooks/vitis-hls-kurulum.md
#
# Sentez KOSULMAZ -- yalnizca blok tasarim cikti urunleri. Birkac dakika surer.
set -eu

export LC_ALL=en_US.UTF-8
export LANG=en_US.UTF-8

VIVADO=/opt/Xilinx/2025.2/Vivado
if [ ! -d "$VIVADO" ]; then
    echo "HATA: Vivado bulunamadi: $VIVADO" >&2
    exit 1
fi
# shellcheck disable=SC1091
source "$VIVADO/settings64.sh"

REPO=$(cd "$(dirname "$0")/../.." && pwd)
LOG=$REPO/artifacts/bitstream/probe_hwh.log
mkdir -p "$REPO/artifacts/bitstream"

echo "repo   : $REPO"
echo "vivado : $(command -v vivado)"
echo "log    : $LOG"
echo

cd "$REPO/artifacts/bitstream"
vivado -mode batch -nojournal -notrace \
       -log "$LOG" \
       -source "$REPO/fpga/bd/probe_hwh.tcl" \
       -tclargs 2>&1 | tee -a "$LOG"

rc=${PIPESTATUS[0]}
echo
if [ "$rc" -eq 0 ] && [ -f "$REPO/artifacts/bitstream/probe.hwh" ]; then
    echo "=== BASARILI ==="
    ls -la "$REPO/artifacts/bitstream/probe.hwh"
    echo
    echo ".hwh icindeki IP modulleri:"
    grep -oE 'MODTYPE="[^"]*"' "$REPO/artifacts/bitstream/probe.hwh" | sort -u | sed 's/^/  /'
else
    echo "=== BASARISIZ (rc=$rc) -- log: $LOG ==="
fi
exit "$rc"
