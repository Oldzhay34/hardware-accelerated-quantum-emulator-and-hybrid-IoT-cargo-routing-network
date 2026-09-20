# G0 uyumluluk denemesi -- kukla blok tasarim, YALNIZCA .hwh uretmek icin.
#
# AMAC: PYNQ 2.5'in (Glasgow, 2019) Vivado 2025.2 .hwh'sini ayristirip
# ayristiramadigini ogrenmek. Cevap, obek 4'teki konak kodunun A yoluna mi
# (Overlay) B yoluna mi (Bitstream + MMIO) gore yazilacagini belirler.
# Bkz. research.md §R1.
#
# ⛔ BU TASARIM PS-ONLY OLAMAZ. PS-only bir .hwh'de ozel IP yoktur; ip_dict bos
# doner ve bilinen ayristirma hatalarinin hicbiri tetiklenmez (hepsi IP
# tarafindadir: MEMORYMAP/ADDRESSBLOCK semasi, arayuz adlandirmasi). Probe
# "gecer", butun konak kodu A yoluna gore yazilir, gercek bitstream gelince
# .hwh ayristirilamaz -- G0'in onlemek icin var oldugu senaryonun ta kendisi.
# Bu yuzden asagida GERCEK qir_kernel IP'si ornekleniyor.
#
# ⚠️ SENTEZ/IMPLEMENTASYON KOSULMAZ. .hwh, cikti urunleri uretilirken
# (validate_bd_design + generate_target) yazilir; launch_runs gereksizdir ve
# saatler alir.

set REPO   [file normalize [file join [file dirname [info script]] .. ..]]
set PART   xc7z020clg400-1
set PRJ    $REPO/artifacts/bitstream/probe_prj
set IPREPO $REPO/artifacts/ip/repo
set BDADI  probe_bd
set CIKTI  $REPO/artifacts/bitstream/probe.hwh

if {![file isdirectory $IPREPO]} {
    puts "HATA: IP deposu yok: $IPREPO"
    puts "      T001 kosulmamis. Once IP zip'ini buraya acin."
    exit 1
}

file mkdir $REPO/artifacts/bitstream
if {[file isdirectory $PRJ]} { file delete -force $PRJ }

puts "=== proje ve IP katalogu ==="
create_project probe_prj $PRJ -part $PART -force
set_property ip_repo_paths $IPREPO [current_project]
update_ip_catalog -rebuild

# ⚠️ Kalip DAR olmali. "*processing_system7*" hem processing_system7:5.5 hem
# processing_system7_vip:1.0 dondurur; ikisi birden -vlnv'ye gidince
# "IP definition not found" alinir (19 Eyl'de tam bu olmustu).
proc tek_vlnv {kalip ad} {
    set bulunan [get_ipdefs -all $kalip]
    if {[llength $bulunan] == 0} {
        puts "HATA: $ad IP katalogda bulunamadi (kalip: $kalip)"
        exit 1
    }
    set secilen [lindex [lsort $bulunan] end]
    puts "$ad VLNV: $secilen"
    return $secilen
}

set vlnv_qir [tek_vlnv {*:qir_kernel:*}            qir_kernel]
set vlnv_ps  [tek_vlnv {xilinx.com:ip:processing_system7:*} processing_system7]

puts "=== blok tasarim ==="
create_bd_design $BDADI

# PS7. Board files YOK -- apply_board_preset 0 ile varsayilan yapilandirma
# kullanilir. Probe icin yeterli: amac .hwh'nin semasi, zamanlama degil.
create_bd_cell -type ip -vlnv $vlnv_ps ps7_0
apply_bd_automation -rule xilinx.com:bd_rule:processing_system7 \
    -config {make_external "FIXED_IO, DDR" apply_board_preset "0" Master "Disable" Slave "Disable"} \
    [get_bd_cells ps7_0]

# Board preset yok; GP0 master portunun ve FCLK_CLK0'in acik oldugunu garanti
# et, yoksa asagidaki axi4 otomasyonu baglayacak master bulamaz.
set_property -dict [list CONFIG.PCW_USE_M_AXI_GP0 {1} \
                         CONFIG.PCW_EN_CLK0_PORT  {1}] [get_bd_cells ps7_0]

# Gercek HLS cekirdegi -- testin belirleyici olmasini saglayan parca.
create_bd_cell -type ip -vlnv $vlnv_qir qir_kernel_0

# AXI-Lite baglantisi. Otomasyon smartconnect + proc_sys_reset'i kendisi
# ekler ve baglar; elle kablolamaktan cok daha saglam.
apply_bd_automation -rule xilinx.com:bd_rule:axi4 \
    -config [list Master {/ps7_0/M_AXI_GP0} Clk {Auto}] \
    [get_bd_intf_pins qir_kernel_0/s_axi_control]

puts "=== adres atamasi ==="
assign_bd_address
foreach seg [get_bd_addr_segs -of_objects [get_bd_cells qir_kernel_0]] {
    puts "  $seg  taban=[get_property OFFSET $seg]  uzunluk=[get_property RANGE $seg]"
}

puts "=== dogrulama ve cikti urunleri ==="
validate_bd_design
save_bd_design
generate_target all [get_files $PRJ/probe_prj.srcs/sources_1/bd/$BDADI/$BDADI.bd]

# .hwh'nin yeri Vivado surumune gore degisir; aramak en saglami.
set bulunan [lsort [glob -nocomplain -directory $PRJ */**/$BDADI.hwh \
                                              **/$BDADI.hwh */*/*/*/*/$BDADI.hwh]]
if {[llength $bulunan] == 0} {
    # genis arama
    set bulunan {}
    foreach f [split [exec find $PRJ -name "*.hwh"] "\n"] {
        if {[string length [string trim $f]]} { lappend bulunan $f }
    }
}
if {[llength $bulunan] == 0} {
    puts "HATA: .hwh uretilmedi. generate_target ciktisina bakin."
    exit 1
}
set kaynak [lindex $bulunan 0]
file copy -force $kaynak $CIKTI
puts ""
puts "=== BITTI ==="
puts "kaynak : $kaynak"
puts "kopya  : $CIKTI"
puts "boyut  : [file size $CIKTI] bayt"
exit 0
