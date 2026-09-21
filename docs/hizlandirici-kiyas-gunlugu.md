# Hızlandırıcı Kıyas Turu — 21 Eylül 2026 günlüğü

Bu belge bir **akış** kaydıdır. Sonuçların kendisi başka yerlerde
([neden-fpga.md](neden-fpga.md), [mimari-gerekce.md](mimari-gerekce.md),
`docs/measurements/`) — burada **hangi soruyu sorup nereye vardığımız** ve
**yolda neyi yanlış yaptığımız** duruyor.

Var olma sebebi: sonuçlar kaydedildi ama onlara götüren akıl yürütme
kaydedilmedi. Bir hafta sonra *"neden şu değil de bu?"* diye sorulduğunda
cevap burada olmalı; yoksa tartışma baştan açılır.

---

## 1. Soru zinciri — bir soru diğerini doğurdu

```
"GPU kullanıyor muyuz? Kullanıyorsak neden FPGA?"
        ↓ ölçüldü: hayır, AerSimulator CPU build'i
"FPGA'nın savunması ne?"
        ↓ neden-fpga.md yazıldı — ama yanlış mimari varsayımıyla
"FPGA kargo aracında değil, merkezî çözücü"
        ↓ sistem-mimarisi.md yazıldı, savunma düzeltildi
"Sadece FPGA ile yapılabilecek kritik bir değer katabilir miyiz?"
        ↓ 18-bit / BRAM36 kesişimi bulundu
"18 bit demek 18 kübit değil mi?"
        ↓ üç ayrı "16" ve iki ayrı "18" ayrıştırıldı
"Paralel processing yapacağız değil mi?"
        ↓ üç katman ayrıştırıldı, ikisi kapalı çıktı
"Proje hâlâ donanım hızlandırmalı kuantum emülatörü mü?"
        ↓ taban yanlış seçilmiş — PS↔PL ölçüldü: 2,26×
```

**Ders**: her cevap bir sonraki soruyu açtı ve her adımda bir varsayım
düştü. Hiçbiri tasarımı değiştirmedi; hepsi **iddiayı** değiştirdi.

---

## 2. Aynı soruya üç taban, üç farklı cevap

Günün en önemli metodolojik bulgusu bu ve tek bir tabloda duruyor:

| Taban | Sonuç | Ne diyor |
|---|---|---|
| Qiskit Aer (Faz 2) | **1,14×** CPU lehine | *"başabaş"* |
| Aynı kod, konak CPU | **11,4×** CPU lehine | *"FPGA çok geride"* |
| Kart üstü ARM (PS) | **2,26×** FPGA lehine | *"donanım hızlandırma var"* |

**Üçü de doğru ölçüm. Üçü de farklı soruyu cevaplıyor.** Taban seçimi
sonucu belirledi — ve bunu fark etmeseydik, seçtiğimiz tabana göre ya
"başabaşız" ya "çok geride" ya da "2,26× hızlandırıyoruz" derdik, hepsi de
"ölçülmüş" olurdu.

> **Kural**: Bir hızlanma sayısı, **tabanı söylenmeden** anlamsızdır.
> Bu projede geçerli olan tek taban, SoC hızlandırması için doğru olan
> **PS↔PL**'dir: *"çekirdeği ARM'dan fabric'e taşımak neye değer?"*

Kayıtlar: [adil-cpu-tabani](measurements/adil-cpu-tabani_20260921_c504294.json),
[ps-pl-hizlanma](measurements/ps-pl-hizlanma_20260921_c504294.json).

### Model üç platformda da tuttu

```
çevrim/çift  =  saat / verim
FPGA  3,56   |  ARM 52,2  |  dizüstü i7 12,5
```

| Karşılaştırma | Mimari üstünlük | Saat dezavantajı | Net | Ölçülen |
|---|---|---|---|---|
| FPGA vs ARM | 14,7× | 6,5× | 2,26× | **2,26×** ✓ |
| FPGA vs i7 | 3,5× | 40× | 0,088× | **0,088×** ✓ |

**FPGA üç platformun en verimlisi** (çevrim başına 3,56). Kaybettiği yer
mimari değil **saat frekansı**. Krossover tam burada.

---

## 3. Yapısal bulgu: emülasyon kaba kuvvetten üstel pahalı

Bu, günün en sert sonucu ve **donanımla ilgisi yok**.

```
statevector  2^((N-1)²)        çözüm uzayı  (N-1)!
N=5 → 65.536 genlik            →  24 tur
```

Ölçüldü: kaba kuvvet **43,2 µs** (kesin sonuç), QAOA yolu **3,69 s**
(doğru olma olasılığı 2,4e-05) — **~85.000×**.

Sonucu: hiçbir uygulama gereksinimi bu iş yükü için hızlandırıcıyı
gerekçelendiremez. Tez çerçevesi bu yüzden değişti — proje bir **rota
optimizasyonu ürünü değil, donanım emülasyon çalışmasıdır**.

---

## 4. Gün içinde düşen varsayımlar

Hepsi *kayda geçirilmeden önce* yakalandı. Sıra, nasıl yakalandıklarını
gösteriyor — hepsi **ölçümle**, tartışmayla değil.

| Varsayım | Gerçek | Nasıl yakalandı |
|---|---|---|
| FPGA kargo aracının içinde | Merkezî çözücü, araçta değil | Kullanıcı düzeltti; mimari hiçbir yerde yazılı değildi |
| Bir rota = 1 FPGA çağrısı | **99 çağrı** (COBYLA) | Referans JSON'da `optimizer_iterations` |
| Yeterlilik = belleğe sığmak | Bellek hiç sınır değil; **durak sayısı** sınır | Çekirdek durumsuz, tek statevector tutuyor |
| "35× mimari üstünlük" | **3,5×** | Adil taban ölçülünce |
| ARM'da 30–50× hızlanma beklentisi | **2,26×** | Ölçüldü |
| Q1.17 taklidi adil ARM tabanı | 18,8× şişik artefakt | Float varyantı yazılıp karşılaştırıldı |
| 18-bit DSP48'e oturuyor | DSP %15'te boşta; kazanç **BRAM'de** | İmplementasyon raporu |
| Derin pipeline + unroll kazandırdı | Unroll **2× yavaşlattı** | ADR 0009, varyant 9 |
| Bellek duvarı FPGA lehine | n=16'da statevector CPU L2'sine sığıyor | Aritmetik |
| Pareto eğrisi 18'i verdi | Eğri **yok**, iki uç kısıt var | Kendi verimize bakınca |

**Ortak nokta**: dokuzunun da kulağa makul geldiği ve dokuzunun da ilk
ölçümde düştüğü. Savunmada kurulsalardı tek tek çökerlerdi.

---

## 5. Kapatılan arama: "FPGA'yı gerekli kılacak gereksinim"

Beş yol denendi, beşi de elendi. Ayrıntı ve gerekçeler:
[dead-ends.md](decisions/dead-ends.md).

Özet: n'i büyütmek (BRAM tavanı), daha çok paralellik (bellek portu),
çoklu örnek (BRAM), bulut bağlantısızlık (kaba kuvvet de çevrimdışı),
mikrosaniye sınıfı (küçük N daha da trivial).

⛔ **Bu arama kapatıldı.** Yeniden açılmadan önce bu bölüm okunmalı.

---

## 6. Bugün değişmeyen şey

Dikkat: **hiç kod silinmedi.** Çekirdek, bitstream, kodlayıcı, doğrulama —
hepsi yerinde ve hepsi geçerli. Fidelity, C/RTL eşdeğerliği, kaynak
kullanımı, zamanlama kapanışı: hiçbiri etkilenmedi.

Değişen tek şey, o işin **ne olduğunun doğru adlandırılması**.

---

## 7. Açık kalanlar

| ⬜ | Konu |
|---|---|
| GPU hiç ölçülmedi — Phase 6B (T064–T069), MVP'den sonra | |
| FPGA enerjisi ölçülmedi — tek taraflı karşılaştırma yapılamaz | |
| Genişlik Pareto eğrisi — Phase 6C (T070–T073) | |
| 37,28 ms hâlâ **sentez tahmini**, kartta doğrulanmadı (T044) | |
| Jitter argümanı beklenenden zayıf — ARM 30 koşumda %1,5 yayılım | |

---

## İlgili belgeler

- [neden-fpga.md](neden-fpga.md) — savunma; kullanılacak ve **kullanılmayacak** argümanlar
- [mimari-gerekce.md](mimari-gerekce.md) — derin teknik gerekçe, [Ö]/[T]/[?] etiketli
- [sistem-mimarisi.md](sistem-mimarisi.md) — FPGA'nın sistemdeki gerçek rolü
- [olculen-degerler.md](olculen-degerler.md) — ölçülen her değer, iddia sınırları
- [dead-ends.md](decisions/dead-ends.md) — elenen yollar
- [faz2-sentez.md §22](measurements/faz2-sentez.md) — §18'in CPU tabanının geçersizliği
