# Faz 2 — İlk sentez raporu (ÖLÇÜLEN)

> ⚠️ **CPU karşılaştırmaları için §15'i okumadan bu dosyadaki hiçbir
> "CPU'dan N kat yavaş/hızlı" ifadesine güvenme.** Bunlar kronolojik kayıttır
> ve §15'e kadar **iki sistematik hata** taşırlar: FPGA tarafı p=3, CPU tarafı
> p=2 idi; ve CPU tabanı olarak medyan değil tek koşunun **en iyi** değeri
> alınmıştı. Doğru sayılar §15'te.

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

---

# 10. Turlar 8-9 — TASARIM ÇİPE SIĞDI (2026-09-16)

| Tur | Değişiklik | Gecikme | BRAM | DSP | FF | LUT |
|---|---|---:|---:|---:|---:|---:|
| 7 | expectation ayrıştırması | 5.766.130 | %61 | %70 | %156 | %289 |
| 8 | `config_compile -pipeline_loops 0` | 14.773.743 | %61 | %70 | **%65** | %149 |
| 9 | **paylaşılan RX (çalışma zamanı k)** | 15.363.498 | **%61** | **%16** | **%12** | **%42** |

**Dört kaynağın dördü de bütçede. SC-002 (BRAM ≤ %85): %61 ✅**

## Tur 8: otomatik boru hattı — pragma değil, PROJE AYARI

`apply_cost_layer` 81.087 → **8.374 LUT** (10×). Sebep: Vitis HLS tur sayısı
64'ün altındaki döngüleri **kendiliğinden** boru hattına alıyor
(`config_compile -pipeline_loops`, varsayılan 64) ve bir döngüyü boru hattına
alırken iç döngülerini **açmak zorunda**. Tablo kurma döngülerimin iç döngüleri
(8, 28, 64 turlu) hepsi eşiğin altındaydı.

`#pragma HLS PIPELINE off` eklemek **işe yaramadı** — iki kez denendi, sonuçlar
bit-birebir aynı çıktı. Bu bir pragma meselesi değildi.

Bedeli gecikmede: tablolar artık tamamen seri, 5,77M → 14,77M.
**Geri alınabilir**: en içteki tablo döngülerine açık `PIPELINE II=1` koymak
hiçbir şeyi açmaz, alan bedeli ~sıfır.

## Tur 9: R-7'nin hipotezi SINANDI ve YANLIŞLANDI

[research.md R-7](../../specs/002-fpga-statevector-cekirdegi/research.md) `k`'nin
derleme zamanı sabiti olmasını şart koşmuştu:

> "HLS, `ARRAY_PARTITION`'lı bir diziye hangi parçadan erişildiğini derleme
> zamanında çözemezse bütün erişimleri seri hale getirir."

**Ölçüm bunu desteklemiyor.**

| | `template<int K>` (16 örnek) | **paylaşılan (çalışma zamanı k)** |
|---|---:|---:|
| LUT | 45.114 | **2.409** |
| DSP | 128 | **8** |
| Toplam gecikme | 14.773.743 | 15.363.498 (**+%4**) |

16× yavaşlama beklenirken **%4** oldu. R-7 bir hipotezi gerekçe olarak
kullanmıştı ve hipotez hiç sınanmamıştı; sınanınca tutmadı.

**C1 kararı geçerliliğini koruyor** — kapı listesi hâlâ derleme zamanında
sabit, konaktan yalnızca parametre geliyor. Değişen, R-7'de C1'e yanlışlıkla
paketlenmiş olan ayrı bir uygulama seçimi.

## Kalan tek sorun: ZAMANLAMA

| Tur | Zamanlama |
|---|---:|
| 1–8 | 25,039 ns |
| 9 | **24,799 ns** |

Dokuz turda pratikte hiç değişmedi. Hedef 10 ns; gerçek ~**40 MHz**.
Kritik yol dokunulan hiçbir yerde değil ve **henüz araştırılmadı**.
NC-4 (Fmax varsayımı) hâlâ açık.

15,36M çevrim @ 40 MHz = **0,384 sn**. CPU tabanı (Aer, ölçülen ~58 ms) hâlâ
**6,6× hızlı**. Hiçbir hızlanma iddiası yapılamaz.

## Ama artık bol kaynak payı var

LUT %42, DSP %16, FF %12. Önceki turlarda sorun "sığmıyor"du; şimdi sorun
"yavaş". Bu, paralelliğe yatırım yapılabileceği anlamına geliyor — çevrim
başına birden fazla genlik işlemek artık kaynak açısından mümkün.

Sıradaki üç iş, öncelik sırasıyla:
1. **Zamanlama** — 25 ns'nin kaynağını bul. Tek başına 2,5× kazanç.
2. **Tablo döngüsü gecikmesi** — en içteki döngülere `PIPELINE II=1`, ~9M geri.
3. **Paralellik** — kalan %58 LUT payını çevrim başına birden fazla genliğe yatır.

---

# 11. Turlar 10-14 — ZAMANLAMA TUTTURULDU, NC-4 KAPANDI (2026-09-16)

| Tur | Değişiklik | Zamanlama | Gecikme | BRAM | DSP | FF | LUT |
|---|---|---:|---:|---:|---:|---:|---:|
| 9 | (paylaşılan RX) | 24,799 ns | 15.363.498 | %61 | %16 | %12 | %42 |
| 10 | *teşhis: AP_TRN+AP_WRAP* | *17,185 ns* | — | — | — | — | — |
| 11 | `config_op mul -latency 3` | 24,323 ns | 15.363.500 | %61 | %16 | %12 | %42 |
| 12 | partition faktörü 16→2 | 23,016 ns | 15.363.500 | %67 | %16 | %9 | %32 |
| 13 | **`DEPENDENCE` (sv bağımsız)** | **12,697 ns** | 15.363.836 | %66 | %16 | %10 | %32 |
| 14 | **`exp_amp_loop` II=4** | **7,195 ns** ✅ | 15.560.447 | %66 | %16 | %10 | %32 |
| 15 | maliyet tablolarına `PIPELINE II=1` | **7,195 ns** ✅ | **9.801.215** | %66 | %16 | %32 | %63 |

**Zamanlama hedefi tutturuldu: 7,195 ns < 7,30 ns efektif bütçe. İhlal uyarısı yok.**
**100 MHz artık VARSAYIM DEĞİL, ÖLÇÜLMÜŞ — NC-4 kapandı.**

## Kritik yol nasıl bulundu

Üç hipotez ölçümle **elendi**:

| Hipotez | Test | Sonuç |
|---|---|---|
| Yuvarlama/doyurma kipleri | `AP_TRN`+`AP_WRAP` | 24,799 → 17,185 ns — yolun %31'i, yetmez |
| Boru hattına alınmamış çarpıcı | `config_op mul -latency 3` | 24,799 → 24,323 ns — **değil** |
| Partition mux'ı | faktör 16 → 4 → 2 | 24,323 → 23,016 ns — **değil** |

Sonra rapor doğrudan söyledi:

> *"Cannot meet target clock period from **'load'** operation on array ... to
> **'store'** operation ... (combination delay: **24,0859 ns**) to honor II or
> Latency constraint"*

Kritik yol `sv[i0]` **oku → çarp → topla → yuvarla → yaz** zinciriydi, tamamı
tek kombinasyonel parçada. HLS bunu bölemiyordu çünkü farklı `j` yinelemelerinin
farklı çiftlere dokunduğunu **kanıtlayamıyordu**.

```cpp
#pragma HLS DEPENDENCE variable = sv type = inter dependent = false
```

Bu pragma bağımsızlığı **bildiriyor**. Sonuç: **23,016 → 12,697 ns**, yineleme
gecikmesi 4 → 11 (HLS load ile store arasına kayıt koyabildi). LUT da düştü.

Kalan 12,697 ns `expectation_scaled`'in akümülatöründeydi ve bu **gerçek** bir
döngü-taşımalı bağımlılık (`add 84 bit → select 48 bit`); `DEPENDENCE` çözemez.
Ama `expectation_scaled` toplam gecikmenin %0,4'ü olduğu için II'sini gevşetmek
bedava: **II=4 → 7,195 ns**.

## Tablo döngüsü gecikmesi geri alındı

Tur 8'de `config_compile -pipeline_loops 0` tabloları tamamen seri bırakmıştı
(+9,8M çevrim). En **içteki** tablo döngülerine açık `PIPELINE II=1` konuldu —
en içteki döngüyü boru hattına almak hiçbir şeyi açmaz.

İlk deneme her iki tablo setini de kapsadı: gecikme 9,78M'e indi **ama zamanlama
8,354 ns'ye çıkıp ihlal etti**. Suçlu `expectation_scaled` tablolarındaki 48-bit
`sum_t` akümülatörüydü. Yalnızca **maliyet** tabloları boru hattında bırakıldı:
zamanlama 7,195 ns'ye döndü, gecikme 9,80M'de kaldı.

Bedeli: LUT %32 → %63, FF %10 → %32.

## Nerede duruyoruz

| Ölçüt | Değer | Durum |
|---|---:|:---:|
| Zamanlama | 7,195 ns (**100 MHz**) | ✅ |
| BRAM_18K | 187 / 280 (%66) | ✅ SC-002 |
| DSP | 36 / 220 (%16) | ✅ |
| FF | 34.444 (%32) | ✅ |
| LUT | 33.968 (%63) | ✅ |
| Gecikme | 9.801.215 çevrim = **0,098 sn** | — |

Fidelity değişmedi: 0,999978179 / 0,999989167 / 0,999999871 / 0,999998860.

⚠️ CPU tabanı (Aer, ölçülen ~58 ms) **hâlâ 1,7 kat hızlı**. Başlangıçtaki
8,9 saniyeden 0,098 saniyeye gelindi (**91×**) ama hızlanma iddiası hâlâ
yapılamaz.

Kalan pay: LUT %37, DSP %84, FF %68, BRAM %34 — paralellik için yer var.

---

# 12. Tur 16 — bekleyen `tablo_yuksek` değişikliği ölçüldü + WSL doğrulaması (2026-09-16)

**Ortam değişti**: bu, Vitis'in **WSL/Ubuntu** altında koştuğu ilk sentez.
Windows'ta Device Guard aracı engellemişti ([SK-05](../risk-register.md)).
Araç sürümü aynı: 2025.2, Build 6295257. Parça `xc7z020-clg400-1`.
Kaynak: `01f643b` (temiz ağaç).

## Önce: platform değişikliği ölçümü bozar mı?

Yeni platformda ölçülen sayıları eski platformdakilerle karşılaştırmak, iki
değişkeni aynı anda oynatmaktır. Bu yüzden önce **Tur 15 yeniden üretildi**:
`tablo_yuksek`'in `k` ve `x/y` pragmaları çıkarılıp yalnızca `D` döngüsününki
bırakıldı — yani Windows'ta ölçülen kaynak durumu.

| | Windows (Tur 15) | WSL (yeniden üretim) |
|---|---:|---:|
| Zamanlama | 7,195 ns | **7,195 ns** |
| Gecikme | 9.801.215 | **9.801.215** |
| BRAM_18K | 187 | **187** |
| DSP | 36 | **36** |
| FF | 34.444 | **34.444** |
| LUT | 33.968 | **33.968** |

**Birebir aynı.** Tek bir çevrim, tek bir LUT farkı yok. WSL'e taşınma
ölçüm açısından nötr; Tur 1–15 ile Tur 16+ aynı ölçekte karşılaştırılabilir.

Yan ürün: Tur 15'in hangi pragma kümesiyle ölçüldüğü de böylece **kanıtlandı**
(kayıt muğlaktı). Tur 15 = `tablo_dusuk`'un iki pragması + `tablo_yuksek`'in
yalnızca `D` döngüsü. Bekleyen değişiklik = `k` ve `x/y` döngüleri.

## Asıl ölçüm

`tablo_yuksek`'in `k` ve `x/y` döngülerine `PIPELINE II = 1`.

| Konfigürasyon | Zamanlama | Gecikme | BRAM | DSP | FF | LUT |
|---|---:|---:|---:|---:|---:|---:|
| `tablo_yuksek` pragmasız | 7,195 ns | 12.713.471 | %66 | %16 | %25 | %53 |
| Tur 15 (yalnız `D`) | 7,195 ns | 9.801.215 | %66 | %16 | %32 | %63 |
| **Tur 16 (hepsi)** | **7,195 ns** ✅ | **6.948.095** | %66 | %16 | **%46** | **%84** |

**Kazanç**: 9.801.215 → 6.948.095 = **−2.853.120 çevrim (−%29,1)**.
0,098 sn → **0,0695 sn**.

Beklenti ~1,4M çevrimdi; gerçekleşen **2,85M — iki katı**. Tahmin düşük kalmıştı
çünkü `D` döngüsü (8×256×8) yanında `x/y` döngüsünün (256×28) maliyeti
küçümsenmişti.

**Bedeli**: LUT %63 → **%84** (+11.196), FF %32 → **%46** (+15.395).
BRAM ve DSP kılını kıpırdatmadı. Zamanlama değişmedi.

`apply_cost_layer` gecikmesi: 1.379.344~2.520.080 → **295.184~598.288**.

## Nerede duruyoruz

| Ölçüt | Değer | Durum |
|---|---:|:---:|
| Zamanlama | 7,195 ns (**100 MHz**) | ✅ |
| BRAM_18K | 187 / 280 (%66) | ✅ SC-002 |
| DSP | 36 / 220 (%16) | ✅ |
| FF | 49.839 / 106.400 (%46) | ✅ |
| LUT | 45.164 / 53.200 (**%84**) | ⚠️ dar |
| Gecikme | 6.948.095 çevrim = **0,0695 sn** | — |

⚠️ CPU tabanı (Aer, ölçülen ~58 ms) **hâlâ 1,2 kat hızlı**. 1,7×'ten 1,2×'e
indi ama **hızlanma iddiası hâlâ yapılamaz**.

⚠️ **LUT payı %37'den %16'ya düştü.** Sıradaki iş olan paralellik, kalan LUT
payına yatırım demekti; o pay artık büyük ölçüde harcandı. Paralellik kararı
bu yeni kısıt altında yeniden düşünülmeli — bu bir ölçüm sonucu, tahmin değil.

---

# 13. Tur 17 — paralellik arama turu: DOKUZ ölçüm, bir kazanan (2026-09-16)

Karar turu, uygulama turu değil. Dokuz konfigürasyon sentezlendi, kaynak ağacı
her denemeden sonra `git checkout` ile geri alındı. Hiçbiri commit edilmedi.

Hepsi: `01f643b` tabanlı · Vitis 2025.2 · `xc7z020clg400-1` · WSL · BRAM %66,
zamanlama 7,195 ns (dokuzunda da **değişmedi**).

## Önce: iş nerede harcanıyor (Tur 16, p=3)

| Kalem | Çevrim | Pay |
|---|---:|---:|
| `mixer_loop` (3 katman × 16 kübit × 98.315) | 4.719.216 | **%67,9** |
| maliyet tabloları (3 × 532.736) | 1.598.208 | %23,0 |
| `expectation_scaled` | 368.465 | %5,3 |
| `cost_amp_loop` (3 × 65.549) | 196.647 | %2,8 |
| `init_loop` | 65.538 | %0,9 |

`apply_cost_layer`'ın içinde **asıl genlik döngüsü yalnızca %11**; kalan %89
tablo kurmak. Yani "maliyet katmanı" diye bilinen kalemin neredeyse tamamı
hazırlık.

Ölçülen II'ler: `rx_dyn_pair_loop` **II=3** (hedef 1), `cost_amp_loop` **II=1**.

## Ölçümler

| # | Konfigürasyon | Gecikme | DSP | FF | LUT | rx II | Sığar |
|---|---|---:|---:|---:|---:|:---:|:---:|
| 0 | Tur 16 (mevcut) | 6.948.095 | %16 | %46 | %84 | 3 | ✅ |
| 1 | `cyclic factor 4` | 6.948.095 | %16 | %47 | %86 | 3 | kazanç **yok** |
| 2 | `cyclic factor 8` | 6.948.240 | %16 | %49 | %90 | 3 | kazanç **yok** |
| **3** | **`RAM_T2P`** | **5.375.327** | %16 | %46 | **%84** | **2** | ✅ |
| 4 | `RAM_T2P` + `cyclic 4` | 5.375.327 | %16 | %47 | %86 | 2 | kazanç **yok** |
| 5 | `RAM_T2P` + `cyclic 8` | 5.375.328 | %16 | %49 | %90 | 2 | kazanç **yok** |
| 6 | `RAM_T2P` + tüm tablolar `II=4` | 3.780.845 | %74 | %122 | **%182** | 2 | ❌ |
| 7 | `RAM_T2P` + yalnız `tablo_yuksek II=4` | 4.333.700 | %74 | %108 | **%166** | 2 | ❌ |
| 8 | `RAM_T2P` + `tablo_yuksek UNROLL 2` | 5.378.015 | %16 | %71 | **%123** | 2 | ❌ |
| 9 | `RAM_T2P` + tablo içleri `UNROLL` | 10.212.635 | %67 | %26 | %53 | 2 | ✅ ama **2× yavaş** |
| 10 | `RAM_T2P` + Tur 16 geri alınmış | 8.228.447 | %16 | %32 | %63 | 2 | ✅ |

## Kazanan: tek kelime, −%22,6, bedeli sıfır

```diff
-#pragma HLS BIND_STORAGE variable = sv type = RAM_2P  impl = BRAM
+#pragma HLS BIND_STORAGE variable = sv type = RAM_T2P impl = BRAM
```

6.948.095 → **5.375.327 çevrim** (−1.572.768, −%22,6). BRAM, DSP, FF, LUT ve
zamanlama **dördü de değişmedi**.

**Neden işe yarıyor**: `RAM_2P` *basit* çift porttur — bir okuma + bir yazma
portu. Yerinde kelebek her çift için **2 okuma + 2 yazma** ister; 1R+1W ile bu
en iyi ihtimalle II=2, HLS II=3'e razı olmuştu. `RAM_T2P` *gerçek* çift
porttur: iki portun ikisi de okuyabilir veya yazabilir → 4 erişim / 2 port =
**II=2**. 7-serisi BRAM bunu donanımda zaten destekliyor, o yüzden BRAM sayısı
artmıyor. Bedava.

⚠️ Bu bir **depolama bağlama** değişikliğidir; C-sim'de görünmez (C-sim BRAM
portu modellemez). Doğrulaması **cosim**'dir — commit'ten önce koşmalı.

## Elenen yollar (hepsi ölçümle)

**Banka sayısı hiçbir şey kazandırmıyor** (#1, #2, #4, #5). `cyclic` faktörünü
2 → 4 → 8 yapmak II'yi kıpırdatmadı, yalnızca LUT'u %84 → %86 → %90 çıkardı.
Sebep: `k` çalışma zamanı değişkeni olduğu için HLS `i0` ile `i1`'in hangi
bankaya düştüğünü **kanıtlayamıyor** ve kaç banka olursa olsun en kötü durumu
varsayıyor. R-7'nin hipotezi yön olarak doğruymuş — ama bedeli tam
serileştirme değil, bir **II tabanı**.

**II=1 ulaşılamaz.** Dizi başına 4 port gerekir. Ping-pong (A'dan oku, B'ye
yaz) bunu verir ama `sv`'nin BRAM'ini 144 → 288 ikiye katlar; toplam 187/280
zaten dolu. [banking-research.md](banking-research.md) §6'daki duvarın aynısı.

**Tablolar bütçeye sığmıyor** (#6, #7, #8). 256 yinelemelik dış döngüyü boru
hattına almak, iç döngüleri açmaya **zorluyor** (~100 toplayıcı) — bu tuzak
zaten `gates_diagonal.hpp:62`'de yazılı. Ölçüldü: LUT %182 / %166 / %123.
Üçü de dışarıda. #6'nın vaat ettiği 1,6M çevrim gerçek ama **satın alınamaz**.

**İç döngüleri açmak ters tepiyor** (#9). LUT %53'e düşüyor ama gecikme
**iki katına** çıkıyor: `config_compile -pipeline_loops 0` altında `UNROLL`
boru hattını tamamen kaldırıyor ve açılmış toplayıcı zinciri seri kalıyor.

## Nerede duruyoruz (kazanan uygulanırsa)

| Ölçüt | Tur 16 | + `RAM_T2P` |
|---|---:|---:|
| Zamanlama | 7,195 ns | 7,195 ns |
| Gecikme | 6.948.095 | **5.375.327** |
| Süre @100 MHz | 69,5 ms | **53,8 ms** |
| BRAM / DSP / FF / LUT | %66/%16/%46/%84 | %66/%16/%46/%84 |

⚠️ **53,8 ms, ölçülen CPU tabanının (~58 ms) ALTINDA.** Bu, projede ilk kez
tahminin CPU'yu geçmesi demek — ama **hızlanma iddiası DEĞİLDİR**. 53,8 ms bir
HLS tahminidir: sentez sonrası, implementasyon öncesi, donanımda koşmamış.
Gerçek sayı Faz 5'te karttan okunacak (Prensip II ve IV).

## Paralellik arama turu KAPANDI

Dokuz ölçümden sonra geriye satın alınabilir paralellik kalmadı: banka artışı
kazanç vermiyor, II=1 BRAM'e sığmıyor, tablolar LUT'a sığmıyor. Tek bulunan
kazanç `RAM_T2P` ve o da paralellik değil, **port** düzeltmesi.

## KARAR: #3 uygulandı (2026-09-16, onaylı)

`qir_kernel.cpp:155` — `RAM_2P` → `RAM_T2P`. Doğrulandı:

| | |
|---|---|
| Sentez | 7,195 ns · 5.375.327 çevrim · BRAM %66 · DSP %16 · FF %46 · LUT %84 |
| C-sim | fidelity **0,999978179** (n=16, p=2) — değişmedi |
| `rx_dyn_pair_loop` | II 3 → **2**, 98.311 → 65.545 çevrim |

Reddedilenler kayıt için tabloda duruyor; birini geri getirmek isteyen önce
oradaki ölçülmüş LUT rakamına baksın.

---

# 14. Cosim ilk kez KOŞTU ve GEÇTİ (2026-09-16)

`RAM_T2P` bir **depolama bağlama** değişikliğidir; C-sim BRAM portlarını
modellemez, dolayısıyla C-sim'in "geçti"si bu değişiklik hakkında **hiçbir şey
kanıtlamaz**. Tek geçerli kanıt RTL simülasyonudur.

## Cosim bu projede bugüne kadar hiç koşmamış

Denendiğinde iki ayrı bozukluk çıktı. İkisi de Device Guard engeli yüzünden
hiç denenemediği için gizli kalmıştı — SC-005 "doğrulandı" sayılıyordu ama
doğrulanmamıştı.

**1. `cosim.tcl` sentez yapmıyordu.** `common.tcl` içindeki
`open_solution -reset` çözüm veritabanını siliyor; `cosim_design` ardından RTL
bulamıyor:

```
ERROR: [COSIM 212-40] C/RTL co-simulation cannot be started,
       possible causes: 1) Synthesis was not successful; ...
```

Çözüm: `cosim_design`'dan önce `csynth_design`.

**2. Testbench sentezlenen üst fonksiyonu hiç çağırmıyordu.**

```
ERROR: [COSIM 212-330] top function 'qir_kernel' is not invoked in the test bench
```

Doğrulama `qir_kernel_debug` üzerinden yapılıyor çünkü statevector'ü dışarı
veren tek yol o — ama o **sentezlenmez** (`add_files -tb`; sentezlenseydi
`sv_out` bir `m_axi` portu doğurur ve sözleşme maddesi K-1'i ihlal ederdi).
Cosim ise sentezlenen üst fonksiyonun çağrılmasını şart koşuyor. Testbench'e
`qir_kernel` çağrısı eklendi; ikisi de `qir::run_circuit`'i çağırdığı için
(madde T-1) aynı devreyi koşarlar.

## n=16 pratikte koşulamadı — ÖLÇÜLDÜ

| Zaman | Simüle edilen | xsim süresi | Hız |
|---|---:|---:|---:|
| 20:03 | 8,249 ms | 9 dk 19 sn | 0,885 ms/dk |
| 20:25 | 9,603 ms | 30 dk 30 sn | **0,064 ms/dk** |

**14 kat yavaşlama.** Hedef 53,75 ms; bu hızda kalan 44,1 ms **11,5 saat**
ederdi ve hız hâlâ düşüyordu. Sebep hesap değil I/O: xsim'in CPU'su %42'den
%3,9'a inmişti ve bağımlılık uyarısı log'u 87 MB'a ulaşmış, `/mnt/c` köprüsü
üzerinden yazılıyordu (127.770 uyarı bloğu).

Bu yüzden `common.tcl` **kübit sayısında parametrik** hâle getirildi:

```bash
QIR_N=8 vitis-run --mode hls --tcl hls/tcl/cosim.tcl
```

n≠16 ayrı proje dizini (`qir_hls_prj_n8`) kullanır ki n=16 sentez sonuçları
ezilmesin, ve sentetik referansı seçer (`synthref_*_p2_n8`).

## Sonuç: n=8 cosim GEÇTİ

```
*** C/RTL co-simulation finished: PASS ***
Fidelity        : 0.999999871
Beklenen deger  : 0.090485483  (qir_kernel, sentezlenen ust)
```

Süre: **4 dk 31 sn** (n=16'nın 11,5 saatine karşı). Fidelity, kayıtlı n=8
değeriyle birebir aynı.

## Bağımlılık uyarıları YANLIŞ POZİTİFMİŞ

xsim, n=16'da 127.770, n=8'de benzer sayıda *Critical WARNING* bastı:

```
Critical WARNING: Due to pragma (hls/src/gates_pairing.hpp:137:1),
dependence access (loop distance = 1) is detected in ...rx_dyn_pair_loop
If cosim fails, the WARNING should be checked.
```

Satır 137, zamanlamayı tutturan pragmadır:
`#pragma HLS DEPENDENCE variable = sv type = inter dependent = false`.
Uyarı gerçek olsaydı Tur 13'ün 23,0 → 12,7 ns kazancı ve dolayısıyla 7,195 ns
şüpheye düşerdi.

**Cosim GEÇTİ**, yani uyarılar yanlış pozitif. Kontrolcü, yerinde
güncellemenin aynı yineleme içindeki oku-sonra-yaz çiftini yinelemeler arası
bağımlılık sanıyor. Farklı `j` değerleri gerçekten farklı çiftlere dokunuyor;
pragma sağlam.

## Kapsam sınırı — açıkça

Bu doğrulama **n=8'de** yapıldı, n=16'da değil. `RAM_T2P` bağlaması,
`DEPENDENCE` pragması, boru hattı yapısı ve kapı sırası n'den bağımsızdır;
değişen yalnızca dizi boyudur. Yine de n=16 RTL eşdeğerliği **ölçülmedi** ve
öyle yazılmamalı. İstenirse gece boyu koşturulabilir — tercihen proje WSL'in
yerel diskine kopyalanarak, çünkü darboğaz `/mnt/c` üzerindeki log yazımıydı.

---

# 15. DÜZELTME — CPU karşılaştırması iki yerden birden yanlıştı (2026-09-16, T054)

> ⛔ **BU BÖLÜMÜN SONUÇLARI DA GEÇERSİZDİR — bkz. §18.** Buradaki FPGA tarafı
> düzeltmesi (p=2 ayrıştırması) **geçerlidir**, ama CPU tarafındaki rakamlar
> (77,6 / 92,7 ms) ve onlardan türetilen **"FPGA 1,6–2,5× önde"** sonucu
> **yanlıştır**: o ölçümler arka planda cosim koşarken alınmış ve ölçüm yöntemi
> yalnızca turbo penceresini görüyordu. Temiz taban §18'de: turbo 32,75 ms,
> plato 41,93 ms. Doğru sonuç **başabaş**.

`quickstart.md` baştan sona koşulunca (T054) ortaya çıktı. Bu bölümden önceki
bütün CPU karşılaştırmaları **hatalıdır**; aşağıdaki sayılar geçerlidir.

## Hata 1 — FPGA tarafı p=3, CPU tarafı p=2 idi

Sentez raporundaki `max` gecikme `P_MAX = 3` içindir. Fidelity testleri ve CPU
referansı ise **p=2** koşar. Yani 53,8 ms ile ~58 ms karşılaştırılırken **farklı
devreler** karşılaştırılıyordu.

Doğru ayrıştırma (`init` 65.538 + p × katman 1.647.107 + `expectation` 368.465):

| p | Çevrim | @100 MHz |
|---|---:|---:|
| 1 | 2.081.110 | 20,81 ms |
| **2** | **3.728.217** | **37,28 ms** |
| 3 | 5.375.324 | 53,75 ms |

## Hata 2 — "~58 ms" CPU tabanı bir MEDYAN değil, bir EN İYİ DURUM

`cpu_reference_time.py` iki kez koştu ve p=2 için şunları ölçtü:

| Koşu | min | **medyan** | max |
|---|---:|---:|---:|
| 2026-09-15 | **58,07** | 77,57 | 120,99 |
| 2026-09-16 | 78,95 | 92,66 | 111,42 |

Proje boyunca kullanılan "~58 ms", 15 Eylül koşusunun **en iyi** değeriydi.
Aynı koşunun medyanı 77,6 ms; bugünkü koşu o en iyi değere **hiç ulaşmadı**
(en iyisi 78,95). `quickstart.md` Adım 0 zaten uyarıyordu:
*"Yayılım geniştir — tek koşuma güvenme."* Uyarı okunmuş ama uygulanmamış.

## Doğru karşılaştırma (p=2, aynı devre)

| | Değer |
|---|---:|
| FPGA, HLS tahmini | **37,28 ms** |
| CPU Aer, medyan (15 Eyl / 16 Eyl) | 77,57 / 92,66 ms |
| CPU Aer, en iyi durum (15 Eyl) | 58,07 ms |

Oran **1,6× – 2,5×** aralığında, hangi CPU değerinin alındığına göre.

## Neden fark edilmedi

İki hata **ters yönlüydü ve birbirini kısmen götürdü**. FPGA sayısı olduğundan
büyük (p=3), CPU sayısı olduğundan küçük (en iyi durum) alınınca sonuç
"CPU 1,2× önde" gibi makul göründü. Gerçekte FPGA tahmini p=2'de **önde**.

Bu, yanlışın en tehlikeli türü: iki hatanın birbirini maskelemesi. Tek bir
sayıya bakarak yakalanamazdı — `quickstart.md`'yi uçtan uca koşmak yakaladı.
T054'ün varlık sebebi tam olarak budur.

## Değişmeyen: HÂLÂ HIZLANMA İDDİASI YAPILAMAZ

Yön değişti (CPU önde değil, FPGA tahmini önde) ama yasak aynı gerekçeyle
duruyor ve şimdi **daha da önemli**:

- 37,28 ms sentez sonrası bir **HLS tahminidir** — implementasyon yapılmadı,
  bitstream üretilmedi, kartta koşulmadı.
- CPU tarafı **±%60 oynuyor** (58–123 ms). Tek koşum taban olamaz; teze
  girecek sayı çoklu koşumun medyanı ve yayılımıyla birlikte verilmelidir.
- Enerji ekseni hiç ölçülmedi.

Karşılaştırma Faz 5/Faz 10'da, kartta, aynı `p` ile ve CPU tarafı çoklu koşumla
yapılacak (Prensip II ve IV).

## Ayrıca: `cpu_reference_time.py` eski tahminleri basıyor

Betik çıktısının sonunda hâlâ şunlar var:

```
yerinde (Q1.17)     237568 cevrim = 2.38 ms  ->  33.2x
ping-pong (Q1.17)    69632 cevrim = 0.70 ms  -> 113.4x
```

Bu sayılar **sentez öncesi aritmetik tahminlerdir** ve ölçülenden 16–54 kat
sapmışlardır (gerçek p=2: 3.728.217 çevrim). Betik "TAHMINDIR" diye uyarıyor
ama ekranda ölçülenin yanında durmaları yanıltıcı. Betiğin ölçülen değeri
kullanacak şekilde güncellenmesi T054'ün kapsamı dışında bırakıldı — Faz 10
(kıyas) işidir ve orada zaten kart ölçümüyle değişecek.

---

# 16. Vivado implementasyonu — HLS tahmini LUT'ta 2× yanılıyor (2026-09-16)

İlk kez `export_design -flow impl` koşuldu: Vivado RTL sentezi + yerleştirme +
yönlendirme. Buraya kadar bütün kaynak sayıları **HLS tahminiydi**.

## Mevcut tasarım: tahmin vs gerçek

| | HLS tahmini | **Vivado P&R** | oran |
|---|---:|---:|---:|
| LUT | 45.164 (%84,9) | **22.535 (%42,4)** | 0,50× |
| FF | 49.839 (%46,8) | **19.466 (%18,3)** | 0,39× |
| DSP | 36 (%16,4) | 33 (%15,0) | 0,92× |
| BRAM_18K | 187 (%66,8) | **187 (%66,8)** | 1,00× |

**Zamanlama tuttu**: post-synthesis 9,171 ns → post-route **9,122 ns**.

BRAM'in birebir tutması beklenir — bellek blokları sayılabilir. LUT ve FF ise
sentezcinin optimize ettiği kaynaklardır; HLS kaba bir üst sınır verir.

⚠️ Bu, ADR 0009'un *"tablolar LUT'a sığmıyor"* gerekçesini geçersiz kıldı.
O gerekçe HLS'in %182/%166 tahminine dayanıyordu.

## #6 ve #7 implementasyona kadar koşuldu

| | LUT | FF | DSP | BRAM | Gecikme p=2 | Post-route |
|---|---:|---:|---:|---:|---:|---:|
| **mevcut** | 22.535 (%42) | 19.466 (%18) | 33 (%15) | 187 (%67) | **37,28 ms** | **9,122 ns** ✅ |
| **#6** (tüm tablolar II=4) | 37.983 (%71) | 56.561 (%53) | 137 (%62) | 187 (%67) | **26,65 ms** | **9,878 ns** ✅ |
| #7 (yalnız `tablo_yuksek`) | 39.191 (%74) | 51.468 (%48) | 137 (%62) | 187 (%67) | 30,34 ms | **10,170 ns** ❌ |

HLS→gerçek oranı **sabit değil**: LUT'ta 0,39× / 0,44× / 0,50×. "HLS'i ikiye
böl" diye bir kural yok; her varyant ayrı ölçülmelidir.

### #7 elendi — domine ediliyor

#7, #6'nın alt kümesidir (yalnızca `tablo_yuksek` boru hattında). Sezgi daha
kolay yerleşeceğini söyler; ölçüm tersini dedi. #6 her eksende daha iyi: daha
az LUT, daha düşük gecikme, zamanlama tutuyor. Yerleştirme-yönlendirme
**monoton değildir** — daha az talep eden netlist daha iyi yerleşmeyebilir.

### #6 KABUL EDİLMEDİ — marj yetersiz

Gecikme kazancı gerçek: 37,28 → **26,65 ms (−%28,5)**, dört kaynak da bütçede,
zamanlama tutuyor. Yine de reddedildi. Ölçüt **sayı görülmeden önce** ilan
edilmişti: *post-route 9,1–9,4 ns ise öner, 9,7+ ise önerme.*

| | post-syn → post-route | Marj |
|---|---|---:|
| mevcut | 9,171 → 9,122 (**iyileşti** −0,049) | **+0,878 ns (%8,8)** |
| #6 | 9,171 → 9,878 (**kötüleşti** +0,707) | **+0,122 ns (%1,2)** |

Üç bağımsız işaret aynı yöne bakıyor:

1. **Marj 7 kat daha az** — %8,8 → %1,2.
2. **Yönlendirme zamanlamayı bozdu.** Mevcut tasarımda yönlendirme 0,049 ns
   *iyileştirdi*; #6'da 0,707 ns *kötüleştirdi*. Bu tıkanıklık işaretidir:
   yönlendirici zamanlamayı tutturmak için uzun yollara mecbur kalmış.
3. **Koşum 3 kat uzun sürdü** — 13 dk → 37 dk. Vivado zorlandı.

Buna Faz 5 eklenecek: PS entegrasyonu, AXI bağlantısı, olası DMA. Bunlar
yonga içinde yer ve yol tüketir. 0,122 ns'lik marj o noktada tükenir ve
tasarım **Faz 5'in ortasında** kırılır — geri dönmenin en pahalı olduğu yerde.

Ayrıca #6 DSP'yi %15 → **%62**, FF'i %18 → **%53** çıkarıyor. Faz 5'in payı
da azalıyor.

**Karar: mevcut tasarımda kalınır.** Hızlanma iddiası zaten yapılamadığı için
26,65 ms ile 37,28 ms arasındaki fark bugün hiçbir kabul ölçütünü değiştirmiyor;
buna karşılık kaybedilen marj Faz 5'i doğrudan riske atıyor.

### #6 ne zaman yeniden açılır

- Faz 5 tamamlanıp **gerçek** PS entegrasyonu sonrası marj ölçülürse ve hâlâ
  yer varsa,
- veya saat hedefi 100 MHz'in altına çekilirse (o zaman 9,878 ns bol marj olur),
- veya gecikme **gerçekten** bir kabul ölçütü hâline gelirse.

Ölçüm burada duruyor; yeniden açan sıfırdan koşmak zorunda değil.

---

# 17. Bellek çakışma uyarıları — T034 (2026-09-16)

SK-02'nin erken uyarı işareti şuydu: *"İlk sentez raporunda II beklenenin 5
katından büyük **ve** bellek çakışma (memory dependency) uyarısı var."*
İki kaynaktan da toplandı ve sonuç **ilk bakışta çelişkili**.

## Sentez (csynth): SIFIR çakışma uyarısı

Yirmiden fazla sentez turunda `SCHED 204-68` / `dependence` sınıfı tek bir
uyarı çıkmadı. `SYNCHK` her turda `0 error(s), 1 warning(s)` verdi ve o tek
uyarı `qir_kernel.cpp:69-70`'teki **çift yazılmış** `PIPELINE off` pragmasıydı
(HLS ikisini birleştiriyor, davranışa etkisi yok).

II tarafı da eşiğin çok altında: beklenen 1–2, ölçülen `cost_amp_loop` **1**,
`rx_dyn_pair_loop` **2**. "5 katı" eşiğine yaklaşılmadı.

## Cosim (xsim): 127.770 uyarı — ve hepsi YANLIŞ POZİTİF

RTL simülasyonu tam tersini bastı:

```
Critical WARNING: Due to pragma (hls/src/gates_pairing.hpp:137:1),
dependence access (loop distance = 1) is detected in ...rx_dyn_pair_loop
  From memory access "..._co_3_address0" = 0x677b @ "8235720000"
  To   memory access "..._co_3_address0" = ... 0x677b @ "8235650000"
If cosim fails, the WARNING should be checked.
```

n=16 koşusunda **127.770 blok** (log 87 MB), n=8'de benzer yoğunlukta.
Satır 137, zamanlamayı tutturan pragmadır:

```cpp
#pragma HLS DEPENDENCE variable = sv type = inter dependent = false
```

**Cosim GEÇTİ** (n=8, `C/RTL co-simulation finished: PASS`, fidelity
0,999999871). Uyarının kendi metni de ölçütü veriyordu: *"If cosim fails, the
WARNING should be checked."* Kalmadı → uyarılar yanlış pozitif.

**Sebebi**: kontrolcü, yerinde güncellemenin **aynı yineleme içindeki**
oku-sonra-yaz çiftini yinelemeler arası bağımlılık sanıyor. Farklı `j`
değerleri gerçekten farklı çiftlere dokunur:
`i0 = (j >> k << (k+1)) | (j & (stride-1))`, `i1 = i0 | stride` — `j` birebir
bir eşlemedir, iki yineleme aynı adrese dokunamaz.

⚠️ **Bu, bedava bir sonuç değildi.** Uyarı gerçek olsaydı Tur 13'ün
23,016 → 12,697 ns kazancı ve dolayısıyla 7,195 ns'nin tamamı — ve nihayetinde
post-route 9,122 ns — şüpheye düşerdi. Pragmanın sağlamlığını **yalnızca**
cosim kanıtlayabilirdi; C-sim bu soruyu hiç göremez.

## SK-02 açısından sonuç

Erken uyarı işaretinin iki koşulu da **gerçekleşmedi**: ne II eşiği aşıldı, ne
sentezde çakışma uyarısı çıktı. K-03'ün üç denemelik bütçesinden **sıfır**
harcandı. Bkz. [risk-register.md](../risk-register.md).

Ancak SK-02'nin *varsayımı* ayrıca yanlışlandı: çakışma bankalama ile
çözülmüyordu, çünkü sınır bankalama değil **bellek portuydu** (§13, ADR 0009).

---

# 18. CPU TABANI YENİDEN ÖLÇÜLDÜ — eski rakamlar kirliydi (2026-09-19)

⚠️ **Bu bölüm §15'i geçersiz kılar.** §15'te "FPGA tahmini CPU'yu 1,6–2,5×
geçiyor" yazıyor; **yanlıştır**. §15 FPGA tarafındaki iki hatayı düzeltmişti
ama CPU tarafının **kendisinin** güvenilmez olduğunu görmemişti.

## İki ayrı kirlenme bulundu

**1. Eski ölçümler arka plan yükü altında alınmış.**
`cpu-referans-zaman_20260916_8fe16e6.json` damgası 2026-09-16 20:59 (yerel).
O saatte **n=16 cosim koşuyordu** (xsim, tam çekirdek RTL simülasyonu;
20:34:37'de başlatılmıştı ve oturum kayıtlarında 20:59'da hâlâ ilerliyordu).
15 Eylül ölçümü için doğrudan kanıt yok ama o gün de sentez turları vardı.

**2. Daha önemlisi: CPU'nun kendisi kararsız ve eski betik bunu göremiyor.**
`cpu_reference_time.py` içinde `TEKRAR = 15`. 15 koşum ≈ 0,6 saniye — yani
tam **turbo penceresi**. Ölçüm sistematik olarak işlemcinin kısa süreli en
iyi hâlini yakalıyor, sürdürülen performansını değil.

Teşhis deneyi (aynı devre, üç koşul):

| Koşul | Medyan |
|---|---:|
| A — temiz, soğuk, 15 tekrar | **35,51 ms** |
| B — Python benchmark'ından sonra, 15 tekrar | 53,47 ms |
| C — sürdürülen, 400 tekrar | 53,44 ms |
| A tekrar — soğuk koşullar yeniden | **53,08 ms** |

"A tekrar"ın düzelmemesi belirleyici: suçlu Python benchmark'ı **değil**,
termal doyum. İşlemci ısındıktan sonra o hızda kalıyor.

## Temiz ölçüm

2026-09-19 · prizde · harici monitör yok · sessiz makine · **7474 koşum / 300 sn**

Pencere medyanları (10 sn'lik dilimler): 34,04 → 35,22 → 36,16 → … → 41,87 →
42,23 → 41,96 → **41,90**. Son altı pencere sabit — **plato oturdu**.

| | Değer |
|---|---:|
| **Turbo** (ilk 2 sn) | **32,75 ms** |
| **Plato** (son 60 sn) | **41,93 ms** |
| Turbo → plato | 1,28× yavaşlama |
| Verim | 24,91 koşum/sn |

**Eski kayıtların sapması:**

| Kayıt | Değer | Platonun katı |
|---|---:|---:|
| 15 Eyl | 77,57 ms | **1,85×** |
| 16 Eyl (xsim koşarken) | 92,66 ms | **2,21×** |

## DÜZELTİLMİŞ KARŞILAŞTIRMA

FPGA p=2: **37,28 ms** (HLS/implementasyon tahmini, 100 MHz)

| Karşısında | Sonuç |
|---|---|
| CPU platosu 41,93 ms | FPGA **1,12× hızlı** |
| CPU turbosu 32,75 ms | FPGA **1,14× YAVAŞ** |

**Gecikme ekseninde kazanç yok — başabaş.** FPGA tahmini, CPU'nun turbo ve
plato değerlerinin tam arasına düşüyor.

Hangisinin adil olduğu kullanım senaryosuna bağlıdır ve tezde tartışılmalıdır:
tek seferlik bir sorgu için turbo, sürekli yük için plato. İkisi de
raporlanmalı, biri seçilip diğeri gizlenmemeli.

## Enerji — asıl hikâye burada olabilir

Ölçülen CPU enerjisi (bkz. §19): **0,644 J/koşum**.

PYNQ-Z2 tüm kart olarak ~3–5 W çeker; 37 ms'lik koşum için 0,11–0,19 J eder,
yani **3,5–5,8× daha az**. ⚠️ Bu bir **hesaptır, ölçüm değildir** — FPGA'nın
gücü henüz ölçülmedi (US3, INA219 bekliyor).

Büyüklük mertebesi doğrularsa tezin sonucu *"FPGA daha hızlı"* değil,
**"FPGA aynı hızda ama belirgin biçimde daha az enerjiyle"** olacaktır.

## Alınan ders

Üç düzeltme üst üste geldi ve üçünün de kökü aynı: **tek koşumluk, kontrolsüz
ortamda alınmış CPU rakamına güvenmek.**

Bundan sonraki kural:
- CPU tabanı **süre tabanlı** ölçülür, sabit tekrar sayısıyla değil
- **Turbo ve plato ayrı** raporlanır
- Plato oturduğu **doğrulanır** (son iki 30 sn'lik dilim %3'ten az farklı)
- Makinede başka **hiçbir ağır iş koşmaz** — özellikle sentez/cosim
- Prizde, harici ekran olmadan

---

# 19. CPU ENERJİSİ ÖLÇÜLDÜ — batarya yöntemi (2026-09-19)

İlk gerçek enerji ölçümü. Anayasa Prensip II enerji rakamlarının gerçek
ölçüme dayanmasını şart koşuyordu; bu bölüm o eksiği CPU tarafı için kapatıyor.

## Neden batarya, neden INA219 değil

Dizüstünün adaptörü **20 V / 6 A / 120 W**. INA219'u araya koymak için o hattı
kesmek gerekirdi ve standart 0,1 Ω şönt 5 A'de **2,5 W** harcayıp yanardı.
Batarya sayacı **aynı kapsamı** (tüm dizüstü) ölçüyor, çözünürlüğü fazlasıyla
yeterli ve riski sıfır.

## Yöntem — delta

Boştaki güç ve yük altındaki güç ayrı ayrı ölçülür, işin maliyeti **farktan**
hesaplanır. Ekran, diskler ve boştaki her şey iki ölçümde de var olduğu için
sadeleşir. Bu, kart tarafında uygulanacak yöntemle **aynıdır**.

Tek koşum ~42 ms; hiçbir batarya sayacı bunu göremez. İş yükü 175 saniye
döngüye alınıp toplam enerji koşum sayısına bölündü.

## Ölçüm

2026-09-19 · fişten çıkık · harici monitör yok · fanlar makste (iki ölçümde de)
· 180 sn kayıt, saniyede bir örnek

| | Boşta | Yük altında |
|---|---:|---:|
| Ortalama güç | **21,58 W** | **34,80 W** |
| Enerji A (gücün integrali) | 1076,29 mWh | 1738,39 mWh |
| Enerji B (kapasite farkı) | 1038,00 mWh | 1755,00 mWh |
| **A/B sapması** | %3,6 | **%0,9** |

İki bağımsız hesap birbirini doğruladı (eşik %10). Ölçüm güvenilir.

| | |
|---|---:|
| Yük − boş güç farkı | **13,22 W** |
| İşin toplam enerjisi | 2374,8 J |
| Koşum sayısı | 3688 |
| **Koşum başına enerji** | **0,644 J** |

## ⚠️ Çalışma noktası uyarısı

Bu enerji **bataryadaki** çalışma noktasında ölçüldü ve orada CPU **kısılıyor**:

| | Prizde | Bataryada |
|---|---:|---:|
| Verim | 25,68 koşum/sn | 21,07 koşum/sn |
| Koşum başına | 38,9 ms | 47,5 ms |

**−%18 verim, +%22 süre.** Yani 0,644 J, 47,5 ms/koşum noktasına aittir;
prizdeki 41,93 ms noktasına değil.

Bu, batarya yönteminin yapısal sınırıdır: ölçüm yalnızca fişten çıkıkken
yapılabiliyor, dolayısıyla enerji ve gecikme **farklı çalışma noktalarından**
geliyor. Rapora böyle yazılmalıdır; düzeltme katsayısıyla uydurulmamalıdır.

## Üretmek için

    # 1) prizde referans verim
    .venv\Scripts\python.exe scripts\cpu_load_loop.py --saniye 60 --p 2 --etiket prizde
    # 2) fisi cek, bosta
    powershell -ExecutionPolicy Bypass -File scripts\battery_logger.ps1 -Saniye 180 -Cikti bos.csv
    # 3) yuk altinda (iki pencere)
    powershell -ExecutionPolicy Bypass -File scripts\battery_logger.ps1 -Saniye 180 -Cikti yuk.csv
    .venv\Scripts\python.exe scripts\cpu_load_loop.py --saniye 175 --p 2 --etiket bataryada
    # 4) hesap
    python scripts\battery_energy.py --bos bos.csv --yuk yuk.csv --kosum <kosum>

---

# §20 — n=16 cosim: bir çökme, bir yanlış teşhis, 76× hızlanma

**19 Eylül 2026 · commit 4282956**

## Özet

n=16 C/RTL cosimulation **geçti**. Çekirdeğin tek çıkış portu `beklenen_deger`,
C modeliyle bit bit aynı: `0xbee28271` (= −0,442401439). Bu, `olculen-degerler.md`
§7'deki *"n=16 RTL eşdeğerliği ölçülmedi"* maddesini kaldırıyor.

Asıl kazanım rakam değil, **yöntem**: cosim'in 13 saat sürmesinin sebebi
tasarımın karmaşıklığı değil, araç zincirindeki bir çıktı aktarımıymış.
Düzeltince koşu **15 dakika 48 saniyeye** indi.

## Ne oldu

**20:51 — makine çöktü.** Yeniden başlatma değil, mavi ekran:
`0x00000116 VIDEO_TDR_ERROR`, parametre 3 = `0xc000009a`
(STATUS_INSUFFICIENT_RESOURCES). Ekran sürücüsü sıfırlanamamış.
**İlk değil**: 17 Eylül 11:47'de birebir aynı kod. Üç günde iki kez.

Cosim %28,9'da öldü (10,787 / 37,28 ms), ~1 saat gitti.

## Yanlış teşhis — iki kez

`/root/cosim-n16.sh` başındaki yorum şunu iddia ediyordu:

> *"darboğaz hesap değil I/O idi... log `/mnt/c` köprüsünden yazılıyordu."*

**Yanlıştı.** Bu koşu zaten WSL yerel diskindeydi (`/root/qir-n16`) ve aynı
eğriyi çizdi:

| | `/mnt/c` (16 Eyl) | yerel disk (19 Eyl) |
|---|---|---|
| başlangıç | 0,885 ms/dk | 0,856 ms/dk |
| çöktüğü yer | 0,064 ms/dk | 0,036 ms/dk |

Disk değişkeni kalktı, davranış değişmedi → **sebep disk değildi.** Bu, 16 Eylül'de
ölçülüp çürütülen hipotezin (`/mnt/c` 9,603 ms @ 30:30 vs yerel 9,604 ms @ 36:05)
ikinci kez doğrulanmasıdır. Yorum, çürütmeden sonra güncellenmemişti.

## Gerçek sebep

`solution1/sim/verilog/run_sim.tcl`:

```tcl
set ret [catch {eval exec "sh ./run_xsim.sh | tee temp2.log" >&@ stdout} err]
```

`>&@ stdout` — xsim'in **her satırı Tcl'in kanal katmanından** geçiyor. Tasarımda
`#pragma HLS DEPENDENCE` yüzünden xsim yüz binlerce 5 satırlık *Critical WARNING*
bloğu basıyor (bkz. §17). Süreç tablosu bunu doğruluyordu:

| süreç | eski (vitis-run içinden) | yeni (baypaslı) |
|---|---|---|
| `xsimk` (asıl simülatör) | **%5,1** — aç bekliyor | **%108** |
| `vitis-run` (Tcl) | **%97,9**, 685 MB | yok |

Yavaşlamanın **süperdoğrusal** olması da buna oturuyor: Tcl biriktirdikçe her
yeni parça daha pahalıya geliyordu.

## Çözüm

Cosim aslında üç ayrı aşama ve dışarıdan sürülebiliyor:

| Aşama | Ne yapar |
|---|---|
| 1 · `wrapc/cosim.tv.exe` | C testbench'i koşup test vektörlerini kaydeder |
| 2 · `verilog/run_xsim.sh` | RTL simülasyonu (`xelab` + `xsim`) |
| 3 · `wrapc_pc/cosim.pc.exe` | RTL çıktısını C ile karşılaştırır |

1. aşama çökmeden önce bitmişti (`tv/cdatafile/` doluydu), tekrarlanmadı.
`/root/cosim-hizli.sh` 2. ve 3. aşamayı **doğrudan kabuktan** koşuyor — aynı RTL,
aynı testbench, aynı uyaran, sadece Tcl araya girmiyor.

| | eski | yeni |
|---|---|---|
| ortalama hız | 0,036 ms/dk (kararlı hal) | **2,73 ms/dk** |
| toplam süre | ~13 saat (öngörü) | **15 dk 48 sn** |
| 3. aşama | — | 8 sn |

**76× hızlanma.** Ve hız bu kez çökmedi: 0,43–5,41 ms/dk arasında salındı, düşüş
eğilimi yok. (Salınım ölçüm yöntemindendir: ilerleme, uyarı satırlarındaki
`@ "NNN"` damgalarından okunuyor, uyarı basılmayan evrelerde sayaç duruyor.)

## Kanıt ve sınırları

Ham kanıt: [cosim-n16_20260919_4282956_p2.kanit.txt](cosim-n16_20260919_4282956_p2.kanit.txt)

**Kanıtlanan**: RTL n=16'da elaborasyondan geçti, kilitlenmeden koştu, çıkış
portunda C ile bit bit aynı değeri üretti. `AESL_mErrNo` yok, `.exit.err` yok,
rc=0/rc=0.

**Kanıtlanmayan**: 65536 genliğin tek tek eşitliği. `sv[]` dahili BRAM'dir,
çıkış portu değildir — cosim onu göremez. Beklenen değer 65536 terimlik bir
indirgeme olduğu için kanıt güçlü ama tüketici değil. Ayrıca **tek uyaran** (tek
problem örneği, p=2).

**Tuzak**: üretilen JSON'daki `fidelity: 0,999978179` **RTL'in değil, C modelinin**
Qiskit'e karşı değeridir. `tb_kernel.cpp`'de karşılaştırılan `cikti[]`, yazılım
`sv[]`'sinden doldurulur. Testbench bunu zaten yazmış:
*"bu çağrı fazladan bir doğrulama değil, cosim'in çalışabilmesi için gereken
kancadır."* Cosim sonucunu fidelity ile raporlamak **yanlış olur**.

## Damga

Üretilen JSON'un `git_hash` alanı `"vitis"` diyor — gerçek commit değil. Sebep:
koşu `/root/qir-n16` kopyasında yapıldı, orada `.git` yok, `common.tcl`'in
`git rev-parse` çağrısı boş döndü. Commit bağlantısı **md5 eşitliğiyle** kuruldu:
`qir_kernel.cpp`, `qir_kernel.hpp`, `gates_pairing.hpp`, `tb_kernel.cpp` —
dördü de repo (HEAD 4282956) ile birebir aynı. Özetler kanıt dosyasında.

## Sonraki koşular için

```bash
wsl -d Ubuntu -e bash /root/cosim-hizli.sh      # 2.+3. asama, ~16 dk
wsl -d Ubuntu -e bash /root/cosim-hizli-durum.sh # ilerleme
```

⚠️ 1. aşama (test vektörleri) mevcut olmalı. Tasarım değişirse `cosim_design`'ı
bir kez normal koşup 1. aşamayı yeniden üretmek gerekir.
⚠️ Log 664 MB'a çıkıyor (`/var/log/cosim-n16-hizli.log`).

---

# §21 — `cost` sessizce doyuyor: sözleşmenin uyardığı hata, zaten depoda

**20 Eylül 2026 · Faz 5 öbek 3 sırasında bulundu**

## Bulgu

Konak kodlayıcıyı C-sim'e karşı doğrularken referans dosyasının ham Ising
katsayılarına bakıldı:

| | |
|---|---|
| `max\|h\|` | **7512,61** |
| `max\|J\|` | **1253,07** |
| Q1.17 üst sınırı | 0,99999237 |
| `AP_SAT` ile doyan `h` | **16 / 16** |
| `AP_SAT` ile doyan `J` | **84 / 120** |

C testbench'i ([tb_kernel.cpp](../../hls/tb/tb_kernel.cpp)) şunu yapıyor:

```cpp
cost.h[k] = qir::real_t(h_j[k].num);      // real_t = ap_fixed<18,1,AP_RND_CONV,AP_SAT>
```

Düz atama. `-6313,985` değeri `AP_SAT` ile **sessizce** `-1,0`'a kırpılıyor.
Doğrulandı: dökülen `cost` word'lerinin ilk altısı `131072 = 0x20000`, yani
Q1.17'nin en negatif ucu.

## Ne etkilenir, ne etkilenmez

**Etkilenir**: `beklenen_deger = -0,442401439`. Bu, **doymuş** bir maliyet
operatörünün beklenen değeridir. Tezde bir enerji olarak raporlanamaz.

**Etkilenmez — ikisi de ayrı yoldan gelir:**

| Sonuç | Neden etkilenmez |
|---|---|
| **fidelity 0,999978179** | `sv`, `qir_kernel_debug(phases, cos_beta, sin_beta, p, sv)` ile üretilir — `cost` bu çağrıya **girmez**. Fazlar mod 1'e indirgendiği için doyma yaşanmaz. |
| **RTL ≡ C (§20)** | İki taraf da aynı doymuş fonksiyonu hesaplar ve bit bit aynı sonucu verir. Eşdeğerlik karşılaştırması bundan bağımsızdır. |

Yani Faz 2'nin iki ana sonucu da ayakta. Düşen tek şey, `beklenen_deger`'in
fiziksel yorumu — ki zaten hiçbir yerde enerji olarak raporlanmamıştı.

## Neden şimdi görüldü

Çünkü ilk kez **konak tarafı** yazıldı. Faz 2 boyunca ölçüt fidelity'ydi ve
fidelity bu hatayı görmüyor. `contracts/host-encoder.md` bu riski açıkça
yazmıştı:

> *"Ham QUBO katsayıları ~1e4 mertebesinde; `ap_fixed` doyurması onları uyarı
> vermeden kırpar ve sonuç yanlış çıkar — üstelik hata **donanıma yıkılır**."*

Sözleşme bir tahmin olarak yazılmıştı. **Ölçüldü: gerçekti ve zaten oluyordu.**

## Kapatan şey

[`agent/encoder.py`](../../agent/encoder.py) ölçekleme protokolünü uygular ve
madde H-3 gereği aynı girdide **istisna fırlatır**:

```
AralikDisi: h[0]=-6313.985 Q1.17'ye sığmıyor: q=-827671482 ∉ [-131072, 131071].
Ölçekleme atlanmış olabilir (madde H-3: sessiz kırpma yasak).
```

Testle sabitlendi: `agent/tests/test_csim_esdegerlik.py::test_kodlayici_doyurmak_yerine_atar`.

## G2 kapısı — kodlayıcı C'ye karşı bit bit doğrulandı

`tb_kernel.cpp`'ye `--dump-words` eklendi (hesabı değiştirmez, yalnız
paketlenmiş word'leri JSON'a yazar). Karşılaştırma:

| Dizi | Sonuç |
|---|---|
| `phases` (816 word) | ✅ **816/816 bit bit aynı** — 200'ü sıfırdan farklı, 51 benzersiz değer |
| `cos_beta`, `sin_beta` | ✅ bit bit aynı |
| `cost` (272 word) | ⚠️ **kasıtlı farklı** — C doyuruyor, kodlayıcı ölçekliyor |

Word karşılaştırması, beklenen değer karşılaştırmasından üstündür: ikinci
yöntemde iki ayrı hata birbirini götürebilir. Bit bit tutuyorsa kodlayıcı,
Qiskit'e (fidelity) ve RTL'e (cosim) karşı doğrulanmış C yolunun **tam
aynısını** üretiyor demektir.

⚠️ Ölçekleme protokolünün C'de karşılığı **yoktur** — orada hiç ölçekleme
yapılmıyor. O yüzden ölçekleme C'ye karşı değil, kendi sözleşmesine karşı
doğrulanır (`test_encoder.py`: H-2 payı, geri dönüş, H-3 istisnası).

---

# §22 — ⛔ §18'in CPU tabanı geçersiz: adil taban ölçüldü

**21 Eylül 2026**

§18'de CPU tabanı **Qiskit Aer** ile ölçülmüştü (turbo 32,75 ms, plato
41,93 ms) ve sonuç *"gecikmede başabaş"* diye kaydedilmişti. **O taban adil
değilmiş.**

Aynı çekirdek kodu (`hls/tb/bench_kernel.cpp`, aynı `qir_kernel` çağrısı)
doğrudan CPU'da zamanlandı:

| Taban | Medyan | FPGA'ya göre |
|---|---:|---|
| Aynı kod, yerel `float` | **3,273 ms** | **CPU 11,4× hızlı** |
| Aynı kod, Q1.17 (taklit) | 12,992 ms | CPU 2,9× hızlı |
| Qiskit Aer (§18 tabanı) | 32,750 ms | CPU 1,14× → *"başabaş"* |
| FPGA | 37,28 ms | — |

**Sebep**: Aer, RZZ'yi CX-RZ-CX olarak ayrıştırır ve p=2'de **384 kapı**
uygular; bizim çekirdek köşegen operatörün tamamını **32 geçişe** füzyonlar
([gates_diagonal.hpp](../../hls/src/gates_diagonal.hpp)). 12× kapı farkı,
ölçülen ~10× süre farkını açıklıyor.

Kayıt: [adil-cpu-tabani](adil-cpu-tabani_20260921_c504294.json)

## Doğru taban: kart üstü ARM (PS↔PL)

| Platform | Gecikme | M çift/s | Saat | çevrim/çift | FPGA'ya göre |
|---|---:|---:|---:|---:|---|
| **FPGA (PL)** | 37,28 ms | 28,1 | 100 MHz | **3,56** | — |
| **ARM Cortex-A9 (PS)** | **84,13 ms** | 12,5 | 650 MHz | 52,2 | **FPGA 2,26×** |
| Dizüstü i7 | 3,27 ms | 320,4 | ~4 GHz | 12,5 | CPU 11,4× |

Kayıt: [ps-pl-hizlanma](ps-pl-hizlanma_20260921_c504294.json)

**FPGA üç platformun en verimlisi** — çevrim başına 3,56, ARM'ın 14,7 katı,
i7'nin 3,5 katı. Sonucu belirleyen mimari değil **saat frekansı**: 100 MHz
650 MHz'i yener, 4 GHz'i yenmez.

## Etkilenmeyenler

Fidelity, C/RTL eşdeğerliği, kaynak kullanımı, zamanlama kapanışı — hiçbiri
etkilenmez. Düşen **yalnız gecikme karşılaştırmasıdır**.
