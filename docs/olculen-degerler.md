# Ölçülen Değerler — tez/makale için tek referans

**Amaç**: makale yazarken sayı aramak için kronolojik ölçüm günlüğünü taramak
zorunda kalmamak. Buradaki her değer **ölçülmüştür**; tahminler ayrı bir
bölümde ve açıkça etiketlidir.

**Son güncelleme**: 2026-09-27 (§2.1 kart doğrulaması) · **Kaynak günlük**:
[measurements/faz2-sentez.md](measurements/faz2-sentez.md)

---

## 1. Deney koşulları (metoda yazılacak)

| | |
|---|---|
| Hedef cihaz | AMD/Xilinx **XC7Z020-CLG400-1** (PYNQ-Z2) |
| Araç | **Vitis HLS 2025.2**, Build 6295257 (14 Kas 2025) |
| İşletim ortamı | WSL2 / Ubuntu 24.04 (Windows'ta Device Guard aracı engelliyor) |
| Saat hedefi | 10 ns (**100 MHz**) |
| Sayı formatı | **Q1.17** — ap_fixed<18,1,AP_RND_CONV,AP_SAT> |
| Kübit sayısı | 16 (statevector 65.536 genlik) |
| QAOA katmanı | p = 1, 2, 3 (P_MAX = 3) |
| CPU tabanı | Qiskit **Aer** (C++ statevector), aynı devre |

⚠️ **Kübit sayısı derleme zamanı parametresidir** (-DQIR_N_QUBITS). n=8 ve
n=12 sonuçları sentetik referanslara karşıdır; tek-sıcak TSP formülasyonunda
kübit sayısı (N−1)² olduğundan 8 ve 12'nin problem karşılığı yoktur.

---

## 2. Doğruluk — altın referansa karşı fidelity

Altın referans **Qiskit Aer**; çekirdeğin kendi çıktısı referans olarak
kullanılmamıştır.

| Durum | Fidelity | M (≥0,99) | H (≥0,999) |
|---|---:|:---:|:---:|
| n=16, p=2 (TSP, 5 durak) | **0,999978179** | ✅ | ✅ |
| n=16, p=1 (TSP, 5 durak) | **0,999989167** | ✅ | ✅ |
| n=12, p=2 (sentetik) | **0,999998860** | ✅ | ✅ |
| n=8, p=2 (sentetik) | **0,999999871** | ✅ | ✅ |
| Aer CPU/GPU (WSL, 0.15.1), p=1/p=2 — GPU tabanının kendisi (T066) | **1,000000000000000** (1−F < 10⁻¹⁵) | ✅ | ✅ |

Format taraması — **SAYISAL MODEL** (`format_fidelity.py`, p=2). ⚠️ Bu tablo
**çekirdeğin değil modelin** çıktısıdır; model her kapıdan sonra yuvarladığı
için hatayı ~3,8× fazla tahmin eder. Çekirdeğin kendi taraması §2.2'de —
orada **16 bit de H'yi geçiyor**. ⛔ *"Q1.17 H eşiğini geçen en dar format"*
cümlesi bu tabloya dayanıyordu ve **artık kullanılmaz** (27 Eyl, 6C):

| Bit | Format | Fidelity (model) | H (model) |
|---:|---|---:|:---:|
| 12 | Q1.11 | 0,714527166 | ❌ |
| 14 | Q1.13 | 0,978861091 | ❌ |
| 16 | Q1.15 | 0,998674120 | ❌ (çekirdekte ✅, §2.2) |
| **18** | **Q1.17** | **0,999917032** | ✅ |
| 20 | Q1.19 | 0,999994814 | ✅ |
| 24 | Q1.23 | 0,999999980 | ✅ |

**RTL eşdeğerliği**: C/RTL cosimulation **PASS**, hem n=8 (fidelity 0,999999871)
hem **n=16** (19 Eylül 2026, commit 4282956).

n=16'da çekirdeğin tek çıkış portu olan `beklenen_deger` (float32), C modeliyle
**bit bit aynı** çıktı: her iki tarafta da `0xbee28271` (= −0,442401439).

⛔ **Bu sayı bir enerji DEĞİLDİR ve tezde enerji olarak raporlanamaz.**
20 Eylül'de ölçüldü: referanstaki ham Ising katsayıları `max|h| = 7512,61`,
`max|J| = 1253,07` — yani Q1.17'nin `[-1, 1)` aralığını kat kat aşıyor.
C testbench'i `cost.h[k] = qir::real_t(h_j[k].num)` diyor ve `AP_SAT`
**16/16 h girdisini, 84/120 J girdisini sessizce kırpıyor**. `-0,442401439`,
doymuş bir maliyet operatörünün beklenen değeridir.

Etkilenmeyenler (ikisi de ayrı yoldan gelir):
* **fidelity 0,999978179 geçerlidir** — `sv` yalnız `phases`'tan üretilir
  (`qir_kernel_debug(phases, cos_beta, sin_beta, p, sv)`), `cost` girmez.
  Fazlar mod 1'e indirgendiği için doyma yaşanmaz.
* **RTL ≡ C eşdeğerliği geçerlidir** — iki taraf da aynı doymuş fonksiyonu
  hesaplar ve bit bit aynı sonucu verir. Karşılaştırma bundan etkilenmez.

Bu, `contracts/host-encoder.md`'nin önlemek için yazıldığı hatanın ta
kendisidir ve Faz 5 kodlayıcısı (`agent/encoder.py`) ölçekleme protokolüyle
bunu kapatır: aynı girdide **istisna fırlatır**, sessizce doyurmaz (madde H-3).
`AESL_mErrNo` hiç üretilmedi, `.exit.err`/`.aesl_error` oluşmadı, her iki
aşamanın dönüş kodu 0. Ham kanıt:
[cosim-n16_20260919_4282956_p2.kanit.txt](measurements/cosim-n16_20260919_4282956_p2.kanit.txt),
ölçüm: [cosim-n16_20260919_4282956_p2.json](measurements/cosim-n16_20260919_4282956_p2.json).

⚠️ **Bu, 65536 genliğin tek tek doğrulandığı anlamına gelmez.** `sv[]` dahili
BRAM'dir, arayüzde çıkış portu değildir; cosim onu göremez. Beklenen değer
65536 terimlik bir indirgeme olduğu için kanıt güçlüdür ama tüketici değildir.
Ayrıca **tek bir uyaran** (tek problem örneği, p=2) için geçerlidir.

⚠️ JSON'daki `fidelity: 0,999978179`, **C modelinin Qiskit'e karşı** değeridir —
RTL'inki değildir. `tb_kernel.cpp`'de karşılaştırılan `cikti[]` dizisi yazılım
`sv[]`'sinden doldurulur; cosim bu sayıyı değiştirmez. Testbench'in kendi yorumu
bunu söylüyor: *"bu çağrı fazladan bir doğrulama değil, cosim'in çalışabilmesi
için gereken kancadır."*

### 2.1 Kartta doğrulama (US1) — 2026-09-27

Bitstream `qir_20260920_d350605` PYNQ-Z2'de koşuldu; C modeline karşı
**bit düzeyinde** karşılaştırıldı (float metni değil, IEEE-754 bit deseni).

| Kontrol | Sonuç |
|---|---|
| Yükleme (T032) | `ap_idle=1`, FCLK0 **100,000 MHz** doğrulandı |
| 20 izdüşüm, p=2 (G3) | **20/20 bit bit aynı**, sapan 0 |
| 20 izdüşüm, p=1 | **20/20 bit bit aynı**, sapan 0 |
| Belirlenimcilik | 5 ardışık tam çağrı, aynı bit deseni |
| Durumsuzluk | yeniden başlatma sonrası 20/20 aynı |
| p=0 / p=4 | çekirdek erken döner, çıkış **değişmez**, `ap_vld` kalkmaz |

Kayıt: [p2](measurements/kart-dogrulama_20260927_67165a7_n16_p2.json),
[p1](measurements/kart-dogrulama_20260927_67165a7_n16_p1.json).

⚠️ **Neyi kanıtlar**: silikon, C modelinin **aynısını** hesaplıyor (20
bağımsız `cost` izdüşümü, iki p için). Fidelity bu zincirle **devralınır**:
C modeli ↔ Qiskit 0,99997 (§2), RTL ↔ C bit bit (cosim), kart ↔ C bit bit
(burada). Genlikler AXI'den görünmediği için kartta doğrudan ölçülmedi
(karar K1).

⚠️ **Bulunan hata**: overlay yüklemesi FCLK0'ı **62,5 MHz**'e çekiyordu —
blok tasarımda PS kristali 33,333 MHz verilmiş, PYNQ-Z2'ninki 50 MHz. Sonuçlar
doğru çıkardı ama **gecikmeler sessizce %60 yavaş** ölçülürdü. Konak kodu artık
saati ayarlayıp doğruluyor. Ayrıntı: [SIRADAKI.md](../specs/003-zynq-ps-kartta-kosum/SIRADAKI.md).

Koşum boyunca besleme (XADC): VCCINT ≥ 1,0151 V, VCCBRAM ≥ 1,0159 V — düşüş yok.

### 2.2 Genişlik taraması — çekirdeğin kendisi (6C, 2026-09-27)

Aynı çekirdek `QIR_REAL_BITS` ile 5 genişlikte derlendi (C-sim + csynth).
Sabit tutulan: n=16, `phase_t` 18 bit, trig indeksi 13 bit, 10 ns hedef,
xc7z020clg400-1. Kayıt:
[genislik-pareto_20260927_dfe3eff.json](measurements/genislik-pareto_20260927_dfe3eff.json)
(beş genişlik + statevector BRAM'i; önceki `_29b253c` W=14'süz, `_924216e`
statevector alanısız). Figür:
[genislik-pareto_20260927_dfe3eff.svg](figures/genislik-pareto_20260927_dfe3eff.svg)
(`scripts/genislik_figur.py`, JSON'dan üretilir).

| W | Format | Fidelity p=2 | Fidelity p=1 | Model p=2 | BRAM_18K | DSP | LUT* | Periyot |
|---:|---|---:|---:|---:|---:|---:|---:|---:|
| 14 | Q1.13 | 0,994507735 ❌H | 0,997262828 | 0,978861 | **152** | 36 | 44.472 | 7,275 ns |
| 16 | Q1.15 | **0,999656239** ✅H | 0,999827344 | 0,998674 | **169** | 36 | 44.800 | 7,278 ns |
| 18 | Q1.17 | 0,999978179 | 0,999989167 | 0,999917 | **187** | 36 | 45.131 | 7,195 ns |
| 20 | Q1.19 | 0,999998540 | 0,999999277 | 0,999995 | **204** | 30 | 45.917 | 7,209 ns |
| 24 | Q1.23 | 0,999999892 | 0,999999946 | 0,99999998 | **238** | 33 | 47.260 | 7,220 ns |

\* HLS tahmini (bu projede ~2× şişik). Çevrim sayısı genişlikten
bağımsız: p=2 için hepsinde ~3.728.217; II 2/1 hepsinde. W=18 tarama
koşusu asıl sentez raporuyla **birebir aynı** — tarama altyapısı tutarlı.
Statevector BRAM'i tam **8W** (112/128/144/160/192); gerisi 40–46 blok.

**Ne gösteriyor**:
* Her 2 bit hatayı ~16× düşürüyor (kuramsal 4²); 24 bitte ~1e-7 tabanı
  (18 bit faz ve 13 bit trig indeksi artık baskın).
* Çekirdek modelden ~3,8× iyi — model her kapıdan sonra yuvarlıyor,
  çekirdek çift genişlikli `acc_t`'de biriktirip bir kez yuvarlıyor.
* BRAM bit başına ~9 blok **düzgün** artıyor; 19. bitte **uçurum yok**.
  DSP'de 18 üstünde sıçrama yok.
* ⛔ Sonuç: **18 bit iki kısıtın kesişimi DEĞİL**. 16 bit H'yi ~3× payla
  geçip 18 blok BRAM (%10) daha az kullanırdı. 18 bir **seçim**
  (Faz 2'de modele göre yapıldı), ölçülmüş bir zorunluluk değil.

**Uygulama düzeyi — genişlik QAOA çıktısını değiştiriyor mu?** (27 Eyl)
Fidelity tek sayıdır; tek bir çıktının olasılığı göreli olarak büyük
sapabilir (sınır yalnız TVD ≤ √(1−F)). Bu yüzden her genişliğin ham
statevector'ünden, altın referansın **kendi tanımlarıyla** ölçüldü
(referansın `optimal_probability` değeri yeniden üretilerek doğrulandı).
p=2 (p=1 aynı eğilim, JSON'da):

| W | TVD | Optimum rota olasılığı, bağıl hata | ⟨E⟩ bağıl hata | En olası geçerli tur | 24 turun sıralaması |
|---:|---:|---:|---:|:---:|:---:|
| 14 | 3,4·10⁻² | +4,9 % | +8,1·10⁻⁴ | aynı | farklı |
| 16 | 8,6·10⁻³ | +1,9 % | −2,5·10⁻⁴ | aynı | farklı (2 takas) |
| **18** | **2,2·10⁻³** | **−0,96 %** | **−1,6·10⁻⁵** | **aynı** | **1 takas** (17.↔18. sıra) |
| 20 | 5,5·10⁻⁴ | +0,075 % | −2,1·10⁻⁷ | aynı | aynı |
| 24 | 1,4·10⁻⁴ | +0,067 % | −2,1·10⁻⁶ | aynı | aynı |

Kayıt: [genislik-uygulama_20260927_3df6a60.json](measurements/genislik-uygulama_20260927_3df6a60.json)
(`scripts/genislik_uygulama.py`; dökümler `hls/genislik_tarama.sh --dump`).

* **Genişlik görünür**: 18 bitte optimum rota olasılığı %1 sapıyor ve 24
  turun sıralamasında bir takas var — referans olasılıkları zaten yalnız
  %1,4 farklı iki düşük olasılıklı tur (7,24·10⁻⁶ / 7,14·10⁻⁶). 20 bitte
  takas yok.
* **Ama uygulama açısından küçük**: en olası geçerli tur **14 bitten 24 bite
  her genişlikte** referansla aynı. Optimum olasılığını **p**'nin değiştirmesi
  (p=1 → p=2: 8,56·10⁻⁶ → 2,38·10⁻⁵, **2,8×**) genişliğin 18 bitteki
  etkisinden (%1) ~180× büyük.
* **24 bit, 20'ye göre uygulama düzeyinde bir şey kazandırmıyor**: optimum
  olasılığı hatası 7,5·10⁻⁴ → 6,7·10⁻⁴, ⟨E⟩ hatası 2,1·10⁻⁷ → 2,1·10⁻⁶
  (daha kötü) — taban artık faz (18 bit) ve trig tablosunda (13 bit).
* ⚠️ Yan bulgu: p=1'de optimum olasılığı (8,56·10⁻⁶) düzgün dağılımın
  (1/65536 = 1,53·10⁻⁵) **altında** — QAOA p=1'de rastgele tahminden kötü.

---

## 3. Kaynak kullanımı — HLS TAHMİNİ vs GERÇEK

Bu ayrım makalede **önemlidir**: literatürde HLS tahmini sayı bildirmek
yaygındır ve bu çalışmada tahmin LUT'ta **2 kata kadar** yanılmıştır.

| Kaynak | HLS tahmini | **Vivado P&R (gerçek)** | Kapasite | Oran |
|---|---:|---:|---:|---:|
| LUT | 45.164 (%84,9) | **22.535 (%42,4)** | 53.200 | 0,50× |
| FF | 49.839 (%46,8) | **19.466 (%18,3)** | 106.400 | 0,39× |
| DSP48E | 36 (%16,4) | **33 (%15,0)** | 220 | 0,92× |
| BRAM_18K | 187 (%66,8) | **187 (%66,8)** | 280 | 1,00× |
| SRL | — | 600 | — | — |

**Gözlem**: BRAM birebir tutuyor (bellek blokları sayılabilir), LUT/FF ise
sentezcinin optimize ettiği kaynaklar olduğu için HLS kaba bir **üst sınır**
veriyor. Oran sabit değil — üç farklı konfigürasyonda LUT için **0,39× / 0,44×
/ 0,50×** ölçüldü.

⚠️ **BRAM birim tuzağı**: HLS 18 Kb birimiyle raporlar. XC7Z020 bütçesi
**280 × BRAM_18K** (= 140 × BRAM36). 140'a bölmek doluluğu iki kat gösterir.

---

## 4. Zamanlama

| Aşama | Periyot | Marj |
|---|---:|---:|
| Hedef | 10,000 ns | — |
| HLS tahmini | 7,195 ns | (belirsizlik %27 dahil) |
| Vivado post-synthesis | 9,171 ns | +0,829 ns |
| **Vivado post-route** | **9,122 ns** | **+0,878 ns (%8,8)** |

**Zamanlama tuttu.** 100 MHz artık varsayım değil, ölçülmüş değerdir.

⚠️ HLS zamanlamada **iyimser**: 7,195 ns dediği tasarım gerçekte 9,122 ns çıktı.

---

## 5. Gecikme

Sentez raporundaki max gecikme P_MAX = 3 içindir. **Karşılaştırmalarda aynı p
kullanılmalıdır.**

Ayrıştırma: init 65.538 + p × katman 1.647.107 + expectation 368.465

| p | Çevrim | @100 MHz |
|---|---:|---:|
| 1 | 2.081.110 | 20,81 ms |
| **2** | **3.728.217** | **37,28 ms** |
| 3 | 5.375.324 | 53,75 ms |

Katman içi dağılım (p=3, toplam 5.375.327 çevrim):

| Kalem | Çevrim | Pay |
|---|---:|---:|
| mixer_loop (3 × 16 × 65.545) | 3.146.160 | **%58,5** |
| maliyet tabloları (3 × 532.736) | 1.598.208 | %29,7 |
| expectation_scaled | 368.465 | %6,9 |
| cost_amp_loop (3 × 65.549) | 196.647 | %3,7 |
| init_loop | 65.538 | %1,2 |

Ölçülen başlatma aralıkları (II): cost_amp_loop **1**, rx_dyn_pair_loop **2**.
Kabul ölçütü ≤ 4.

### 5.1 Kartta ölçülen gecikme — 2026-09-27 (US2, protokol v1.0)

PYNQ-Z2, FCLK0 100,000 MHz (seri başı ve sonu doğrulandı), JP5=USB, her
koşum **tam çağrı** ve sonucu C-sim ile **bit bit** doğrulandı; 300 sn/seri,
ilk 3 koşum ısınma, zaman değerine göre koşum atılmadı.

| Kapsam | p=2 medyan | IQR | p99 | maks | p=1 medyan |
|---|---:|---:|---:|---:|---:|
| **`T_cekirdek`** (ap_start → ap_done) | **36,578 ms** | 0,015 | 36,594 | 36,626 | **20,385 ms** |
| `T_yazma` (1.095 yazma) | 1,342 ms | 0,024 | 1,405 | 1,703 | 1,332 ms |
| `T_uctan_uca` (kodlama + yazma + koşum + okuma) | 48,947 ms | 0,046 | 49,107 | 55,643 | 29,726 ms |
| ↳ içinde Python kodlaması | 10,96 ms | | | | 7,94 ms |

Koşum sayısı: p=2 **6.102**, p=1 **10.027**; zaman aşımı 0. Yoklama periyodu
δ ≈ 21,5 µs — `T_cekirdek`'e üst taraftan en fazla bir δ eklenir. Kayıt:
[p2](measurements/kart-gecikme_20260927_201475a_n16_p2.json),
[p1](measurements/kart-gecikme_20260927_201475a_n16_p1.json).

**HLS modeliyle kıyas (T045)**:

| p | Model | Ölçülen (çevrim eşdeğeri) | Fark |
|---|---:|---:|---:|
| 2 | 3.728.217 | 3.657.789 | **−70.428 (−%1,89)** |
| 1 | 2.081.110 | 2.038.511 | **−42.599 (−%2,05)** |

Ölçülen, modelin **altında**. İki p'nin farkından: katman başına ~27.800,
sabit kısımda ~14.800 çevrim.

**Neden (T045, 27 Eyl)** — model HLS raporunun **en kötü durum** gecikmesiydi;
iki alt birimin gecikmesi raporda bir **aralık**:

| Birim | min | max (modelde) |
|---|---:|---:|
| `apply_cost_layer` | 295.184 | 598.288 |
| `expectation_scaled` | 318.289 | 368.465 |

Değişkenliğin kaynağı **üçgen döngüler** (`for x … for y = x+1 …`): iç
döngünün tur sayısı dış değişkene bağlı; HLS dış döngüyü açmadığı için her
`x` için en kötüsünü (7 tur) varsayar. Gerçekte 7+6+…+0 = 28 tur, varsayılan
8×7 = 56. **Belirlenimcidir** — veriye ve indekse bağlı değil; farklı `cost`
vektörüyle sürenin değişmemesi (seri K, 2,3 µs) bununla uyumlu.

**Çevrim düzeyinde kanıt — RTL simülasyonu**: 19 Eylül n=16 cosim'inde
(aynı çekirdek kaynağı; `15931cc`→`4282956` arasında `hls/src` değişmedi)
çekirdek çağrısı **125 ns'de başlayıp 36.546.545 ns'de bitiyor** →
RTL ≤ **36,5464 ms**. Kart medyanı **36,5779 ms**: fark **31 µs**, yani
ölçüm yükü mertebesinde (Python'dan `ap_start` yazımı + en fazla bir δ =
21,5 µs yoklama). Kartın **en kısa** koşumu 36,5618 ms — RTL'in 15 µs
üstünde, altında değil. **Kart, RTL'in çevrim sayısını koşuyor; %2'lik fark
HLS raporu ile RTL arasında, kartla değil.**

⬜ **Kapanmayan kısım**: raporun döngü formülleriyle (iç döngü II=1,
derinlik 69) yapılan hesap üçgen döngülerden katman başına **48.640**
çevrim kazanç öngörüyor; ölçülen **27.829**. Aradaki ~20.800 çevrim/katman,
raporun alt döngü çağrılarının giriş/çıkış maliyetini eksik saymasından
olabilir (4.096 çağrı × ~5 çevrim ≈ 20.500) — **doğrulanmadı**. Doğrulamak
için RTL simülasyonunda alt birimlerin `ap_start`/`ap_done` zamanları
izlenmeli (~16 dk cosim). Manşet sonucu değiştirmez.

**Ders**: HLS'in gecikme tahmini değişken turlu döngülerde **tutucu**
(burada %2); kaynak tahmini ise LUT'ta 2× fazla (§3). İkisi de "rapora göre"
değil "ölçüme göre" kararı destekliyor.

**Yapısal gözlemler**:
- **Yayılım yok denecek kadar küçük**: IQR 15 µs, jitter (maks−min) 65 µs —
  δ'nın birkaç katı. Çevrim sayısı sabit; kalan yayılım yoklamadan ve
  Linux'tan geliyor.
- **Termal plato yok**: çip 48,9 → 52,3 °C ısındı, son 6 pencere medyanı
  %0,002 içinde. Dizüstündeki turbo→plato (1,28×) davranışının karşılığı yok.
- **Kuyruk yalnız Python yolunda**: `T_cekirdek` maksı medyanın 0,05 ms
  üstünde; `T_uctan_uca` maksı **6,7 ms** üstünde (Linux zamanlaması).
- **Girdiden bağımsız**: farklı bir `cost` vektörüyle kontrol serisi (n=30)
  medyanı 2,3 µs farklı (2δ = 43 µs).
- ⚠️ **Ön kayıtlı beklenti B7 tutmadı**: `T_uctan_uca`'yı Python kodlamasının
  domine edeceği beklenmişti; kodlama yalnız **%22–27**, çekirdek **%69–75**.

---

## 6. CPU tabanı — TEMİZ ÖLÇÜM (2026-09-19)

⛔ **15–16 Eylül ölçümleri GEÇERSİZDİR.** Arka planda cosim koşarken alınmışlar
ve yöntem (`TEKRAR = 15`, ~0,6 sn) yalnızca **turbo penceresini** görüyordu.
Sapma: platonun 1,85× ve 2,21× katı. Ayrıntı: [faz2-sentez.md](measurements/faz2-sentez.md) §18.

**Geçerli taban** — 2026-09-19, prizde, harici monitör yok, sessiz makine,
**7474 koşum / 300 sn**, plato oturduğu doğrulandı:

| | Değer |
|---|---:|
| **Turbo** (ilk 2 sn) | **32,75 ms** |
| **Plato** (son 60 sn) | **41,93 ms** |
| Turbo → plato | 1,28× yavaşlama |

İşlemci ısındıkça yavaşlıyor ve orada kalıyor; iki değer de raporlanmalı,
hangisinin adil olduğu kullanım senaryosuna bağlıdır.

### Karşılaştırma (p=2, aynı devre)

FPGA **37,28 ms** (HLS/implementasyon tahmini):

| Karşısında | Sonuç |
|---|---|
| CPU platosu 41,93 ms | FPGA **1,12× hızlı** |
| CPU turbosu 32,75 ms | FPGA **1,14× YAVAŞ** |

**Gecikmede kazanç yok — başabaş.** FPGA tahmini CPU'nun iki değeri arasına
düşüyor.

### Enerji (CPU tarafı, ÖLÇÜLDÜ)

Batarya delta yöntemiyle, tüm dizüstü kapsamı (§19):

| | |
|---|---:|
| Boşta / yük altında güç | 21,58 W / 34,80 W |
| Güç farkı | **13,22 W** |
| **Koşum başına enerji** | **0,644 J** |

İki bağımsız hesap (gücün integrali ve kapasite farkı) %0,9 sapmayla uyuştu.

⚠️ Bu değer **bataryadaki** çalışma noktasına aittir (47,5 ms/koşum); batarya
yöntemi yalnızca fişten çıkıkken çalışabildiği için enerji ve gecikme farklı
noktalardan geliyor. Bataryada kısma ölçüldü: **−%18 verim, +%22 süre**.

---

## 7. NE İDDİA EDİLEBİLİR, NE EDİLEMEZ

**Edilebilir** (hepsi ölçüldü):

- 16 kübitlik statevector **tamamen çip içinde** tutulur (BRAM %66,8, DDR yok).
- Fidelity **≥ 0,99997**, dört konfigürasyonda, Qiskit Aer altın referansına karşı.
- Tasarım **100 MHz'de yerleşir ve zamanlamayı tutturur** (post-route 9,122 ns).
- Kaynak kullanımı **implementasyon sonrası** ölçülmüştür, HLS tahmini değildir.
- RTL, C ile **eşdeğerdir** (cosim PASS, n=8 **ve n=16**); n=16'da çıkış portu
  bit bit aynı — ama tek uyaran ve yalnızca çıkış portu üzerinden (bkz. §2).
- ~~Q1.17, H eşiğini geçen **en dar** sabit nokta formatıdır.~~ ⛔ **27 Eyl
  düştü** (§2.2): çekirdekte Q1.15 de H'yi geçiyor (0,999656). Yerine:
  *"Genlik genişliği ölçülmüş bir maliyet/doğruluk eğrisi olan serbest bir
  tasarım parametresidir; 16→24 bitte fidelity 0,99966→0,9999999, BRAM
  169→238 blok (csynth), çevrim sayısı sabit."*
- ✅ **Emülatör kartta çalışıyor ve doğrulandı** (27 Eyl): 20 izdüşüm, p=1 ve
  p=2, C modeliyle bit bit aynı; belirlenimci ve durumsuz (§2.1).
- ✅ **Kartta ölçülen gecikme** (27 Eyl): p=2 `T_cekirdek` **36,578 ms**
  (IQR 0,015), p=1 **20,385 ms**; sentez modelinin ~%2 altında (§5.1).
- ✅ **PS↔PL hızlanması 2,30×** — iki taraf da kartta ölçüldü (ARM 84,13 ms,
  FPGA 36,578 ms). **Daima tabanıyla** yazılır: *"kart üstü ARM Cortex-A9'a
  karşı"*.

**EDİLEMEZ**:

- ❌ **Genel bir hızlanma iddiası.** Geçerli tek hızlanma PS↔PL 2,30×'tir;
  aynı çekirdek dizüstü CPU'da FPGA'dan **11,2× hızlı** (3,273 ms vs
  36,578 ms). "FPGA hızlandırıyor" cümlesi tabansız kurulamaz.
- ⚠️ **Enerji karşılaştırması** — CPU tarafı ölçüldü (0,644 J/koşum), **FPGA
  tarafı ölçülmedi**. Tek taraflı rakam karşılaştırma üretmez.
- ❌ **Rota optimizasyonunda herhangi bir hızlanma.** Kaba kuvvet aynı makinede
  **43,2 µs**'de kesin sonucu veriyor; QAOA yolu 3,69 s ve doğru olma olasılığı
  2,4e-05 — **~85.000× kaba kuvvet lehine**, ölçüldü
  ([kaba-kuvvet-kiyas](measurements/kaba-kuvvet-kiyas_20260921_c504294.json)).
  Bu yapısaldır ve donanımla ilgisizdir; ayrıntı: [neden-fpga.md](neden-fpga.md).
- ❌ **GPU'ya karşı hiçbir şey.** Kıyas yalnız CPU'ya karşı kuruldu ve GPU
  **hiç ölçülmedi** (`AerSimulator` CPU build'i, `available_devices() == ('CPU',)`).
  Makinede RTX 4060 var; ölçülene kadar "FPGA daha hızlı/verimli" **hiçbir
  biçimde** yazılamaz. Beklenti GPU'nun hızda, muhtemelen enerjide de önde
  olduğu yönünde — FPGA'nın savunması **dağıtım zarfı**, hız değil.
  Ölçüm görevi: Faz 5 Phase 6B (T064–T069).
- ⚠️ **n=16 RTL eşdeğerliği kısmen** — çıkış portu bit bit doğrulandı, ancak
  65536 genliğin tek tek eşitliği ve birden fazla uyaran gösterilmedi.

Hızlanma ve enerji karşılaştırması **Faz 5/10'da, kartta, aynı p ile ve CPU
tarafı çoklu koşumla** yapılacaktır.

---

## 8. Yanlışlanan hipotezler — makalenin en değerli kısmı olabilir

Bu çalışmada **tahmine dayalı altı tasarım kararı ölçümle yanlışlandı**
(5 ve 6: 27 Eyl, genişlik taraması).

| # | Hipotez | Ölçüm | Sonuç |
|---|---|---|---|
| 1 | Mikserde k derleme zamanı sabiti olmalı, yoksa HLS erişimleri serileştirir | Şablon sürüm **45.114 LUT**, paylaşılan birim **2.409 LUT**; bedel yalnızca **+%4 gecikme** | 42.000 LUT boşuna harcanacaktı |
| 2 | Çakışma bankalama ile çözülür → daha çok banka daha iyi | cyclic 2→4→8: II **değişmedi** (3), LUT %84→%86→%90 | Sınır bankalama değil **bellek portu**: RAM_2P→RAM_T2P II'yi 3→2 yaptı, **bedelsiz** |
| 3 | Bankalama analizi işin çoğunu belirler | Bankalama araştırması toplam çalışma süresinin **%0,4'ünü** optimize etmiş | Köşegen maliyet katmanı işin %98'iydi |
| 4 | Tablo varyantları LUT'a sığmıyor (HLS: %182, %166) | Gerçek: **%71** ve **%74** — ikisi de sığıyor | HLS tahminiyle varyant elemek **güvenilmez** |
| 5 | 18 bit, H eşiğini geçen en dar genişlik (sayısal modelden) | Çekirdeğin C-sim'i: **16 bit 0,999656** — geçiyor (6C, 27 Eyl) | Model hatayı ~3,8× fazla tahmin ediyor; format seçimi modelle değil **çekirdekle** yapılmalıydı |
| 6 | 19+ bit BRAM36 kelimesini aşar → BRAM uçurumu; DSP48 18-bit portu → DSP sıçraması | csynth: BRAM 169/187/204/238 (16/18/20/24) — bit başına ~9 blok **düzgün**; DSP 36/36/30/33 | "18 = iki kısıtın kesişimi" anlatısı **düştü**; eğride dirsek yok |

Ayrıca: yerleştirme-yönlendirme **monoton değildir**. Daha az talep eden bir
varyant (#7, #6'nın alt kümesi) daha kötü yerleşti ve zamanlamayı tutturamadı
(10,170 ns), oysa daha agresif olan (#6) tutturdu (9,878 ns).

**Çıkan kural**: *kaynak gerekçesiyle bir varyant elenecekse gerekçe
implementasyondan gelmelidir.* HLS tahmini yalnızca hangi varyantların
ölçülmeye değer olduğunu sıralamaya yarar.

---

## 9. Reddedilen iyileştirme — kayda değer bir denge

#6 (tablo döngüleri PIPELINE II=4) gecikmeyi p=2'de **37,28 → 26,65 ms
(−%28,5)** düşürüyor, dört kaynak da bütçede kalıyor ve **zamanlama tutuyor**.
Yine de **reddedildi**:

| | post-syn → post-route | Marj |
|---|---|---:|
| Kabul edilen tasarım | 9,171 → 9,122 (iyileşti) | **+0,878 ns (%8,8)** |
| #6 | 9,171 → 9,878 (kötüleşti +0,707) | **+0,122 ns (%1,2)** |

Gerekçe: marj 7 kat azalıyor, yönlendirme zamanlamayı **bozuyor** (tıkanıklık
işareti), koşum süresi 3 katına çıkıyor (13→37 dk), ve Faz 5'te eklenecek PS
entegrasyonu + AXI bu marjı tüketir. Hızlanma iddiası zaten yapılamadığı için
kazanç hiçbir kabul ölçütünü değiştirmiyordu.

Karar ölçütü **sayı görülmeden önce** ilan edildi (post-route ≤9,4 ns → kabul,
≥9,7 ns → ret). Ayrıntı:
[ADR 0009](decisions/0009-paralellik-turu-kapatildi.md).

---

## 10. Üretilebilirlik

Bütün sayılar yeniden üretilebilir; hiçbiri elle yazılmadı.

```bash
wsl -d Ubuntu -e bash hls/build_and_run.sh        # doğruluk (Vitis gerekmez)
wsl -d Ubuntu -e bash hls/run.sh csynth           # sentez
wsl -d Ubuntu -e bash hls/run.sh impl             # gerçek kaynak + zamanlama
QIR_N=8 wsl -d Ubuntu -e bash hls/run.sh cosim    # RTL eşdeğerliği
```

```bash
.venv\Scripts\python.exe scripts\cpu_reference_time.py
```

Adım adım ve beklenen çıktılarla:
[quickstart.md](../specs/002-fpga-statevector-cekirdegi/quickstart.md).
Ölçüm dosyaları docs/measurements/ altında tarih + git hash + konfigürasyon
damgasıyla saklanır.
