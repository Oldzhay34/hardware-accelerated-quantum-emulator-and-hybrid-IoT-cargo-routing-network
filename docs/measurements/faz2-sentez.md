# Faz 2 — İlk sentez raporu (ÖLÇÜLEN)

**Tarih**: 2026-09-15 · **Araç**: Vitis HLS 2025.2 · **Hedef**: xc7z020clg400-1
**Saat hedefi**: 10 ns (100 MHz) · **Rapor**: `qir_hls_prj/solution1/syn/report/qir_kernel_csynth.rpt`

> Bu belgedeki her sayı **GERÇEK SENTEZ RAPORUNDAN** okundu. Faz 2'nin asıl
> kanıtı budur — C-sim değil (US2, US3).

---

## 1. Sonuç özeti

| Ölçüt | Hedef | **Ölçülen** | Durum |
|---|---|---:|:---:|
| **SC-002** BRAM | ≤ %85 (238/280) | **148 BRAM_18K = %52** | ✅ **GEÇTİ** |
| **SC-003** II, k=0 | ≤ 4 | **1** | ✅ **GEÇTİ** |
| **SC-003** II, k=15 | ≤ 4 | **3** | ✅ **GEÇTİ** |
| LUT | ≤ %100 | **98.627 / 53.200 = %185** | ❌ **SIĞMIYOR** |
| DSP | ≤ %100 | **337 / 220 = %153** | ❌ **SIĞMIYOR** |
| FF | ≤ %100 | 90.626 / 106.400 = %85 | ⚠️ sınırda |
| Zamanlama | 10 ns | **25,039 ns (~40 MHz)** | ❌ **İHLAL** |
| Toplam gecikme | — | **355.140.025 çevrim = 8,892 sn** | ❌ |

**Yani: iki kabul ölçütü de geçti ama tasarım çipe sığmıyor ve çok yavaş.**

---

## 2. Doğrulanan tahminler

**BRAM aritmetiği tuttu.** `scripts/memory_budget.py` statevector için 128
BRAM_18K öngörmüştü; rapordaki `Memory` satırı tam olarak **128** gösteriyor.
Toplam 148'e çıkışı geri kalan 20 blok (ara tamponlar, trig LUT'u) getiriyor.
%45,7 tahmini → **%52,9 gerçek**. Blok düzeyinde hesaba geçme kararı doğruydu;
bayt düzeyindeki eski hesap bunu göremezdi.

**Bankalama analizi niteliksel olarak doğru, niceliksel olarak bir birim yanlış.**

| | Tahmin (`banking_analysis.py`) | **Ölçülen** |
|---|---:|---:|
| II, k=0 | 1 | **1** ✅ |
| II, k=15 | 2 | **3** ❌ |

Yüksek `k`'nin daha kötü olduğu doğru çıktı — ama II=2 değil 3. Aritmetik model
yalnızca banka çakışmasını sayıyordu; gerçek boru hattı ek bir çevrim daha
istiyor. **İkisi de SC-003'ün ≤4 sınırının altında**, yani karar değişmiyor.

**SK-02 kapanabilir.** Projenin 1 numaralı riski *"bankalama çözülemiyor"*du.
Sentez raporu her iki uç `k` için de eşiğin altında II gösteriyor ve bellek
çakışma uyarısı yok. Risk **gerçekleşmedi**.

---

## 3. 🔴 Çürüyen tahmin: gecikme

Aritmetik model p=2 için **237.568 çevrim** öngörmüştü. Gerçek: **355.140.025
çevrim** — **1.495 kat fazla.**

100 MHz varsayımıyla 2,38 ms bekleniyordu; gerçek 40 MHz'de **8,892 saniye**.
CPU tabanı (Aer, ölçülen ~58 ms) ile kıyaslandığında FPGA **~150 kat YAVAŞ**.

> Tahmini "~24× hızlanma" rakamı **geçersizdir** ve hiçbir yere yazılmamalıdır.
> Bu, Prensip II'nin tam olarak önlemek için var olduğu durum.

### Neden: aritmetik modelin göremediği iki şey

**(a) Çift duyarlıklı trigonometri.** `hls/src/trig.hpp` `std::cos`/`std::sin`
kullanıyor ve argümanı `double`. HLS bunu tam bir çift duyarlıklı transandantal
birim olarak sentezledi:

| `sin_or_cos_double` tek örnek | DSP | LUT | FF | BRAM_18K |
|---|---:|---:|---:|---:|
| | **85** | 6.364 | 5.562 | 8 |

220 DSP'nin 85'i tek bir sinüs/kosinüs birimine gidiyor. Buna `double` çarpanlar
ekleniyor (`mul_64ns_66ns_129_5_1` → 16 DSP). **DSP %153 ve LUT %185'in ana
kaynağı burası.**

Bu borç [trig.hpp](../../hls/src/trig.hpp) içinde "SENTEZ BORCU" olarak
yazılıydı — ama bedeli *tahmin edilmemişti*. Şimdi ölçüldü: borç, tasarımın
sığmamasının birinci sebebi.

**(b) Genlik başına 136 seri faz toplaması.** `apply_cost_layer` her genlik için
16 `h` + 120 `J` terimini **sırayla** topluyor. Model bunu "köşegen geçiş,
erişim sıralı, II=1" diye saymıştı — erişim gerçekten sıralı, ama *hesap*
sıralı değil ve genlik başına yüzlerce çevrim tutuyor. 65.536 genlik × 2 katman
× ~2.700 çevrim ≈ 355M.

---

## 4. Ne yapılmalı (öncelik sırası)

Bu bir kesme (K-02/K-04) durumu **değil**: kabul ölçütleri geçti, sığmama ve
yavaşlık **bilinen ve adreslenebilir** iki nedenden geliyor.

| # | İş | Beklenen etki | Kapsam |
|---|---|---|---|
| 1 | `trig.hpp`: `double` → sabit-nokta LUT veya CORDIC | DSP ve LUT'un ana kaynağını kaldırır | **M** |
| 2 | Faz hesabını Gray-kod artımlı yap (NC-2) | Genlik başına 136 toplamayı ~1'e indirir | **M** |
| 3 | Yeniden sentezle, zamanlamayı kontrol et | 25 ns → hedef 10 ns | **M** |
| 4 | Şerit sayısını gerçek kaynağa göre ayarla | — | H |

**(1) ve (2) zaten planda açık kalemlerdi** — NC-2 "sentez raporundan sonra
karar verilecek" diye ertelenmişti ve trig borcu yazılıydı. Sentez raporu
ikisinin de **M kapsamına girdiğini** gösterdi.

⚠️ Bu ikisi çözülmeden hiçbir hızlanma iddiası yapılamaz.

---

## 5. Ham veriler

- Rapor: `qir_hls_prj/solution1/syn/report/qir_kernel_csynth.rpt`
- Alt modül raporları: `apply_rx_{0..15}_s`, `apply_cost_layer`,
  `sin_or_cos_double_s`, `expectation_scaled`, `turn_to_cos_sin`
- Sentez süresi: ~2 dakika
- Sentez uyarısı: 0 hata, 1 uyarı (SYNCHK 200-10)

---

# 6. İkinci sentez turu — trig LUT'a çevrildi (2026-09-15)

`hls/src/trig.hpp` çift duyarlıklı `std::cos/sin` yerine 8192 girdilik
sabit-nokta sinüs tablosu kullanıyor (`scripts/gen_trig_lut.py` üretiyor;
tek tablo, kosinüs çeyrek periyot kaydırmayla).

| | 1. tur (double) | **2. tur (LUT)** | Değişim |
|---|---:|---:|---|
| BRAM_18K | 148 (%52) | **141 (%50)** | −7 |
| **DSP** | 337 (**%153**) | **156 (%70)** | **−181 ✅ ÇÖZÜLDÜ** |
| FF | 90.626 (%85) | 78.286 (%73) | −12.340 |
| **LUT** | 98.627 (**%185**) | **81.902 (%153)** | −16.725 ❌ hâlâ taşıyor |
| Zamanlama | 25,039 ns | **25,039 ns** | **değişmedi** |
| Gecikme | 355.140.025 | **337.838.521** | −%5 |

Fidelity bedeli ihmal edilebilir: 0,999978359 → **0,999978179** (n=16, p=2).

**Trig yalnızca DSP'yi yiyormuş.** Ne kritik yoldaydı (zamanlama hiç değişmedi)
ne de gecikmenin kaynağıydı (%5).

---

## 7. 🔴 Asıl bulgu: bankalama araştırması YANLIŞ YERİ optimize etmiş

Rapor gecikmeyi modül modül veriyor:

| Modül | Çevrim | Payı |
|---|---:|---:|
| `apply_cost_layer` | 12.451.842 – 98.435.074 | **~%70** |
| `expectation_scaled` | 8.847.424 – 38.338.624 | **~%28** |
| 16 × `apply_rx` (**toplam**) | ~1.400.000 | **%0,4** |
| `init_loop` | 65.538 | %0,02 |

Faz 2'nin araştırma adımının tamamı — üç bankalama stratejisi, XOR şemaları,
ping-pong, `(i, i XOR 2^k)` çakışma analizi — **eşlemeli kapılar** üzerineydi.
Ölçüm onların **toplam sürenin %0,4'ü** olduğunu söylüyor.

"RZZ'yi yerleşik köşegen kapı yap, eşlemeli kapı 12× azalsın" bulgusu **doğruydu
ama performans açısından anlamsız**: azaltılan şey zaten ihmal edilebilirdi.
Buna karşılık "köşegen kapı genliği yerinde çarpar, erişim sıralı, sorun yok"
diye geçiştirdiğim katman işin **%98'i**.

**Neden kaçırdım**: `scripts/banking_analysis.py` yalnızca **bellek erişimini**
sayıyordu. Köşegen katmanın genlik başına 136 seri faz toplaması yaptığını —
yani *aritmetik* maliyetini — model hiç görmüyordu.

### Ölçülen II (SC-003 — hepsi geçiyor)

| k | Çevrim | II | Tahmin |
|---|---:|---:|---:|
| 0 | 32.774 | **1** | 1 ✅ |
| 1, 2 | 65.538 | **2** | 1 ❌ |
| 3 | 32.774 | **1** | 1 ✅ |
| 4–15 | 98.310 | **3** | 2 ❌ |

Aritmetik model yönü doğru (yüksek k daha kötü), büyüklüğü tutarsız.
**Hepsi ≤ 4**, SC-003 geçiyor.

---

## 8. Kalan iki sorun ve ikisinin de aynı kökü

**LUT %153** — `Instance` 63.442 + `Multiplexer` 18.033. Kaynak: **16 ayrı
`apply_rx` örneği**, her biri tam bir veri yolu; artı partition'lı diziyi 17
kullanıcı (16 RX + maliyet + beklenti) arasında paylaştıran multiplexer.

Yani LUT bütçesinin büyük kısmı, çalışma süresinin **%0,4'ünü** oluşturan işe
gidiyor. Bu takas savunulamaz.

**Gecikme 338M çevrim** — `apply_cost_layer` + `expectation_scaled`, ikisi de
genlik başına 136 terimi seri topluyor.

### Bu, onaylanmış bir kararı sorgulatıyor

[research.md R-7](../../specs/002-fpga-statevector-cekirdegi/research.md) `k`'nin
**derleme zamanı sabiti** olmasını şart koşmuştu; gerekçe HLS'in partition'ı
çözememesi riskiydi. Bedeli şimdi ölçüldü: 16 örnek = LUT taşması.

RX katmanı toplam sürenin %0,4'ü olduğuna göre, **tek bir paylaşılan `apply_rx`
birimi** (çalışma zamanı `k` ile) II'yi 10 kat kötüleştirse bile toplam etkisi
%4 olurdu — buna karşılık LUT'un büyük kısmı serbest kalırdı.

⚠️ Bu, **onay kapısından geçmiş bir kararın (C1) tersine çevrilmesi** anlamına
gelir ve Prensip I gereği yeniden onay ister.

---

# 9. Turlar 3-6 — gecikme çözüldü, alan çözülmedi (2026-09-15/16)

| Tur | Değişiklik | Gecikme | BRAM | DSP | FF | LUT |
|---|---|---:|---:|---:|---:|---:|
| 1 | (başlangıç, double trig) | 355.140.025 | %52 | %153 | %85 | %185 |
| 2 | trig → sabit-nokta LUT | 337.838.521 | %50 | **%70** | %73 | %153 |
| 3 | iç döngüler açıldı | **4.457.934** | %50 | %129 | %198 | %359 |
| 4 | II=4 / II=16 denendi | 5,2M / 8,4M | %50 | %129 | %198 | %359 |
| 5 | iki seviyeli faz ayrıştırması | 4.458.579 | %53 | %129 | %198 | %360 |
| 6 | tablo döngüleri kapatıldı | **5.665.983** | **%53** | **%70** | %174 | %344 |

**Gecikme 355M → 5,67M: 63× iyileşme.** BRAM ve DSP bütçe içinde.
**LUT %344 ve FF %174 — tasarım hâlâ sığmıyor.**

## Ne işe yaradı

**Trig LUT'u**: DSP'yi %153'ten %70'e indirdi. Tek başına yeterli değildi ama
gerekliydi.

**İç döngülerin açılması**: gecikmeyi 76× iyileştirdi (338M → 4,46M). Sorun
terim *sayısı* değil, `acc` üzerindeki **seri bağımlılıktı** — bu yüzden çözüm
Gray-kod değil açmaktı.

**İki seviyeli faz ayrıştırması**: `acc(i) = FL[düşük] + FH[yüksek] +
Σ s_a·D_a[yüksek]`. Genlik başına 136 terim → ~10. Modül gecikmeleri:
`apply_cost_layer` 98.435.074 → **66.028** (1.490×),
`expectation_scaled` 38.338.624 → **65.820** (582×). Fidelity **değişmedi**
(0,999978179) — ayrıştırma matematiksel olarak tam.

## Ne işe YARAMADI

**II gevşetme.** II=1/4/16 için LUT 191.223 / 190.726 / 190.341 — **%0,5
değişim**, gecikme ise kötüleşiyor. HLS `UNROLL` ile örneklenen toplayıcıları
II artınca paylaştırmıyor. Alanı düşürmenin tek yolu terim sayısını azaltmak.

**Tablo döngülerini açmak — kendi hatam.** Tabloları kuran döngüleri de
açmıştım; yalnızca 256 kez çalışan bir döngü için 100 toplayıcılık donanım
örnekleniyordu. Kapatınca DSP %129 → %70 düştü, LUT yalnızca %360 → %344.
**Kural**: `UNROLL` yalnızca genlik başına çalışan yola uygulanır.

## Kalan LUT nerede (183.203, bütçe 53.200)

| Modül | LUT | Pay | Durum |
|---|---:|---:|---|
| `apply_cost_layer` | 81.087 | %44 | ayrıştırma yapıldı, hâlâ büyük — **araştırılmalı** |
| 16 × `apply_rx` | 45.114 | %25 | paylaşım kararı bekliyor (C1 tartışması) |
| `expectation_scaled` | 38.012 | %21 | **aynı ayrıştırma uygulanmadı** |
| Multiplexer (üst) | 18.033 | %10 | 17 kullanıcı → paylaşım azaltır |

**Tek bir düzeltme yetmez.** RX paylaşımı (~42k) ve expectation ayrıştırması
(~28k) birlikte ~113k'ya indirir — hâlâ %212. `apply_cost_layer`'ın 81k'sının
neden bu kadar büyük olduğu **henüz açıklanamadı** ve bir sonraki adım orası.

## Zamanlama — altı turda hiç değişmedi

**25,039 ns**, altı turun hepsinde aynı. Kritik yol ne trig'de, ne açılan
toplama ağacında, ne de tablo döngülerinde. Henüz bulunmadı. 100 MHz varsayımı
(NC-4) tüm süre hesaplarının altında duruyor ve **hâlâ doğrulanmadı**.

⚠️ Mevcut hâliyle 5,67M çevrim @ 40 MHz = **0,142 sn**; CPU tabanı (Aer,
ölçülen ~58 ms) hâlâ **2,4× hızlı**. Hiçbir hızlanma iddiası yapılamaz.
