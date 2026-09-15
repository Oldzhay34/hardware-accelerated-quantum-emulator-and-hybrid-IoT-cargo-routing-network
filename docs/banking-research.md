# Bankalama araştırması — Faz 2 ARAŞTIR adımı (a şıkkı)

**Tarih**: 2026-09-15 · **Durum**: araştırma tamamlandı, `/speckit-plan` onay kapısına hazır
**Üretici**: `scripts/banking_analysis.py`, `scripts/format_fidelity.py`, `scripts/memory_budget.py`
**Ham çıktı**: [docs/measurements/](measurements/) → `banking-analysis_20260915_cbe4d38.json`

> **Prensip II uyarısı.** Bu belgede iki tür sayı var ve karıştırılmamaları gerekir:
> **ÖLÇÜLEN** (fidelity, devre profili — CPU'da gerçekten çalıştırıldı) ve
> **HESAPLANAN** (II, BRAM blok, DSP — saf aritmetik + veri sayfası).
> Hiçbir HESAPLANAN sayı tez raporuna "sonuç" diye girmez; sentez raporu gelene
> kadar hepsi **tahmindir**. Her tablo hangi türde olduğunu başlığında söyler.

---

## 0. Soru

SK-02, projenin 1 numaralı riski: kübit `k`'ye kapı uygulanırken `(i, i XOR 2^k)`
genlik çiftleri işlenir. Erişim adımı `2^k` olduğundan **tek bir bankalama şeması
bütün k değerlerinde çakışmasız paralellik vermez** — ya da öyle varsayılıyordu.

Faz 2 promptu üç strateji istedi: (i) XOR tabanlı banka eşlemesi, (ii) yüksek k
için iki geçişli devrik, (iii) kapı füzyonu. Üçü de aşağıda. Ama araştırma,
sorulmayan iki şeyi buldu ve asıl cevap onlarda çıktı.

---

## 1. Önce sorunun boyutunu ölçtüm (ÖLÇÜLEN)

Strateji seçmeden önce sorulması gereken soru: **bankalama sorunu kaç kapıyı
gerçekten etkiliyor?**

Kritik ayrım: **köşegen** kapılar (RZ, RZZ, faz) genliği yerinde bir sayıyla
çarpar. `(i, i XOR 2^k)` eşlemesi **yoktur**, erişim sıralıdır, bankalama sorunu
da yoktur. Yalnızca köşegen-olmayan kapılar (RX karıştırıcı) eşleme ister.

QAOA maliyet operatörü (5 durak → 16 kübit): **100 Pauli terimi, hepsi köşegen**
(16 tanesi ağırlık-1 = RZ, 84 tanesi ağırlık-2 = RZZ).

| p | Qiskit'in ayrıştırdığı devre | bundan eşlemeli | **yerleşik RZZ ile** | bundan eşlemeli |
|--:|--:|--:|--:|--:|
| 1 | 300 kapı | 200 | **116** | **16** |
| 2 | 584 kapı | 384 | **232** | **32** |
| 3 | 868 kapı | 568 | **348** | **48** |

Qiskit RZZ'yi `CX–RZ–CX` olarak ayrıştırır ve CX köşegen değildir. Ama bu
**Qiskit'in kapı kümesinin kısıtı, bizim çekirdeğimizin değil**: kendi
donanımımızda RZZ doğrudan faz çarpımı olarak uygulanır.

> **Bulgu 1.** Yerleşik RZZ ile eşlemeli kapı sayısı **12× azalıyor**. Bankalama
> sorunu p=2'de 584 kapının 384'ünü değil, 232 kapının **yalnızca 32'sini (%13,8)**
> etkiliyor. Optimize edilecek şey, sanılandan bir kat küçük.

**İkinci derece sonuç**: köşegen matrislerin çarpımı köşegendir → maliyet
katmanının 100 kapısı **bedelsiz füzyonlanır**, tek geçişe iner. Bedeli sıfır
değil: her `i` için toplam fazın hesaplanması gerekir (ya 65536 girdilik faz
tablosu = +64 BRAM bloğu, ya Gray-kod artımlı güncelleme). Planın seçmesi gerekir.

---

## 2. Çakışma analizi (HESAPLANAN)

16 banka (b=4), çift portlu BRAM → banka başına 2 erişim/çevrim serbest.

**Yerinde (in-place) uygulamada her çift DÖRT erişim ister**: `oku(i)`, `oku(i')`,
`yaz(i)`, `yaz(i')`. *(İlk denememde yalnızca okumaları saymıştım; çakışma hiç
görünmüyordu. Yerinde güncelleme yazmaları da aynı bankaya bindirir.)*

### 2a. II=1'i koruyan azami şerit sayısı (= gerçek verim)

"II=1" tek başına aldatıcıdır — şerit sayısını düşürünce çakışma doğal olarak
kaybolur. Bağlayıcı ölçüt, çakışmadan kaç çift/çevrim işlenebildiğidir.

| Banka şeması | Tamponlama | En kötü k'de verim | Tavan |
|---|---|---:|---:|
| naif (düşük bitler) | yerinde | **II=1 imkânsız** | 8 |
| XOR (2 parça) | yerinde | **II=1 imkânsız** | 8 |
| XOR (tam katlama) | yerinde | 1 çift/çevrim | 8 |
| naif (düşük bitler) | **ping-pong** | **16 (tavan)** | 16 |
| XOR (2 parça) | **ping-pong** | **16 (tavan)** | 16 |
| XOR (tam katlama) | **ping-pong** | **16 (tavan)** | 16 |

"II=1 imkânsız": k≥4 için çiftin iki üyesinin de düşük 4 biti aynıdır, ikisi de
aynı bankaya düşer → **tek şeritle bile** 4 erişim olur. Şerit sayısını
azaltmak kurtarmaz.

> **Bulgu 2.** Çift tamponlama (ping-pong) okumayı A dizisinden, yazmayı B
> dizisine ayırır; banka başına yük 4'ten 2'ye iner ve **her şema, her k için
> teorik tavana (16 çift/çevrim) çıkar**. k=0 ve k=15 uç durumları elle
> doğrulandı.
>
> **Yani ping-pong varken banka şeması seçimi anlamsızlaşıyor** — naif düşük-bit
> eşlemesi, ki HLS'in `cyclic` partition'ının doğal davranışıdır, XOR şemaları
> kadar iyi. Promptun (i) şıkkı, kendisinden daha ucuz bir çözümle gereksiz hale
> geliyor.

### 2b. Ping-pong'un bedeli: parçalanma (HESAPLANAN)

Bankalama bedava değildir. `ARRAY_PARTITION` faktörü F, diziyi F ayrı BRAM'e böler;
parça 1024 kelimeden küçükse bloğun kalanı israf olur.

| F | kelime/parça | blok toplam | ping-pong | %140 | israf |
|--:|--:|--:|--:|--:|---|
| 1–64 | 65536 … 1024 | 64 | 128 | **%91,4** | **yok** |
| 128 | 512 | 128 | 256 | %182,9 | +64 blok (2×) |
| 256 | 256 | 256 | 512 | %365,7 | +192 blok (4×) |

> **Bulgu 3.** F ≤ 64 **bedava**. F=16'da 65536/16 = 4096 = 4×1024, tam bölünüyor;
> tek blok bile israf yok. Uçurum F=64'ün üstünde. Seçilen F=16 bu uçurumun
> rahatça altında.
>
> Fatura ping-pong'un kendisinde: **%45,7 → %91,4**. XC7Z020'nin 140 BRAM36'sının
> neredeyse tamamı. Geriye AXI tamponları, faz tablosu ve kontrol için **pay
> kalmıyor** — K-02 kesme ölçütü tam da burada tetiklenebilir.

---

## 3. Promptun istediği üç strateji — değerlendirme

### (i) XOR tabanlı banka eşlemesi

| Eksen | Değerlendirme |
|---|---|
| Beklenen II | Yerinde: hiçbir XOR varyantı kurtarmıyor (tablo 2a). Ping-pong'la naif ile aynı. |
| BRAM/parçalanma | Naif ile özdeş — XOR yalnızca adres bitlerini karıştırır, blok saymaz. |
| HLS pragma karmaşıklığı | **Yüksek.** `ARRAY_PARTITION` XOR eşlemesi üretemez; dizi elle F parçaya bölünüp indeks aritmetiği kod içinde yazılır. |
| Doğrulama zorluğu | Orta — eşleme bijektif olmalı; hata *sessiz* bozulma verir. |
| k=0 / k=15 | Tam katlama k=15'i düzeltiyor ama k=4, 8, 12'yi bozuyor (bkz. 2a). Bir k'yi kazanıp başkasını kaybetmek tipik. |

**Karar: ELENDİ.** Ping-pong bedava yaptığı için ödenen karmaşıklığın karşılığı yok.

### (ii) Yüksek k için iki geçişli devrik (transpose)

Fikir: k ≥ b olduğunda kübit k'yi düşük bir k′ ile yer değiştirip kapıyı uygula, sonra geri al.

| Eksen | Değerlendirme |
|---|---|
| Beklenen II | Kapı geçişi T ise: devrik + kapı + geri-devrik = **3T**, doğrudan yerinde uygulama 2T. **Daha kötü.** Üstelik permütasyonun kendisi de `2^k` adımlı erişimdir — çözmeye çalıştığı sorunun aynısı. |
| BRAM/parçalanma | 65536 elemanın yerinde permütasyonu döngü-takibi ister, boru hattına uygun değil → **ikinci tampon zaten gerekir**. Yani ping-pong ile aynı %91,4'ü öder. |
| HLS pragma karmaşıklığı | Yüksek — permütasyon çekirdeği + kübit yeniden etiketleme muhasebesi. |
| Doğrulama zorluğu | **En kötüsü.** Permütasyon hatası durumu normalize bırakır, fidelity sessizce düşer. Altın referans yakalar ama *nereyi* söylemez. |
| k=0 / k=15 | k<4'te hiç gerekmez, k≥4'te her seferinde gerekir — kontrol akışı k'ye dallanır. |

**Karar: ELENDİ, kesin olarak.** *İkinci tamponu zaten ödüyorsan, ping-pong bunu
her eksende yener: daha az geçiş, daha az kod, daha az sessiz hata yüzeyi.*
Devrik, statevector'ün hızlı belleğe **sığmadığı** dağıtık/çekirdek-dışı
simülasyondan gelen bir tekniktir; burada BRAM'e sığıyor, motivasyon yok.

### (iii) Kapı füzyonu (3–4 kübitlik bloklar tek geçişte)

| Eksen | Değerlendirme |
|---|---|
| Beklenen II | Bellek geçişi q kübit için 2^q kat azalır; **aritmetik artar**. q=4'te genlik başına 16 karmaşık MAC, 4 ayrı kapıda ise 4×2 = 8. Karıştırıcı katmanı *farklı* kübitlerde tensör çarpımı olduğu için füzyon **aritmetiği ikiye katlar**. Yalnızca bellek-bağımlıysak kazandırır. |
| BRAM/parçalanma | Füzyon matrisi küçük (16×16 karmaşık, Q1.17 → ~1 blok). Asıl bedel toplama/dağıtma (gather/scatter) mantığı. |
| HLS pragma karmaşıklığı | Yüksek — tile toplama, matris üretimi, kübit blok seçimi. |
| Doğrulama zorluğu | Orta-yüksek: füzyon matrisi tek tek kapıların çarpımına karşı ayrıca doğrulanmalı (ek altın referans katmanı). |
| k=0 / k=15 | Blok sınırını aşan kapılar füzyonlanamaz → yine özel durum. |

**Karar: İ (isteğe bağlı), Faz 2 kapsamı dışı.** Bulgu 1'den sonra füzyonun
hedefi zaten 232 kapının 32'si; tavanı küçük. **Ama köşegen füzyonu ayrı ve
bedavadır** (§1) — o M kapsamında kalır.

---

## 4. Format kararıyla kesişim — üç kısıt tek noktada buluşuyor

Bankalama ile format bağımsız değil. Üç bağımsız kısıt aynı formatta kesişiyor:

| Kısıt | Yön | Sınır | Kaynak |
|---|---|---|---|
| Fidelity eşiği H (≥0,999) | **en az** | Q1.17 (Q1.15 = 0,998674 **kalıyor**) | **ÖLÇÜLEN** — `format_fidelity.py` |
| BRAM 36-bit kelime | **en çok** | Q1.17 (Q1.19 iki kelime ister → BRAM 2×) | HESAPLANAN — DS190 |
| DSP48E1 18-bit B portu | **en çok** | Q1.17 (Q1.19 = 20 bit, tek DSP'ye sığmaz) | HESAPLANAN — DS190 / UG479 |

> **Bulgu 4.** Üç kısıt **tam olarak Q1.17'de** buluşuyor. Daha dar format
> doğruluktan kalıyor; daha geniş format hem BRAM'i hem DSP'yi ikiye katlıyor.
> Q1.17, 36-bit BRAM kelimesini **israfsız** dolduran tek format
> (bkz. [memory-budget.md](memory-budget.md) §3b).
>
> Ölçülen fidelity: Q1.15 = 0,998674 (M✓ H✗) · **Q1.17 = 0,999917 (M✓ H✓)** · float32 = 1,0

---

## 5. Aritmetiğin GÖREMEDİĞİ şey — dürüst uyarı

Yukarıdaki II sayıları saf aritmetiktir ve **gerçek bir başarısızlık kipini
modellemez**: HLS, `ARRAY_PARTITION`'lı bir diziye hangi parçadan erişildiğini
**derleme zamanında** çözemezse bütün erişimleri seri hale getirir. `k` çalışma
zamanı değişkeniyse II aritmetikten çok daha kötü çıkar.

**Bu projede o risk büyük ölçüde çözülüyor** — ama tesadüfen değil, tasarım
seçimiyle:

- Karıştırıcı katmanı `for k in 0..15: RX(β, k)` şeklindedir. `k` **derleme
  zamanı** sabitidir (β değil); HLS döngüyü açıp her k'yi özelleştirebilir.
- Maliyet katmanı köşegendir → erişim sıralıdır, parçalama çözümlemesi gerekmez.

**Ama bu, çekirdeği QAOA'ya özel yapar.** Konaktan rastgele kapı listesi alan
*genel* bir statevector motoru yazılırsa `k` çalışma zamanına döner ve risk geri
gelir. **Planın vermesi gereken karar budur** ve ucuz olan taraf bellidir.

Her hâlükârda: **buradaki hiçbir II sayısı sentez raporu gelene kadar
doğrulanmış değildir** (K-02 / K-04 ölçütü).

---

## 6. Öneri (onay kapısına giden)

> ⚠️ **2026-09-15 düzeltmesi.** Bu bölümün ilk hâli ping-pong'u **M** olarak öneriyordu.
> **Yanlıştı.** Ping-pong %91,4 BRAM demek ve bu, spec'in kendi kabul ölçütü
> **SC-002'yi (BRAM ≤ %85) aşıyor** — "tetiklenebilir" değil, aritmetikte zaten aşıyor.
> Buna karşılık SC-003 II ≤ 4'e izin veriyor ve yerinde şema II=2 veriyor.
>
> Yani ping-pong'un satın aldığı şey (II=1) projenin ölçütünde **zaten karşılanmış**;
> ödediği şey (SC-002 ihlali) karşılanmamış. Öneri **yerinde (in-place)** olarak
> düzeltildi. Ayrıntılı gerekçe ve hız karşılaştırması:
> [plan.md §Onay Kapısı](../specs/002-fpga-statevector-cekirdegi/plan.md).

| Kapsam | Karar | Gerekçe |
|---|---|---|
| **M** | Naif `cyclic` partition (F=16) + **yerinde (in-place)** + **Q1.17** | %45,7 BRAM (SC-002 ✅), II=2 (SC-003 ✅), en az HLS karmaşıklığı, üç kısıt Q1.17'de kesişiyor |
| **M** | RZZ **yerleşik** köşegen kapı olarak (CX'e ayrıştırma yok) | Eşlemeli kapıyı 12× azaltıyor — tek en büyük kazanç |
| **M** | Maliyet katmanını tek köşegen geçişe füzyonla | Köşegen çarpımı köşegendir, bedelsiz |
| **H** | Faz tablosu mu Gray-kod artımlı mı? | Tam tablo +64 blok → %91,4 (SC-002 ✗); açı tablosu +32 → %69,3 (✅); Gray-kod 0 → %45,7 (✅) |
| **İ** | **Ping-pong'a yükseltme** | Ancak sentez raporu BRAM'i tahminden ucuz gösterirse. Önce yerinde sentezlenir, gerçek sayı okunur |
| **İ** | Çok-kübitli kapı füzyonu | Tavanı küçük (32 kapı), karmaşıklığı yüksek |
| **ELENDİ** | XOR banka eşlemesi | Ping-pong bedava yapıyor |
| **ELENDİ** | İki geçişli devrik | Her eksende ping-pong'a yeniliyor |

**En büyük tehlike bankalama değil, doluluk**: ping-pong %91,4 BRAM demek ve
geriye pay kalmıyor. Yerinde şema %45,7'de kalıp **55 blok pay** bırakıyor — faz
tablosu, AXI tamponları ve kontrol mantığı oraya sığar. Sentez raporunun ilk
bakılacak satırı BRAM_18K kullanımıdır (bütçe **280**, 140 değil).

### Hız farkı gerçekte ne kadar? (ÖLÇÜLEN taban + HESAPLANAN çevrim)

CPU tabanı: Aer C++ statevector, p=2, bu makinede **en iyi ≈ 58 ms**
(`scripts/cpu_reference_time.py`). Qiskit'in Python `Statevector`'ü taban **değildir** —
20× yavaş, kullanılsaydı hızlanmayı o kadar şişirirdi.

| | FPGA çevrim (HESAPLANAN) | 100 MHz'de | CPU'ya karşı |
|---|---:|---:|---:|
| **yerinde** | 237.568 | 2,38 ms | **~24×** |
| ping-pong | 69.632 | 0,70 ms | ~83× |

24× zaten savunulabilir bir sonuç. Ek 3,4× için kabul ölçütü kırılmaz.
