# Sistem Mimarisi

**Oluşturma**: 2026-09-21 · **Durum**: canlı belge

Bu belge, sistemin **uçtan uca** nasıl çalıştığını yazar. Var olma sebebi:
2026-09-21'de mimari hiçbir yerde yazılı olmadığı için
[neden-fpga.md](neden-fpga.md) *"FPGA kargo aracının içinde"* varsayımıyla
yazıldı ve **yanlıştı**. Yazılı olmayan mimari, uydurulan mimaridir.

---

## 1. Tek cümlede

**Tek bir merkezî PYNQ-Z2**, kargoları bölgelere göre gruplanmış alt
problemlere böler, her alt problemi QAOA ile çözer, turları birleştirir ve
sonucu servislerdeki ESP32'lere ulaştırır. Railway sunucusu **kayıt sistemi**
ve **ML/API katmanıdır** — hesap taşması yeri değildir.

```
  Kargo kayıtları (adres)
          │
          ▼
  ┌─────────────────────────────────────────┐
  │ RAILWAY — kayıt sistemi + ML + API      │
  │  • kargoyu bölgeye ata                  │
  │  • bölge × kargo sayısı TABLOSU         │
  │  • zorluk tipi sınıflandırması (A/B*/C) │
  └────────────────┬────────────────────────┘
                   │  alt problem listesi
                   ▼
  ┌─────────────────────────────────────────┐
  │ PYNQ-Z2 — TEK merkezî çözücü + G/Ç göbeği│
  │  ARM (Linux): kümeleme, klasik döngü,   │
  │               tur birleştirme, ağ       │
  │  PL (FPGA)  : QAOA statevector emülatörü│
  └────────────────┬────────────────────────┘
                   │  rotalar
        ┌──────────┴──────────┐
        │ doğrudan            │ ya da Railway üzerinden
        ▼                     ▼
   servislerdeki ESP32'ler ◄──┘
```

⚠️ **FPGA araçta değildir.** Sabit, merkezî, sürekli çalışan bir düğümdür.
Elde **tek kart** var (bütçe) — mimari buna göre kurulmuştur ve bölge başına
kart varsayımı **yoktur**.

---

## 2. Railway'in tablosu — mimarinin yükünü belirleyen şey

Railway, kargoları bölgelere atar ve **kargo sayılarına göre bir tablo**
tutar. Bu tablo yalnız muhasebe değildir: **FPGA'nın o gece kaç alt problem
çözeceğini belirleyen girdidir**.

| Bölge | Araç | Kargo sayısı | Alt problem (⌈K/4⌉) |
|---|---|---:|---:|
| Beylikdüzü ve çevresi | 1 | K₁ | ⌈K₁/4⌉ |
| Kağıthane ve çevresi | 1 | K₂ | ⌈K₂/4⌉ |
| Beykoz ve çevresi | 1 | K₃ | ⌈K₃/4⌉ |
| **Toplam** | | **ΣK** | **N_alt** |

**Neden ⌈K/4⌉**: çekirdek bir alt problemde **5 şehir** çözer ve biri depodur
→ alt problem başına **4 teslimat durağı** (bkz. §4).

Tablo aynı zamanda ML'in zorluk tipi (A / B* / C) kararının ve yeniden
kümelemenin girdisidir.

---

## 3. İki ayrı yol — karıştırılmamalı

Sistemin **iki** çalışma kipi var ve gereksinimleri taban tabana zıt.

### Yol 1 — Gecelik toplu iş (00:00)

Bütün rotalar sıfırdan hesaplanır.

| | |
|---|---|
| Sıklık | Günde 1 |
| Gecikme gereksinimi | **Yok** — gece boyunca zamanı var |
| Belirleyici | Toplam verim |

### Yol 2 — Artımlı güncelleme (adres değişikliği)

Yalnız etkilenen alt problem(ler) yeniden çözülür.

| | |
|---|---|
| Sıklık | Olay bazlı, gün içinde |
| Gecikme gereksinimi | **Var** — kullanıcı bekliyor |
| Belirleyici | Tek alt problem süresi |

> ⚠️ `neden-fpga.md` §2.3'teki **belirlenimci gecikme** argümanı yalnız
> **Yol 2** için geçerlidir. Gecelik toplu işte jitter'ın hiçbir önemi yoktur.

---

## 4. Ölçülen sayılar ve kapasite

### Bir alt problem kaç FPGA çağrısı eder

QAOA **değişimseldir**: klasik optimize edici (γ, β) ararken her adımda bir
beklenen değer hesaplatır. Referans koşumda:

```
optimizer            = cobyla
optimizer_iterations = 99
```

Yani **bir alt problem = 99 FPGA çağrısı**, bir değil.

| | |
|---|---|
| 1 çağrı (p=2) | **37,28 ms** ⚠️ *sentez tahmini, kartta henüz ölçülmedi* |
| 1 alt problem | 99 × 37,28 ms = **3,69 s** |
| 60 alt problem | **221 s ≈ 3,7 dakika** |
| 1000 alt problem | ≈ **62 dakika** |

### Kapasite sonucu

Gecelik toplu iş için **kapasite sorun değildir.** 60 alt problem gecenin
%0,26'sını kullanır; kart günün **%99,7'sinde boşta**.

> ⛔ **Railway'e hesap taşması yüzünden devretmeye gerek yoktur.** Bu
> mekanizma kapasite için kurulmamalıdır.

---

## 5. Gerçek sınır: alt problem başına 5 durak

```
(N-1)² = 16 kübit  →  N = 5 şehir  →  depo + 4 teslimat durağı
```

Gerçek bir kargo rotası 50–150 duraktır. **Çekirdek bir rotanın tamamını
çözemez** — çözemeyeceği de en baştan belliydi, çünkü 16 kübit tavanı
BRAM'den geliyor ([Prensip III](../.specify/memory/constitution.md)).

**Zorunlu yaklaşım — hiyerarşik ayrıştırma:**

```
bölge → ≤4 duraklık kümeler → her küme QAOA ile çözülür → turlar birleştirilir
        (klasik)               (FPGA)                      (klasik)
```

Kuantum-esinli kısım **küçük alt problemleri** çözer; üst katman klasiktir.
Bu meşru bir yaklaşımdır ama **açıkça yazılmalıdır** — *"QAOA ile kargo
rotası optimize ediyoruz"* cümlesi bundan fazlasını ima eder.

⬜ **Açık tasarım kararı**: kümeleme algoritması (k-means? coğrafi ızgara?
en yakın komşu?) ve tur birleştirme yöntemi henüz seçilmedi.

---

## 6. Yeterlilik ölçütü — düzeltildi

Önceki plan *"donanımın yetmesi = rota sayısını bellekte tutmak"* diyordu.
**Bu yanlış ölçüttü.**

| Kaynak | Durum |
|---|---|
| **Bellek** | ❌ hiç sınır değil. Çekirdek **durumsuzdur** ve aynı anda **tek** statevector tutar (2,36 Mbit BRAM). Rota verisi ARM'ın **512 MB DDR**'sinde durur; 60 rotanın metası birkaç KB |
| **Zaman (toplu)** | ✅ bol bol yetiyor — 3,7 dk / gece |
| **Zaman (artımlı)** | 🟡 3,69 s/alt problem — iyileştirilebilir (§7) |
| **Durak sayısı** | 🔴 **asıl sınır** — alt problem başına 4 teslimat |

### Railway ne için var

| ✅ Öyle | ❌ Değil |
|---|---|
| Kayıt sistemi (kargo, adres, bölge) | Hesap taşması |
| **Kargo sayısı tablosu** (§2) | FPGA'nın yükünü hafifletmek |
| ML: zorluk tipi sınıflandırması | |
| API ve web katmanı | |
| Erişilebilirlik yedeği (FPGA düşerse) | |

---

## 7. En yüksek kaldıraçlı iyileştirme: 99 iterasyonu düşürmek

Süreyi domine eden şey optimize edici döngüsüdür, tek çağrı değil.

| Yaklaşım | Beklenen etki | Durum |
|---|---|---|
| **Sıcak başlangıç** — bir önceki çözümün (γ, β) değerleriyle başla | Artımlı yolda 99 → birkaç adım | ⬜ denenmedi |
| **Sabit açı QAOA** — açılar önceden belirlenir, optimize edici kalkar | 99 → **1** çağrı | ⬜ denenmedi |

Artımlı güncelleme yolunda bu, 3,69 s'yi **saniyenin altına** indirir — ve
gecikmenin gerçekten önemli olduğu tek yol orası.

---

## 7.5 Paralellik katmanları — nerede var, nerede yok, neden gerekmiyor

*"Neden paralelleştirmediniz?"* sorusunun hazır cevabı. Üç ayrı katman var ve
üçünün durumu farklı.

| Katman | Paralellik | Durum | Neden |
|---|---|---|---|
| **Çekirdek içi** | var, II=2 | ✅ **tavanda** | Bellek portu, ölçümle kapandı |
| **Alt problemler arası** | problemde var | ❌ kullanılamıyor | BRAM %67, ikinci örnek sığmaz |
| **Optimize edici** | yok | ❌ yapısal | COBYLA sıralı |

### Katman 1 — çekirdek içi: **zaten paralel, ve sınırında**

Karıştırıcı boru hattında **II=2** çalışıyor (iki çevrimde bir genlik çifti),
`sv` dizisi `cyclic factor 2` ile bankalanmış, köşegen katmanın iç tablo
döngüleri açılmış (`UNROLL`).

Daha fazlası **ölçümle denendi ve kapandı**
([ADR 0009](../docs/decisions/0009-paralellik-turu-kapatildi.md),
[faz2-sentez.md Tur 17](measurements/faz2-sentez.md)):

| Bankalama | Çevrim | LUT |
|---|---:|---:|
| cyclic 2 | 5.375.327 | %84 |
| cyclic **4** | 5.375.327 | %86 |
| cyclic **8** | 5.375.328 | %90 |

Bankayı dörde katlamak **sıfır** kazanç verdi (fark: bir çevrim), LUT'u %84'ten
%90'a çıkardı.

**Mekanizma**: yerinde kelebek, çift başına **dört** bellek erişimi ister
(`oku i`, `oku i′`, `yaz i`, `yaz i′`). BRAM'in **iki** portu var →
`II = 4/2 = 2`. Bu donanımsal tabandır. Bankalama en kötü durumu düzeltmez,
çünkü `2ᵏ ≥ F` olan her kübitte iki erişim **aynı bankaya** düşer ve boru
hattı II'si en kötü *k*'ye göre belirlenir. Yalnız **port** eklemek düzeltir —
ve BRAM'de ikiden fazla port yoktur.

> `RAM_2P` → `RAM_T2P` (basit çift port → gerçek çift port) tek kelimelik
> değişiklikle II'yi 3'ten 2'ye, gecikmeyi **%22,6** düşürdü ve **bedeli
> sıfırdı**. Satın alınabilir tek paralellik buydu ve alındı.

### Katman 2 — alt problemler arası: problem paralel, **çip değil**

60 alt problem birbirinden tamamen bağımsızdır — *utanç verici derecede
paralel* bir iş yükü. Eşzamanlı koşturmak için birden fazla çekirdek örneği
gerekir ve **sığmaz**:

```
tek n=16 statevector  : 2,36 Mbit  →  BRAM %67 (tablolarla birlikte)
ikinci örnek          : → %134.  SIĞMAZ.
```

LUT %43 ve DSP %15'te boşta durduğu hâlde bağlayıcı kaynak **BRAM**'dir ve
orada yer yoktur. Bu çipte alt problemler **sırayla** koşar.

### Katman 3 — optimize edici: yapısal olarak sıralı

COBYLA her adımda bir öncekinin sonucuna bakar; 99 iterasyon zorunlu olarak
ardışıktır. Gradyan tabanlı bir yönteme geçilse sonlu fark hesapları
paralelleşebilirdi — ama paralel koşturacak ikinci bir örnek yok (katman 2).

### Neden hiçbiri gerekmiyor

```
60 alt problem × 3,69 s = 221 s ≈ 3,7 dakika / gece
kart günün %99,7'sinde BOŞTA
```

Gecelik toplu iş için paralellik **olmayan bir problemi çözer**. Sığsaydı bile
kazanç *"3,7 dakika yerine 1,8 dakika"* olurdu.

Tek bedava kazanç, PL hesaplarken ARM'ın bir sonraki alt problemin 1.095
word'ünü hazırlaması olurdu — ama yazma ~1 ms, hesap 37 ms: **%3**. Uğraşmaya
değmez.

> **Savunmadaki ifade**: *"Paralellik çekirdeğin içinde mevcut ve ölçülmüş
> tavanındadır; tavanı belirleyen bellek portudur, banka sayısı değil. Alt
> problem düzeyinde paralellik BRAM kapasitesiyle sınırlıdır ve iş yükü
> profili (gecelik toplu iş) onu zaten gereksiz kılmaktadır."*

---

## 8. Dürüst uyarı: QAOA'nın çözüm kalitesi ayrı bir iddiadır

Referans koşumda:

```
optimal_probability = 2,38e-05
1/65536 (tamamen rastgele)  = 1,53e-05
```

p=2'de QAOA, doğru turu bulma olasılığını rastgeleye göre yalnız **1,56 kat**
artırıyor.

**İki iddia birbirinden ayrı tutulmalı:**

| İddia | Durum |
|---|---|
| *"FPGA, Qiskit'in ürettiği devreyi doğru taklit ediyor"* | ✅ **ölçüldü** — fidelity 0,999978, cosim bit bit |
| *"QAOA rotaları iyileştiriyor"* | ⚠️ bu veriyle **zayıf** |

⛔ **Daha sertine hazır ol**: aynı makinede kaba kuvvet çözücü N=5'i **43,2 µs**'de
**kesin** olarak çözüyor — QAOA yolu 3,69 s. **~85.000× fark** ve bu yapısal
([neden-fpga.md §0.5](neden-fpga.md)). Yani sistem, rota kalitesi veya hızı için
QAOA'ya ihtiyaç duymuyor. QAOA burada **doğrulanabilir bir iş yüküdür**.

Bu projenin katkısı **birincisidir**. İkincisi p'yi artırmayı veya farklı
parametre başlatması denemeyi gerektirir ve bu fazın kapsamında değildir.
Karıştırılırsa savunma çöker.

---

## 9. Açık kalanlar

| ⬜ | Konu |
|---|---|
| Kümeleme algoritması ve tur birleştirme yöntemi (§5) | |
| ML zorluk tipi (A/B*/C) girdileri ve eşikleri | |
| ESP32 haberleşme yolu: doğrudan mı Railway üzerinden mi — **hangi koşulda** | |
| Sıcak başlangıç / sabit açı denemesi (§7) | |
| 37,28 ms'nin **kartta** doğrulanması (Faz 5, öbek 4) | |

---

## İlgili belgeler

- [neden-fpga.md](neden-fpga.md) — *"GPU varken neden FPGA?"* savunması
- [olculen-degerler.md](olculen-degerler.md) — ölçülen her değer ve iddia sınırları
- [memory-budget.md](memory-budget.md) — 16 kübit tavanının nereden geldiği
- [Prensip III](../.specify/memory/constitution.md) — statevector çip-içi kalmalı
