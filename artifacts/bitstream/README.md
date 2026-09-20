# `artifacts/bitstream/` — üretilen bitstream'ler

**Bu dizindeki `.bit`/`.hwh` dosyaları git'e GİRMEZ**
([repo-conventions §3](../../docs/repo-conventions.md)). Depoda yalnız bu
README durur: üretim komutu, araç sürümü, kaynak git hash'i ve **SHA-256**
özetleri. FR-016 izlenebilirliği böyle karşılanır — dosyanın kendisi değil,
*hangi kaynaktan hangi komutla üretildiği ve özetinin ne olduğu* saklanır.

---

## `qir_20260920_d350605` — ilk tam bitstream

| | |
|---|---|
| Üretim tarihi | 2026-09-20 14:19 |
| Kaynak git hash | `d350605` |
| Araç | **Vivado 2025.2** (WSL/Ubuntu, `/opt/Xilinx/2025.2`) |
| Parça | `xc7z020clg400-1` (PYNQ-Z2) |
| Kullanılan IP paketi | `qir_kernel_ip_20260917_15931cc.zip` → `qir-engine:hls:qir_kernel:0.1` |
| **AXI-Lite taban adresi** | **`0x43C00000`**, uzunluk `0x10000` |
| Süre | ~13 dakika (BD + sentez + implementasyon + bitstream) |

### SHA-256

```
d4ca4522265253a7a9660e78657ec488443357524915867954bf4d40eb070f6f  qir_20260920_d350605.bit
b216737ceccca3141dfd625e1918bb027113388911e6f7ad4655cd35f2b56ff4  qir_20260920_d350605.hwh
```

### Üretim komutu

```bash
wsl -d Ubuntu -e bash fpga/bd/build.sh
```

Betik `fpga/bd/qir_bd.tcl` (blok tasarım) ve `fpga/bd/qir_constraints.xdc`
(pin kısıtları) dosyalarını kullanır; ikisi de depoda.

### Zamanlama — 100 MHz'de tuttu

| | |
|---|---|
| **WNS** (setup) | **+0,776 ns** ✅ |
| **WHS** (hold) | **+0,015 ns** ✅ |

⚠️ Hold payı **15 pikosaniye** — geçti ama çok ince. Tasarım veya araç sürümü
değişirse bu ilk kaybedilecek şeydir ve **hold ihlali saat düşürerek
çözülmez**. Her yeni bitstream'de WHS ayrıca kontrol edilmeli.

Kritik yol 9,224 ns. Faz 2'nin yalnız-HLS export'u 9,122 ns demişti; aradaki
~0,1 ns, eklenen PS altyapısının (interconnect + reset) bedelidir ve
beklenendir.

### Kaynak kullanımı — Faz 2 ile çapraz doğrulama

| Kaynak | Bu bitstream | Faz 2 (yalnız HLS) | Fark |
|---|---|---|---|
| LUT | **22.940** (%43,1) | 22.535 (%42,4) | +405 |
| FF | **19.973** (%18,8) | 19.466 (%18,3) | +507 |
| BRAM | **93,5 tile** (%66,8) | 187 RAMB18 (%67) | aynı (93,5 × 2 = 187) |
| DSP | **33** (%15,0) | 33 (%15) | aynı |
| IOB | 2 (%1,6) | — | EMIO I2C'nin iki pini |

LUT ve FF'deki küçük artış PS altyapısından geliyor; DSP ve BRAM **birebir
aynı**, yani çekirdek değişmemiş. Bu, Faz 2 ölçümlerinin bu bitstream için
hâlâ geçerli olduğunun çapraz kontrolüdür.

### İçerik

`.hwh` şu blokları içerir: `processing_system7`, `qir_kernel`,
`axi_interconnect`, `proc_sys_reset`. `.bit` boyutu 3,86 MB.

### ⚠️ Çalışma zamanında FCLK doğrulanmalı

BD'deki **FCLK0 = 100 MHz bir implementasyon zamanı kısıtıdır** — zamanlama
analizi ona göre yapıldı. Çalışma zamanında PL saatini bu bitstream değil,
kartın boot'taki `ps7_init`'i belirler; PYNQ `.bit` indirirken PS'i yeniden
yapılandırmaz. Konak kodu bunu **doğrulamak zorundadır**:

```python
from pynq.ps import Clocks
Clocks.fclk0_mhz = 100
```

Doğrulanmazsa çekirdek başka bir saatte koşar ve bütün gecikme ölçümleri
sessizce yanlış çıkar — sonuç "makul" göründüğü için de fark edilmez.

Aynı sebeple BD'deki DDR ayarları çalışma zamanında etkisizdir (PS tarafı;
bizim `.bit` yalnız PL'i programlar).

### Pin kısıtları

Dışarıya çıkan tek arayüz PS I2C0'ın EMIO hattıdır (karar K2):

| Port | Pin | Konektör |
|---|---|---|
| `IIC_0_scl_io` | **P15** | Arduino başlığı SCL |
| `IIC_0_sda_io` | **P16** | Arduino başlığı SDA |

⚠️ PYNQ-Z2'de üç ayrı I2C var. `IIC_1` (U9/T9) **kart üzerindeki ses kodeki**
hattıdır, dışarıya açık değildir — oraya bağlamak veri yolu çakışması demektir.
Pin kaynağı: Xilinx/PYNQ deposu `boards/Pynq-Z2/base/vivado/constraints/base.xdc`.
