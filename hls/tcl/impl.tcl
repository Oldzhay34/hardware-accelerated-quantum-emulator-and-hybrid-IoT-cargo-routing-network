# IMPLEMENTASYON -- HLS TAHMINLERINI GERCEK SAYILARLA DEGISTIRIR.
#
# NEDEN AYRI BIR BETIK: export.tcl yalnizca IP paketler
# (export_design -format ip_catalog). Paketleme, tasarimin FPGA'ya
# YERLESTIRILEBILDIGINI kanitlamaz -- kaynak sayilarini da olcmez.
#
# csynth raporundaki LUT/FF/DSP/BRAM sayilari HLS TAHMINIDIR ve kabadir.
# Bizim icin kritik: LUT %84 (45.164 / 53.200). Bu tahmin tutmazsa tasarim
# karta sigmaz. Gercek sayi ancak Vivado sentez + yerlestirme + yonlendirme
# sonrasi bilinir; zamanlamanin da gercekten tuttugu orada gorulur
# (HLS'in 7,195 ns'i kendi tahminidir, Vivado'nun WNS'i degil).
#
# -flow impl: Vivado'yu cagirir, RTL sentezi + implementasyon kosar ve
# "Resource & Timing" raporunu HLS cozumune geri yazar.
#
# UYARI: UZUN SURER (xc7z020 icin tipik 30-90 dk) ve Vivado birkac GB RAM ister.
#
# CALISTIRMA (depo kokunden, WSL icinde):
#   wsl -d Ubuntu -e bash hls/run.sh impl
source [file join [file dirname [info script]] common.tcl]

# common.tcl "open_solution -reset" yapar ve cozum veritabanini SILER; bu yuzden
# export_design tek basina calismaz (cosim.tcl ile ayni tuzak, COSIM 212-40).
puts "=== impl oncesi sentez ==="
csynth_design

puts "=== export_design -flow impl (UZUN SURER: 30-90 dk) ==="
export_design -flow impl -format ip_catalog -rtl verilog \
    -display_name "QIR Statevector Kernel" \
    -description "16-kubit QAOA statevector emulatoru, Q1.17 (ADR 0008)" \
    -vendor "qir-engine" -version "0.1"
close_project
exit
