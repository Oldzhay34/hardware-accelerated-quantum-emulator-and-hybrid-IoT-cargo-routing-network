# `fpga/` — Vivado tarafı

**Açılış**: Faz 5, karar **K3** ([plan.md](../specs/003-zynq-ps-kartta-kosum/plan.md))

Bu dizin **Vivado** işidir: blok tasarım, kısıtlar ve elle yazılan RTL.
Vitis HLS işi `hls/` altındadır ve oraya karışmaz.

## `hls/` ile sınır — tek cümle

> **HLS `artifacts/ip/` içinde biter, Vivado orada başlar.**

`hls/` bir C++ çekirdeğini alıp paketlenmiş bir IP üretir. O IP'nin zip'i
`artifacts/ip/` altına damgalı olarak konur. `fpga/` o zip'i bir **girdi**
olarak tüketir; `hls/` altındaki hiçbir dosyaya bakmaz, hiçbir şey yazmaz.

```
hls/  ──(csynth + export)──>  artifacts/ip/qir_kernel_ip_<tarih>_<hash>.zip
                                          │
                                          ▼  girdi
                              fpga/bd/  ──(BD + sentez + impl)──>
                                          artifacts/bitstream/qir_<tarih>_<hash>.{bit,hwh}
```

Neden ayrı: `hls/` iki dakikada koşan bir C-sim'den on dakikalık bir senteze
kadar her şeyi kapsar ve **kart gerektirmez** (Anayasa Prensip V). `fpga/` ise
karta özgüdür — PYNQ-Z2 pin haritası, DDR preset'i, EMIO çıkışları. İkisini
aynı dizine koymak, kartsız geliştirmeyi kart ayarlarına bağımlı hâle getirirdi.

## İçerik

| Yol | Ne |
|---|---|
| `bd/` | Blok tasarım Tcl betikleri, XDC kısıtları, yapı betikleri |
| `rtl/` | **Elle yazılan** Verilog/VHDL. HLS üretimi buraya konmaz. |

### `bd/` dosyaları

| Dosya | Ne |
|---|---|
| `probe_hwh.tcl` | **G0**: PS + gerçek `qir_kernel` IP içeren kukla BD; yalnız `.hwh` üretir, sentez koşmaz |
| `probe_hwh.sh` | Yukarıdakinin WSL koşucusu |
| `probe_test.py` | **Kartta** koşar: PYNQ'nun `.hwh`'yi ayrıştırıp ayrıştıramadığını ölçer |

> ✅ **G0 sonucu (2026-09-20): A yolu açık.** PYNQ 2.5, Vivado 2025.2'nin
> `.hwh`'sini okudu — `ip_dict`, taban adres ve 11 register'ın hepsi.
> Ayrıntı ve iki yeni kısıt (root gereksinimi, `HWH` sınıfının yokluğu):
> [research.md §R1](../specs/003-zynq-ps-kartta-kosum/research.md).

## Neden `rtl/` boşken bile duruyor

Elle yazılacak RTL'in `hls/` altına konacak yeri **yok** — orası tanımı gereği
"Vitis HLS kaynakları"dır ([repo-conventions.md](../docs/repo-conventions.md) §2).
Dizin şimdiden ayrılır ki ilk Verilog dosyası yazıldığında yer tartışması
açılmasın.

## Koşturma

```bash
# G0 sonda .hwh'si (sentez yok, birkac dakika)
wsl -d Ubuntu -e bash fpga/bd/probe_hwh.sh
```

⚠️ Vitis/Vivado yalnız **WSL**'de kurulu ve her çağrıda `LC_ALL=en_US.UTF-8`
şarttır — yoksa araçlar çekirdek döker
([runbook](../docs/runbooks/vitis-hls-kurulum.md)).

## Git

`fpga/` bir **kaynak** dizinidir, commit edilir. Vivado'nun ara çıktıları
(`*.log`, `*.jou`, proje dizinleri) `.gitignore`'dadır; üretilen bitstream'ler
`artifacts/bitstream/` altına gider ve commit **edilmez**.
