# SENTEZ -- SC-002 (BRAM) ve SC-003 (II) buradan gelir. Fazin ASIL KANITI.
#
# UYARI: C-sim bu adimin soyledigi hicbir seyi soyleyemez. C kodu dogru
# calisirken sentez sonucu on kat yavas cikabilir -- SK-02'nin tam tanimi.
#
# Rapordan okunacaklar ve esikleri:
#   BRAM_18K   <= 238   (= %85 x 280).  DIKKAT: BUTCE 280'DIR, 140 DEGIL.
#                       Tahmin: 128 BRAM_18K = %45,7 -- DOGRULANMAMIS.
#   II (k=0)   <= 4     Tahmin: 1
#   II (k=15)  <= 4     Tahmin: 2
#   Fmax                NC-4'u cozer; 100 MHz su an VARSAYIM.
source [file join [file dirname [info script]] common.tcl]

puts "=== csynth: part $PART, saat ${CLOCK_NS}ns ==="
csynth_design

set rpt $PROJ/$SOLUTION/syn/report/${TOP}_csynth.rpt
if {[file exists $rpt]} {
    puts "\n=== RAPOR: $rpt ==="
    puts "Once BRAM_18K satirina bak. Butce 280, esik 238."
} else {
    puts "UYARI: beklenen rapor yolu bulunamadi -> $rpt"
}
close_project
exit
