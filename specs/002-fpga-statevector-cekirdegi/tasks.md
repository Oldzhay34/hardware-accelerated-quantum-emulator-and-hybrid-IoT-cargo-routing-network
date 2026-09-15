# Tasks: Faz 2 — FPGA Statevector Hızlandırıcı Çekirdeği

**Input**: `specs/002-fpga-statevector-cekirdegi/` altındaki tasarım belgeleri
**Prerequisites**: [plan.md](plan.md) ✅ onaylandı · [spec.md](spec.md) · [research.md](research.md) · [data-model.md](data-model.md) · [contracts/](contracts/)

## SIRADAKİ

**Hedef (tek cümle)**: Faz 2 uygulaması başlıyor — T001'den itibaren `hls/` iskeleti kurulacak,
MVP hedefi US1 (C-sim ile altın referansa karşı fidelity ≥ 0,99).

**Dokunulacak dosyalar**: `hls/src/qir_types.hpp`, `hls/src/statevector.hpp`,
`hls/src/gates_diagonal.hpp`, `hls/src/gates_pairing.hpp`, `hls/tb/tb_kernel.cpp`

**Bilinen tuzaklar**:
- **Vitis HLS kurulu değil** ([SK-04](../../docs/risk-register.md), karar 20 Eylül). Faz 3, 4, 5, 7
  (US2/US3/US5) bu araca bağlı; **Faz 1–3 ve 6 bağlı değil** ve fazın M kapsamını kapsıyor.
  İndirme yarım kaldı: `.digests` indi, `.exe` inmedi.
- **`k` şablon parametresi olmalı** (`template <int K>`), çalışma zamanı değişkeni **değil**.
  Aksi hâlde HLS `ARRAY_PARTITION`'ı çözemez, tüm erişimleri serileştirir ve plandaki II
  aritmetiğinin tamamı geçersiz olur ([R-7](research.md)).
- **BRAM birim tuzağı**: HLS **BRAM_18K** birimiyle raporlar, bütçe **280** (140 değil).
  %85 eşiği = **238 BRAM_18K**. 140'a bölmek doluluğu iki kat gösterir.
- **C-sim bankalamaya kördür.** T0xx'lerde C-sim geçiyor diye II sorunu yok sanılmamalı.

**Son güncelleme**: 2026-09-15, Faz 2 — plan onaylandı (A1+B4+C1), uygulama başlamadı

---

**Onaylanan mimari** ([ADR 0008](../../docs/decisions/0008-statevector-cekirdek-mimarisi.md)):
A1 (naif `cyclic` F=16 + **yerinde**) + B4 (**Q1.17**) + C1 (**QAOA'ya özel**).

**Tests**: Bu fazda doğrulama ayrı bir "test" katmanı değil, **ürünün kendisidir** (US1 =
altın referansa karşı doğrulama). Bu yüzden doğrulama görevleri uygulama görevi olarak
listelendi, ayrı TDD bloğu olarak değil.

## Format: `[ID] [P?] [Story] Açıklama`

- **[P]**: Paralel koşabilir (farklı dosyalar, bekleyen bağımlılık yok)
- **[Story]**: Görevin ait olduğu kullanıcı hikâyesi (US1–US5)
- 🔴 = Vitis HLS gerektirir (NC-1'e bağlı)

---

## Phase 1: Setup (Paylaşılan altyapı)

**Amaç**: `hls/` iskeletini kurmak. Kod yok, yapı var.

- [ ] T001 `hls/src/`, `hls/tb/`, `hls/tcl/`, `hls/build/` dizinlerini oluştur ve her birine amacını yazan bir `README.md` koy (plan.md §Project Structure)
- [ ] T002 [P] `.gitignore`'a `hls/build/`, `hls/*_prj/`, `*.log`, `vitis_hls.log` satırlarını ekle — sentez çıktısı git'e girmez ([repo-conventions.md](../../docs/repo-conventions.md))
- [ ] T003 [P] `hls/README.md` yaz: onaylanan mimari (A1+B4+C1), ADR 0008 bağlantısı, "sentez raporu olmadan hiçbir sayı iddia edilmez" notu

---

## Phase 2: Foundational (Bloke edici ön koşullar)

**⚠️ KRİTİK**: Bu faz bitmeden hiçbir kullanıcı hikâyesi başlayamaz.

- [ ] T004 `hls/src/qir_types.hpp` oluştur: `N_QUBITS = 16`, `N_AMP = 1 << N_QUBITS` (65536), `BANKS = 16`, `LANES = 8`, `P_MAX = 3`; `using real_t = ap_fixed<18, 1>` (**Q1.17: 1 işaret + 17 kesir biti**) ve `struct amp_t { real_t re, im; }` (**36 bit — tam bir BRAM36 kelimesi**) ([data-model.md §1](data-model.md))
- [ ] T005 `hls/tb/ap_fixed_mock.hpp` yaz: `QIR_NO_VITIS` tanımlıyken `ap_fixed<W,I>`'yi taklit eden, **aynı yuvarlama ve doyurma (saturation) davranışını** veren şablon. Amaç FR-018 / Anayasa Prensip V — çekirdeğin Vitis başlıkları olmadan `g++` ile derlenebilmesi
- [ ] T006 `hls/src/statevector.hpp` oluştur: `amp_t sv[N_AMP]` dizisi + `#pragma HLS ARRAY_PARTITION variable=sv cyclic factor=16 dim=1` + `#pragma HLS BIND_STORAGE variable=sv type=RAM_2P impl=BRAM`. **`m_axi` portu AÇILMAZ** — DDR'a taşma yasağı, sözleşme maddesi K-1 ([kernel-interface.md](contracts/kernel-interface.md))
- [ ] T007 [P] `hls/tb/npy_reader.hpp` yaz: bağımlılıksız `.npy` okuyucu (NumPy v1 başlığı, `complex128`, C-sırası). Faz 1'in `docs/measurements/reference_*.npy` dosyalarını okuyacak
- [ ] T008 [P] `hls/tb/meta_reader.hpp` yaz: referansın yanındaki `.json` metadata'sından **`qubit_order` alanını okur**. Konvansiyon **varsayılmaz** (FR-009, sözleşme maddesi T-2)
- [ ] T009 `hls/tb/quantize.hpp` yaz: `complex128 → Q1.17` indirgeme fonksiyonu. Kıyas **referansı donanımın formatına indirgeyerek** yapılır, tersi değil (sözleşme maddesi T-3). `scripts/format_fidelity.py`'deki `q_fixed()` ile **aynı** yuvarlama/kırpma davranışını vermeli

**Checkpoint**: Tipler, bellek yerleşimi ve referans okuma hazır — hikâyeler başlayabilir.

---

## Phase 3: User Story 1 — Çekirdeğin doğru hesapladığını kanıtlamak (P1) 🎯 MVP

**Goal**: HLS çekirdeğinin bir QAOA devresini doğru hesapladığını, Faz 1'in altın referansına
karşı genlik düzeyinde kanıtlamak. **Kart ve Vitis GEREKMEZ.**

**Independent Test**: `g++` ile derle, `docs/measurements/reference_*_p2_n5.npy` dosyasına karşı
koş, fidelity ≥ 0,99 (beklenen **0,999917**).

### Köşegen yol — bankalama sorunu YOK

- [ ] T010 [US1] `hls/src/gates_diagonal.hpp` yaz: `apply_rz(sv, theta, k)` ve `apply_rzz(sv, theta, a, b)`. **Köşegen kapılar genliği yerinde bir sayıyla çarpar — `(i, i XOR 2^k)` eşlemesi YOKTUR**, erişim `i = 0…N_AMP-1` sıralıdır ([data-model.md §2a](data-model.md))
- [ ] T011 [US1] `hls/src/gates_diagonal.hpp` içine `apply_cost_layer(sv, terms, gamma)` ekle: maliyet katmanının **100 Pauli teriminin tamamını tek geçişte** uygular. Köşegen matrislerin çarpımı köşegendir → füzyon **bedelsizdir** ([R-4](research.md))
- [ ] T012 [US1] NC-2 için **geçici** çözüm: fazı her `i` için doğrudan hesapla (tablo yok, Gray-kod yok). Basit ve **0 ek BRAM**. Eniyileme kararı sentez raporundan sonra verilecek — bu görev onu **engellemeyecek** şekilde ayrı fonksiyonda kalmalı

### Eşlemeli yol — SK-02 yalnızca burada geçerli

- [ ] T013 [P] [US1] `hls/src/gates_pairing.hpp` yaz: `template <int K> void apply_rx(amp_t sv[N_AMP], real_t beta)`. **`K` şablon parametresi olmak ZORUNDA** — çalışma zamanı değişkeni olursa HLS partition'ı çözemez ve plandaki tüm II aritmetiği geçersiz olur ([R-7](research.md))
- [ ] T014 [P] [US1] Aynı dosyaya `template <int K> apply_h` ve `apply_x` ekle (FR-002 kapı kümesi)
- [ ] T015 [US1] Aynı dosyaya `template <int C, int T> apply_cnot` ekle (FR-002)
- [ ] T016 [US1] `hls/src/qir_kernel.cpp` içine karıştırıcı katmanını yaz: `for k in 0..15` döngüsü **derleme zamanında açılır**, her `k` için `apply_rx<k>` çağrılır

### Doğrulama yüzeyi

- [ ] T017 [US1] `hls/src/qir_kernel.cpp` içine `#ifdef QIR_VERIFICATION` altında `qir_kernel_debug(...)` ekle: genlik dizisinin tamamını `sv_out[N_AMP]`'e yazar. **`qir_kernel` ile AYNI hesaplama yolunu kullanmalı** (sözleşme maddesi T-1); ayrı uygulama olursa doğrulama hiçbir şey kanıtlamaz
- [ ] T018 [US1] `hls/tb/tb_kernel.cpp` yaz: referans `.npy` + `.json` oku (T007, T008), çekirdeği koş, `fidelity = |⟨ref|out⟩|²` hesapla (ikisi de normalize)
- [ ] T019 [US1] `tb_kernel.cpp`'ye **DG-02 ayırt etme** ekle: fidelity **ve** genlik büyüklük vektörünü ayrı ayrı raporla. `fidelity ≈ 0` ama büyüklükler doğruysa teşhis "kübit sıralaması ters", sayısal hata **değil** ([testbench-interface.md](contracts/testbench-interface.md#dg-02-ayırt-etme-kuralı))
- [ ] T020 [US1] `tb_kernel.cpp`'ye damgalı JSON çıktısı ekle → `docs/measurements/` altına (tarih + git hash + konfig, VR-03). Alanlar: `fidelity`, `referans_dosya`, `kubit_konvansiyonu`, `n_qubits`, `format`, `gecti_M`, `gecti_H`. **Sayı elle sabitlenmez** (CLAUDE.md kırmızı çizgisi)
- [ ] T021 [US1] `tb_kernel.cpp`'ye `--n` argümanı ekle ve **n = 8, 12, 16 için ayrı ayrı** koşulabilir yap (US1 senaryo 4, SC-001)
- [ ] T022 [P] [US1] `scripts/compare_amplitudes.py` yaz: C-sim çıktısını altın referansla kıyaslayan Python tarafı; testbench'ten bağımsız ikinci bir göz (Faz 1'in `services/reference/amplitudes.py` yükleyicisini kullanır)
- [ ] T023 [US1] `g++ -std=c++17 -O2 -DQIR_VERIFICATION -DQIR_NO_VITIS` ile derle ve koş; **fidelity ≥ 0,99** (M) doğrulandığında US1 tamam

**Checkpoint**: 🎯 **MVP.** SC-001, SC-004, SC-006 karşılandı — kart ve Vitis olmadan.
Fazın **M kapsamı burada tamamlanır**.

> **Beklenen değerden sapma da bir bulgudur**: Q1.17 için CPU taklidi 0,999917 ölçtü. C-sim
> bundan anlamlı ölçüde saparsa, taklidin yakalamadığı bir donanım davranışı (taşma, farklı
> yuvarlama kipi, ara sonuç genişliği) var demektir — **kaydedilir, gizlenmez**.

---

## Phase 4: User Story 2 — Tasarımın çipe sığdığını sentez raporuyla göstermek (P1) 🔴

**Goal**: BRAM kullanımını **gerçek sentez raporundan okumak** — tahminle değil.

**Independent Test**: `csynth` koş, rapordan BRAM_18K oku, **≤ 238** mi kontrol et.

**⚠️ Bloke**: Vitis HLS kurulu değil (NC-1 / [SK-04](../../docs/risk-register.md)).

- [ ] T024 [US2] `hls/src/qir_kernel.cpp` üst seviye imzasını tamamla: `gamma[P_MAX]`, `beta[P_MAX]`, `h[N_QUBITS]`, `J[N_QUBITS][N_QUBITS]`, `p`, ve **tek skaler** `beklenen_deger` çıkışı (FR-015, sözleşme maddeleri K-1…K-6). `beklenen_deger` **`float` döner**, `real_t` değil (madde K-5)
- [ ] T025 [US2] Tüm portlara `#pragma HLS INTERFACE mode=s_axilite` ekle ([kernel-interface.md](contracts/kernel-interface.md))
- [ ] T026 [US2] `hls/tcl/csynth.tcl` yaz: proje oluştur, hedef `xc7z020clg400-1`, saat 10 ns, `QIR_VERIFICATION` **tanımlanmadan** (tanımlanırsa `sv_out` bir `m_axi` portu doğurur ve K-1'i ihlal eder)
- [ ] T027 [US2] Sentezi koş ve rapordan oku: **BRAM_18K**, DSP48E, LUT, FF, latency, Fmax. **Bütçe 280 BRAM_18K'dir, 140 değil**; %85 eşiği = **238**
- [ ] T028 [US2] `docs/measurements/faz2-sentez.md` oluştur ve tabloyu yaz. Her satır **gerçek rapordan** gelmeli (FR-010, FR-011, Prensip II). Tahmin sütunu ayrı tutulur: beklenen **128 BRAM_18K = %45,7**
- [ ] T029 [US2] Ölçülen BRAM'i tahminle karşılaştır. **Sapma varsa gizlenmez** (FR-012, SC-008): nedeni ve bir sonraki deneme yazılır
- [ ] T030 [US2] BRAM > %85 ise **yeniden yazılmış K-02 merdivenini** uygula ([cut-plan.md](../000-kapsam-takvim/cut-plan.md), T048'de güncellenir — bu görevden **önce** yapılmalı). Eski merdivenin ilk iki basamağı **geçersizdir** — ikisi de %91,4
- [ ] T031 [US2] NC-2 kararını ver: sentez raporundaki gerçek BRAM payına bakarak faz stratejisini seç — tam tablo (+64 blok, %91,4 ✗), açı tablosu (+32, %69,3 ✅) veya Gray-kod artımlı (0, %45,7 ✅). **H etiketli** ([R-5](research.md))

**Checkpoint**: SC-002 karşılandı (veya karşılanmadığı açıkça yazıldı).

---

## Phase 5: User Story 3 — Bankalamanın gerçekten çözülüp çözülmediğini görmek (P1) 🔴

**Goal**: Seçilen şemanın **tüm `k` değerlerinde** çakışmasız çalışıp çalışmadığını sentez
raporundaki II'den anlamak. **C-sim'e güvenilmez — bu soruna kördür.**

**Independent Test**: Rapordaki II'yi oku; `k=0` ve `k=15` **ayrı ayrı**; **en kötü durum** esas.

**⚠️ Bloke**: Vitis HLS kurulu değil (NC-1).

- [ ] T032 [US3] Sentez raporundan `k=0` ve `k=15` için II'yi **ayrı ayrı** oku (FR-013, SC-003). Ortalama **değil**, en kötü durum raporlanır
- [ ] T033 [US3] Ölçülen II'yi `scripts/banking_analysis.py` tahminiyle karşılaştır: **k=0–3 → II=1, k=4–15 → II=2**. Bu tahmin saf aritmetiktir ve **doğrulanmamıştır**
- [ ] T034 [US3] Bellek çakışma (memory dependency) uyarılarını rapordan topla ve `docs/measurements/faz2-sentez.md`'ye yaz
- [ ] T035 [US3] **II tahminden belirgin kötüyse** ilk şüpheli: `k`'nin şablon parametresi olmaması. `gates_pairing.hpp`'de `template <int K>` kullanımını ve karıştırıcı döngüsünün derleme zamanında açıldığını denetle — bu, aritmetiğin göremediği **tek** başarısızlık kipidir
- [ ] T036 [US3] `docs/measurements/faz2-sentez.md`'ye **deneme sayacı** ekle. [K-03](../000-kapsam-takvim/cut-plan.md) üst sınırı **3 denemedir**; 4. deneme yapılmaz. Her denemenin sentez verisi kaydedilir (SC-007)
- [ ] T037 [US3] Üç deneme de tutmazsa: tasarımı tek banka + seri erişim + yüksek II'ye sabitle ve proje iddiasını **"bankalama kısıtının nicel karakterizasyonu"na** çevir. Üç denemenin sentez verisi **ana sonuç** olur (US3 senaryo 4)

**Checkpoint**: SC-003 ve SC-007 karşılandı.

---

## Phase 6: User Story 4 — Donanım olmadan ilerleyebilmek (P2)

**Goal**: Kart bağlı değilken tüm doğrulama zincirinin koştuğunu kanıtlamak.

**Independent Test**: Kart takılı değilken `g++` derlemesi + C-sim koşar, çıkış kodu **0**.

> **Vitis GEREKMEZ** — bu hikâye US2/US3'ten önce yapılabilir ve yapılmalıdır.

- [ ] T038 [US4] `hls/src/*` başlıklarının **Vitis başlıkları olmadan** (`-DQIR_NO_VITIS`) `g++` ile derlendiğini doğrula (FR-018, Anayasa Prensip V, sözleşme maddesi T-4)
- [ ] T039 [US4] Kart bağlı **değilken** Adım 0–2 zincirini uçtan uca koş ve çıkış kodunun **0** olduğunu doğrula (SC-004)
- [ ] T040 [P] [US4] `hls/tb/ap_fixed_mock.hpp`'nin gerçek `ap_fixed` ile **aynı sonucu** verdiğini doğrulayan küçük bir kıyas testi yaz — mock sessizce farklı davranırsa tüm C-sim doğrulaması yanıltıcı olur

**Checkpoint**: SC-004 karşılandı; Prensip V fiilen kanıtlandı.

---

## Phase 7: User Story 5 — Uçtan uca tekrarlanabilir akış (P3) 🔴

**Goal**: Sentez–cosim–IP export zincirini tek komutla koşmak.

**Independent Test**: `.\hls\run.ps1` iki kez koşulur; **aynı II ve kaynak sayıları** çıkar.

**⚠️ Bloke**: Vitis HLS kurulu değil (NC-1).

- [ ] T041 [P] [US5] `hls/tcl/csim.tcl` ve `hls/tcl/cosim.tcl` yaz — cosim, C-sim'in göremediği RTL uyuşmazlıklarını yakalar
- [ ] T042 [P] [US5] `hls/tcl/export.tcl` yaz (IP export)
- [ ] T043 [US5] `hls/run.ps1` yaz: csim → csynth → cosim → export zincirini elle tıklamadan koşar (FR-017). **PowerShell sözdizimi** — `&&` yok, `;` veya `if ($?)`
- [ ] T044 [US5] Akışı iki kez koş ve **raporlanan II ile kaynak sayılarının aynı olduğunu** doğrula (SC-005)

**Checkpoint**: SC-005 karşılandı.

---

## Phase 8: Polish & Cross-Cutting — belge düzeltmeleri

**Amaç**: Planın ortaya çıkardığı **aritmetik hataları** düzeltmek. Prensip II gereği
gizlenmezler; [ADR 0008](../../docs/decisions/0008-statevector-cekirdek-mimarisi.md)'de
kayıtlılar ama kaynak belgeler hâlâ yanlış.

- [ ] T045 [P] [spec.md](spec.md) §"Kritik bulgu: bankalama ve format bağımsız değil" bölümünü düzelt: **"16 kübitte ping-pong'a yalnızca Q1.15 ile para yetiyor" YANLIŞ** — Q1.11–Q1.17 *hepsi* aynı 64 bloğu kullanır, ping-pong hepsinde 128 blok = %91,4. Q1.15'in ayrıcalığı yok
- [ ] T046 [P] `spec.md` §bellek tablosunu blok düzeyinde yeniden yaz: **"16 kübit float32 yerinde = %81,3 🟡 sınırda" YANLIŞ**, gerçek değer **%91,4** ve SC-002'yi aşıyor — "sınırda" değil **başarısız**
- [ ] T047 [P] `spec.md` §"ya doğruluk ya bankalama kolaylığı" gerilimini kaldır: **gerilim yok**, Q1.17 ikisini de veriyor (fidelity 0,999917 + %45,7 BRAM)
- [ ] T048 [P] [cut-plan.md](../000-kapsam-takvim/cut-plan.md) **K-02 merdivenini yeniden yaz**: eski sıra "16+float32-yerinde → 16+Q1.15-ping-pong → 14+float32 → şerit yarıya" idi; **ilk iki basamak geçersiz** (ikisi de %91,4, ikisi de SC-002'yi aşıyor). Yeni ilk basamak **16+Q1.17-yerinde (%45,7)** ve zaten hedefin altında. Ayrıca 14 kübitin problem karşılığı yok — tek-sıcak TSP'de bir sonraki geçerli adım **9 kübit (4 durak)**
- [ ] T049 [P] [docs/risk-register.md](../../docs/risk-register.md) SK-02 satırını sentez sonuçlarıyla güncelle; şu an 🟡, kapanışı **H5 (18 Eki)** sentez raporuna bağlı
- [ ] T050 [P] [docs/memory-budget.md](../../docs/memory-budget.md)'ye onaylanan konfigürasyonu (A1+B4) ve %45,7 rakamını işle
- [ ] T051 [CLAUDE.md](../../CLAUDE.md) "Şu anki faz" satırını güncelle
- [ ] T052 Bu dosyanın **SIRADAKİ** bloğunu güncelle ([siradaki-standardi.md](../../docs/siradaki-standardi.md)) — güncellenmeyen SIRADAKİ hiç olmamasından kötüdür
- [ ] T053 [faz-sonu-kontrol.md](../../docs/faz-sonu-kontrol.md) listesini uygula: kararlar ADR'ye yazıldı mı, dead-ends güncel mi, ölçümler damgalı mı
- [ ] T054 [quickstart.md](quickstart.md) Adım 0–6'yı baştan sona koş ve belgedeki beklenen çıktıların gerçekle uyuştuğunu doğrula

---

## Dependencies & Execution Order

### Faz bağımlılıkları

- **Phase 1 (Setup)**: bağımlılık yok
- **Phase 2 (Foundational)**: Phase 1'e bağlı — **tüm hikâyeleri bloke eder**
- **Phase 3 (US1)**: Phase 2'ye bağlı · **Vitis GEREKMEZ** 🎯
- **Phase 4 (US2)**: Phase 3'e bağlı (çekirdek yazılmadan sentezlenemez) · 🔴 Vitis
- **Phase 5 (US3)**: Phase 4'e bağlı (aynı sentez raporunu okur) · 🔴 Vitis
- **Phase 6 (US4)**: Phase 3'e bağlı · **Vitis GEREKMEZ**
- **Phase 7 (US5)**: Phase 4'e bağlı · 🔴 Vitis
- **Phase 8 (Polish)**: T045–T048 **hemen** yapılabilir (belge düzeltmeleri, koda bağlı değil);
  T049–T054 ilgili fazlar bitince

### ⚠️ Pratik koşum sırası — Vitis engeli yüzünden öncelik sırasından FARKLI

Öncelik sırası US1 → US2 → US3 → US4 → US5'tir, ama US2/US3/US5 araca bağlı. Gerçek sıra:

```text
1. Phase 1 → Phase 2 → Phase 3 (US1)     ← MVP, araç gerekmez
2. Phase 6 (US4)                          ← araç gerekmez
3. T045–T048                              ← belge düzeltmeleri, araç gerekmez
   ── Vitis HLS kurulumu (SK-04, 20 Eylül) ──
4. Phase 4 (US2) → Phase 5 (US3) → Phase 7 (US5)
5. T049–T054
```

**Anayasa Prensip V'in fiilî anlamı**: Vitis gelene kadar **duracak iş yok** — yalnızca
doğrulanamayacak ölçüt var (SC-002, SC-003, SC-005).

### Paralel fırsatlar

- **Phase 1**: T002, T003 paralel
- **Phase 2**: T007, T008 paralel (farklı dosyalar); T004 → T005 → T006 sıralı
- **Phase 3**: T013, T014 paralel; T022 bağımsız (Python tarafı)
- **Phase 6**: T040 bağımsız
- **Phase 7**: T041, T042 paralel
- **Phase 8**: T045–T050 **hepsi paralel** (farklı dosyalar)

---

## Implementation Strategy

### MVP — yalnızca US1

1. Phase 1 (Setup) → Phase 2 (Foundational) → Phase 3 (US1)
2. **DUR ve DOĞRULA**: fidelity ≥ 0,99 (beklenen 0,999917)
3. Bu noktada **SC-001, SC-004, SC-006** karşılanmış ve fazın **M kapsamı tamamlanmış** olur

MVP'nin kritik özelliği: **kart ve Vitis olmadan** tamamlanabilir. Tek bir sentez
başarısızlığı projenin çekirdeğini yıkmaz — [Faz 0 triyajının](../000-kapsam-takvim/scope-triage.md)
M sınırını bilinçli olarak buraya koymasının nedeni budur.

### Artımlı teslim

1. Setup + Foundational → temel hazır
2. **US1** → bağımsız doğrula → **MVP** ✅
3. US4 → Prensip V kanıtlandı
4. *(Vitis kurulumu)*
5. US2 → BRAM gerçeği öğrenildi → NC-2 kararı verilebilir
6. US3 → II gerçeği öğrenildi → SK-02 kapanır veya K-03 merdiveni işler
7. US5 → tekrarlanabilirlik

### Kapsam etiketleri (Prensip VI)

| Etiket | Fazlar |
|---|---|
| **M** | Phase 1, 2, 3 (US1), 6 (US4) — araç gerektirmez |
| **H** | Phase 4 (US2), 5 (US3), 7 (US5), T031 (NC-2) |
| **İ** | Ping-pong'a yükseltme (yalnızca sentez BRAM'i ucuz gösterirse), F=32 denemesi, çok kübitli füzyon, C2 genel motor |

---

## Notes

- [P] = farklı dosyalar, bağımlılık yok
- Her görev veya mantıksal grup sonrası commit — **commit'i Olcay atar**
- Ölçüm rakamı (fidelity, II, BRAM %, Fmax) **elle sabitlenmez**; `docs/measurements/` altına
  damgalı (tarih + git hash + konfig) yazılır — CLAUDE.md kırmızı çizgisi
- **Hedef tutturulamazsa gizlenmez** (FR-012, SC-008): nedeni ve bir sonraki deneme yazılır
- C-sim'in geçmesi bankalama hakkında **hiçbir şey söylemez** — kabul ölçütü sentez raporudur
