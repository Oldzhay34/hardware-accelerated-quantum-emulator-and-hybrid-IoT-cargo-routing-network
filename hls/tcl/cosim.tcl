# COSIM -- RTL'in C ile ayni sonucu verdigini dogrular.
#
# C-sim'in GOREMEDIGI sey budur: C dogru, RTL yanlis olabilir (kapi seviyesinde
# zamanlama, ap_fixed kose durumlari, pipeline yeniden siralamasi).
#
# UYARI 1: bu adim kullanici kodundan ikili uretip CALISTIRIR. Bu makinede
# Smart App Control acik (SK-05) ve imzasiz ikilileri engelleyebilir.
# Engellenirse KAYIP SINIRLIDIR: yalnizca SC-005 (US5, P3) duser; SC-002 ve
# SC-003 csynth'ten geldigi icin etkilenmez.
#
# UYARI 2: 65536 genlikli tam devre icin RTL simulasyonu COK uzun surebilir.
# Once kucuk n ile denemek mantikli: -DQIR_N_QUBITS=8.
source [file join [file dirname [info script]] common.tcl]

puts "=== cosim (uzun surebilir) ==="
cosim_design -argv $TB_ARGV -trace_level none
close_project
exit
