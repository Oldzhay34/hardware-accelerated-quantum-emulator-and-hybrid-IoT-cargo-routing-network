# Sözleşme: AXI-Lite Register Haritası (kart yüzeyi)

**Uygular**: FR-001, FR-002, FR-005, FR-006, FR-007 ·
**Kaynak**: IP paketi içindeki `drivers/qir_kernel_v0_1/src/xqir_kernel_hw.h`
(Vitis HLS 2025.2 üretimi) ·
**Faz 2 karşılığı**: [kernel-interface.md](../../002-fpga-statevector-cekirdegi/contracts/kernel-interface.md)

Bu dosya, PYNQ'nun `.hwh`'yi ayrıştıramaması hâlinde (§[research.md](../research.md) R1)
**tek doğruluk kaynağıdır**. `Overlay` çalışsa bile bu harita geçerlidir;
`Overlay` yalnızca onu otomatik keşfeder.

---

## Adres penceresi

| | |
|---|---|
| Taban adres | Blok tasarımda atanır — tipik `0x43C0_0000`. **`fpga/bd/qir_bd.tcl` içinde sabitlenir ve `DonanimYapiti.axi_taban_adres` olarak kaydedilir.** |
| Uzunluk | `0x2800` kullanılır, **`0x10000` ile eşlenir** (sayfa hizası) |

```python
from pynq import MMIO
mmio = MMIO(TABAN, 0x10000)
```

---

## Harita

| Ofset | Ad | Erişim | Genişlik |
|---|---|---|---|
| `0x0000` | `AP_CTRL` | R/W | bit0 `ap_start`, bit1 `ap_done`, bit2 `ap_idle`, bit3 `ap_ready`, bit7 `auto_restart` |
| `0x0004` | `GIE` | R/W | Genel kesme izni |
| `0x0008` | `IER` | R/W | IP kesme izni |
| `0x000c` | `ISR` | R/TOW | Kesme durumu |
| `0x0020`–`0x002f` | `cos_beta[3]` | W | word başına bit[17:0] |
| `0x0030`–`0x003f` | `sin_beta[3]` | W | word başına bit[17:0] |
| `0x0048` | `p` | R/W | bit[31:0] |
| `0x0050` | `beklenen_deger` | **R** | bit[31:0], IEEE-754 float |
| `0x0054` | `beklenen_deger_ap_vld` | R/COR | bit0 |
| `0x1000`–`0x1fff` | `phases[816]` | W | word başına 32b |
| `0x2000`–`0x27ff` | `cost[272]` | W | word başına 32b |

**Eleman adresleme**: `adres(dizi[n]) = taban_ofset + 4*n`. Her eleman **kendi
32-bit word'ünde** durur; bit paketleme **yoktur** (18-bit tipler 32-bit word'e
yastıklanır).

> ⚠️ Kesme kullanılmaz. `GIE`/`IER`/`ISR` haritada var ama bu fazda `ap_done`
> **yoklanır** (§R4). Kesme yolu Faz 5 kapsamı dışıdır.

---

## Dizi yerleşimi

`phases` ve `cost`, C tarafındaki struct sırasını **düz** izler:

```
cost[0..15]      = cost_scaled_t.h[k]        k = 0..15
cost[16..271]    = cost_scaled_t.J[a][b]     satır öncelikli: 16 + 16*a + b
```

```
phases[r*272 + 0..15]    = phases[r].h[k]
phases[r*272 + 16..271]  = phases[r].J[a][b]      r = 0..2  (P_MAX = 3)
```

`J` yalnızca `a < b` için okunur, ama **256 word'ün tamamı yazılır** —
kullanılmayanlar sıfırlanır. 816 = 3 × 272 ✓ (`DEPTH_PHASES` ile uyumlu).

---

## Çağrı sırası

```
1. ap_idle (0x0000 bit2) == 1 olduğu doğrulanır       → meşgulse hata
2. cost[272], phases[816], cos_beta[3], sin_beta[3], p yazılır   → 1.095 yazma
3. ap_start (0x0000 bit0) <- 1
4. ap_done (0x0000 bit1) yoklanır                     → zaman aşımı: 5 sn
5. beklenen_deger (0x0050) okunur, uint32 -> float yeniden yorumlanır
```

**Yazma sayısı 1.095** — `phases` 816 + `cost` 272 + `cos_beta` 3 +
`sin_beta` 3 + `p` 1. Bu sayı gecikme kapsamının (`T_yazma`) tanımıdır ve
raporlanması zorunludur: CPU tarafında böyle bir aktarım maliyeti **yoktur**.

### İzdüşüm koşumu (kısa yol)

`cost`, `run_circuit`'e girmez — yalnız `expectation_scaled`'i besler. Aynı
devrenin başka bir izdüşümü için **yalnız adım 2'nin `cost` kısmı** (272 word)
yeniden yazılır; `phases`, `cos_beta`, `sin_beta`, `p` yerinde kalır:

```
2'. cost[272] yazılır          → 272 yazma (1.095 değil)
3'. ap_start <- 1
4'. ap_done yoklanır
5'. beklenen_deger okunur      → aynı statevector'ün yeni izdüşümü
```

> ⚠️ **Gecikme ölçümünde bu kısa yol KULLANILMAZ.** G4 tam çağrı sırasını
> ölçer; kısa yol yalnız G3 doğrulamasına aittir. Karıştırılırsa `T_yazma`
> olduğundan küçük raporlanır.

---

## Sözleşme maddeleri

| # | Madde |
|---|---|
| A-1 | `ap_start` yazılmadan önce `ap_idle` **doğrulanır**. "Yükledim, koşuyordur" varsayımı FR-001'in reddettiği şeydir. |
| A-2 | `beklenen_deger` yalnızca `ap_done` görüldükten sonra okunur. Önce okunan değer **geçersizdir**. |
| A-3 | `p < 1` veya `p > 3` → çekirdek çalışmaz ve `0x0050` **değişmez** (madde K-2). Bu davranış test edilir. |
| A-4 | `ap_done` 5 sn içinde gelmezse koşum `gecerli=false` işaretlenir; kısmî sonuç **ölçüm sayılmaz**. |
| A-5 | Çekirdek durumsuzdur (madde K-4): art arda iki koşum arasında sıfırlama gerekmez, ama **belirlenimcilik test edilir** (SC-002). |
| A-6 | `0x0050` ham 32-bit okunur ve `struct.unpack('<f', ...)` ile yorumlanır. Float'a kesme (cast) **yapılmaz** — bit deseni korunur. |

---

## Bu yüzeyin vermediği şey

**Genlik vektörü.** Madde K-1 gereği `m_axi` yoktur; statevector çip-içi BRAM'de
kalır ve AXI'den görünmez. Doğrulama bu yüzden beklenen değer üzerinden kurulur
— gerekçe ve sınırları [research.md](../research.md) §R3'te.
