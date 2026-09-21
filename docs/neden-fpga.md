# Neden FPGA — GPU varken

**Oluşturma**: 2026-09-21 · **Durum**: canlı belge, ölçümler geldikçe güncellenir

Bu belge tek bir soruya cevap verir: *"Makinende RTX 4060 varken bu işi neden
FPGA'da yaptın?"*

Bu, savunmada sorulacak **ilk** sorudur. Zayıf bir cevap, hiç cevap
vermemekten kötüdür — çünkü zayıf argüman sorgulanınca çöker ve geri kalan
her şeyi şüpheli hâle getirir. Bu yüzden belge iki bölümdür: **kullanılacak**
argümanlar ve **kullanılmayacak** olanlar.

---

---

## 0. Aynı sayı, farklı anlam — önce bunu netleştirin

Bu projede aynı sayılar birbirinden **tamamen bağımsız** üç şeyi gösteriyor ve
karışmaları çok kolay. Geliştirme sırasında iki kez karıştı; jüride de karışır.

| Sayı | Ne demek | Nereden geldi | Kod |
|---|---|---|---|
| **16** kübit | Problem boyutu → 2¹⁶ = 65.536 genlik | Prensip III tavanı → 5 şehirlik TSP, (5−1)² = 16 | `N_QUBITS` |
| **16** banka | `cyclic` bölümlenme faktörü | 65536'yı tam böler, parçalanma uçurumu F > 64'te | `BANKS` |
| **18** bit | Her **reel sayının** hassasiyeti | Q1.17 — doğruluk ve BRAM kelimesinin kesişimi | `real_t` |
| **18** bit | Faz çözünürlüğü (TUR cinsinden) | Ayrı ve **bağımsız** karar | `phase_t` |

### "18 bit" kübit sayısı değildir

```cpp
constexpr int N_QUBITS = QIR_N_QUBITS;   // 16    <- KÜBİT SAYISI
constexpr int N_AMP    = 1 << N_QUBITS;  // 65536 <- genlik sayısı

using real_t = ap_fixed<18, 1, ...>;     // 18    <- HER SAYININ HASSASİYETİ
struct amp_t { real_t re; real_t im; };  // 36 bit/genlik
```

```
65.536 genlik   ×   36 bit/genlik   =   2,36 Mbit statevector
 (kübit sayısından)   (hassasiyetten)
```

Hassasiyeti değiştirmek kübit sayısına dokunmaz; ikisi ayrı parametredir.

### "16 kübit" bankalamadan gelmez

Nedensellik zinciri **donanımdan probleme** doğrudur, tersi değil:

```
BRAM bütçesi (4,9 Mbit)
        ↓
Anayasa Prensip III: üst sınır 16 kübit        <- Faz 0, donanımdan türedi
        ↓
5 şehir seçildi:  (5-1)² = 16 değişken          <- tavana "birebir oturduğu" için
```

`services/qubo/qubo.py`: *"N=5 → 16 kübit, Anayasa Prensip III tavanına
**birebir oturur**."*

Yani **16 kübit 5 şehirden çıkmadı; 5 şehir 16 kübitten seçildi.** Bu,
savunmada güçlü bir noktadır: *problem boyutunu donanım bütçesi belirledi.*

`BANKS = 16` ise bambaşka bir şeydir — dizinin bölümlenme faktörü, seçilme
sebebi 65536'yı tam bölmesi. `N_QUBITS` ile eşit olması **tesadüftür**; 8 veya
32 de olabilirdi. Üstelik bankalama turu [ADR 0009](decisions/0009-paralellik-turu-kapatildi.md)
ile ölçümle kapandı: II tabanının kaynağı bankalama değil **bellek portu**
çıktı. Bankalama bir tasarım *sonucudur*, kübit sayısının *sebebi* değil.

---

---

## 0.5 Önce bu: projenin ne OLMADIĞI

### ⛔ Emülasyon, kaba kuvvetten üstel olarak pahalıdır — yapısal

Tek-sıcak TSP kodlamasında statevector `2^((N-1)²)` büyür, çözüm uzayı
`(N-1)!`. Makas her N'de açılır:

| N (şehir) | kübit | genlik | **gerçek tur sayısı** | makas |
|---|---|---:|---:|---:|
| 4 | 9 | 512 | 6 | 85× |
| **5** | **16** | **65.536** | **24** | **2.731×** |
| 6 | 25 | 33.554.432 | 120 | 279.620× |

**N=5'te 65.536 genlik emüle ediliyor — 24 tur arasından seçim yapmak için.**

Aynı makinede ölçüldü
([kaba-kuvvet-kiyas](measurements/kaba-kuvvet-kiyas_20260921_c504294.json)):

```
Kaba kuvvet (Python+numpy, 2000 tekrar) :  43,2 µs medyan  →  KESİN sonuç
QAOA yolu (FPGA)  99 × 37,28 ms         :   3,69 s         →  doğru olma olasılığı 2,4e-05

ORAN: ~85.000× kaba kuvvet lehine
```

Üstelik kaba kuvvet **Python'da**; C'de bir iki mertebe daha.

> Bir statevector emülatörü, **emüle edebildiği her boyutta**, aynı TSP'yi
> kaba kuvvetle çözmekten üstel olarak pahalıdır. Bu N'i küçültmekle
> düzelmez — **kötüleşir**. Donanım seçimiyle de ilgisi yoktur; CPU, GPU,
> FPGA fark etmez.

**Sonucu**: Hiçbir *uygulama* gereksinimi (bulut bağlantısızlık, gecikme,
enerji) bu iş yükü için hızlandırıcıyı gerekçelendiremez. Gerekçe
uygulamada değil, **emülatörün kendisinde**dir: bu proje bir rota
optimizasyonu ürünü değil, bir **donanım emülasyon çalışmasıdır**. TSP/QAOA
burada çözülecek problem değil, altın referansı olduğu için **doğrulanabilir
bir iş yüküdür**.

---


### Projenin adı ölçüme bağlıdır

*"Donanım hızlandırmalı"* ifadesi şu an **ölçümle desteklenmiyor** — ama
yanlış tabana karşı ölçtüğümüz için.

| Taban | Sonuç |
|---|---|
| Dizüstü i7 (Faz 2'de ölçüldü) | **başabaş** — 37,28 ms vs 32,75–41,93 ms ❌ |
| **Kart üstü ARM** (Cortex-A9 650 MHz) | ✅ **84,13 ms → FPGA 2,26× hızlı** (2026-09-21) |

Dizüstü karşılaştırması *"dizüstüm yerine PYNQ mı alsam"* sorusunu cevaplar;
mimari olarak anlamsızdır. SoC hızlandırmasında doğru soru **"çekirdeği
PS'ten PL'e taşımak neye değer?"**dir ve tabanı aynı çipteki ARM'dır. Bu,
zayıf taban seçmek değil, **mimari olarak doğru** tabanı seçmektir; HLS
literatürü hızlanmayı böyle raporlar.

✅ **ÖLÇÜLDÜ (2026-09-21, T045b)**: ARM float 84,13 ms (IQR 0,210, n=30),
FPGA 37,28 ms → **2,26×**
([ps-pl-hizlanma](measurements/ps-pl-hizlanma_20260921_c504294.json)).

> **Karar: *"donanım hızlandırmalı"* ifadesi kullanılabilir — ama daima
> sayısıyla ve tabanıyla birlikte**: *"kart üstü ARM Cortex-A9'a karşı
> 2,26×"*. Genel bir hızlanma ima edecek şekilde tek başına kullanılmaz;
> aynı çekirdek bir dizüstü CPU'da FPGA'dan 11,4× hızlıdır.

| Sonuç | Proje adı |
|---|---|
| ARM belirgin şekilde yavaş | *"Donanım hızlandırmalı gömülü kuantum devre emülatörü"* — ölçülmüş |
| Değilse | *"FPGA tabanlı gömülü kuantum devre emülatörü"* — "hızlandırmalı" **çıkarılır** |


---

## 1. Kullanılmayacak argümanlar (savunulamaz — kurmayın)

Bunların her biri kulağa makul gelir ve her biri ilk soruda çöker.

| ❌ Argüman | Neden çöker |
|---|---|
| *"FPGA daha hızlı"* | **Değil.** n=16 yalnızca 65.536 genlik ≈ 1 MB; bir GPU'nun L2 önbelleğine sığar. Beklenti GPU'nun iki-üç kat büyüklük önde olduğu yönünde. Zaten CPU'ya karşı bile **başabaşız** (37,28 ms vs 32,75–41,93 ms) |
| *"FPGA daha çok kübite ölçeklenir"* | **Tam tersi.** Biz 16 kübitte BRAM'e sıkıştık (%67 dolu). GPU 30+ kübite çıkar, çünkü GB'larca belleği var. Bu argüman kurulursa karşı taraf bir cümleyle yıkar |
| *"FPGA daha az enerji harcar"* | **Henüz ölçülmedi.** Kaba hesap GPU'nun bu boyutta enerjide de önde olabileceğini söylüyor. Ölçmeden söylenirse Anayasa madde II ihlal edilir |
| *"Kuantum-esinli hesap özel donanım ister"* | İstemez. Yapılan iş doğrusal cebir; GPU'lar bunda mükemmeldir |
| *"Rota optimizasyonunu hızlandırıyoruz"* | **Hayır.** Kaba kuvvet ~85.000× hızlı ve kesin (§0.5). Bu cümle projenin temelini çürütür |

> **Kural**: Bu dört cümlenin hiçbiri teze, sunuma veya makaleye girmez.

---

## 2. Kullanılacak argümanlar

### 2.1 Sistem rolü: FPGA merkezî çözücü **ve** G/Ç göbeği

> ⛔ **2026-09-21 DÜZELTME.** Bu bölüm önce *"FPGA kargo aracının içinde"*
> diye yazılmıştı. **Yanlıştı** ve savunmada çökerdi. FPGA araçta değil;
> **merkezî bir düğüm** olarak, ana bilgisayar gibi davranır. Aşağısı gerçek
> mimariye göre yeniden yazıldı.

**Gerçek mimari:**

```
        FPGA (PYNQ-Z2) — merkezî çözücü düğüm
        ≥60 kargo rotası, servis bölgelerine göre bölümlenir
        bölgeler arası pipeline burada kurulur
                 │
       ┌─────────┴─────────┐
       │                   │
  donanım yeterse     yetmezse
  DOĞRUDAN            Railway sunucusuna gönderir
       │                   │
       ▼                   ▼
   servislerdeki ESP32'ler ◄┘
```

Buradan çıkan üç argüman — ve hiçbiri "araca sığar mı" değil:

**(a) Sürekli çalışan bir servis düğümü.** Bu bir pil ömrü meselesi değil,
**7/24 işletme maliyeti** meselesi. PYNQ-Z2 ~5 W sürekli ≈ 44 kWh/yıl. Aynı
işi yapan bir GPU + konak sistem 150–300 W bandındadır. Görev döngüsü sürekli
olduğu için enerji argümanı zayıflamaz, **şekil değiştirir**.

**(b) FPGA aynı zamanda G/Ç göbeğidir.** Kartın kendi ARM'ı Linux koşuyor;
Ethernet, I2C, GPIO, UART üstünde. ESP32'lerle **doğrudan** konuşabiliyor.
GPU bunu yapamaz — G/Ç'si yoktur, bir konak makine şarttır. Yani gerçek
karşılaştırma *"FPGA vs GPU"* değil:

| | Tek PYNQ-Z2 kutusu | GPU çözümü |
|---|---|---|
| Çözücü | ✅ PL'de | ✅ |
| İşletim sistemi / ağ | ✅ kart üstündeki ARM | konak makine gerekir |
| ESP32 ile doğrudan G/Ç | ✅ Ethernet/I2C/UART | konak üzerinden |
| Sürekli güç | ~5 W | 150–300 W |

**(c) Uygulamanın ölçütü tek atış gecikmesi değil, verimdir.** ≥60 rota
bölgelere bölünüp bir **pipeline**'dan geçiyor. Anlamlı sayı tek bir çözümün
37,28 ms'si değil, **tam turun süresi**: 60 × 37,28 ms ≈ **2,24 s**. Boru
hattı zaten FPGA'nın doğal işidir.

### 2.2 Sıfır çip-dışı bellek trafiği — mimari argüman

Bu, mimari bilen bir değerlendiriciye söylenecek asıl şeydir ve **yapısal
olarak doğrulanabilir**: çekirdeğin arayüz listesinde `m_axi` **yoktur**.

```
#pragma HLS INTERFACE mode = s_axilite port = phases / cos_beta / sin_beta
#pragma HLS INTERFACE mode = s_axilite port = cost / p / beklenen_deger
```

65.536 genliğin tamamı hesap boyunca **çip içi BRAM'de** durur (187 RAMB18,
%67). DDR'a tek bir erişim yoktur. Birkaç watt'lık zarfı mümkün kılan şey
budur — GPU, aynı hesabı yaparken statevector'ü bellek hiyerarşisinde
gezdirmek ve 4600 çekirdek + bellek denetleyicilerini besler durumda tutmak
zorundadır.

Bu, Anayasa madde III'ün (çip-içi bellek zorunluluğu) bir kısıt değil bir
**tasarım tercihi** olduğunu gösterir.

### 2.2b Sayısal genişlik — GPU'nun ifade edemediği tasarım noktası

> ⚠️ **"18 bit" kübit sayısı değil, her reel sayının hassasiyetidir.**
> Ayrıntı ve diğer sayı çakışmaları: [§0](#0-aynı-sayı-farklı-anlam--önce-bunu-netleştirin).

**Bulgu: 18, iki bağımsız kısıtın tam kesişimidir.**

**Yukarıdan — doğruluk.** H eşiğini (≥0,999) geçen en dar format Q1.17'dir;
Q1.15 kalır ([olculen-degerler.md](olculen-degerler.md)):

| bit | format | fidelity | H |
|---|---|---|---|
| 16 | Q1.15 | 0,998674120 | ❌ |
| **18** | **Q1.17** | **0,999917032** | ✅ |

**Aşağıdan — donanım.** Zynq'teki BRAM36 bloğunun **azami kelime genişliği
36 bittir**. Bir genlik re+im = 2 × 18 = **tam 36 bit**, yani bir kelimeye
sıfır israfla oturur ([memory-budget.md](memory-budget.md)):

| Hassasiyet | bit/genlik | Kelime | İsraf |
|---|---|---|---|
| 16 bit | 32 | sığıyor | 4 bit boşta — **ve fidelity kalıyor** |
| **18 bit** | **36** | **tam oturuyor** | **0** ✅ |
| 19 bit | 38 | ❌ taşıyor | **ikinci blok → BRAM ikiye katlanır** |
| 32 bit (fp32) | 64 | ❌ | ping-pong'da %162 → **sığmıyor** |

Altında doğruluk yetmiyor, üstünde bellek iki katına çıkıyor. İki bağımsız
kısıtın aynı sayıya düşmesi bu tasarımın ana bulgusudur.

**GPU'da bu nokta yoktur.** Menü sabittir: fp16 / bf16 / fp32 / fp64 / int8.
18 bitlik reel sayı yoktur; "36 bitlik bellek kelimesine hizalamak" diye bir
kavram yoktur. Ve GPU'nun doğal formatı fp32, bu çipe **sığmaz**.

> Yani bu tasarım, **18 bit seçilebildiği için var olabiliyor**.

⚠️ **Aşırı iddia etmeyin**: "18 bit fp16'dan daha doğru" **denmez**. Kayan
noktanın üssü vardır; küçük genliklerde fp16 bizden iyi bile çıkabilir.
Savunulabilir iddia doğruluk üstünlüğü değil, **ifade edilebilirlik ve
sığma**: bu nokta GPU'da seçilemez, GPU'nun seçebildikleri de bu çipe sığmaz.

**Ölçüm görevi**: her genişlikte donanım maliyetini (BRAM/DSP/LUT/gecikme/
zamanlama) ölçüp fidelity ile yan yana koymak — Pareto eğrisi. Faz 5
Phase 6C, T070–T073.

### 2.3 Belirlenimci gecikme — **yalnız artımlı yolda geçerli**

> ⚠️ **Kapsam**: Sistem iki kipte çalışıyor ([sistem-mimarisi.md §3](sistem-mimarisi.md)). **Gecelik toplu işte jitter'ın hiçbir önemi yoktur** — gece boyunca zaman var. Bu argüman yalnız **adres değişikliği** yolunda, kullanıcı beklerken anlamlıdır. Her yere yayılırsa zayıflar.


FPGA'da gecikme çevrim cinsinden sabittir: p=2 için **3.728.217 çevrim**, her
seferinde. Kuyruk yok, işletim sistemi araya girmiyor, sürücü zamanlaması
yok. Bir denetim döngüsünde önemli olan ortalama değil **en kötü durumdur**.

GPU'da aynı hesap makineyi işletim sistemi, sürücü ve diğer süreçlerle
paylaşır; gecikmenin uzun bir kuyruğu vardır. Bu **ölçülebilir** bir farktır:
bizim T034 belirlenimcilik testimiz bit düzeyinde aynılığı zaten kanıtlıyor;
gecikme histogramı da farkı gösterir.

> Yan gözlem (argüman olarak fazla yaslanmayın): geliştirme makinesi NVIDIA
> sürücüsü yüzünden **günde ~1 çöküyor** ([GK-01](risk-register.md)). Bir
> anekdottur, kanıt değildir — ama sürücü yığınının bir güvenilirlik yüzeyi
> olduğunu hatırlatır. FPGA'da öyle bir katman yoktur.

### 2.4 Mühendislik katkısı hız rekoru değil, tasarımın kendisidir

Bitirme projesi yapılan tasarım işiyle değerlendirilir. Buradaki bulgular
gerçek ve **ölçülmüş**:

| Bulgu | Değer |
|---|---|
| Sabit nokta genişliği **ölçerek** seçildi | Q1.17, H eşiğini geçen **en dar** format (Q1.15 kalıyor, Q1.19 israf) |
| II tabanının kaynağı | Bankalama değil **bellek portu** — `RAM_2P` → `RAM_T2P` ([ADR 0009](decisions/0009-paralellik-turu-kapatildi.md)) |
| HLS tahmini güvenilmez | LUT'u **2× fazla** sayıyor (ölçülen oran 0,39–0,50×, **sabit değil**) |
| Yerleştirme monoton değil | Daha az kaynak isteyen varyant daha kötü yerleşti ve zamanlamayı tutturamadı |
| C/RTL eşdeğerliği | n=8 ve n=16, çıkış portu **bit bit** aynı |

Bunların hiçbiri "GPU daha hızlıymış" denince geçersizleşmez.

---

## 3. Dürüst kısıt: n=16 bu iddiayı taşıyacak kadar büyük değil

Bu, savunmanın **kendi zayıflığını önce kendisinin söylediği** yerdir ve
gücünü oradan alır.

FPGA'nın yapısal üstünlükleri (özel veri yolu, bellek hiyerarşisi yok,
belirlenimci boru hatları) problem **önbelleğe sığmadığında** ya da **çok
sayıda bağımsız küçük problem düşük güçte paralel koşturulduğunda** ortaya
çıkar. n=16'da problem her önbelleğe sığar. Yani:

> **Bu ölçekte FPGA verim yarışını kazanmaz. Bulgu, bu hesabı bir uç
> zarfına koymanın gecikme ve enerji olarak neye mal olduğudur.**

Bu cümle teze böyle girmelidir. "Kaybettik" değil, **ölçtük ve bedelini
biliyoruz** demektir.

⚠️ Bir sonraki adım olarak cazip gelen *"o zaman çok sayıda düğümde
watt başına verim"* argümanı **ölçülmedi** — kurulmamalı.

---

## 4. Savunmayı kusursuz yapacak tek şey: GPU'yu ölçmek

Elinde GPU varken ölçmemek, savunmanın tek gerçek açığıdır. Görev olarak
eklendi: **Faz 5 Phase 6B, T064–T069**
([tasks.md](../specs/003-zynq-ps-kartta-kosum/tasks.md)).

Üç sütunlu bir tablo — CPU / GPU / FPGA, gecikme ve enerji — ve yanında
dağıtım zarfı argümanı, GPU'dan hiç söz etmeyen bir tezden **çok daha
güçlüdür**. Çünkü:

- Sorulacak soruyu **siz sormuş** olursunuz,
- Cevabı ölçümle verirsiniz,
- Ve kaybettiğiniz eksende kaybettiğinizi söylemeniz, kazandığınızı
  söylediğiniz eksende size güvenilmesini sağlar.

⛔ **Sonuç ne çıkarsa çıksın raporlanır.** "GPU kazandı" çıkması bu ölçümün
başarısızlığı değil, tam da varlık sebebidir.

---

## 5. Tek paragrafta savunma

> Bu projede amaç en hızlı statevector simülatörünü yapmak değildi. FPGA
> burada **merkezî çözücü ve G/Ç göbeği** olarak duruyor: ≥60 kargo rotasını
> bölgelere bölüp bir boru hattından geçiriyor ve servislerdeki ESP32'lerle
> doğrudan konuşuyor — tek kutu, ~5 W, sürekli çalışıyor, konak bilgisayar
> yok, çip-dışı belleğe hiç dokunmuyor. GPU tek bir çözümü daha hızlı yapar;
> ölçtük ve raporluyoruz. Ama GPU'nun G/Ç'si yoktur, bir konak makine ister
> ve sürekli görev döngüsünde iki kat büyüklük daha fazla güç çeker. Bizim
> ölçtüğümüz şey, bu işi **tek bir düşük güçlü düğümde** yapmanın kapasitesi
> ve bedelidir — ve o kapasitenin nerede yetmeyip Railway'e devrettiğidir.

## İlgili belgeler

- [mimari-gerekce.md](mimari-gerekce.md) — **derin teknik gerekçelendirme**: çevrim başına
  ayrıştırma, bellek-portu kanıtı, 18-bit silikon tanecikliği. Hakem/jüri seviyesi.
- [sistem-mimarisi.md](sistem-mimarisi.md) — **uçtan uca mimari**; FPGA'nın sistemdeki gerçek rolü
- [olculen-degerler.md](olculen-degerler.md) — ölçülen her değer, ne iddia
  edilebilir/edilemez
- [risk-register.md](risk-register.md) — GK-01 (sürücü çökmeleri)
- [ADR 0008](decisions/0008-statevector-cekirdek-mimarisi.md) — çekirdek mimarisi
- [ADR 0009](decisions/0009-paralellik-turu-kapatildi.md) — paralellik turu ölçümle kapandı
