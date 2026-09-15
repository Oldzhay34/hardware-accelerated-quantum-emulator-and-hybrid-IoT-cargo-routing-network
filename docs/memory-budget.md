# Bellek Bütçesi — PYNQ-Z2 Statevector

**Kaynak**: Faz 0 ucuz sigortası **S-3** ([risk-register.md](risk-register.md)) · **Tarih**: 2026-09-13
**Üreten**: [`scripts/memory_budget.py`](../scripts/memory_budget.py) — sentez gerektirmez, saf aritmetik.

> Bu belgenin amacı: **16 kübitin çip-içi belleğe sığıp sığmadığını ilk sentez raporundan (H4) üç hafta önce söylemek.**
> Anayasa Prensip III doğrudan buna dayanıyor: *"Her tasarım kararı önce bellek bütçesine karşı doğrulanır."*
> Faz 2.1 bu tabloyu kaynak (DSP/LUT/FF) tarafıyla genişletecek; burada yalnızca bellek var.

---

## 1. Donanım gerçekleri

**Kaynak: [DS190 — Zynq-7000 SoC Data Sheet: Overview](https://docs.amd.com/v/u/en-US/ds190-Zynq-7000-Overview)**, AMD resmî veri sayfası, Z-7020 sütunu (2026-09-15'te indirilip okundu).

| | XC7Z020 (PYNQ-Z2) | DS190'daki karşılığı |
|---|---|---|
| Toplam BRAM | 140 × 36 Kb = **645.120 B (630 KB)** | "Total Block RAM (# 36Kb Blocks): **4.9Mb (140)**" |
| **URAM** | ❌ **YOK** | Tabloda böyle bir satır yok — URAM UltraScale+ özelliğidir |
| DSP Slices (DSP48E1) | **220** | "DSP Slices: **220**" |
| LUT | **53.200** | "Look-Up Tables (LUTs): **53,200**" |
| Flip-Flop | **106.400** | "Flip-Flops: **106,400**" |
| Logic Cells | 85K | "Logic Cells: **85K**" |
| PL eşdeğeri | Artix-7 | "7 Series PL Equivalent: **Artix-7**" |
| %85 tavanı ([K-02 ölçütü](../specs/000-kapsam-takvim/cut-plan.md)) | **548.352 B (536 KB)** | — |

> Faz 0'da (S-3, 2026-09-13) bu sayılar hafızadan yazılmıştı. 2026-09-15'te resmî veri sayfasından
> **birebir doğrulandı** — hiçbir düzeltme gerekmedi. Artık tahmin değil, kaynaklı.

### ⚠️ Sentez raporunu okurken: BRAM_18K, BRAM_36K değil

DS190 **36Kb blok** sayısını veriyor (140). Ama her 36Kb blok iki bağımsız 18Kb bloğa bölünebilir
ve **Vitis HLS kaynak tablosunda `BRAM_18K` olarak raporlar**:

| Sayım birimi | Bütçe |
|---|---:|
| BRAM36 (veri sayfası) | **140** |
| **BRAM_18K (HLS raporu)** | **280** |

Bunu karıştırmak pahalıdır: HLS raporunda "BRAM_18K: 240" görüp 140'a bölersen **%171** (panik),
280'e bölersen **%86** (gerçek). [K-02](../specs/000-kapsam-takvim/cut-plan.md)'nin %85 ölçütü
**280 üzerinden** okunmalıdır.

### ⚠️ Anayasa metninde bir düzeltme gerekiyor

Anayasa Prensip III *"Statevector çip-içi bellekte (BRAM/**URAM**) kalmalıdır"* diyor.
**Zynq-7000 ailesinde URAM yoktur** — UltraRAM bir UltraScale+ özelliğidir. Bu çipte tek seçenek BRAM.

Bu bir ilke değişikliği değil, olgusal bir düzeltme; ilkenin özü (çip-içi bellekte kal, DDR'a taşma) aynen geçerli. Anayasayı düzeltmek istersen versiyon 1.0.1 olarak işaretlerim — söyle yeter.

---

## 2. Hesap

Statevector = `2^n` karmaşık genlik × 2 reel sayı × (format genişliği) × (tampon sayısı).

| Kübit | Format | Tamponlama | Boyut | BRAM % | Durum |
|---:|---|---|---:|---:|---|
| **16** | double (64-bit) | yerinde | 1024 KB | 162,5% | 🔴 **SIĞMIYOR** |
| **16** | double (64-bit) | ping-pong | 2048 KB | 325,1% | 🔴 **SIĞMIYOR** |
| **16** | float (32-bit) | yerinde | 512 KB | 81,3% | 🟡 sığıyor (dar) |
| **16** | float (32-bit) | ping-pong | 1024 KB | 162,5% | 🔴 **SIĞMIYOR** |
| **16** | Q1.31 | yerinde | 512 KB | 81,3% | 🟡 sığıyor (dar) |
| **16** | Q1.31 | ping-pong | 1024 KB | 162,5% | 🔴 **SIĞMIYOR** |
| **16** | Q1.15 | yerinde | 256 KB | 40,6% | 🟢 sığıyor |
| **16** | Q1.15 | ping-pong | 512 KB | 81,3% | 🟡 sığıyor (dar) |
| **14** | double | yerinde | 256 KB | 40,6% | 🟢 sığıyor |
| **14** | double | ping-pong | 512 KB | 81,3% | 🟡 sığıyor (dar) |
| **14** | float | ping-pong | 256 KB | 40,6% | 🟢 sığıyor |
| **12** | double | ping-pong | 128 KB | 20,3% | 🟢 sığıyor |

*(Tam tablo için script'i çalıştır.)*

---

## 3. 🔴 Asıl bulgu: 16 kübitte tasarım alanı çok dar

**Çift duyarlık (double) 16 kübitte imkânsızdır** — tek tampon bile BRAM'in 1,6 katını istiyor. Bu, tartışmaya açık değil, aritmetik.

16 kübitte sığan **tek** seçenekler şunlar, ve ikisi de bir bedel getiriyor:

| Seçenek | BRAM | Bedeli |
|---|---:|---|
| **(a)** float32 + **yerinde** | 81,3% | Ping-pong yok → okuma ve yazma aynı diziye. **Bankalama problemini en zor haliyle çözmek zorundasın** ([SK-02](risk-register.md) / [K-03](../specs/000-kapsam-takvim/cut-plan.md) — projenin 1 numaralı riski). |
| **(b)** Q1.15 + ping-pong | 81,3% | Bankalama kolaylaşır, ama **16-bit sabit nokta** → biriken yuvarlama hatası fidelity eşiğini (≥0,99, [DG-01](risk-register.md)) tehdit eder. |
| **(c)** 14 kübit + float32 + ping-pong | 40,6% | İkisi de rahat — ama **"16 kübit" iddiası düşer**. |

### Bunun anlamı

Bellek bütçesi ile bankalama riski **birbirine bağlı** çıktı, ve bu bağ sentezden önce görülmeseydi H4–H5'te sürpriz olurdu:

> Ping-pong tamponlama, bankalama çakışmasından kaçınmanın standart yoludur.
> **16 kübitte ping-pong'a yalnızca Q1.15 ile para yetiyor.**
> Yani 16 kübitte ya doğruluğu (Q1.15) ya da bankalama kolaylığını (yerinde) feda ediyorsun.

### Kesme planına etkisi — K-02'nin merdiveni düzeltilmeli

[cut-plan.md K-02](../specs/000-kapsam-takvim/cut-plan.md) şu sırayı yazıyordu: *kübit 16→14→12, format çift→tek→Q1.15*.

**Merdivenin ilk basamağı zaten yok**: 16 kübit + double hiçbir zaman mümkün değildi. Merdiven gerçekte şöyle başlıyor:

```
16 kübit + float32 yerinde   (81%, bankalama zor)
16 kübit + Q1.15 ping-pong   (81%, fidelity riskli)
14 kübit + float32 ping-pong (41%, rahat — "16 kübit" iddiası düşer)
12 kübit + ...               (taban, K-02'deki nihai sınır)
```

---

## 4. Faz 2.1'e devredilenler

Bu, S-3'ün *ucuz ve erken* versiyonu. Faz 2.1 (M) şunları eklemeli:

| Eksik | Neden önemli |
|---|---|
| Kapı katsayısı / twiddle depolama | Küçük ama 81% doluluğun üstüne biniyor — payı yok |
| Kontrol/FSM tamponları, FIFO derinlikleri | Aynı gerekçe |
| **BRAM granülaritesi kaybı** | 36 Kb bloklar tam dolmaz; port genişliği/derinlik uyumsuzluğu efektif kapasiteyi düşürür. Gerçek doluluk buradaki sayılardan **yüksek** çıkar. |
| DSP/LUT/FF bütçesi | Bu belge yalnızca belleği kapsıyor |
| Q1.15'in fidelity'ye etkisi | (b) seçeneği ancak bu ölçülürse değerlendirilebilir — [S-6](risk-register.md) ile bağlı |

⚠️ **Granülarite uyarısı önemli**: %81,3 rakamları *ideal paketleme* varsayıyor. Gerçek sentezde BRAM blokları tam dolmayacağı için bu sayılar yukarı gidecek — yani (a) ve (b) seçenekleri **%85 tavanını aşabilir**. Faz 2.1 bunu netleştirene kadar 16 kübit "sığıyor" değil, **"sınırda"** kabul edilmelidir.

---

## 5. Tekrar üretim

```bash
.venv/Scripts/python.exe scripts/memory_budget.py
```

Deterministik ve girdisiz — donanım sabitleri script içinde tanımlı. Varsayım değişirse (ör. %85 tavanı) script'teki sabit güncellenir, tablo yeniden üretilir.
