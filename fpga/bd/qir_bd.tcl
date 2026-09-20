# Gercek blok tasarim — PYNQ-Z2 uzerinde qir_kernel (gorevler T013, T014).
#
# Board files YOK (research.md §R2): PS7 Tcl ile ELLE yapilandirilir. Board
# preset'inin verdigi sey DDR modeli, PS referans saati ve FCLK ayarlaridir;
# ucu de burada birkac satirdir ve depoya commit edilebilir METINDIR — board
# dosyasi ise harici, surumsuz bir bagimliliktir.
#
# EMIO I2C (karar K2, §R5): US3'te INA219'u KART kendisi okuyacak. Simdi
# eklemek ~10 dakika; sonra eklemek tam bir sentez turu ARTI US1/US2
# olcumlerinin tekrari demek (olculen ikili degisir, FR-016 izlenebilirligi
# bozulur).
#
# ⚠️ FCLK0 = 100 MHz burada IMPLEMENTASYON ZAMANI kisitidir; zamanlama analizi
# buna gore yapilir (T017: WNS >= 0). CALISMA ZAMANINDA FCLK'yi bu bitstream
# DEGIL, kartin boot'taki ps7_init'i belirler — PYNQ .bit'i indirirken PS'i
# yeniden yapilandirmaz. Konak kodu bu yuzden frekansi dogrulamak/ayarlamak
# zorundadir:
#     from pynq.ps import Clocks;  Clocks.fclk0_mhz = 100
# Dogrulanmazsa cekirdek baska bir saatte kosar ve butun gecikme olcumleri
# sessizce yanlis cikar.

set REPO   [file normalize [file join [file dirname [info script]] .. ..]]
set PART   xc7z020clg400-1
set PRJ    $REPO/artifacts/bitstream/qir_prj
set IPREPO $REPO/artifacts/ip/repo
set BDADI  qir_bd

# AXI-Lite taban adresi SABITLENIR. B yolunun (Bitstream + MMIO) tek dogruluk
# kaynagi budur ve contracts/axi-register-map.md ile ayni olmak ZORUNDA.
set AXI_TABAN 0x43C00000
set AXI_UZUNLUK 64K

if {![file isdirectory $IPREPO]} {
    puts "HATA: IP deposu yok: $IPREPO  (T001 kosulmamis)"
    exit 1
}

# Kalip DAR olmali: "*processing_system7*" hem processing_system7:5.5 hem
# processing_system7_vip:1.0 dondurur ve ikisi birden -vlnv'ye gidince
# "IP definition not found" alinir (19 Eylul'de bu yasandi).
proc tek_vlnv {kalip ad} {
    set bulunan [get_ipdefs -all $kalip]
    if {[llength $bulunan] == 0} {
        puts "HATA: $ad IP katalogda bulunamadi (kalip: $kalip)"
        exit 1
    }
    set secilen [lindex [lsort $bulunan] end]
    puts "  $ad: $secilen"
    return $secilen
}

file mkdir $REPO/artifacts/bitstream
if {[file isdirectory $PRJ]} { file delete -force $PRJ }

puts "=== proje ve IP katalogu ==="
create_project qir_prj $PRJ -part $PART -force
set_property ip_repo_paths $IPREPO [current_project]
update_ip_catalog -rebuild
set vlnv_qir [tek_vlnv {*:qir_kernel:*} qir_kernel]
set vlnv_ps  [tek_vlnv {xilinx.com:ip:processing_system7:*} processing_system7]

puts "=== blok tasarim ==="
create_bd_design $BDADI
create_bd_cell -type ip -vlnv $vlnv_ps ps7_0
apply_bd_automation -rule xilinx.com:bd_rule:processing_system7 \
    -config {make_external "FIXED_IO, DDR" apply_board_preset "0" Master "Disable" Slave "Disable"} \
    [get_bd_cells ps7_0]

puts "=== PS7 elle yapilandirma (board preset yerine) ==="
set_property -dict [list \
    CONFIG.PCW_UIPARAM_DDR_PARTNO        {MT41J256M16 RE-125} \
    CONFIG.PCW_UIPARAM_DDR_BUS_WIDTH     {16 Bit} \
    CONFIG.PCW_CRYSTAL_PERIPHERAL_FREQMHZ {33.333333} \
    CONFIG.PCW_EN_CLK0_PORT              {1} \
    CONFIG.PCW_FPGA0_PERIPHERAL_FREQMHZ  {100} \
    CONFIG.PCW_USE_M_AXI_GP0             {1} \
    CONFIG.PCW_I2C0_PERIPHERAL_ENABLE    {1} \
    CONFIG.PCW_I2C0_I2C0_IO              {EMIO} \
] [get_bd_cells ps7_0]

puts "=== qir_kernel ==="
create_bd_cell -type ip -vlnv $vlnv_qir qir_kernel_0

# Otomasyon smartconnect/interconnect + proc_sys_reset'i kendisi ekler ve
# baglar. Elle kablolamaktan cok daha saglam; tek AXI-Lite kolesi icin ikisi
# arasindaki fark islevsel degildir (G0 sondasi ayni yolla kosuldu).
apply_bd_automation -rule xilinx.com:bd_rule:axi4 \
    -config [list Master {/ps7_0/M_AXI_GP0} Clk {Auto}] \
    [get_bd_intf_pins qir_kernel_0/s_axi_control]

puts "=== EMIO I2C disari veriliyor (karar K2) ==="
make_bd_intf_pins_external -name IIC_0 [get_bd_intf_pins ps7_0/IIC_0]

puts "=== adres atamasi ==="
# ⚠️ `set_property offset` CALISMAZ: bd_addr_seg uzerinde 'offset' SALT
# OKUNURDUR ("Cannot change read-only property 'offset'"). Adres yalnizca
# assign_bd_address'e parametre olarak verilebilir.
assign_bd_address
set seg [get_bd_addr_segs -of_objects [get_bd_cells qir_kernel_0]]
if {[llength $seg] != 1} {
    puts "HATA: beklenen tek adres segmenti, bulunan: $seg"
    exit 1
}
assign_bd_address -force -offset $AXI_TABAN -range $AXI_UZUNLUK $seg

# ⚠️ OFFSET, KOLE segmentinde (/qir_kernel_0/s_axi_control/Reg) DEGIL, efendi
# adres uzayindaki eslemede (/ps7_0/Data/SEG_...) durur. Kole segmentini
# sorgulamak bos dize dondurur ve dogrulama, atama basarili olsa bile duser.
set mseg {}
foreach s [get_bd_addr_segs /ps7_0/Data/*] {
    if {[string match -nocase *qir_kernel* $s]} { set mseg $s }
}
if {$mseg eq ""} {
    puts "HATA: /ps7_0/Data altinda qir_kernel eslemesi yok."
    puts "      Mevcut: [get_bd_addr_segs /ps7_0/Data/*]"
    exit 1
}
set gercek [get_property OFFSET $mseg]
if {$gercek eq "" || [expr {$gercek + 0}] != [expr {$AXI_TABAN + 0}]} {
    puts "HATA: taban adres '$gercek', beklenen '$AXI_TABAN'"
    puts "      contracts/axi-register-map.md ile uyusmuyor."
    exit 1
}
puts "  $mseg  taban=[format 0x%08X $gercek]  uzunluk=[get_property RANGE $mseg]"

puts "=== kisitlar ==="
add_files -fileset constrs_1 -norecurse $REPO/fpga/bd/qir_constraints.xdc

puts "=== dogrulama ve cikti urunleri ==="
validate_bd_design
save_bd_design
set bd_dosya [get_files $PRJ/qir_prj.srcs/sources_1/bd/$BDADI/$BDADI.bd]
generate_target all $bd_dosya
make_wrapper -files $bd_dosya -top
add_files -norecurse $PRJ/qir_prj.gen/sources_1/bd/$BDADI/hdl/${BDADI}_wrapper.v
set_property top ${BDADI}_wrapper [current_fileset]
update_compile_order -fileset sources_1
puts "=== BD HAZIR ==="
