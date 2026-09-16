# Ortak proje kurulumu -- csim / csynth / cosim / export bunu source eder.
#
# Tek yerde tutulmasinin sebebi: dort akis AYNI proje ve cozumu paylasmak
# zorunda (cosim, csynth'in urettigi RTL'i ister). Ayarlarin kopyalanmasi,
# iki akisin sessizce farkli konfigurasyon sentezlemesine yol acar.
#
# NOT: bu dosyalar ASCII'dir ve BOM TASIMAZ. Tcl, BOM'u ilk komut sanar ve
# "invalid command name" verir; ayrica dosyayi sistem kod sayfasiyla okudugu
# icin Turkce karakterler bozulur. Bu yuzden yorumlar diakritiksiz.
#
# CALISTIRMA: depo kokunden.
#   vitis-run --mode hls --tcl hls/tcl/csynth.tcl

# --- Depo koku ------------------------------------------------------------
# csim, cozumun alt dizininde kosar; testbench'e verilen yollar bu yuzden
# MUTLAK olmak zorunda.
set REPO [pwd]
if {![file exists $REPO/hls/src/qir_kernel.cpp]} {
    puts "HATA: depo kokunden calistirilmalidir (su an: $REPO)"
    exit 1
}

# --- Kubit sayisi: varsayilan 16, QIR_N ortam degiskeniyle degistirilir ----
#
# NEDEN: cosim n=16 icin 5,4 milyon cevrim simule etmek zorunda. OLCULDU:
# xsim 30 dakikada yalnizca %18 ilerledi ve hizi 14 kat dustu -- bagimlilik
# uyarisi log u 87 MB a ulasmisti ve /mnt/c uzerinden yaziliyordu. Yapisal
# dogrulama (RTL, C ile ayni sonucu veriyor mu) n den BAGIMSIZDIR: RAM_T2P
# baglamasi, DEPENDENCE pragmasi ve boru hatti yapisi n=8 de de AYNIDIR,
# yalnizca dizi boyu kucuktur. Bu yuzden cosim kucuk n ile kosulabilir.
#
#   QIR_N=8 vitis-run --mode hls --tcl hls/tcl/cosim.tcl
set QIR_N 16
if {[info exists ::env(QIR_N)]} { set QIR_N $::env(QIR_N) }

# --- Hedef ----------------------------------------------------------------
# PYNQ-Z2 = XC7Z020, clg400 paket, -1 hiz sinifi.
set PART        {xc7z020clg400-1}
# 100 MHz. UYARI: bu bir VARSAYIMDIR (NC-4), olculmus deger degil. Gercek Fmax
# sentez raporundan okunur ve tum sure tahminleri ona gore yeniden hesaplanir.
set CLOCK_NS    10
# Proje DEPO KOKUNDE. Neden: Vitis 2025.2, kaynak yollarini proje dizinine
# goreli olarak kaydederken BIR SEVIYE EKSIK hesapliyor. Proje hls/build/
# altindayken dogru yol ../../src/... olmasi gerekirken ../src/... yaziyor,
# sonra bulamayip dosyayi SESSIZCE atliyor. Kokte hicbir ".." gerekmedigi
# icin sorun olusmuyor.
set PROJ        $REPO/qir_hls_prj
# n != 16 AYRI proje dizini kullanir: n=16 sentez sonuclari ezilmesin.
if {$QIR_N != 16} { set PROJ ${PROJ}_n$QIR_N }
set SOLUTION    solution1
set TOP         qir_kernel

# --- Derleyici bayraklari -------------------------------------------------
# QIR_NO_VITIS TANIMLANMAZ: burada gercek ap_fixed kullanilir. Mock yalnizca
# Vitis'siz g++ yolu icindir ve bu iki yolun AYNI sonucu verip vermedigi
# T040'in konusudur -- csim ciktisi WSL sonucuyla karsilastirilarak sinanir.
set CFLAGS      "-std=c++17 -DQIR_N_QUBITS=$QIR_N -I$REPO/hls/src -I$REPO/hls/tb"

# --- Altin referans (en yenisi) -------------------------------------------
# n=16 icin gercek TSP referansi (Faz 1); digerleri icin sentetik referans
# (scripts/make_synthetic_reference.py -- tek-sicak TSP de kubit sayisi
# (N-1)^2 oldugu icin 8 ve 12 nin problem karsiligi YOKTUR).
if {$QIR_N == 16} {
    set _kalip $REPO/docs/measurements/reference_*_p2_n5.npy
} else {
    set _kalip $REPO/docs/measurements/synthref_*_p2_n$QIR_N.npy
}
set _refs [lsort [glob -nocomplain $_kalip]]
if {[llength $_refs] == 0} {
    puts "HATA: altin referans bulunamadi ($_kalip)"
    exit 1
}
set REFERENCE [file rootname [lindex $_refs end]]

# --- Proje ----------------------------------------------------------------
open_project -reset $PROJ
set_top $TOP

# SENTEZLENEN: yalnizca ust seviye cekirdek.
#
# DIKKAT -- yollar MUTLAK DEGIL, depo kokune GORELI verilir. Mutlak yol
# verilince Vitis 2025.2 bunu hatali bir goreli yola ceviriyor
# ("../src/qir_kernel.cpp" -- bir seviye eksik), sonra bulamayip
# "Cannot find source file ...; skipping it" diyerek SESSIZCE atliyor.
# Sonuclari: csim linker hatasi (undefined symbol: qir::run_circuit) ve
# csynth asamasinda "Cannot find any design unit to elaborate".
# Testbench dosyalarinda ayni sorun gorulmedi ama tutarlilik icin onlar da
# goreli verilir.
add_files hls/src/qir_kernel.cpp -cflags $CFLAGS

# SENTEZLENMEYEN: testbench + dogrulama yuzeyi.
# qir_kernel_debug bilincli olarak -tb tarafindadir; sentezlenseydi sv_out
# bir m_axi portu dogurur ve sozlesme maddesi K-1'i ihlal ederdi.
add_files -tb hls/tb/tb_kernel.cpp        -cflags $CFLAGS
add_files -tb hls/tb/qir_kernel_debug.cpp -cflags $CFLAGS

open_solution -reset $SOLUTION -flow_target vivado
set_part $PART
create_clock -period $CLOCK_NS -name default

# --- Otomatik boru hatti KAPALI ---------------------------------------------
# Vitis HLS varsayilan olarak tur sayisi 64'un altindaki donguleri KENDILIGINDEN
# boru hattina alir (config_compile -pipeline_loops, varsayilan 64). Bir donguyu
# boru hattina alirken ic dongulerini ACMAK ZORUNDA oldugu icin, tablo kurma
# dongulerimin ic donguleri (8, 28 ve 64 turlu) aciliyordu.
#
# OLCULDU: apply_cost_layer'in 81.087 LUT'unun ~78.000'i tablo kurma
# dongulerindeydi; asil genlik dongusu yalnizca 2.276 LUT. "#pragma HLS PIPELINE
# off" eklemek ISE YARAMADI -- bu bir pragma meselesi degil, PROJE AYARI.
#
# 0 = otomatik boru hatti yok; yalnizca acikca yazilan PIPELINE pragma'lari
# gecerli olur.
config_compile -pipeline_loops 0

# --- Carpicilari boru hattina al -------------------------------------------
# OLCULDU: kritik yol apply_rx_dyn'in carp-topla-yuvarla zincirinde, 24,799 ns
# (hedef 10 ns). Yuvarlama+doyurma kiplerini en ucuza (AP_TRN/AP_WRAP)
# cekmek 17,185 ns'ye indiriyor -- yani onlar yolun 7,6 ns'si, ama kalan 17,2 ns
# hala hedefin ustunde. Geri kalan, boru hattina ALINMAMIS carpicidir:
# HLS DSP'yi varsayilan olarak kombinasyonel kullaniyor.
#
# -latency 3: carpma 3 cevrime yayilir. Gecikme artar ama saat hizlanir; net
# etki olculecek.
config_op mul -impl dsp -latency 3

# Zamanlama zorlaninca daha cok arama yap.
config_schedule -effort high

# Testbench argumanlari -- mutlak yol (csim alt dizinde kosuyor)
set TB_ARGV "--reference $REFERENCE --out-dir $REPO/docs/measurements --git-hash vitis --n $QIR_N"
