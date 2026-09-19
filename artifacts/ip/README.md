# artifacts/ip/ — Faz 2 çıktısı, Faz 5 girdisi

Vitis HLS `export_design -flow impl` çıktısı: Vivado IP kataloğu paketi.

⚠️ **BU BİR BITSTREAM DEĞİLDİR.** İçinde RTL ve IP meta verisi var. Bitstream,
Faz 5'te bu IP bir Zynq PS blok tasarımına konup Vivado ile sentezlendiğinde
üretilecek.

## Neden burada saklanıyor

Kaynağı `qir_hls_prj/solution1/impl/` — ama orası **gitignore'da** ve
`common.tcl`'deki `open_solution -reset` her `csynth`/`cosim` koşusunda o
dizini **siliyor**. 2026-09-16'da tam olarak bu oldu ve paket kaybedildi;
yeniden üretimi 13 dakika sürdü.

Buradaki kopya o sıfırlamalardan etkilenmez.
git add -A; git commit -m "tasks(faz5): 63 gorev uretildi - G0 ilk, olcum disiplini gomulu"
## Dosya adlandırma

`qir_kernel_ip_<tarih>_<git-hash>.zip` — hangi kod sürümünden üretildiği
ad içinde. Yanındaki `.rpt` o koşumun gerçek P&R sayılarıdır.

## Ölçülen (2026-09-17, git 15931cc)

    LUT   22.535 (%42)    FF  19.466 (%18)
    DSP       33 (%15)    BRAM   187 (%67)
    Post-route 9,122 ns — zamanlama tuttu

İki ayrı koşumda **birebir aynı** çıktı: Vivado P&R bu tasarımda belirlenimci.

## Yeniden üretmek için

    wsl -d Ubuntu -e bash hls/run.sh impl
