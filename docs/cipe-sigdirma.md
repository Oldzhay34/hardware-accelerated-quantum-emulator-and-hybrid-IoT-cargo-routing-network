# Tasarımı çipe sığdırma — dokuz sentez turunun anatomisi

**Tarih**: 2026-09-15/16 · **Hedef**: XC7Z020 (PYNQ-Z2) · **Araç**: Vitis HLS 2025.2
**Ham ölçümler**: [measurements/faz2-sentez.md](measurements/faz2-sentez.md)

> Bu belge **ne yaptığımızı ve neden yaptığımızı** anlatır. Her sayı gerçek
> sentez raporundan okunmuştur (Anayasa Prensip II). Başarısız denemeler ve
> yanlış teşhisler de burada — çünkü hangi yolun çıkmaz olduğunu bilmek, hangi
> yolun işe yaradığını bilmek kadar değerlidir.

---

## Özet: nereden nereye

| | 1. tur | **9. tur** | Bütçe |
|---|---:|---:|:---:|
| BRAM_18K | 148 (%52) | **171 (%61)** | ✅ |
| DSP | 337 (**%153**) | **36 (%16)** | ✅ |
| FF | 90.626 (%85) | **13.391 (%12)** | ✅ |
| LUT | 98.627 (**%185**) | **22.572 (%42)** | ✅ |
| Gecikme | 355.140.025 | **15.363.498** | — |
| Zamanlama | 25,039 ns | 24,799 ns | ❌ hedef 10 ns |

İlk sentezde tasarım **çipe sığmıyordu** (LUT %185, DSP %153) ve bir QAOA
değerlendirmesi **8,9 saniye** sürüyordu. Dokuzuncu turda dört kaynağın dördü
de bütçede ve gecikme **23 kat** azaldı.

**Zamanlama hâlâ çözülmedi** ve bu belge onu çözülmüş gibi göstermez.

---

## Başlangıç durumu: neden sığmıyordu

C-simülasyon fidelity'si mükemmeldi (0,999978) ve bu yanıltıcıydı. Faz 2
spec'inin uyardığı tuzak tam olarak gerçekleşti:

> *"C-sim geçiyor ama sentez II'si kötü çıkarsa? Tam olarak beklenen tuzak."*

İlk rapor iki şeyi söyledi: tasarım sığmıyor, ve CPU'dan 150 kat yavaş.

---

## Düzeltme 1 — Çift duyarlıklı trigonometriyi tablodan okumak

**Sorun.** `trig.hpp` `std::cos`/`std::sin` çağırıyordu ve argüman `double`'dı.
HLS bunu tam bir çift duyarlıklı transandantal birim olarak sentezledi:

| `sin_or_cos_double` tek örnek | DSP | LUT | FF |
|---|---:|---:|---:|
| | **85** | 6.364 | 5.562 |

220 DSP'nin 85'i tek bir sinüs/kosinüs birimine gidiyordu.

**Çözüm.** 8192 girdilik sabit-nokta sinüs tablosu
([scripts/gen_trig_lut.py](../scripts/gen_trig_lut.py) üretiyor). Tablo derleme
zamanında sabittir; HLS onu ROM olarak yerleştirir ve hiçbir aritmetik birim
sentezlemez.

İki tasarım ayrıntısı:

- **Tek tablo yeter.** `cos(x) = sin(x + π/2)` olduğu için kosinüs aynı
  tablodan indeks kaydırmayla okunur. Tablo yarıya iner **ve** kadran/işaret
  mantığının ince hataları hiç doğmaz — iki okuma da aynı tablodan.
- **13 bit indeks.** Faz akümülatörü 18 bit; alttaki 5 bit atılır. Bedel
  önceden ölçüldü: 12 bit → 0,999950, 14 bit → 0,999998 fidelity. 13 bit
  ikisinin arasında ve H eşiğini (≥0,999) rahat geçiyor.

**Sonuç**: DSP %153 → **%70**. Fidelity 0,999978359 → 0,999978179 (ihmal
edilebilir).

**Ama**: zamanlama hiç değişmedi ve gecikme sadece %5 düştü. Trig yalnızca DSP
yiyormuş — ne kritik yoldaydı ne de gecikmenin kaynağıydı.

---

## Düzeltme 2 — Seri bağımlılığı kırmak (Gray-kod DEĞİL)

**Sorun.** `apply_cost_layer` toplam gecikmenin %70'iydi. İlk teşhisim "genlik
başına 136 terim çok fazla"ydı ve plan Gray-kod önermişti (136 → 16 terim).

**Ölçüm başka bir şey söyledi.** Sorun terim *sayısı* değil, `acc` üzerindeki
**seri bağımlılıktı**: iç döngüler kapalıyken HLS dış döngüyü boru hattına
alamıyordu. 136 terim bile paralel bir toplama ağacı olarak II=1 ile
işlenebilir.

**Çözüm.** İç döngülere `#pragma HLS UNROLL`, dış döngüye `PIPELINE II=1`.

**Sonuç**: gecikme 337.838.521 → **4.457.934** çevrim (**76×**).

**Bedeli**: LUT %153 → **%359**. Klasik alan/gecikme takası.

> **Ders**: "çok terim var" ile "seri bağımlılık var" farklı teşhislerdir ve
> farklı çözümler ister. Gray-kod ilkini çözerdi; sorun ikincisiydi.

---

## Çıkmaz 1 — II gevşetme (ÖLÇÜLDÜ, İŞE YARAMADI)

Alanı geri kazanmak için II'yi gevşetmek mantıklı görünüyordu: HLS toplayıcıları
paylaştırsın, alan düşsün.

| II | LUT | Gecikme |
|---:|---:|---:|
| 1 | 191.223 | 4.457.934 |
| 4 | 190.726 | 5.244.417 |
| 16 | 190.341 | 8.390.097 |

**Alan %0,5 değişti, gecikme kötüleşti.** HLS `UNROLL` ile örneklenen
toplayıcıları II artınca paylaştırmıyor. Alanı düşürmenin tek yolu **terim
sayısını azaltmak**.

Bu ölçüm bir saat kazandırdı: yanlış yolda ısrar etmek yerine yön değiştirildi.

---

## Düzeltme 3 — İki seviyeli faz ayrıştırması

**Fikir.** Kübitleri ikiye böl: L = {0..7}, H = {8..15}.

```
acc(i) = FL[düşük 8 bit] + FH[yüksek 8 bit] + Σ_{a∈L} s_a · D_a[yüksek 8 bit]
```

Dayanağı, çapraz terimlerin çarpanlara ayrılabilmesi:

```
Σ_{a∈L, b∈H} s_a s_b J[a][b] = Σ_{a∈L} s_a · ( Σ_{b∈H} s_b J[a][b] )
                                              └──── yalnızca YÜKSEK bitlere bağlı ────┘
```

İçteki toplam yalnızca yüksek bitlere bağlı olduğu için **önceden
hesaplanabilir**. Katman başına bir kez 256 girdilik üç tablo kurulur
(`FL`, `FH`, `D`), sonra genlik başına yalnızca 2 tablo okuması + 8 koşullu
toplama kalır.

**136 terim → ~10 terim.** Gray-kod da 136 → 16 yapardı, ama çalışma zamanı bit
indeksi (16 yollu mux) ve permüte edilmiş gezinme getirirdi; bu ayrıştırma hem
daha aza iniyor hem sıralı erişimi koruyor.

**Sonuç**:
- `apply_cost_layer` 98.435.074 → **66.028** çevrim (**1.490×**)
- `expectation_scaled` 38.338.624 → **65.820** çevrim (**582×**), LUT 38.012 → 9.049
- Fidelity **değişmedi** — ayrıştırma matematiksel olarak tam

---

## Düzeltme 4 — Otomatik boru hattını kapatmak (pragma değil, proje ayarı)

**Sorun.** Ayrıştırmadan sonra bile `apply_cost_layer` 81.087 LUT tutuyordu.
Alt modül raporu nedenini gösterdi:

| Alt modül | LUT |
|---|---:|
| `VITIS_LOOP_103_7` | **51.224** |
| `VITIS_LOOP_74/79/90/95` | ~6.600 ×4 |
| **`cost_amp_loop`** (asıl geçiş) | **2.276** |

Asıl genlik döngüsü 2.276 LUT — ayrıştırma mükemmel çalışmıştı. 78.000'i
**tablo kurma döngülerindeydi**, yani katman başına yalnızca 256 kez çalışan
koda gidiyordu.

**İki başarısız deneme.** Önce `UNROLL` pragma'larını kaldırdım — değişmedi.
Sonra `#pragma HLS PIPELINE off` ekledim — sonuçlar **bit-birebir aynı** çıktı.
İkinci denemede pragma'yı etiketle `for` arasına koymuştum (yanlış kapsam);
düzeltip gövdenin içine aldım, yine değişmedi.

**Gerçek neden.** Vitis HLS, tur sayısı 64'ün altındaki döngüleri
**kendiliğinden** boru hattına alır (`config_compile -pipeline_loops`,
varsayılan 64). Bir döngüyü boru hattına alırken iç döngülerini **açmak
zorundadır**. Tablo döngülerimin iç döngüleri 8, 28 ve 64 turluydu — hepsi
eşiğin altında.

Bu bir pragma meselesi değildi, **proje ayarıydı**:

```tcl
config_compile -pipeline_loops 0
```

**Sonuç**: `apply_cost_layer` 81.087 → **8.374 LUT** (10×). FF %156 → **%65**.

**Bedeli**: tablolar artık tamamen seri, gecikme 5,77M → 14,77M. Bu geri
alınabilir — en içteki tablo döngülerine açık `PIPELINE II=1` koymak hiçbir
şeyi açmaz, alan bedeli ~sıfırdır. Henüz yapılmadı.

> **Ders**: bir pragma iki kez denenip sonuç **bit-birebir** aynı çıkıyorsa,
> sorun pragma'da değildir. Aynı şeyi üçüncü kez denemek yerine aracın
> varsayılan davranışına bakmak gerekir.

---

## Düzeltme 5 — Paylaşılan RX birimi: bir hipotezin sınanması

**Sorun.** Kalan 79.383 LUT'un 45.114'ü (%57) **16 ayrı `apply_rx` örneğine**
gidiyordu. Karıştırıcı katmanı `template <int K>` ile açılmış, her kübit için
ayrı bir veri yolu örneklenmişti.

**Neden öyle yapılmıştı.** [research.md R-7](../specs/002-fpga-statevector-cekirdegi/research.md):

> *"HLS, `ARRAY_PARTITION`'lı bir diziye hangi parçadan erişildiğini derleme
> zamanında çözemezse bütün erişimleri seri hale getirir."*

Bu bir **hipotezdi** ve hiç sınanmamıştı. Gerekçe olarak kullanılıp karara
dönüşmüştü.

**Sınama.** Tek bir `apply_rx_dyn(sv, k, cos, sin)` yazıldı; `k` artık normal
bir fonksiyon argümanı.

| | `template<int K>` (16 örnek) | **paylaşılan (çalışma zamanı k)** |
|---|---:|---:|
| LUT | 45.114 | **2.409** |
| DSP | 128 | **8** |
| Toplam gecikme | 14.773.743 | 15.363.498 (**+%4**) |

**16 kat yavaşlama beklenirken %4 oldu.** Hipotez yanlışlandı.

**Sonuç**: LUT %149 → **%42**, DSP %70 → **%16**, FF %65 → **%12**.
**Tasarım ilk kez çipe sığdı.**

> **Ders**: bir hipotezi gerekçe olarak kullanmak, onu doğrulamakla aynı şey
> değildir. R-7 makul bir korkuydu ama sınanmamıştı; sınandığında maliyeti
> 45.000 LUT'luk bir karardı.

Not: bu, onay kapısından geçen **C1 kararını bozmaz**. C1 "kapı listesi derleme
zamanında sabit" diyordu ve o hâlâ geçerli. R-7'de C1'e yanlışlıkla iki ayrı
şey paketlenmişti; değişen, ikincisi.

---

## Neyi yanlış optimize ettim

Faz 2'nin araştırma adımının tamamı — üç bankalama stratejisi, XOR şemaları,
ping-pong, `(i, i XOR 2^k)` çakışma analizi — **eşlemeli kapılar** üzerineydi.

İlk sentez raporu modül modül gecikme verdi:

| Modül | Payı |
|---|---:|
| `apply_cost_layer` | ~%70 |
| `expectation_scaled` | ~%28 |
| 16 × `apply_rx` (**tüm bankalama işi**) | **%0,4** |

"RZZ'yi yerleşik köşegen kapı yap, eşlemeli kapı 12× azalsın" bulgusu
**doğruydu ama performans açısından anlamsızdı**: azaltılan şey zaten ihmal
edilebilirdi. "Köşegen kapı genliği yerinde çarpar, erişim sıralı, sorun yok"
diye geçiştirilen katman ise işin %98'iydi.

**Neden kaçırıldı**: `scripts/banking_analysis.py` yalnızca **bellek erişimini**
sayıyordu. Köşegen katmanın genlik başına 136 seri faz toplaması yaptığını —
yani *aritmetik* maliyetini — model hiç görmüyordu.

> **Ders**: bir performans modeli neyi saymadığını da söylemelidir. Erişim
> sayan bir model, hesabın pahalı olduğu bir tasarımda yanlış yere bakar.

---

## Özet tablo: hangi düzeltme neyi çözdü

| # | Düzeltme | Çözdüğü | Bedeli |
|---|---|---|---|
| 1 | Sabit-nokta sinüs tablosu | DSP %153 → %70 | fidelity −1,8e-7 |
| 2 | İç döngüleri açmak | Gecikme 76× | LUT %153 → %359 |
| — | *II gevşetme* | *hiçbir şey* | *gecikme kötüleşti* |
| 3 | İki seviyeli faz ayrıştırması | cost_layer 1.490×, expectation 582× | +20 BRAM |
| 4 | `config_compile -pipeline_loops 0` | LUT 81k → 8,4k; FF %156 → %65 | gecikme 2,6× |
| 5 | Paylaşılan RX birimi | LUT %149 → %42; DSP %70 → %16 | gecikme +%4 |

---

## Hâlâ açık olanlar

**Zamanlama.** Dokuz turda 25,039 → 24,799 ns. Hedef 10 ns; gerçek ~40 MHz.
Kritik yol dokunulan hiçbir yerde değil ve **henüz araştırılmadı**. NC-4 (Fmax
varsayımı) açık; tüm süre hesapları onun üstünde duruyor.

**Gecikme.** 15.363.498 çevrim @ 40 MHz = **0,384 sn**. CPU tabanı (Aer,
ölçülen ~58 ms) hâlâ **6,6 kat hızlı**. **Hiçbir hızlanma iddiası yapılamaz.**

**Ama durum tersine döndü.** Önceki sorun "sığmıyor"du; şimdiki sorun "yavaş" —
ve elde **%58 LUT, %84 DSP payı** var. Paralelliğe yatırım artık kaynak
açısından mümkün: çevrim başına birden fazla genlik işlenebilir.

Sıradaki üç iş, öncelik sırasıyla:

1. **Zamanlama** — 25 ns'nin kaynağını bul. Tek başına 2,5× kazanç ve NC-4'ü kapatır.
2. **Tablo döngüsü gecikmesi** — en içteki döngülere `PIPELINE II=1`; ~9M çevrim geri gelir, alan bedeli ~sıfır.
3. **Paralellik** — kalan kaynak payını çevrim başına birden fazla genliğe yatır.

---

## Genellenebilir dersler

1. **Fidelity bir kabul ölçütüdür, doğrulama yöntemi değildir.** C-sim %100
   geçerken tasarım çipe sığmıyordu ve CPU'dan 150 kat yavaştı.
2. **Erişim sayan bir performans modeli, hesabın pahalı olduğu tasarımda
   yanlış yere bakar.** Bankalama analizinin tamamı işin %0,4'ünü optimize etti.
3. **"Çok terim var" ile "seri bağımlılık var" farklı teşhislerdir.**
4. **Bir pragma iki kez denenip sonuç bit-birebir aynıysa, sorun pragma'da
   değildir.** Aracın varsayılan davranışına bakılmalıdır.
5. **Hipotezi gerekçe olarak kullanmak, onu doğrulamak değildir.** R-7'nin
   sınanmamış korkusu 45.000 LUT'a mal olmuştu.
6. **`UNROLL` yalnızca sıcak yola uygulanır.** 256 kez çalışan bir döngüyü
   açmak, 65.536 kez çalışan döngü kadar donanım örnekler.

---

# EK — Bütün ölçümler

Her satır gerçek bir çalıştırmadan gelir. Ham dosyalar
[measurements/](measurements/) altında, tarih + git hash + konfig damgalı.

## E.1 — Dokuz sentez turu (tam tablo)

Hedef `xc7z020clg400-1`, saat hedefi 10 ns. Bütçeler: BRAM_18K 280, DSP 220,
FF 106.400, LUT 53.200.

| Tur | Değişiklik | BRAM_18K | DSP | FF | LUT | Gecikme (çevrim) | Zamanlama |
|---|---|---:|---:|---:|---:|---:|---:|
| 1 | başlangıç, `double` trig | 148 (%52) | **337 (%153)** | 90.626 (%85) | **98.627 (%185)** | 355.140.025 | 25,039 ns |
| 2 | trig → sabit-nokta LUT | 141 (%50) | 156 (%70) | 78.286 (%73) | **81.902 (%153)** | 337.838.521 | 25,039 ns |
| 3 | iç döngüler açıldı | 141 (%50) | **284 (%129)** | **210.884 (%198)** | **191.223 (%359)** | **4.457.934** | 25,039 ns |
| 4a | *II = 4 denemesi* | 141 | 284 | 207.147 | 190.726 | 5.244.417 | — |
| 4b | *II = 16 denemesi* | 141 | 284 | 206.435 | 190.341 | 8.390.097 | — |
| 5 | iki seviyeli ayrıştırma (maliyet) | 151 (%53) | 284 (%129) | 211.227 (%198) | 192.047 (%360) | 4.458.579 | 25,039 ns |
| 6 | tablo `UNROLL` kaldırıldı | 151 (%53) | 156 (%70) | 185.671 (%174) | 183.203 (%344) | 5.665.983 | 25,039 ns |
| 7 | iki seviyeli ayrıştırma (beklenti) | 171 (%61) | 156 (%70) | 166.058 (%156) | 154.240 (%289) | 5.766.130 | 25,039 ns |
| 8 | `config_compile -pipeline_loops 0` | 171 (%61) | 156 (%70) | **69.408 (%65)** | 79.383 (%149) | 14.773.743 | 25,039 ns |
| **9** | **paylaşılan RX (çalışma zamanı k)** | **171 (%61)** | **36 (%16)** | **13.391 (%12)** | **22.572 (%42)** | 15.363.498 | 24,799 ns |

Tur 4 iki alt ölçümdür ve **kaynak değiştirmediği için** ayrı tur sayılmaz.

## E.2 — Modül düzeyinde gecikme (tur 2, darboğaz teşhisi)

| Modül | Çevrim | Payı |
|---|---:|---:|
| `apply_cost_layer` | 12.451.842 – 98.435.074 | ~%70 |
| `expectation_scaled` | 8.847.424 – 38.338.624 | ~%28 |
| 16 × `apply_rx` (toplam) | ~1.400.000 | **%0,4** |
| `qir_kernel_Pipeline_init_loop` | 65.538 | %0,02 |

Bankalama araştırmasının tamamı son satırdan bir öncekini hedefliyordu.

## E.3 — Ayrıştırma sonrası modül gecikmeleri (tur 5)

| Modül | Önce | Sonra | Kazanç |
|---|---:|---:|---:|
| `apply_cost_layer` | 98.435.074 | **66.028** | 1.490× |
| `expectation_scaled` | 38.338.624 | **65.820** | 582× |

## E.4 — `apply_cost_layer` iç dağılımı (tur 7, LUT teşhisi)

| Alt modül | LUT |
|---|---:|
| `VITIS_LOOP_103_7` (tablo) | **51.224** |
| `VITIS_LOOP_95_6` (tablo) | 6.671 |
| `VITIS_LOOP_79_3` (tablo) | 6.614 |
| `VITIS_LOOP_74_1` (tablo) | 6.546 |
| `VITIS_LOOP_90_4` (tablo) | 6.546 |
| **`cost_amp_loop` (asıl geçiş)** | **2.276** |
| `mul_64ns_66ns_129_5_1` | 256 (+16 DSP) |

Asıl geçiş 2.276; geri kalan ~78.000 yalnızca 256 kez çalışan tablo kodunda.

## E.5 — Üst seviye LUT dağılımının evrimi

| Modül | Tur 6 | Tur 7 | Tur 8 | Tur 9 |
|---|---:|---:|---:|---:|
| `apply_cost_layer` | 81.087 | 81.087 | 8.374 | 8.374 |
| 16 × `apply_rx` | 45.114 | 45.114 | 45.114 | **2.409** (tek birim) |
| `expectation_scaled` | 38.012 | 9.049 | ~7.900 | ~7.900 |
| Multiplexer (üst seviye) | 18.033 | 18.033 | 18.033 | küçüldü |
| `init_loop` | 76 | 76 | 76 | 76 |

## E.6 — II ölçümleri (SC-003, tur 2)

| k | Çevrim | **Ölçülen II** | Aritmetik tahmin |
|---:|---:|---:|---:|
| 0 | 32.774 | **1** | 1 ✅ |
| 1 | 65.538 | **2** | 1 ❌ |
| 2 | 65.538 | **2** | 1 ❌ |
| 3 | 32.774 | **1** | 1 ✅ |
| 4–15 | 98.310 | **3** | 2 ❌ |

Hepsi SC-003'ün ≤ 4 sınırının altında. Model yönü doğru, büyüklüğü tutarsız.

## E.7 — C-simülasyon fidelity (SC-001)

`ap_fixed<18,1,AP_RND_CONV,AP_SAT>`, faz 18 bit, trig LUT 13 bit.

| n | p | Referans | Kapı | Fidelity | M (≥0,99) | H (≥0,999) |
|--:|--:|---|--:|---:|:-:|:-:|
| 8 | 2 | sentetik | 209 | 0,999999871 | ✅ | ✅ |
| 12 | 2 | sentetik | 457 | 0,999998860 | ✅ | ✅ |
| 16 | 1 | TSP (Faz 1) | 300 | 0,999989167 | ✅ | ✅ |
| 16 | 2 | TSP (Faz 1) | 584 | 0,999978179 | ✅ | ✅ |

Trig LUT'a geçmeden önce n=16 p=2 için 0,999978359 idi; bedel **1,8e-7**.

## E.8 — Mock doğrulaması (T040)

| Yol | Fidelity (n=16, p=2) |
|---|---:|
| Vitis csim, **gerçek** `ap_fixed` | 0,999978359 |
| WSL g++, **mock** `ap_fixed` | 0,999978359 |

Dokuz hanede birebir. Ayrıca C++ çıktısı bağımsız bir NumPy uygulamasına karşı
**bit düzeyinde** kıyaslandı: n=8/12/16'da üçünde de 0 farklı genlik.

## E.9 — `ap_fixed` kip seçimi

| Kuantalama | Normalizasyon | Fidelity | H |
|---|---|---:|:-:|
| **AP_RND_CONV + AP_SAT** | her kapıda | **0,999917** | ✅ |
| **AP_RND_CONV + AP_SAT** | yok | **0,999917** | ✅ |
| AP_TRN + AP_SAT *(Vitis varsayılanı)* | her kapıda | 0,997417 | ❌ |
| AP_TRN + AP_SAT *(Vitis varsayılanı)* | yok | 0,999607 | ✅ |
| AP_RND_CONV + AP_WRAP *(varsayılan)* | her kapıda | 0,999917 | ✅ |
| AP_RND_CONV + AP_WRAP *(varsayılan)* | yok | 0,999917 | ✅ |

İki karar: yuvarlama şart (kırpma hatayı ~5× büyütüyor), ve **kapı başına
yeniden normalizasyon gereksiz** — donanımda tam geçiş + ters karekök maliyeti
hiç ödenmeyecek.

`AP_WRAP` fark göstermedi ama ölçüm tehlikeli durumu uyandırmıyor: emülasyon
başlangıç durumunu kuantalamıyor, donanım ise onu belleğe yazar. `|0…0⟩`'ın
genliği tam 1,0 ve Q1.17 aralığı `[-1, 1)`.

## E.10 — Faz akümülatörü bit genişliği

| Bit | Çözünürlük (rad) | Fidelity |
|---:|---:|---:|
| 12 | 1,534e-03 | 0,999950 |
| 14 | 3,835e-04 | 0,999998 |
| 16 | 9,587e-05 | 0,9999999 |
| **18** | **2,397e-05** | **0,999999995** |
| 20 | 5,992e-06 | 1,000000 |
| 24 | 3,745e-07 | 1,000000 |
| 32 | 1,463e-09 | 1,000000 |

## E.11 — Sayı formatı taraması (p=2, 584 kapı)

| Format | Toplam bit | Fidelity | M | H | BRAM36 (yerinde) |
|---|---:|---:|:-:|:-:|---:|
| Q1.11 | 12 | 0,714527 | ❌ | ❌ | 64 |
| Q1.13 | 14 | 0,978861 | ❌ | ❌ | 64 |
| Q1.15 | 16 | 0,998674 | ✅ | ❌ | 64 |
| **Q1.17** | **18** | **0,999917** | ✅ | ✅ | **64** |
| Q1.19 | 20 | 0,999995 | ✅ | ✅ | 128 |
| Q1.23 | 24 | 0,99999998 | ✅ | ✅ | 128 |
| float32 | 32 | 1,0 (referans) | ✅ | ✅ | 128 |

Q1.11–Q1.17 **aynı** blok sayısını kullanır (hepsi tek 36-bit kelimeye sığar);
daralmanın BRAM karşılığı yoktur.

## E.12 — CPU referans tabanı

| Taban | p=1 | p=2 medyan | p=2 en iyi |
|---|---:|---:|---:|
| Qiskit `Statevector` (Python) | ~975 ms | ~1.585 ms | — |
| **Aer statevector (C++)** | ~42 ms | ~78 ms | **~58 ms** |

Aradaki 20 kat, taban seçiminin sonucu 20 kat şişirebileceği anlamına gelir.
Adil taban Aer'dir. Ölçüm gürültülüdür (p=2'de 66–981 ms arası tek koşumlar
görüldü); Faz 10 kıyası çok tekrarlı olmalı ve yayılımı raporlamalıdır.

## E.13 — Bankalama analizi (HESAPLANAN, sentez öncesi)

16 banka, çift portlu BRAM. Verim = çevrim başına işlenen genlik çifti.

| Şema | Tamponlama | En kötü k | En iyi k | Tavan |
|---|---|---:|---:|---:|
| naif (düşük bitler) | yerinde | 4 | 8 | 8 |
| XOR (2 parça) | yerinde | 4 | 8 | 8 |
| XOR (tam katlama) | yerinde | 4 | 8 | 8 |
| naif | ping-pong | 16 | 16 | 16 |
| XOR (2 parça) | ping-pong | 16 | 16 | 16 |
| XOR (tam katlama) | ping-pong | 16 | 16 | 16 |

Üç şema **birebir aynı**; şema seçimi fark etmiyor. Parçalanma: F ≤ 64 bedava
(65536/F ≥ 1024), F > 64'te blok sayısı katlanıyor.

⚠️ Bu tablo yalnızca **bellek erişimini** sayar. E.2 gösterdi ki asıl maliyet
aritmetiktedir ve bu model onu görmez.

## E.14 — Devre profili (yerleşik vs ayrıştırılmış)

| p | Qiskit'in ayrıştırdığı | bundan eşlemeli | Yerleşik | bundan eşlemeli |
|--:|--:|--:|--:|--:|
| 1 | 300 | 200 | 116 | 16 |
| 2 | 584 | 384 | **232** | **32** |
| 3 | 868 | 568 | 348 | 48 |

Maliyet operatörü: 100 Pauli terimi (16 ağırlık-1, 84 ağırlık-2), **hepsi
köşegen**. Yerleşik RZZ ile eşlemeli kapı 12× azalıyor — doğru ama E.2'ye göre
performans açısından anlamsız.
