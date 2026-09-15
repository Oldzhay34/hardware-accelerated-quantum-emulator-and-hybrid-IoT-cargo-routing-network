# Implementation Plan: Faz 2 — FPGA Statevector Hızlandırıcı Çekirdeği

**Branch**: `002-fpga-statevector-cekirdegi` | **Date**: 2026-09-15 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `/specs/002-fpga-statevector-cekirdegi/spec.md`

**Durum**: ✅ **ONAYLANDI** — 2026-09-15, kullanıcı onayı (Anayasa Prensip I).
Onaylanan kombinasyon: **A1 + B4 + C1**. Karar kaydı:
[ADR 0008](../../docs/decisions/0008-statevector-cekirdek-mimarisi.md).
`/speckit-tasks` çalıştırılabilir.

---

## Summary

16 kübitlik statevector emülasyon çekirdeği, Zynq-7020'nin çip-içi belleğinde kalarak
Vitis HLS ile sentezlenir ve Faz 1'in altın referansına karşı C-simülasyonda doğrulanır.

Araştırma (Faz 2 ARAŞTIR adımı) tamamlandı ve **spec'in merkezi varsayımını çürüttü.**
Spec şöyle diyordu:

> "16 kübitte ya **doğruluğu** (Q1.15 → fidelity riski) ya da **bankalama kolaylığını**
> (yerinde → SK-02'nin en zor hali) feda ediyorsun."

Bu ikilem **yok**. Üç ölçüm/hesap onu ortadan kaldırdı:

1. **Q1.17 her iki kısıtı da karşılıyor** — fidelity 0,999917 (H eşiğini geçiyor) *ve*
   BRAM'in 36-bit kelimesine israfsız sığıyor. Spec'in "yalnızca Q1.15" varsayımı
   bayt düzeyinde hesaba dayanıyordu; blok düzeyinde hesap onu düzeltti.
2. **Bankalama şeması seçimi tamamen anlamsız.** Üç şema (naif, XOR-2, XOR-tam) her
   tamponlama ve her `k` için **birebir aynı** verimi veriyor. Önemli olan şema değil,
   tamponlama.
3. **Asıl darboğaz bankalama değil, BRAM doluluğu.** Ping-pong II'yi düşürüyor ama
   %91,4 BRAM demek — bu **SC-002'nin kendi eşiğini (%85) aşıyor.**

**Teknik yaklaşım**: Q1.17 sabit nokta + yerinde (in-place) güncelleme + naif `cyclic`
partition (F=16). RZZ **yerleşik köşegen kapı** olarak uygulanır (CX'e ayrıştırılmaz),
maliyet katmanı tek köşegen geçişe füzyonlanır.

---

## Technical Context

**Language/Version**: C++17 (Vitis HLS 2025.2 alt kümesi) — çekirdek;
Python 3.13 — doğrulama koşum takımı ve analiz

**Primary Dependencies**: Vitis HLS (`ap_fixed`, `hls::stream`), NumPy, Qiskit
(yalnızca referans üretimi — çekirdek tarafında bağımlılık yok)

**Storage**: Yok. Statevector iki BRAM dizisi olarak çip-içinde tutulur; kalıcılık yok.

**Testing**: HLS C-simülasyon (`csim`) + C/RTL cosim; `pytest` ile genlik kıyas takımı.
C-sim standart `g++` ile de derlenebilir (FR-018, Prensip V).

**Target Platform**: Zynq-7020 (XC7Z020), PYNQ-Z2. PL: Artix-7, 140×BRAM36 (=280 BRAM_18K),
220 DSP48E1, 53.200 LUT, 106.400 FF. **URAM yok.**

**Project Type**: Donanım çekirdeği (HLS) + Python doğrulama koşum takımı

**Performance Goals**: SC-003 → **II ≤ 4** (`k=0` ve `k=15` ayrı raporlanır).
II=1 hedef değil, İ etiketli (K-04).

**Constraints**:
- SC-002 → **BRAM ≤ %85** (140 blokun 119'u). Bu planın **bağlayıcı kısıtı budur.**
- Anayasa Prensip III → statevector tamamen çip-içi, DDR'a taşma yasak, üst sınır 16 kübit
- Anayasa Prensip V → kart hiçbir modülde derleme koşulu olamaz

**Scale/Scope**: 2^16 = 65.536 karmaşık genlik. Yerleşik formülasyonda p=2 için 232 kapı
(200 köşegen + 32 eşlemeli).

### NEEDS CLARIFICATION

| # | Belirsizlik | Çözüm yolu | Bloke ettiği |
|---|---|---|---|
| **NC-1** | **Vitis HLS kurulu değil** ([SK-04](../../docs/risk-register.md), karar 20 Eylül) | Kurulum runbook'u hazır; indirme yarım kaldı | SC-002, SC-003, SC-005 |
| **NC-2** | Köşegen faz: tablo mu, Gray-kod artımlı mı? | Sentez raporu (BRAM payı) karar verir — **H** etiketli | Maliyet katmanı eniyilemesi |
| **NC-3** | Çekirdek QAOA'ya mı özel, genel kapı motoru mu? | §Kritik Tasarım Kararı — onay kapısında | `k`'nin derleme zamanı sabiti olup olmaması |
| **NC-4** | Gerçek Fmax | Sentez raporu. 100 MHz **varsayımdır**, ölçüm değil | Hızlanma tahmininin ölçeği |

NC-1 ve NC-4 **araçla** çözülür, tasarımla değil — Prensip V gereği kod yazımını
durdurmazlar, yalnızca ilgili ölçütleri "doğrulanmamış" bırakırlar.

---

## 🔴 Onay Kapısı — Anayasa Prensip I

> Bu bölüm onaylanmadan implementasyona geçilemez. Her satırın kaynağı ve türü
> (**ÖLÇÜLEN** / **HESAPLANAN**) belirtilmiştir.

### Tablo A — Bankalama / tamponlama stratejisi

Verim = çevrim başına işlenen genlik çifti (şerit sayısı üzerinde eniyilenmiş).
Kaynak: `scripts/banking_analysis.py` — **HESAPLANAN** (saf aritmetik, sentez değil).

| # | Strateji | Verim (en kötü k) | BRAM blok | BRAM % | SC-002 (≤%85) | SC-003 (II≤4) | HLS karmaşıklığı |
|---|---|---:|---:|---:|:---:|:---:|---|
| **A1** | **Naif `cyclic` F=16 + yerinde** | **4 çift/çevrim** | **64** | **%45,7** | ✅ | ✅ (II=2) | **En düşük** — tek pragma |
| A2 | Naif `cyclic` F=16 + ping-pong | 16 çift/çevrim | 128 | %91,4 | ❌ | ✅ (II=1) | Düşük — iki dizi |
| A3 | XOR banka eşlemesi + yerinde | 4 çift/çevrim | 64 | %45,7 | ✅ | ✅ (II=2) | **Yüksek** — elle indeks aritmetiği |
| A4 | XOR banka eşlemesi + ping-pong | 16 çift/çevrim | 128 | %91,4 | ❌ | ✅ | Yüksek |
| A5 | İki geçişli devrik (yüksek k) | ~1,3 çift/çevrim eşdeğeri | 128 | %91,4 | ❌ | ✅ | Yüksek |

**Okuma notları:**

- **A3/A4 elendi**: XOR şemaları naif şemayla **birebir aynı** verimi veriyor — her
  tamponlama, her `k` için. Ödenen pragma karmaşıklığının ölçülebilir karşılığı yok.
- **A5 elendi**: devrik + kapı + geri-devrik = 3 geçiş, doğrudan uygulama 2 geçiş.
  Üstelik permütasyonun kendisi de `2^k` adımlı erişimdir — çözmeye çalıştığı sorunun
  aynısı. İkinci tamponu zaten ödediği için ping-pong'a her eksende yeniliyor.
- **A2 tek başına en hızlı ama SC-002'yi kırıyor.** Üstünlüğü bankalamadan değil,
  **port sayısını ikiye katlamasından** geliyor — bedeli de tam olarak o: 2× BRAM.

**Hız farkı ne kadar önemli?** CPU tabanına karşı (Aer C++ statevector, bu makinede
**ÖLÇÜLEN** en iyi zaman ≈ 58 ms, p=2):

| | FPGA çevrim (HESAPLANAN) | 100 MHz'de süre | CPU'ya karşı |
|---|---:|---:|---:|
| A1 (yerinde) | 237.568 | 2,38 ms | **~24×** |
| A2 (ping-pong) | 69.632 | 0,70 ms | ~83× |

A2'nin ek 3,4×'i, **BRAM'in %45,7'den %91,4'e çıkması** ve SC-002'nin kırılması
pahasına geliyor. A1 zaten 24× veriyor ve geriye **55 blok (%39)** pay bırakıyor —
faz tablosu, AXI tamponları ve kontrol mantığı oraya sığar. A2'de pay **12 blok**.

> **ÖNERİ: A1.** Gerekçe tek cümle: *SC-003 zaten II≤4'e izin veriyor ve A1 II=2 veriyor;
> yani A2'nin satın aldığı şey projenin ölçütünde zaten karşılanmış durumda — ama
> ödediği şey (SC-002'nin ihlali) karşılanmamış bir ölçüt.*
>
> A2, sentez raporu BRAM'i tahminden ucuz gösterirse **İ etiketli yükseltme** olarak
> saklanır. Sıra önemli: önce A1 sentezlenir, gerçek sayı okunur, sonra karar verilir.

### Tablo B — Sayı formatı

Fidelity **ÖLÇÜLEN** (`scripts/format_fidelity.py`, p=2, 584 kapı, her kapıdan sonra
kuantalama). BRAM/DSP **HESAPLANAN** (DS190 / UG479 veri sayfası aritmetiği).

| # | Format | bit/genlik | Fidelity (ölçülen) | M (≥0,99) | H (≥0,999) | BRAM blok (yerinde) | BRAM % | DSP/çarpma |
|---|---|---:|---:|:---:|:---:|---:|---:|---:|
| B1 | Q1.11 | 24 | 0,714527 | ❌ | ❌ | 64 | %45,7 | 1 |
| B2 | Q1.13 | 28 | 0,978861 | ❌ | ❌ | 64 | %45,7 | 1 |
| B3 | Q1.15 | 32 | 0,998674 | ✅ | ❌ | 64 | %45,7 | 1 |
| **B4** | **Q1.17** | **36** | **0,999917** | **✅** | **✅** | **64** | **%45,7** | **1** |
| B5 | Q1.19 | 40 | 0,999995 | ✅ | ✅ | **128** | %91,4 | **2** |
| B6 | Q1.23 | 48 | 0,99999998 | ✅ | ✅ | 128 | %91,4 | 2 |
| B7 | float32 | 64 | 1,0 (referans) | ✅ | ✅ | 128 | %91,4 | 2+ (float IP) |

**Üç bağımsız kısıt tam olarak Q1.17'de buluşuyor:**

| Kısıt | Yön | Sınır |
|---|---|---|
| Fidelity H eşiği (≥0,999) | **en az** | Q1.17 — Q1.15 kalıyor (0,998674) |
| BRAM36'nın 36-bit kelimesi | **en çok** | Q1.17 — Q1.19 iki kelime ister, BRAM 2× |
| DSP48E1'in 18-bit B portu | **en çok** | Q1.17 — Q1.19 = 20 bit, tek DSP'ye sığmaz |

B1–B3 daha dar olmalarına rağmen **hiç BRAM kazandırmıyor** (hepsi tek 36-bit kelimeye
sığdığı için aynı 64 bloğu kullanıyor). Q1.17 israfsız olan tek format: 36 bitin 36'sı da
kullanılıyor.

> **ÖNERİ: B4 (Q1.17).** Daha dar format doğruluktan kalıyor ve hiçbir şey kazandırmıyor;
> daha geniş format hem BRAM'i hem DSP'yi ikiye katlıyor. Tasarım alanında tek nokta.

### Kritik Tasarım Kararı — çekirdek ne kadar genel olsun? (NC-3)

Bu, tablolardan bağımsız ama onlarla aynı kapıdan geçmesi gereken bir karar:

| | **C1 — QAOA'ya özel** | C2 — genel kapı motoru |
|---|---|---|
| Kapı listesi | Derleme zamanı: maliyet + karıştırıcı | Çalışma zamanı: konaktan gelir |
| `k` (hedef kübit) | **Derleme zamanı sabiti** (`for k in 0..15`) | **Çalışma zamanı değişkeni** |
| HLS partition çözümlemesi | Çözülebilir | **Çözülemeyebilir → her şey serileşir** |
| SK-02 riski | Büyük ölçüde kalkıyor | Tam güçte geri geliyor |
| Faz 10 esnekliği | Yalnızca QAOA kıyaslanabilir | Başka devreler de |

> **ÖNERİ: C1.** §Aritmetiğin göremediği şey bölümündeki tek gerçek başarısızlık kipi
> (`k` runtime olunca HLS'in partition'ı çözememesi) yalnızca C1'de ortadan kalkıyor.
> Faz 2'nin M sınırı QAOA'yı hızlandırmak; genellik İ'dir.

### ✍️ Onaylanan satır

> ✅ **A1 (naif cyclic F=16 + yerinde) + B4 (Q1.17) + C1 (QAOA'ya özel çekirdek)**
>
> **Onay**: 2026-09-15, kullanıcı. Karar kaydı:
> [ADR 0008](../../docs/decisions/0008-statevector-cekirdek-mimarisi.md).
>
> Onayın kapsamadığı, **açık bırakılan** kalemler: NC-2 (faz stratejisi — H, sentez
> raporuna bağlı), A2'ye yükseltme (İ, yalnızca sentez BRAM'i ucuz gösterirse).

---

## Constitution Check

*GATE: Phase 0 öncesi geçmeli, Phase 1 sonrası yeniden denetlenmeli.*

| İlke | Denetim | Durum |
|---|---|---|
| **I. Onay Kapısı** | Tablo A ve B üretildi, her satır kaynaklı; implementasyon onaya bağlandı | ✅ **kapı açık, onay bekliyor** |
| **II. Ölçüm Dürüstlüğü** | Her sayı ÖLÇÜLEN/HESAPLANAN etiketli. Hızlanma tahminleri teze **giremez** — Faz 10 ölçer. CPU tabanı olarak Aer (C++) seçildi; Qiskit'in Python `Statevector`'ü **adil taban değil** ve 20× yanıltırdı | ✅ |
| **III. Donanım Bütçesi Önce** | A1+B4 = 64 blok = %45,7 < %85. Statevector tamamen çip-içi. 16 kübit tavanı korunuyor | ✅ |
| **IV. Altın Referans** | Doğrulama Faz 1'in `reference_*.npy` dosyalarına karşı, genlik düzeyinde. Kübit konvansiyonu metadata'dan okunur, varsayılmaz | ✅ |
| **V. Donanımsız Süreklilik** | C-sim standart `g++` ile de derlenir; kart hiçbir modülde derleme koşulu değil. Vitis HLS eksikliği (NC-1) **kod yazımını durdurmaz**, yalnızca SC-002/003/005'i doğrulanmamış bırakır | ✅ |
| **VI. 14 Hafta Kısıtı** | Her iş kalemi M/H/İ etiketli (§Kapsam). A3/A4/A5 elenerek 3 denemelik K-03 bütçesi korundu | ✅ |

**Sonuç: ihlal yok.** Complexity Tracking tablosu boş kalıyor.

### Phase 1 sonrası yeniden denetim

Phase 1 tasarımı (data-model, contracts, quickstart) yukarıdaki altı ilkeyi değiştirmedi:
yeni bağımlılık eklenmedi, bellek bütçesi değişmedi, doğrulama yolu aynı kaldı.
✅ **Yeniden denetim geçti.**

---

## ⚠️ Bu planın spec'te ve cut-plan'da düzelttiği şeyler

Araştırma, daha önce yazılmış iki belgedeki **aritmetik hataları** ortaya çıkardı.
Prensip II gereği düzeltmeler gizlenmiyor:

| Belge | Yazan | Düzeltme |
|---|---|---|
| [spec.md](spec.md) §"bağımsız değil" | "16 kübitte ping-pong'a yalnızca Q1.15 ile para yetiyor" | **Yanlış.** Q1.11–Q1.17 *hepsi* aynı 64 bloğu kullanır; ping-pong hepsinde 128 blok = %91,4. Q1.15'in ayrıcalığı yok. Hesap bayt düzeyindeydi; BRAM36 blok granülaritesini görmüyordu |
| spec.md §bellek tablosu | "16 kübit, float32 yerinde = %81,3 🟡 sınırda" | **Yanlış.** Blok düzeyinde %91,4 — SC-002'yi aşıyor, "sınırda" değil **başarısız** |
| [cut-plan.md](../000-kapsam-takvim/cut-plan.md) K-02 merdiveni | "16+float32-yerinde → 16+Q1.15-ping-pong → 14+float32 → şerit yarıya" | **İlk iki basamak geçersiz** — ikisi de %91,4, ikisi de SC-002'yi aşıyor. Merdiven yeniden yazılmalı; yeni ilk basamak **16+Q1.17-yerinde (%45,7)** ve zaten hedefin altında |
| spec.md §"ya doğruluk ya bankalama" | Fazın "merkezi gerilimi" | **Gerilim yok.** Q1.17 ikisini de veriyor |

Bu düzeltmeler `/speckit-tasks` aşamasında ilgili dosyalara işlenecek (görev olarak
kaydedilecek), bu planın onayından sonra.

---

## Project Structure

### Documentation (this feature)

```text
specs/002-fpga-statevector-cekirdegi/
├── plan.md              # Bu dosya
├── research.md          # Phase 0 çıktısı — karar gerekçeleri
├── data-model.md        # Phase 1 çıktısı — varlıklar ve bellek yerleşimi
├── quickstart.md        # Phase 1 çıktısı — doğrulama koşum rehberi
├── contracts/
│   ├── kernel-interface.md    # AXI dağıtım yüzeyi (FR-015)
│   └── testbench-interface.md # doğrulama yüzeyi (FR-016)
└── tasks.md             # /speckit-tasks çıktısı — bu komut ÜRETMEZ
```

### Source Code (repository root)

```text
hls/
├── src/
│   ├── qir_types.hpp        # ap_fixed<18,1> tipleri, N_QUBITS, BANKS sabitleri
│   ├── statevector.hpp      # dizi tanımı + ARRAY_PARTITION pragma'ları
│   ├── gates_diagonal.hpp   # köşegen kapılar (RZ, RZZ, faz) — eşleme yok
│   ├── gates_pairing.hpp    # eşlemeli kapılar (H, X, RX, CNOT)
│   └── qir_kernel.cpp       # üst seviye: QAOA katman döngüsü + AXI arayüzü
├── tb/
│   ├── tb_kernel.cpp        # C-sim testbench — altın referansı okur
│   └── npy_reader.hpp       # .npy okuyucu (bağımlılıksız)
├── tcl/
│   ├── csim.tcl · csynth.tcl · cosim.tcl · export.tcl
└── run.ps1                  # tek komut uçtan uca akış (FR-017)

scripts/
├── banking_analysis.py      # ✅ var — Tablo A'nın kaynağı
├── format_fidelity.py       # ✅ var — Tablo B'nin kaynağı
├── memory_budget.py         # ✅ var — BRAM blok aritmetiği
├── cpu_reference_time.py    # ✅ var — CPU tabanı
└── compare_amplitudes.py    # 🆕 C-sim çıktısını altın referansla kıyaslar
```

**Structure Decision**: `hls/` dizini [repo-conventions.md](../../docs/repo-conventions.md) §2'de
zaten ayrılmıştı ve şu an boş. Hexagonal paket iskeleti **uygulanmaz** — o kural `services/`
altındaki uygulama kodu içindir; HLS çekirdeği donanım tanımıdır, katmanlı mimari kavramı
karşılığı yoktur. `src/` ve `tb/` ayrımı Vitis HLS'in kendi proje yapısını izler
(sentezlenen kaynak vs. sentezlenmeyen testbench).

---

## Kapsam etiketleri (Prensip VI)

| Etiket | İş | Neden |
|---|---|---|
| **M** | Çekirdek + C-sim doğrulaması (SC-001, SC-004, SC-006) | Fazın çekirdeği; kart ve Vitis'ten bağımsız |
| **M** | A1+B4+C1 uygulaması | Onaylanan kombinasyon |
| **H** | Sentez raporu: BRAM/II/Fmax (SC-002, SC-003) | NC-1'e bağlı; araç gelince |
| **H** | NC-2 faz stratejisi kararı | Sentez BRAM payını gösterince |
| **H** | Tek komut akış (SC-005) | Tekrarlanabilirlik, ölçüm eksenini taşımaz |
| **İ** | A2'ye (ping-pong) yükseltme | Yalnızca sentez BRAM'i ucuz gösterirse |
| **İ** | Çok kübitli kapı füzyonu | Hedefi 232 kapının 32'si; tavanı küçük |
| **İ** | C2 genel kapı motoru | SK-02'yi geri getirir |

---

## Complexity Tracking

> Constitution Check'te ihlal yok — tablo boş.

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| — | — | — |
