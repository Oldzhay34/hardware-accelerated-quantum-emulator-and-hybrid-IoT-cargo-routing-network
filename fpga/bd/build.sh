#!/bin/bash
# Bitstream uretir: BD -> sentez -> implementasyon -> write_bitstream (T016).
#
#   wsl -d Ubuntu -e bash fpga/bd/build.sh
#
# ⚠️ LC_ALL SART — yoksa Xilinx araclari cekirdek doker
# ("locale::facet::_S_create_c_locale name not valid").
# Bkz. docs/runbooks/vitis-hls-kurulum.md
#
# UZUN SURER (sentez + implementasyon, tahminen 30-60 dk). Arka planda kosun.
set -eu

export LC_ALL=en_US.UTF-8
export LANG=en_US.UTF-8

VIVADO=/opt/Xilinx/2025.2/Vivado
[ -d "$VIVADO" ] || { echo "HATA: Vivado yok: $VIVADO" >&2; exit 1; }
# shellcheck disable=SC1091
source "$VIVADO/settings64.sh"

REPO=$(cd "$(dirname "$0")/../.." && pwd)
CIKTI="$REPO/artifacts/bitstream"
TARIH=$(date +%Y%m%d)
GIT_HASH=$(git -C "$REPO" rev-parse --short HEAD 2>/dev/null || echo unknown)
DAMGA="${TARIH}_${GIT_HASH}"
LOG="$CIKTI/build_${DAMGA}.log"
mkdir -p "$CIKTI"

echo "repo     : $REPO"
echo "damga    : $DAMGA"
echo "log      : $LOG"
echo

# Tcl'i gecici bir dosyaya yazip BD betigini kaynak gosteriyoruz; boylece
# qir_bd.tcl tek sorumlulukta kalir (BD kurar, sentez bilmez).
AKIS=$(mktemp /tmp/qir_akis_XXXX.tcl)
trap 'rm -f "$AKIS"' EXIT
cat > "$AKIS" <<TCL
source $REPO/fpga/bd/qir_bd.tcl

puts "=== sentez ==="
launch_runs synth_1 -jobs 6
wait_on_run synth_1
if {[get_property PROGRESS [get_runs synth_1]] != "100%"} {
    puts "HATA: sentez tamamlanmadi"
    exit 1
}

puts "=== implementasyon + bitstream ==="
launch_runs impl_1 -to_step write_bitstream -jobs 6
wait_on_run impl_1
if {[get_property PROGRESS [get_runs impl_1]] != "100%"} {
    puts "HATA: implementasyon tamamlanmadi"
    exit 1
}

open_run impl_1
set wns [get_property SLACK [get_timing_paths -delay_type max]]
set whs [get_property SLACK [get_timing_paths -delay_type min]]
puts "WNS_DEGERI=\$wns"
puts "WHS_DEGERI=\$whs"
report_utilization -file $CIKTI/utilization_${DAMGA}.rpt
report_timing_summary -file $CIKTI/timing_${DAMGA}.rpt
exit 0
TCL

cd "$CIKTI"
vivado -mode batch -nojournal -notrace -log "$LOG" -source "$AKIS" 2>&1 | tee -a "$LOG"
rc=${PIPESTATUS[0]}
[ "$rc" -eq 0 ] || { echo "=== VIVADO DUSTU (rc=$rc) — log: $LOG ==="; exit "$rc"; }

PRJ="$CIKTI/qir_prj"
BIT=$(find "$PRJ" -name "qir_bd_wrapper.bit" | head -1)
HWH=$(find "$PRJ" -name "qir_bd.hwh" | head -1)
[ -n "$BIT" ] || { echo "HATA: .bit uretilmedi" >&2; exit 1; }
[ -n "$HWH" ] || { echo "HATA: .hwh uretilmedi" >&2; exit 1; }

cp -f "$BIT" "$CIKTI/qir_${DAMGA}.bit"
cp -f "$HWH" "$CIKTI/qir_${DAMGA}.hwh"

WNS=$(grep -a "WNS_DEGERI=" "$LOG" | tail -1 | cut -d= -f2 | tr -d ' \r')
WHS=$(grep -a "WHS_DEGERI=" "$LOG" | tail -1 | cut -d= -f2 | tr -d ' \r')

echo
echo "=== URETILDI ==="
echo "  bit : $CIKTI/qir_${DAMGA}.bit"
echo "  hwh : $CIKTI/qir_${DAMGA}.hwh"
echo "  WNS : $WNS ns"
echo "  WHS : $WHS ns"
echo "  sha256:"
sha256sum "$CIKTI/qir_${DAMGA}.bit" "$CIKTI/qir_${DAMGA}.hwh" | sed 's/^/    /'
echo

# ⛔ Zamanlama tutmazsa FCLK DUSURULMEZ. 100 MHz, Faz 2'nin butun
# olcumlerinin dayanagidir; dusurmek gecikme rakamlarini gecersiz kilar.
# Faz DURUR ve sebep arastirilir (gorev T017).
if [ -z "$WNS" ]; then
    echo "HATA: WNS okunamadi — log'a bakin: $LOG" >&2
    exit 1
fi
if awk -v w="$WNS" 'BEGIN{exit !(w < 0)}'; then
    echo "⛔ ZAMANLAMA TUTMADI: WNS=$WNS ns < 0" >&2
    echo "   FCLK DUSURULMEYECEK. Faz durur, sebep arastirilir (T017)." >&2
    echo "   Rapor: $CIKTI/timing_${DAMGA}.rpt" >&2
    exit 1
fi
echo "✅ WNS >= 0 — 100 MHz'de zamanlama tuttu."
