# Ölçülen Değerler — tez/makale için tek referans

**Amaç**: makale yazarken sayı aramak için kronolojik ölçüm günlüğünü taramak
zorunda kalmamak. Buradaki her değer **ölçülmüştür**; tahminler ayrı bir
bölümde ve açıkça etiketlidir.

**Son güncelleme**: 2026-09-16 · **Kaynak günlük**:
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

Format taraması (p=2, en zorlu durum) — **Q1.17 H eşiğini geçen en dar format**:

| Bit | Format | Fidelity | H |
|---:|---|---:|:---:|
| 12 | Q1.11 | 0,714527166 | ❌ |
| 14 | Q1.13 | 0,978861091 | ❌ |
| 16 | Q1.15 | 0,998674120 | ❌ |
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
- Q1.17, H eşiğini geçen **en dar** sabit nokta formatıdır.

**EDİLEMEZ**:

- ❌ **Hiçbir hızlanma iddiası.** 37,28 ms sentez sonrası bir **tahmindir**;
  bitstream üretilmedi, kartta koşulmadı. CPU tarafı ayrıca ±%60 oynuyor.
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

Bu çalışmada **tahmine dayalı dört tasarım kararı ölçümle yanlışlandı**.

| # | Hipotez | Ölçüm | Sonuç |
|---|---|---|---|
| 1 | Mikserde k derleme zamanı sabiti olmalı, yoksa HLS erişimleri serileştirir | Şablon sürüm **45.114 LUT**, paylaşılan birim **2.409 LUT**; bedel yalnızca **+%4 gecikme** | 42.000 LUT boşuna harcanacaktı |
| 2 | Çakışma bankalama ile çözülür → daha çok banka daha iyi | cyclic 2→4→8: II **değişmedi** (3), LUT %84→%86→%90 | Sınır bankalama değil **bellek portu**: RAM_2P→RAM_T2P II'yi 3→2 yaptı, **bedelsiz** |
| 3 | Bankalama analizi işin çoğunu belirler | Bankalama araştırması toplam çalışma süresinin **%0,4'ünü** optimize etmiş | Köşegen maliyet katmanı işin %98'iydi |
| 4 | Tablo varyantları LUT'a sığmıyor (HLS: %182, %166) | Gerçek: **%71** ve **%74** — ikisi de sığıyor | HLS tahminiyle varyant elemek **güvenilmez** |

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
