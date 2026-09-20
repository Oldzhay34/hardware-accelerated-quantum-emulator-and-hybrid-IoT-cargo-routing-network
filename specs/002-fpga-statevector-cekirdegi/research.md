# Phase 0 — Araştırma: Faz 2 FPGA Statevector Çekirdeği

**Tarih**: 2026-09-15 · **Plan**: [plan.md](plan.md) · **Spec**: [spec.md](spec.md)

Ayrıntılı analiz ve ham çıktılar: [docs/banking-research.md](../../docs/banking-research.md),
[docs/memory-budget.md](../../docs/memory-budget.md), [docs/measurements/](../../docs/measurements/).
Bu belge **kararları ve gerekçelerini** taşır, analizi tekrarlamaz.

---

## R-1: Bankalama şeması

**Decision**: Naif düşük-bit eşlemesi — HLS'in `#pragma HLS ARRAY_PARTITION cyclic factor=16`
pragma'sının doğal davranışı. Özel eşleme yazılmaz.

**Rationale**: Üç şema (naif, XOR-2 parça, XOR-tam katlama) **her tamponlama ve her `k` için
birebir aynı verimi** veriyor: yerinde 4 çift/çevrim (en kötü k), ping-pong 16. XOR'un
ölçülebilir hiçbir üstünlüğü yok, ama `ARRAY_PARTITION` XOR eşlemesi üretemediği için diziyi
elle bölüp indeks aritmetiğini kod içinde yazmayı gerektiriyor. Karşılıksız karmaşıklık.

**Alternatives considered**:
- *XOR tabanlı eşleme (2 parça / tam katlama)*: Yukarıdaki gerekçeyle elendi. Tam katlama
  yerinde şemada `k=15`'i düzeltiyor ama `k=4, 8, 12`'yi bozuyor — tipik "bir k'yi kazan,
  başkasını kaybet" davranışı; en kötü durum değişmiyor.
- *İki geçişli devrik (yüksek k için)*: Elendi. Devrik + kapı + geri-devrik = 3 geçiş,
  doğrudan uygulama 2 geçiş — **daha yavaş**. Permütasyonun kendisi de `2^k` adımlı
  erişimdir, yani çözmeye çalıştığı sorunun aynısıdır. İkinci tamponu zaten gerektirdiği
  için BRAM'de ping-pong kadar pahalı, ama her eksende ona yeniliyor. Bu teknik
  statevector'ün hızlı belleğe **sığmadığı** dağıtık simülasyondan gelir; burada sığıyor.

---

## R-2: Tamponlama — yerinde (in-place)

**Decision**: Yerinde güncelleme. Ping-pong **kullanılmayacak**, İ etiketli yükseltme olarak
saklanacak.

**Rationale**: Bu fazın bağlayıcı kısıtı bankalama değil, **SC-002 (BRAM ≤ %85)**.

| | Verim (en kötü k) | BRAM | SC-002 | SC-003 (II≤4) |
|---|---:|---:|:---:|:---:|
| yerinde | 4 çift/çevrim | %45,7 | ✅ | ✅ (II=2) |
| ping-pong | 16 çift/çevrim | %91,4 | ❌ | ✅ (II=1) |

Ping-pong'un satın aldığı şey (II=1) **projenin ölçütünde zaten karşılanmış** — SC-003
II≤4'e izin veriyor, yerinde şema II=2 veriyor. Ödediği şey (%91,4 BRAM) ise
karşılanmamış bir ölçüt. Ayrıca %45,7, faz tablosu ve AXI tamponları için **55 blok**
pay bırakıyor; %91,4 yalnızca 12 blok bırakıyor.

Hız farkı sayıyla: CPU tabanına (Aer C++, **ÖLÇÜLEN** en iyi ≈58 ms) karşı yerinde ~24×,
ping-pong ~83× (ikisi de **HESAPLANAN**, 100 MHz varsayımıyla). 24× zaten savunulabilir
bir sonuç; ek 3,4× için kabul ölçütü kırılmaz.

**Alternatives considered**:
- *Ping-pong*: Yukarıda. Sentez raporu BRAM'i tahminden ucuz gösterirse yeniden açılır —
  ama **önce A1 sentezlenir, gerçek sayı okunur**, sonra karar verilir. Sıra önemli.
- *14 kübite inmek*: Gereksiz. 16 kübit Q1.17 yerinde ile %45,7'de rahat oturuyor. Ayrıca
  16 kübit = (5-1)² tek-sıcak TSP formülasyonunun doğal boyutu; 14'ün problem karşılığı yok
  (bir sonraki geçerli adım 9 kübit = 4 durak).

---

## R-3: Sayı formatı — Q1.17

**Decision**: `ap_fixed<18, 1>` — 1 işaret + 17 kesir biti, reel ve sanal ayrı.
Genlik başına 36 bit.

**Rationale**: Üç **bağımsız** kısıt tam olarak bu noktada buluşuyor:

| Kısıt | Yön | Sınır | Tür |
|---|---|---|---|
| Fidelity H eşiği ≥0,999 | **en az** Q1.17 | Q1.15 = 0,998674, kalıyor | **ÖLÇÜLEN** |
| BRAM36'nın 36-bit kelimesi | **en çok** Q1.17 | Q1.19 iki kelime ister → BRAM 2× | HESAPLANAN |
| DSP48E1'in 18-bit B portu | **en çok** Q1.17 | Q1.19 = 20 bit → 2 DSP/çarpma | HESAPLANAN |

Fidelity, sabit-nokta aritmetiği CPU'da taklit edilerek ölçüldü: devre **kapı kapı**
uygulandı ve **her kapıdan sonra** genlikler hedef formata yuvarlandı — donanımın yapacağı
şeyin aynısı, yani hata birikimi gerçekten modellendi.

**Alternatives considered**:
- *Q1.15 (16 bit)*: Fidelity 0,998674 — M eşiğini geçiyor ama **H eşiğinde kalıyor**.
  Kritik olan: Q1.15 **hiç BRAM kazandırmıyor** (32 bit de, 36 bit de tek 36-bit kelimeye
  sığar → aynı 64 blok). Yani daralmanın karşılığı yok, yalnızca doğruluk kaybı var.
- *float32*: Fidelity referans (1,0) ama 64 bit/genlik → 128 blok = %91,4, SC-002'yi
  aşıyor. Ayrıca Artix-7'de kayan nokta çarpma bir IP çekirdeği gerektirir: daha çok DSP,
  daha çok LUT/FF, daha yüksek gecikme. Üç eksende de kaybediyor.
- *Q1.23 / Q1.19*: Fidelity daha iyi ama her ikisi de 36 bitin üstünde → BRAM ve DSP iki
  katına çıkıyor. Q1.17 zaten H eşiğini geçtiği için ek doğruluğun alıcısı yok.

---

## R-4: Kapı kümesinin donanım biçimi — yerleşik RZZ

**Decision**: RZZ ve RZ **köşegen kapı** olarak doğrudan uygulanır; Qiskit'in
`CX–RZ–CX` ayrıştırması **taklit edilmez**. Maliyet katmanının tüm köşegen kapıları
tek geçişe füzyonlanır.

**Rationale** (**ÖLÇÜLEN**): QAOA maliyet operatörünün 100 Pauli teriminin **hepsi
köşegen** (16 ağırlık-1 = RZ, 84 ağırlık-2 = RZZ). Köşegen kapı genliği yerinde bir
sayıyla çarpar — `(i, i XOR 2^k)` **eşlemesi yoktur**, erişim sıralıdır, bankalama sorunu
da yoktur.

| p | Ayrıştırılmış devre | bundan eşlemeli | Yerleşik | bundan eşlemeli |
|--:|--:|--:|--:|--:|
| 1 | 300 | 200 | 116 | 16 |
| 2 | 584 | 384 | **232** | **32** |
| 3 | 868 | 568 | 348 | 48 |

Eşlemeli kapı sayısı **12× azalıyor**. Yani SK-02 — projenin 1 numaralı riski — p=2'de
584 kapının 384'ünü değil, 232 kapının yalnızca **32'sini (%13,8)** etkiliyor.
`CX–RZ–CX` ayrıştırması Qiskit'in kapı kümesinin kısıtıdır, bizim çekirdeğimizin değil.

**İkinci derece sonuç**: köşegen matrislerin çarpımı köşegendir → maliyet katmanının 100
kapısı tek geçişe iner. Bu **bedelsiz füzyondur** (R-6'daki çok kübitli füzyondan farklı
olarak aritmetiği artırmaz).

**Alternatives considered**:
- *Qiskit'in ayrıştırmasını birebir uygulamak*: 12× daha fazla eşlemeli kapı, sıfır kazanç.
  Tek "avantajı" referansla kapı-kapı karşılaştırılabilmesi olurdu — ama doğrulama zaten
  **genlik düzeyinde** yapılıyor (FR-006), kapı düzeyinde değil.

---

## R-5: Faz hesaplama stratejisi — ✅ KAPALI (NC-2, 2026-09-16)

**Karar (2026-09-16, ölçümle)**: üç yoldan **hiçbiri** seçilmedi. Uygulama
**dördüncü bir yol** izledi ve soruyu konusuz bıraktı: **iki seviyeli faz
ayrıştırması**.

    acc(i) = FL[low8] + FH[high8] + Σ_{a∈L} s_a · D_a[high8]

Çapraz terimler çarpanlarına ayrıldığı için 136 terim ~10'a düşer ve tablolar
16 bitlik indeks yerine **256 girdilik** olur. Tablolar katman başına bir kez
kurulur, genlik başına değil.

**Ölçülen BRAM** (`qir_kernel_csynth.rpt`, 2026-09-16):

| Bileşen | BRAM_18K |
|---|---:|
| `sv` statevector (4 dizi × 32.768 × 18 bit) | **144** |
| `apply_cost_layer` (FL + FH + D + trig LUT) | **19** |
| `expectation_scaled` (EL + EH) | 20 |
| `control_s_axi` (AXI-Lite) | 4 |
| **Toplam** | **187 / 280 = %66,8** ✅ SC-002 |

Yani faz tablolarının gerçek bedeli **19 blok** — R-5'in "yalnızca açı tablosu"
seçeneğine (+33) yakın ama ondan ucuz, "tam tablo"dan (+64) çok ucuz. Gray-kod
yolunun sıfır BRAM avantajı, 19 blok için kontrol mantığı ve DSP yükü almaya
değmedi.

⚠️ **Aritmetik tahmin statevector'de de şaştı**: R-5 tablosu `sv` için 128 blok
(%45,7) diyordu, ölçülen **144** (%51,4). Sebep `ARRAY_PARTITION cyclic
factor=2`: dizi 4 parçaya bölününce (2 banka × re/im) blok granülaritesi
kayboluyor. Tahmin, bankalamanın blok sayısını değiştirdiğini hesaba katmıyordu
— `memory_budget.py` bunu zaten uyarıyordu (*"kesin sayı yalnızca sentez
raporundan okunur"*).

**NC-2 KAPANDI.** Ayrıntı: [olculen-degerler.md](../../docs/olculen-degerler.md) §3.

<!-- Aşağısı kararın verildiği andaki özgün gerekçedir; tarihsel kayıttır. -->

**Ertelenme gerekçesi (2026-09-14)**: Füzyonlanmış köşegen katman, her `i` indeksi için
toplam fazı gerektirir. Üç yol var ve aralarındaki fark tam olarak BRAM'dir:

| Yol | Ek BRAM | Toplam (statevector + bu) | SC-002 |
|---|---:|---:|:---:|
| Tam `(cos, sin)` tablosu, Q1.17 | 64 blok | 128 = %91,4 | ❌ |
| Yalnızca açı tablosu (18 bit) + küçük sin/cos LUT | 32 + ~1 blok | 97 = %69,3 | ✅ |
| Gray-kod artımlı (tablo yok) | 0 blok | 64 = %45,7 | ✅ |

Gray-kod yolu: ardışık indeksler tek bit farkla gezilirse, yalnızca o biti içeren Pauli
terimleri değişir → faz güncellemesi ucuzlar. Tablo yok ama kontrol mantığı ve DSP yükü var.

**Neden şimdi seçilmiyor**: üçü de SC-002 açısından *aritmetikte* ayrışıyor, ama LUT/DSP
maliyetleri yalnızca sentez raporundan okunur. Prensip II gereği tahminle seçilmez.
Karar, ilk sentez raporundan sonra verilecek (H etiketli).

---

## R-6: Çok kübitli kapı füzyonu

**Decision**: **Kapsam dışı (İ).** Faz 2'de uygulanmayacak.

**Rationale**: q kübitlik füzyon bellek geçişini 2^q kat azaltır ama **aritmetiği artırır**.
Karıştırıcı katmanı *farklı* kübitlerde tensör çarpımıdır: 4 kübitlik füzyon genlik başına
16 karmaşık MAC ister, 4 ayrı kapı ise 4×2 = 8. Yani aritmetik **ikiye katlanır** ve
yalnızca tasarım bellek-bağımlıysa kazandırır.

Ayrıca R-4'ten sonra füzyonun hedefi zaten 232 kapının 32'si — tavanı küçük, karmaşıklığı
(tile toplama/dağıtma, füzyon matrisi üretimi, ek doğrulama katmanı) yüksek.

**Alternatives considered**:
- *Köşegen füzyonu*: **Kabul edildi** ve R-4'ün parçası. Bu farklı bir şeydir: köşegen
  matrislerin çarpımı köşegen olduğu için aritmetik artmaz, bedelsizdir.

---

## R-7: Çekirdeğin genelliği — QAOA'ya özel (NC-3)

**Decision**: Çekirdek QAOA'ya özeldir. Kapı listesi derleme zamanında sabittir; konaktan
yalnızca **devre parametreleri** (γ, β açıları ve QUBO katsayıları) gelir.

**Rationale**: Bu, §R-1..R-3'teki tüm II aritmetiğinin **geçerli kalmasının koşulu**.
Aritmetiğin göremediği tek gerçek başarısızlık kipi şudur: HLS, `ARRAY_PARTITION`'lı bir
diziye hangi parçadan erişildiğini **derleme zamanında** çözemezse bütün erişimleri seri
hale getirir — ve `k` çalışma zamanı değişkeniyse tam da bu olur.

QAOA'ya özel çekirdekte bu risk oluşmuyor:
- Karıştırıcı katmanı `for k in 0..15: RX(β, k)` — `k` derleme zamanı sabiti (β değil).
- Maliyet katmanı köşegen — erişim sıralı, partition çözümlemesi gerekmiyor.

Genel bir kapı motorunda `k` çalışma zamanına döner ve SK-02 tam güçte geri gelir.

**Alternatives considered**:
- *Genel kapı motoru (konaktan kapı listesi)*: Faz 10'da başka devreleri de kıyaslama
  esnekliği verirdi. Ama SK-02'yi geri getiriyor ve Faz 2'nin M sınırı QAOA'yı
  hızlandırmak. İ etiketli.

---

## R-8: CPU karşılaştırma tabanı

**Decision**: Adil CPU tabanı **Aer'in C++ statevector simülatörüdür**. Qiskit'in Python
`Statevector.evolve`'u taban olarak kullanılmayacak.

**Rationale** (**ÖLÇÜLEN**, p=2, 16 kübit, bu makine):

| Taban | Medyan | En iyi |
|---|---:|---:|
| Qiskit `Statevector` (Python) | ~1.585 ms | — |
| **Aer statevector (C++)** | ~78 ms | **~58 ms** |

Arada **20×** var. Python yolunu taban almak, FPGA'nın hızlanmasını 20 kat şişirirdi —
Prensip II'nin doğrudan ihlali.

Ayrıca iki **dürüstlük uyarısı** Faz 10 için kaydedildi:
1. **Ölçüm gürültülü**: p=2'de tek tek koşumlarda 66 ms ile 981 ms arası değerler görüldü.
   Faz 10 kıyası çok tekrarlı olmalı ve yayılımı raporlamalı; tek ölçüm yanıltıcıdır.
   Bu yüzden burada **en iyi zaman** kullanıldı — FPGA'yı en az kayıran, yani en muhafazakâr
   seçim.
2. **Hızlanmanın bir kısmı donanımdan değil formülasyondan geliyor**: CPU ayrıştırılmış
   devreyi (584 kapı) koşuyor, FPGA yerleşik formülasyonu (232 kapı) koşuyor. Aynı
   formülasyonu CPU da benimseyebilir. **Faz 10 bu iki etkiyi ayırmak zorundadır**, yoksa
   donanıma ait olmayan bir kazanç donanıma yazılmış olur.

**Alternatives considered**:
- *Qiskit Python `Statevector`*: Reddedildi — adil değil.
- *Aer `matrix_product_state` veya GPU*: Kapsam dışı; kıyas tek çekirdekli CPU'ya karşı.
  > ⚠️ **2026-09-21: GPU kısmı geri alındı.** Gerekçe daireseldi (*neden* tek
  > çekirdekli CPU'ya karşı?) ve geliştirme makinesinde RTX 4060 var. Elinde GPU
  > varken ölçmeden "FPGA üstün" demek savunulamaz. GPU tabanı Faz 5'e görev
  > olarak eklendi (Phase 6B, T064–T069). `matrix_product_state` kapsam dışı kalır.

---

## Çözülen NEEDS CLARIFICATION özeti

| # | Durum |
|---|---|
| NC-1 (Vitis HLS yok) | ✅ **Çözüldü (2026-09-16)** — Vitis 2025.2 WSL/Ubuntu'da kurulu; csim, csynth, cosim ve implementasyon uçtan uca koştu. SC-002/003/005 doğrulandı |
| NC-2 (faz stratejisi) | ✅ **Çözüldü (2026-09-16)** → R-5. Üç seçenekten hiçbiri değil: iki seviyeli ayrıştırma, ölçülen **19 BRAM**, toplam %66,8 |
| NC-3 (genellik) | ✅ **Çözüldü** → R-7, QAOA'ya özel |
| NC-4 (Fmax) | ✅ **Çözüldü (2026-09-16)** — 100 MHz artık varsayım değil: Vivado **post-route 9,122 ns**, zamanlama tuttu (%8,8 marj) |
