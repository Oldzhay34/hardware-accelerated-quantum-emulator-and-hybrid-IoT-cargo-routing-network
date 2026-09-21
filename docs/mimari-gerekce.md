# Mimari Gerekçelendirme — Hızlandırıcı Hedefi Seçimi

**Oluşturma**: 2026-09-21 · **Kapsam**: bu belge bir *argüman* belgesidir,
ölçüm kaydı değildir. Her nicel iddia ya `docs/measurements/` altındaki bir
dosyaya işaret eder ya da **açıkça türetim/tahmin** olarak etiketlenir.

---

## §0. Yöntem ve üç premis düzeltmesi

Bu analiz üç etiket kullanır ve her iddia bunlardan **birini** taşır:

| Etiket | Anlamı |
|---|---|
| **[Ö]** | Ölçüldü — kaynak dosya verilir |
| **[T]** | Türetildi — ölçülen değerlerden hesap, varsayımlar açık yazılır |
| **[?]** | Kurulmadı — gerekçelendirmede **kullanılamaz** |

Analize başlamadan önce, bu projede yaygın olarak varsayılan üç önermeyi
kendi verimize karşı denetledim. **Üçü de düzeltme gerektiriyor.** Bunları
gizlemek yerine öne almak, geri kalanın güvenilirliğini kurar.

### Premis 1 — *"Tasarım derin boru hattı ve agresif döngü açma kullanıyor"*

**Kısmen doğru, ama kritik nüansla.** İç döngüler gerçekten `PIPELINE II=1`
ile açıkça boru hattına alınmış (`gates_pairing.hpp`, `gates_diagonal.hpp`).
Ancak:

- `config_compile -pipeline_loops 0` — **otomatik** boru hattı kapalı;
  yalnızca elle işaretlenenler boru hattında.
- `sv` dizisinin bölümlenmesi `cyclic factor = **2**`, 16 değil.
- Döngü açma **denendi ve elendi**: tablo içlerini `UNROLL` etmek gecikmeyi
  5,38M → **10,21M çevrime çıkardı** — iki kat *yavaşlattı*
  ([faz2-sentez.md](measurements/faz2-sentez.md) varyant 9). **[Ö]**

Yani "agresif mekânsal açılım" bu tasarımın özelliği **değildir**; ölçümle
**reddedilmiştir**. Savunmada aksini söylemek, kendi ADR'mizle çelişmek olur
([ADR 0009](decisions/0009-paralellik-turu-kapatildi.md)).

### Premis 2 — *"18-bit aritmetik DSP48'in 18×25 MAC'ine birebir oturuyor, sıfır artık mantık"*

⛔ **Bu, bizim tasarımımız için YANLIŞ.** Ölçülen kaynak dağılımı:

```
LUT: 22.535 (%42,4)     FF: 19.466 (%18,3)
DSP:     33 (%15,0)     BRAM: 187 (%67)      SRL: 600
```
**[Ö]** `artifacts/ip/export_impl_20260917_15931cc.rpt`

DSP kullanımı **%15**. Eğer 18-bit genlik aritmetiği DSP48E1'lere oturuyor
olsaydı DSP baskın kaynak olurdu. Üstelik implementasyon raporu, kullanılan
DSP'lerin nerede olduğunu adıyla söylüyor:

```
grp_apply_cost_layer_fu_184/mul_64ns_66ns_129_4_1_U70/...  MULT.dsp.DSP48E1
```

Bu bir **64×66 → 129 bit** çarpma — maliyet katmanının **tablo kurulumunda**,
genlik aritmetiğinde değil. Genlik aritmetiği LUT'larda.

**Doğru argüman DSP'de değil, BELLEKTE.** Ayrıntı: §4.

### Premis 3 — *"Pareto optimizasyonu 18 biti optimum eşik olarak verdi"*

**Yarısı doğru.** Pareto **eğrisi henüz yok**. Elde olan, eğrinin iki **uç
kısıtı**:

- Doğruluk tabanı: Q1.15 H eşiğinde kalıyor (0,998674), Q1.17 geçiyor
  (0,999917) **[Ö]**
- Donanım tavanı: BRAM36 kelime genişliği 36 bit; 2×18 tam oturuyor **[Ö]**

Her genişlikte **donanım maliyeti** ölçülmedi — görev olarak var (Phase 6C,
T070–T073) ama **kapsam dondurulmuş** durumda. Bu belgede "Pareto eğrisi
gösterdi ki..." denemez; "iki bağımsız kısıt aynı noktada kesişiyor"
denebilir. **[?]** → eğri.

---

## §1. İş yükünün mimari imzası

Gerekçelendirme, iş yükünün ne olduğunu saymadan yapılamaz.

| Nicelik | Değer |
|---|---|
| Genlik sayısı | 2¹⁶ = **65.536** |
| Genlik temsili (FPGA) | 2 × Q1.17 = **36 bit** → çalışma kümesi **288 KiB** |
| Genlik temsili (Aer, complex128) | 2 × 64 bit = 128 bit → çalışma kümesi **1,00 MiB** |
| Karıştırıcı: çift güncellemesi / katman | 16 kübit × 32.768 çift = **524.288** |
| p=2 toplam çift güncellemesi | **1.048.576** |
| Köşegen katman: genlik güncellemesi | 2 × 65.536 = **131.072** |
| Ölçülen gecikme (p=2) | **3.728.217 çevrim** @ 100 MHz = **37,28 ms** **[Ö]** *(sentez sonrası; kartta henüz doğrulanmadı)* |

**Erişim deseni** — mimari olarak belirleyici olan budur. Karıştırıcı, kübit
*k* için `i` ve `i ⊕ 2ᵏ` genliklerini eşler. Adım uzunluğu **2ᵏ**, yani
*k* büyüdükçe iki erişim arasındaki mesafe 1'den 32.768'e kadar çıkar.

Bu, klasik bir FFT kelebeğinin erişim desenidir ve iki sonucu vardır:

1. Yerinde güncellemede çift başına **dört** bellek erişimi gerekir:
   `oku i`, `oku i′`, `yaz i`, `yaz i′`.
2. Yüksek *k* için iki erişim, bölümlenmiş bir dizide **aynı bankaya** düşer
   (çünkü `i mod F` ve `(i ⊕ 2ᵏ) mod F`, `2ᵏ > F` iken eşittir).

§3'ün tamamı bu iki maddenin sonucudur.

---

## §2. Aşama 1 — FPGA vs. CPU: ölçülen başabaşın mimari açıklaması

### 2.1 Ölçülen sonuç

| | Gecikme | Verim [T] |
|---|---|---|
| FPGA (sentez tahmini) | **37,28 ms** | 28,1 M çift/s |
| CPU turbo | **32,75 ms** | 32,0 M çift/s |
| CPU plato | **41,93 ms** | 25,0 M çift/s |

**[Ö]** CPU: [faz2-sentez.md §18](measurements/faz2-sentez.md), 19 Eylül temiz ölçüm.

FPGA, CPU'nun turbo ve plato değerlerinin **arasına** düşüyor.

⛔ **Bu tablo aşıldı — §2.2'ye bakın.** Buradaki CPU rakamları **Qiskit Aer**'e
aittir ve o taban ~10× adil değildir. Aynı algoritma konak CPU'da **3,273 ms**
sürüyor. Tablo, Faz 2'nin ne ölçtüğünü göstermek için bırakıldı.

### 2.2 ⛔ DÜZELTME (2026-09-21): başabaş sonucu zayıf tabandan geliyordu

Bu bölüm önce *"35× mimari üstünlük, 40× saat dezavantajı, sadeleşiyor,
başabaş"* diyordu. **Girdisi yanlıştı.** §2.4'te "geçerliliğe yönelik gerçek
tehdit" diye işaretlenen şey ölçüldü ve gerçekleşti.

**Deney**: aynı çekirdek kodu (`hls/tb/bench_kernel.cpp`, `qir_kernel`
çağrısı) konak CPU'da zamanlandı. **[Ö]**
[adil-cpu-tabani](measurements/adil-cpu-tabani_20260921_c504294.json)

| Taban | Medyan | FPGA'ya göre |
|---|---:|---|
| **Aynı kod, yerel `float`** | **3,273 ms** | **CPU 11,4× hızlı** |
| Aynı kod, Q1.17 (taklit, `double` aritmetik) | 12,992 ms | CPU 2,9× hızlı |
| Qiskit Aer (Faz 2 tabanı) | 32,750 ms | CPU 1,14× hızlı → *"başabaş"* |
| FPGA (sentez tahmini) | 37,28 ms | — |

**Aer tabanı ~10× adil değildi.** Sebep §2.4'te yazılıydı: Aer, RZZ'yi
CX-RZ-CX olarak ayrıştırıp p=2'de **384 kapı** uygularken bizim çekirdek
köşegen operatörün tamamını **32 geçişe** füzyonluyor.

### Düzeltilmiş çevrim başına ayrıştırma

```
FPGA :  3.728.217 çevrim / 1.048.576 çift  ≈  3,56 çevrim/çift   [Ö]
CPU  :  4,0 GHz / 320,4 M çift/s           ≈ 12,5  çevrim/çift   [T]
```

| | |
|---|---|
| Mimari üstünlük (çevrim başına) | **3,5×** FPGA lehine — *35× değil* |
| Saat frekansı | **40×** CPU lehine |
| **Net** | **11,4× CPU lehine** |

Model, ölçümü yine birebir öngörüyor (40 / 3,5 = 11,4). **Değişen model
değil, girdisiydi.** Mekânsal hesaplamanın çevrim başına kazancı gerçektir —
ama bu iş yükünde **3,5 kat**, ve 100 MHz'lik bir saat bunu taşımaya yetmez.

⚠️ CPU satırı sürdürülen çekirdek frekansı için **4,0 GHz varsayar**;
ölçülmedi.

### 2.5 PS↔PL — doğru taban ve ölçülen hızlanma **[Ö]**

Dizüstü karşılaştırması *"dizüstüm yerine PYNQ mı alsam"* sorusunu cevaplar;
mimari olarak anlamsızdır. SoC hızlandırmasında doğru soru **"çekirdeği
PS'ten PL'e taşımak neye değer?"**dir. Ölçüldü (görev T045b):
[ps-pl-hizlanma](measurements/ps-pl-hizlanma_20260921_c504294.json)

| Platform | Gecikme | M çift/s | Saat | **çevrim/çift** | FPGA'ya göre |
|---|---:|---:|---:|---:|---|
| **FPGA (PL)** | 37,28 ms | 28,1 | 100 MHz | **3,56** ← en verimli | — |
| **ARM Cortex-A9 (PS)** | **84,13 ms** | 12,5 | 650 MHz | 52,2 | **FPGA 2,26× hızlı** |
| Dizüstü i7 | 3,27 ms | 320,4 | ~4 GHz | 12,5 | CPU 11,4× hızlı |

> **Çekirdeği PS'ten PL'e taşımak 2,26× hızlandırıyor** — aynı SoC, aynı güç
> zarfı, aynı kutu. *"Donanım hızlandırmalı"* ifadesinin ölçülmüş dayanağı
> budur ve **tek** dayanağıdır.

**Model üçüncü kez tutuyor**: ARM'a karşı mimari üstünlük 14,7×, saat
dezavantajı 6,5× → net **2,26×**. Üç platformda da aynı ayrıştırma çalışıyor.

**Asıl mimari bulgu tabloda**: FPGA, üç platformun **en verimlisi** —
çevrim başına 3,56, ARM'ın 14,7 katı, i7'nin 3,5 katı. Sonucu belirleyen
mimari değil **saat frekansıdır**. 100 MHz, 650 MHz'i yenmeye yeter; 4 GHz'i
yenmeye yetmez. Krossover tam olarak buradadır.

⚠️ **Q1.17 taklit varyantı hızlanma iddiasında KULLANILMAZ.** Kartta 1579 ms
ölçüldü (42×) ama bu sayı sahtedir: `ap_fixed_mock` her işlemi `double`'da
yapar ve Cortex-A9'un NEON'u çift duyarlık **desteklemez**. Float varyantından
**18,8× yavaş** olması bir mimari gerçek değil, taklit sınıfın artefaktıdır.
Yalnız float varyantı raporlanır.

⚠️ Jitter farkı beklenenden **küçük**: ARM 30 koşumda 1,244 ms yayılım
(%1,5). Yüksüz gömülü Linux oldukça belirlenimci. §2.3'teki jitter argümanı
bu veriyle **zayıftır**.

### 2.3 Bellek duvarı argümanı n=16'da GEÇERLİ DEĞİL

Yaygın gerekçelendirme şöyle kurulur: *"CPU bellek hiyerarşisinde boğulur,
FPGA her şeyi çip içinde tutar."* **Bu ölçekte bu argüman yanlıştır** ve
kurulursa ilk soruda çöker:

```
Aer statevector (complex128) = 65.536 × 16 B = 1,00 MiB
```

Modern bir dizüstü P-çekirdeğinin L2'si 1,25–2 MiB, L3'ü 24 MiB
mertebesindedir. **Statevector L2'ye sığar.** CPU da bu hesap boyunca DRAM'e
gitmez.

Yani FPGA'nın "sıfır çip-dışı trafik" özelliği **gerçektir ama n=16'da
ayırt edici değildir** — çünkü rakip de çip-dışına çıkmıyor. Bu özellik,
çalışma kümesi son seviye önbelleği aştığında (n ≳ 21–22, complex128 ile
≳ 32 MiB) ayırt edici olmaya başlar. Orada değiliz.

⚠️ Yüksek *k* için CPU'nun erişimi 512 KiB uzaklıkta bir adımla gerçekleşir;
bu, L1 ve TLB açısından düşmanca bir desendir ve CPU'nun 12,5 çevrim/çift
değerinin bir kısmını açıklar. Ama DRAM'e çıkmaz — **önbellek içi** bir
maliyettir. **[T]**

### 2.4 ⚠️ Geçerliliğe yönelik gerçek tehdit: taban Qiskit Aer'dir

Bu, belgenin en dürüst olması gereken yeridir.

Çekirdeğimiz, QAOA maliyet operatörünün **100 Pauli teriminin tamamını tek
bir köşegen geçişe füzyonluyor**. Qiskit ise RZZ'yi CX-RZ-CX olarak
ayrıştırıyor; p=2'de eşlemeli kapı sayısı **384'e** karşı bizim **32**
([gates_diagonal.hpp](../hls/src/gates_diagonal.hpp)). **12× algoritmik
fark.** **[Ö]**

Bu fark **donanım değil, algoritma** farkıdır. Elle füzyon yapan bir CPU
çekirdeği yazılsaydı CPU tarafı da hızlanırdı.

> ⛔ **BU TEHDİT GERÇEKLEŞTİ (2026-09-21).** Ölçüldü: aynı algoritma konak
> CPU'da **3,273 ms**, Aer ise 32,75 ms — **~10× fark**, tam da öngörülen 12×
> kapı farkı mertebesinde. Faz 2'nin *"gecikmede başabaş"* sonucu bir
> **taban artefaktıydı**. Adil tabanla dizüstü CPU, FPGA'dan **11,4× hızlıdır**.
>
> Bu, Faz 2'nin fidelity ve eşdeğerlik sonuçlarını etkilemez — yalnız
> **gecikme karşılaştırmasını** geçersiz kılar.

---

## §3. Bağlayıcı kısıt: bellek portu — ölçülmüş bir mimari sonuç

Bu bölüm, projenin en güçlü **ölçülmüş** mimari bulgusudur.

### 3.1 Deney

`sv` dizisinin `cyclic` bölümlenme faktörü ve bellek tipi süpürüldü.
Tam tablo: [faz2-sentez.md](measurements/faz2-sentez.md) §Tur 17. **[Ö]**

| # | Konfigürasyon | Çevrim | DSP | LUT | **rx II** |
|---|---|---:|---:|---:|:---:|
| 0 | `RAM_2P`, cyclic 2 | 6.948.095 | %16 | %84 | **3** |
| 1 | `RAM_2P`, cyclic **4** | 6.948.095 | %16 | %86 | 3 |
| 2 | `RAM_2P`, cyclic **8** | 6.948.240 | %16 | %90 | 3 |
| **3** | **`RAM_T2P`, cyclic 2** | **5.375.327** | %16 | %84 | **2** |
| 4 | `RAM_T2P`, cyclic **4** | 5.375.327 | %16 | %86 | 2 |
| 5 | `RAM_T2P`, cyclic **8** | 5.375.328 | %16 | %90 | 2 |

### 3.2 Okuma

**Bankalama faktörünü 2 → 4 → 8 katlamak gecikmeyi HİÇ değiştirmedi**
(5.375.327 → 5.375.327 → 5.375.328 çevrim: fark **bir** çevrim), buna karşılık
LUT'u %84'ten %90'a çıkardı. Dört katı banka, **sıfır** kazanç.

**Bellek tipini `RAM_2P` → `RAM_T2P` yapmak** — tek kelimelik bir değişiklik —
II'yi 3'ten 2'ye, gecikmeyi **%22,6** düşürdü ve **kaynak maliyeti sıfırdı**.

### 3.3 Mekanizma

`RAM_2P` **basit çift port**tur: bir okuma + bir yazma. `RAM_T2P` **gerçek
çift port**tur: iki bağımsız oku/yaz. Yerinde kelebek çift başına **dört**
erişim istiyor (§1). Dolayısıyla:

```
II_alt_sınır = (erişim / çift) / (port / çevrim)
RAM_2P  :  4 / 1 okuma+1 yazma  →  II = 3   (ölçülen: 3) ✓
RAM_T2P :  4 / 2 port           →  II = 2   (ölçülen: 2) ✓
```

Model, ölçümü **iki konfigürasyonda da** birebir öngörüyor.

**Bankalamanın neden işe yaramadığı**: `cyclic` bölümlenmede `i` bankası
`i mod F`'tir. Kelebek `i` ile `i ⊕ 2ᵏ`'yi eşler. `2ᵏ ≥ F` olan her kübit
için bu iki indeks **aynı bankaya** düşer. Döngü tüm *k* değerleri üzerinde
tek biçimlidir, dolayısıyla boru hattı II'si **en kötü k**'ye göre belirlenir.
Banka eklemek en kötü durumu düzeltmez; yalnız **port** eklemek düzeltir.
BRAM'in portu ikiden fazla olmadığına göre **II=2 bu mimaride donanımsal
tabandır**.

### 3.4 Sonuçları

1. Tasarım **hesap-bağlı değil, bellek-portu-bağlıdır.** DSP %15'te boşta
   durması bunun doğrudan göstergesidir.
2. Bu yüzden *"daha fazla paralellik satın al"* yolu **kapalıdır** — ve
   kapalı olduğu tahminle değil **ölçümle** gösterilmiştir
   ([ADR 0009](decisions/0009-paralellik-turu-kapatildi.md)).
3. Ve bu yüzden 18-bit argümanı **çarpıcılarda değil, bellekte** aranmalıdır.

---

## §4. Aşama 2 — 18 bit: silikonun doğal tanecikliği

### 4.1 İki bağımsız kısıt, tek nokta

**Yukarıdan — doğruluk** **[Ö]**:

| bit | format | fidelity | H (≥0,999) |
|---|---|---|---|
| 14 | Q1.13 | 0,978861091 | ❌ |
| 16 | Q1.15 | 0,998674120 | ❌ |
| **18** | **Q1.17** | **0,999917032** | ✅ |
| 20 | Q1.19 | 0,999994814 | ✅ |

**Aşağıdan — donanım** **[Ö]** ([memory-budget.md](memory-budget.md)):

Zynq-7'deki BRAM36 bloğunun **azami kelime genişliği 36 bittir**. Bir genlik
`{re, im}` = 2 × 18 = **tam 36 bit**.

| Hassasiyet | bit/genlik | Kelime | İsraf bit |
|---|---:|---|---:|
| Q1.13 | 28 | sığar | 8 |
| Q1.15 | 32 | sığar | 4 |
| **Q1.17** | **36** | **tam** | **0** |
| Q1.19 | 40 | ❌ taşar → **ikinci blok** | — |

> **18, doğruluğu sağlayan en dar genişlik ile BRAM kelimesine sıfır israfla
> oturan en geniş genişliğin kesişimidir.** Altında doğruluk yetmiyor,
> üstünde bellek maliyeti iki katına çıkıyor.

Bu, tesadüf değildir. 36 = 2 × 18 ve DSP48E1'in çarpan portu **25 × 18**:
Xilinx'in bu ailedeki taneciklik seçimi 18 bittir. **Sabit noktalı sinyal
işleme için silikonun doğal birimi 18 bittir** ve bizim doğruluk tabanımız
tam oraya düşmüştür.

### 4.2 Dürüst sınırlama: bizim tasarımımız DSP tarafını kullanmıyor

Q1.17 × Q1.17, tek bir DSP48E1'e (25×18) sığar ve 25-bit portun 7 biti boşta
kalır. Yani **prensip olarak** 18-bit, bu silikonun çarpanına da oturur.

Ancak bizim tasarımımızda genlik aritmetiği **LUT'lardadır**, DSP kullanımı
%15'tir ve o DSP'ler de maliyet katmanının tablo kurulumundaki 64×66'lık
çarpmada kullanılmaktadır (§0, Premis 2). **[Ö]**

Sebebi §3'tedir: tasarım bellek-portu-bağlıdır, çarpan-bağlı değildir. HLS,
darboğaz bellekteyken çarpanları DSP'ye taşımak için bir sebep görmemiştir.

> **Savunmada söylenecek olan**: *"18 bit, bu silikonun bellek kelimesine
> sıfır israfla oturur ve doğruluk tabanımız tam oraya düşer."*
> **Söylenmeyecek olan**: *"18 bit DSP48'e birebir oturduğu için %100 silikon
> verimliliği sağlıyor."* İkincisi bizim kaynak tablomuzla çelişir.

### 4.3 GPU'da bu nokta yoktur

GPU aritmetik menüsü ayrıktır: INT8 / FP16 / BF16 / TF32 / FP32 / FP64.
**18-bit yerel bir ALU yoktur** ve "bellek kelimesine hizalama" diye bir
tasarım değişkeni yoktur.

Bir GPU'da 18-bit emülasyonu, INT32 üzerinde maskeleme ve kaydırma ile
yapılırdı: her işlem başına ek AND/SHIFT komutları, doyurma ve yakınsak
yuvarlama için dallanma veya seçim komutları. Bu, **aritmetik yoğunluğu
düşürür ve komut sayısını artırır** — yani 18 bite inmenin GPU'da bir
*kazancı olmaz*, aksine maliyeti vardır. GPU'da aşağı inmenin tek verimli yolu
FP16'dır ve o da 18 bit değildir. **[T]**

Ve asıl nokta: GPU'nun doğal formatı olan **FP32, bu çipe sığmaz** —
64 bit/genlik, ping-pong tamponlamayla BRAM'in %162'si. **[Ö]**

> Bu tasarım, **18 bit seçilebildiği için var olabiliyor.**

⚠️ **Aşırı iddia yasağı**: *"18-bit sabit nokta FP16'dan daha doğrudur"*
**denmez**. FP16'nın üssü vardır ve küçük genliklerde bağıl hassasiyeti daha
iyi olabilir. Savunulabilir iddia doğruluk üstünlüğü değil, **ifade
edilebilirlik ve sığma**dır. **[?]** → FP16 doğruluk karşılaştırması.

---

## §5. Aşama 2 — FPGA vs. GPU: dürüst nicel akıl yürütme

⚠️ **Bu bölümün tamamı [T]/[?]'dir.** GPU ölçülmedi
(`available_devices() == ('CPU',)`). Görev olarak var (Phase 6B, T064–T069).

### 5.1 İşgal (occupancy) analizi

Bir kübitin karıştırıcı geçişi **32.768 bağımsız çift** üretir. RTX 4060'ta
3.072 CUDA çekirdeği vardır → çekirdek başına **~11 çift**. Bir GPU için bu,
tek bir dalga bile değildir; kitlesel paralellik makinesi **birkaç yüzde**
işgalle çalışır.

Dahası, kapı başına bir çekirdek (kernel) başlatması gerekir:
p=2'de 32 kapı × ~5–10 µs başlatma ek yükü ≈ **160–320 µs** — ve asıl hesap
bunun yanında küçüktür. Yani GPU koşumu **başlatma ek yükü baskın** olur.

### 5.2 Ama sonuç yine de GPU lehinedir

Burada dürüst olmak gerekir: **başlatma ek yükü baskın ve %3 işgalle çalışan
bir GPU bile 37,28 ms'yi büyük farkla yener.** Kaba mertebe: birkaç yüz
mikrosaniye, yani **~100×**. **[T]**

> Yani *"GPU düşük batch'te atıl kalır"* önermesi **doğrudur** ama
> **"dolayısıyla FPGA kazanır"** sonucu **yanlıştır**. GPU, atıl hâldeyken
> bile hızlıdır. Bu zinciri kuran bir savunma, ilk ölçümde çöker.

Doğru çerçeve hız değil **verimliliktir**: birim güç veya birim silikon
başına iş. Ve o eksen **henüz ölçülmemiştir** — FPGA enerjisi bilinmiyor.
**[?]**

### 5.3 GPU'nun yapısal olarak yapamadığı şey

Ölçüm gerektirmeyen tek mimari fark: **GPU'nun G/Ç'si yoktur.** Bir konak
makine, PCIe, sürücü yığını ve işletim sistemi gerektirir. Bizim düğümümüz
aynı kutuda Linux koşan bir ARM, Ethernet, I2C ve GPIO taşır ve ESP32'lerle
doğrudan konuşur ([sistem-mimarisi.md](sistem-mimarisi.md)). Karşılaştırma
*"FPGA vs GPU"* değil, *"tek kutu"* vs *"GPU + konak sistem"*tir. **[Ö]**
(yapısal; `m_axi` yokluğu ve kart üstü Linux doğrulandı)

---

## §6. Pareto — ne var, ne yok

**Var** **[Ö]**: eğrinin iki uç kısıtı (§4.1) — doğruluk tabanı 18 bit,
BRAM kelime tavanı 18 bit.

**Yok** **[?]**: genişlik → {BRAM, DSP, LUT, II, çevrim, periyot} eşlemesi.
Yani gerçek bir Pareto **eğrisi** elimizde yoktur; iki nokta vardır ve
aralarındaki eğri çizilmemiştir.

Ölçüm görevi tanımlıdır (Phase 6C, T070–T073) ve kapsam dondurulduğu için
MVP'den sonraya bırakılmıştır. Eğri çıkana kadar bu belgede kullanılacak
ifade şudur:

> *"İki bağımsız kısıt aynı genişlikte kesişiyor"* — ✅
> *"Pareto analizi 18 biti optimum olarak verdi"* — ❌ (henüz)

---

## §7. SWaP-C ve kenar uygunluğu

| Boyut | Durum |
|---|---|
| Güç (FPGA) | **[?] ölçülmedi.** Görev: Faz 5 öbek 6 (INA219) |
| Güç (CPU) | **[Ö] 0,644 J/koşum** (batarya delta, 19 Eylül) |
| Perf/Watt karşılaştırması | **[?]** — bir taraf eksikken oran hesaplanamaz |
| Çip-dışı bellek trafiği | **[Ö] sıfır** — arayüzde `m_axi` yok, yalnız `s_axilite` |
| Sistem bütünleşmesi | **[Ö]** kart üstü Linux + Ethernet/I2C/GPIO; konak gerekmez |
| Belirlenimci gecikme | **[Ö]** 3.728.217 çevrim, sabit. ⚠️ Yalnız **artımlı** yolda anlamlı; gecelik toplu işte jitter önemsizdir ([sistem-mimarisi.md §3](sistem-mimarisi.md)) |

> **Perf/Watt üstünlüğü bu belgede iddia EDİLMEZ.** Enerji ölçülene kadar
> Anayasa madde II bunu yasaklar. Sıfır çip-dışı trafik ve düşük güç zarfı
> *mekanizmadır*; sonucu değil.

---

## §8. Bu belgenin iddia ETMEDİKLERİ

Savunmanın sağlamlığı, neyi iddia etmediğini bilmesinden gelir.

| ❌ | Neden |
|---|---|
| FPGA **her şeyden** hızlıdır | Hayır. Dizüstü CPU 11,4× önde. FPGA yalnız **kart üstü ARM'ı** yener — 2,26× (§2.5) |
| 42× hızlanma (Q1.17 taklit tabanı) | Sahte sayı — `double` emülasyonunun artefaktı, mimari fark değil |
| FPGA daha az enerji harcar | Ölçülmedi |
| 18 bit DSP48'e oturduğu için %100 silikon verimi | Kaynak tablosuyla çelişir (DSP %15) |
| Derin boru hattı / agresif unroll kazandırdı | Unroll **ölçümle elendi** (2× yavaşlama) |
| Bellek duvarı FPGA lehine çalışıyor | n=16'da statevector CPU'nun L2'sine sığıyor |
| Pareto eğrisi 18 biti optimum verdi | Eğri henüz çizilmedi |
| FPGA daha çok kübite ölçeklenir | Tam tersi; 16'da BRAM'e sıkışıldı |

---

## §9. Savunulabilir tez — tek paragraf

> Bu iş yükü, n=16'da hiçbir modern işlemcinin bellek hiyerarşisini
> zorlamayacak kadar küçüktür; dolayısıyla hızlandırıcı seçimi bir *hız*
> yarışı değildir — ve bu yarışı **kaybettiğimizi ölçtük**: aynı algoritma
> bir dizüstü CPU'da 3,27 ms, FPGA'da 37,28 ms. Mekânsal mimari çevrim başına
> **3,5 kat** fazla yararlı iş yapar, ama **40 kat** düşük saatle çalışır;
> net sonuç CPU lehine 11,4 kattır. Bu sonucu gizlemiyoruz, **modelle
> açıklıyoruz** — ve yol boyunca Faz 2'nin *"başabaş"* sonucunun zayıf bir
> tabandan (Qiskit Aer'in 12× fazla kapı uygulamasından) kaynaklandığını da
> ölçerek gösterdik. Tasarımın bağlayıcı kısıtı aritmetik değil **bellek
> portudur**: bankalama faktörünü dörde katlamak sıfır kazanç verirken,
> bellek tipini gerçek çift porta çevirmek tek kelimeyle %22,6 kazandırmıştır.
> Aynı bellek-merkezli mantık sayısal genişliği de belirlemiştir: 18 bit,
> doğruluk eşiğini geçen en dar format olmakla kalmaz, BRAM36'nın 36-bit
> kelimesine iki genlik bileşeni hâlinde **sıfır israfla** oturur. Katkımız
> bir hız rekoru değil — hız rekorunun **neden mümkün olmadığının** ölçülmüş
> ve modellenmiş açıklamasıdır.

## İlgili belgeler

- [neden-fpga.md](neden-fpga.md) — savunma özeti; kullanılmayacak argümanlar
- [sistem-mimarisi.md](sistem-mimarisi.md) — FPGA'nın sistemdeki rolü
- [olculen-degerler.md](olculen-degerler.md) — ölçülen her değer, iddia sınırları
- [memory-budget.md](memory-budget.md) — 16 kübit tavanı ve BRAM kelime analizi
- [ADR 0009](decisions/0009-paralellik-turu-kapatildi.md) — paralellik turu ölçümle kapandı
- [faz2-sentez.md](measurements/faz2-sentez.md) — ham ölçüm kaydı
