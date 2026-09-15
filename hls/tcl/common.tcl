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
set SOLUTION    solution1
set TOP         qir_kernel

# --- Derleyici bayraklari -------------------------------------------------
# QIR_NO_VITIS TANIMLANMAZ: burada gercek ap_fixed kullanilir. Mock yalnizca
# Vitis'siz g++ yolu icindir ve bu iki yolun AYNI sonucu verip vermedigi
# T040'in konusudur -- csim ciktisi WSL sonucuyla karsilastirilarak sinanir.
set CFLAGS      "-std=c++17 -I$REPO/hls/src -I$REPO/hls/tb"

# --- Altin referans (en yenisi) -------------------------------------------
set _refs [lsort [glob -nocomplain $REPO/docs/measurements/reference_*_p2_n5.npy]]
if {[llength $_refs] == 0} {
    puts "HATA: altin referans bulunamadi (docs/measurements/reference_*_p2_n5.npy)"
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

# Testbench argumanlari -- mutlak yol (csim alt dizinde kosuyor)
set TB_ARGV "--reference $REFERENCE --out-dir $REPO/docs/measurements --git-hash vitis"
