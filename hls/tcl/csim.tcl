# C-SIMULASYON -- altin referansa karsi dogrulama (SC-001).
#
# Bu adimin Faz 2'deki OZEL degeri: gercek ap_fixed'i kullanir. WSL'deki g++
# yolu hls/tb/ap_fixed_mock.hpp taklidini kullaniyor ve oradan cikan fidelity
# sayilari MOCK'A DAYANIYOR. Ikisi ayni cikarsa mock dogrulanmis olur ve T040
# kapanir; ayrisirsa tum C-sim sonuclari yeniden degerlendirilir.
#
# BEKLENEN (WSL/mock ile olculen, n=16 p=2): fidelity 0.999978359
source [file join [file dirname [info script]] common.tcl]

puts "=== csim: referans $REFERENCE ==="
csim_design -argv $TB_ARGV
puts "=== csim bitti -- sonucu WSL ciktisiyla karsilastir (T040) ==="
close_project
exit
