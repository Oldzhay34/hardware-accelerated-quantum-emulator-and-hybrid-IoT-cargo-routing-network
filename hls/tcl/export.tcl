# IP EXPORT -- Faz 5'in (PS entegrasyonu, kartta kosum) girdisi.
#
# Cikti Vivado IP katalogu bicimindedir; artifacts/ altina gider ve git'e
# GIRMEZ (repo-conventions.md par.3 -- buyuk ikili dosyalar harici depoda).
source [file join [file dirname [info script]] common.tcl]

puts "=== export_design: ip_catalog ==="
export_design -format ip_catalog -rtl verilog \
    -display_name "QIR Statevector Kernel" \
    -description "16-kubit QAOA statevector emulatoru, Q1.17 (ADR 0008)" \
    -vendor "qir-engine" -version "0.1"
close_project
exit
