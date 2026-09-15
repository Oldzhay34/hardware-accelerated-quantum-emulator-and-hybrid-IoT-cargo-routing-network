# Feature Specification: Faz 2 — FPGA Statevector Hızlandırıcı Çekirdeği

**Feature Branch**: `002-fpga-statevector-cekirdegi`

**Created**: 2026-09-13

**Status**: Draft — araştırma/onay döngüsü bekliyor

**Input**: User description: "Zynq-7020 (PYNQ-Z2) çip-içi belleğinde kalan, 16 qubit'lik statevector kuantum devre emülatörü çekirdeği; Vitis HLS (C++) ile yazılıp Tcl scriptleriyle sentezlenir."

**Kapsam dışı**: Zynq PS entegrasyonu ve kartta koşum (Faz 5), panel (Faz 6/8), klasik çözücü kıyası (Faz 10).

---

## SIRADAKİ

> ➡️ **SIRADAKİ bloğu [tasks.md](tasks.md)'ye taşındı** — `/speckit-tasks` çalıştığı için
> standart konumuna geçti ([docs/siradaki-standardi.md](../../docs/siradaki-standardi.md)).
> Güncel durum oradan okunur.

**Faz durumu**: ✅ spec → ✅ plan (onaylandı: **A1 + B4 + C1**,
[ADR 0008](../../docs/decisions/0008-statevector-cekirdek-mimarisi.md)) → ✅ tasks (54 görev)
→ ⏳ implement

> ⚠️ **Bu spec kod üretmez ve bankalama/format seçimi yapmaz.** Prompt'un çalışma kuralı ve Anayasa Prensip I gereği bu seçimler `/speckit-plan` aşamasında karşılaştırma tablolarıyla sunulup **yazılı onay** alındıktan sonra kesinleşir. **Onay 2026-09-15'te alındı.**

> 🔴 **Aşağıdaki §"Kritik bulgu" ve §bellek tablosu ARTIK GEÇERSİZDİR.** Faz 2 araştırması
> üçünü de çürüttü; düzeltme görevleri T045–T047. Doğru sayılar için
> [plan.md §Onay Kapısı](plan.md) ve [docs/banking-research.md](../../docs/banking-research.md).

---

## Neden bu faz projenin en riskli parçası

[Faz 0 triyajında](../000-kapsam-takvim/scope-triage.md) Faz 2 **M** etiketli — ama M'in sınırı bilinçli olarak *kartta koşan bitstream* değil, **C-sim doğrulaması + sentez raporu** seviyesinden geçirildi. Gerekçe: tek bir sentez başarısızlığı projenin çekirdeğini yıkmamalı.

Risk kaydındaki [SK-02](../../docs/risk-register.md) bu fazı projenin **1 numaralı teknik riski** olarak işaretliyor:

> Kapının uygulandığı kübit `k` için erişim adımı `2^k` değişir. Tek bir bankalama şeması bütün `k` değerlerinde çakışmasız paralellik **vermez**. **C-simülasyon bu soruna kördür** — C kodu doğru çalışır, sentez sonucu on kat yavaş çıkar.

### Bellek bütçesi — ⚠️ ilk hesap YANLIŞTI, düzeltildi (2026-09-15)

Bu bölümün ilk hâli **bayt düzeyinde** hesaplanmıştı ve BRAM36'nın 36-bit kelime
granülaritesini görmüyordu. Blok düzeyinde hesap (`scripts/memory_budget.py`
`blok_analizi()`) onu düzeltti. Doğru tablo:

| Konfigürasyon | bit/genlik | BRAM36 blok | % (140 üzerinden) | Durum |
|---|--:|--:|---:|---|
| 16 kübit, **Q1.17 yerinde** | 36 | **64** | **%45,7** | 🟢 **onaylanan** |
| 16 kübit, Q1.15 yerinde | 32 | 64 | %45,7 | 🟢 ama H eşiğinde kalıyor |
| 16 kübit, Q1.17 + ping-pong | 36 | 128 | %91,4 | 🔴 SC-002'yi (%85) **aşıyor** |
| 16 kübit, float32 **yerinde** | 64 | 128 | %91,4 | 🔴 SC-002'yi **aşıyor** |
| 16 kübit, float32 + ping-pong | 64 | 256 | %182,9 | 🔴 imkânsız |
| 16 kübit, double | 128 | 256 | %182,9 | 🔴 imkânsız |

**Düzeltilen iki ifade:**
- ~~"float32 yerinde = %81,3 🟡 sınırda"~~ → gerçek değer **%91,4**, yani
  "sınırda" değil **SC-002'ye göre başarısız**.
- ~~"Q1.15 + ping-pong = %81,3"~~ → **%91,4**. Q1.15'in ping-pong'da hiçbir
  ayrıcalığı yok.

**Kritik ayrıntı**: Q1.11–Q1.17 **hepsi aynı 64 bloğu** kullanır, çünkü hepsi tek
bir 36-bit BRAM kelimesine sığar. Yani Q1.15'e daralmanın **BRAM karşılığı
yoktur** — yalnızca doğruluk kaybı vardır. Q1.17 kelimeyi israfsız dolduran tek
formattır.

> ⚠️ Vitis HLS BRAM'i **18Kb** biriminde (BRAM_18K) raporlar: bütçe **280**,
> 140 değil. %85 eşiği = **238 BRAM_18K**.

### ✅ Çözülen ikilem: bankalama ve format bağımsız değil — ama çatışmıyor

Bu bölümün ilk hâli şöyle diyordu:

> ~~"16 kübitte ping-pong'a yalnızca Q1.15 ile para yetiyor. Yani ya doğruluğu ya
> bankalama kolaylığını feda ediyorsun."~~

**Bu ikilem yoktur.** Faz 2 araştırması üç sebeple çürüttü
([docs/banking-research.md](../../docs/banking-research.md)):

1. **Q1.17 her iki kısıtı da karşılıyor**: fidelity 0,999917 (ÖLÇÜLEN, H eşiğini
   geçiyor) *ve* 36-bit kelimeye israfsız sığıyor.
2. **Bankalama şeması seçimi anlamsız**: naif, XOR-2 ve XOR-tam şemaları her
   tamponlama ve her `k` için **birebir aynı** verimi veriyor.
3. **Bağlayıcı kısıt bankalama değil, SC-002**: ping-pong %91,4 BRAM demek ve
   eşiği aşıyor. Yerinde şema %45,7'de kalıp II=2 veriyor — SC-003 zaten II≤4'e
   izin verdiği için **ikisi de karşılanıyor**.

İki tablo yine de **kombinasyon olarak** değerlendirildi; onaylanan kombinasyon
**A1 + B4 + C1**'dir
([ADR 0008](../../docs/decisions/0008-statevector-cekirdek-mimarisi.md)).

---

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Donanım çekirdeğinin doğru hesapladığını kanıtlamak (Priority: P1) 🎯

Proje sahibi, yazdığı HLS çekirdeğinin bir kuantum devresini **doğru** hesapladığını, Faz 1'in altın referansına karşı genlik düzeyinde karşılaştırarak kanıtlar. Karta ihtiyaç duymaz — C-simülasyon yeterlidir.

**Why this priority**: Anayasa Prensip IV'ün doğrudan karşılığı — doğrulanmamış bir hızlandırıcı hiçbir şey ifade etmez. Ayrıca [K-05](../000-kapsam-takvim/cut-plan.md) bu doğrulamanın karar tarihini **H3 sonu** olarak bilinçli erken koymuştur: geç öğrenmek felakettir.

**Independent Test**: Faz 1'in ürettiği `docs/measurements/reference_*.npy` dosyası okunur; aynı devre HLS çekirdeğinde C-sim ile koşulur; genlikler karşılaştırılır. Kart, Vivado, bitstream **gerekmez**.

**Acceptance Scenarios**:

1. **Given** Faz 1'in altın referans genlik vektörü, **When** aynı devre çekirdekte C-sim ile koşulur, **Then** durum fideliteti **≥ 0,99** olur (M eşiği; H eşiği 0,999).
2. **Given** kübit sıralama konvansiyonu referansın metadata'sında yazılı, **When** karşılaştırma yapılır, **Then** konvansiyon **açıkça dönüştürülür** — varsayılmaz ([DG-02](../../docs/risk-register.md)).
3. **Given** sayı formatı daraltıldı (float32 → Q1.15), **When** doğrulama yeniden koşulur, **Then** fidelity **yeniden ölçülür**; eşik altına düşerse daraltma **geri alınır**.
4. **Given** çekirdek `n` kübit için parametrik, **When** n=8, 12, 16 ile koşulur, **Then** üçünde de doğrulama geçer.

---

### User Story 2 - Tasarımın çipe sığdığını sentez raporuyla göstermek (Priority: P1)

Proje sahibi, tasarımın Zynq-7020'nin kaynak bütçesine sığdığını **gerçek sentez raporundan okuyarak** kanıtlar — tahminle değil.

**Why this priority**: Anayasa Prensip III'ün uygulama noktası. [K-02](../000-kapsam-takvim/cut-plan.md)'nin karar tarihi **H4 sonu** ve ölçütü doğrudan bu rapordur. Bu olmadan "donanım hızlandırmalı" iddiası dayanaksızdır.

**Independent Test**: Sentez komutu çalıştırılır, üretilen rapordan BRAM/DSP/LUT/FF kullanımı ve Fmax okunur, tabloya yazılır. Kart gerekmez.

**Acceptance Scenarios**:

1. **Given** sentez tamamlandı, **When** rapor okunur, **Then** **BRAM ≤ %85** ve statevector'ün tamamı çip-içindedir (DDR'a taşma yok).
2. **Given** rapordaki sayılar, **When** belgeye yazılır, **Then** **gerçek rapordan** gelirler; tahmini değer yazılmaz (Prensip II).
3. **Given** hedef tutturulamadı, **When** rapor yazılır, **Then** bu **gizlenmez** — nedeni ve bir sonraki deneme yazılır.
4. **Given** BRAM %85'i aşıyor, **When** [K-02 merdiveni](../000-kapsam-takvim/cut-plan.md) uygulanır, **Then** sıra: 16+float32-yerinde → 16+Q1.15-ping-pong → 14+float32 → şerit yarıya.

---

### User Story 3 - Bankalama probleminin gerçekte çözülüp çözülmediğini görmek (Priority: P1)

Proje sahibi, seçtiği bankalama şemasının **tüm `k` değerlerinde** çakışmasız çalışıp çalışmadığını sentez raporundaki II sayısından anlar — C-sim'e güvenmez, çünkü **C-sim bu soruna kördür**.

**Why this priority**: [SK-02](../../docs/risk-register.md) projenin 1 numaralı riski. C-sim körlüğü, hatanın haftalarca fark edilmemesine yol açabilecek tek mekanizmadır.

**Independent Test**: Sentez raporundaki II değeri ve bellek çakışma (memory dependency) uyarıları okunur. `k=0` ve `k=15` uç durumları ayrı ayrı kontrol edilir.

**Acceptance Scenarios**:

1. **Given** sentez tamamlandı, **When** rapor okunur, **Then** **II ≤ 4** (kabul edilebilir taban; II=1 hedef **değil**, İ etiketli).
2. **Given** `k=0` ve `k=15` uç durumları, **When** her biri için II ölçülür, **Then** ikisi de raporlanır — ortalama değil, **en kötü durum** esastır.
3. **Given** bankalama denemesi başarısız, **When** yeni şema denenir, **Then** **deneme üst sınırı 3'tür** ([K-03](../000-kapsam-takvim/cut-plan.md)); 4. deneme yapılmaz.
4. **Given** üç deneme de tutmadı, **When** karar verilir, **Then** tasarım tek banka + seri erişim + yüksek II'ye sabitlenir ve proje iddiası **"bankalama kısıtının nicel karakterizasyonu"na** döner — üç denemenin sentez verisi **ana sonuç** olur.

---

### User Story 4 - Donanım olmadan ilerleyebilmek (Priority: P2)

Proje sahibi, PYNQ-Z2 kartı elde olmasa da çekirdeği yazabilir, doğrulayabilir ve sentezleyebilir.

**Why this priority**: Anayasa Prensip V'in doğrudan karşılığı. Bu spec yazıldığı anda kart **henüz elde değil** ([DT-00](../../docs/risk-register.md), teslim 14 Eylül) ve Vitis HLS **kurulu değil** ([SK-04](../../docs/risk-register.md), karar tarihi H1 sonu) — yani bu senaryo teorik değil, **şu anki gerçek durum**.

**Independent Test**: Kart bağlı değilken tüm doğrulama zinciri (C-sim + sentez) uçtan uca koşar ve çıkış kodu 0 verir.

**Acceptance Scenarios**:

1. **Given** kart bağlı değil, **When** C-sim ve sentez koşulur, **Then** ikisi de başarıyla tamamlanır — kart **hiçbir modülde derleme koşulu değildir**.
2. **Given** sentez araç zinciri henüz kurulu değil, **When** çekirdek kodu yazılır, **Then** kod, araçtan bağımsız bir derleyiciyle (mock/standart C++) da derlenebilir olmalıdır.

---

### User Story 5 - Uçtan uca tekrarlanabilir sentez akışı (Priority: P3)

Proje sahibi, sentez–cosim–IP export zincirini tek bir komutla, elle arayüz tıklamadan çalıştırır.

**Why this priority**: Tekrarlanabilirlik ([11.5 donanımsız CI](../000-kapsam-takvim/scope-triage.md)) ve sentez turlarının sayısı (K-03: 3 deneme, K-04: 4 tur) düşünüldüğünde elle koşum hata kaynağıdır. Ama ölçüm eksenini taşımaz.

**Acceptance Scenarios**:

1. **Given** temiz bir ortam, **When** tek komut çalıştırılır, **Then** sentez, cosim ve IP export uçtan uca tamamlanır.
2. **Given** aynı kaynak ve aynı ayarlar, **When** akış iki kez koşulur, **Then** raporlanan II ve kaynak sayıları aynıdır.

---

### Edge Cases

- **`k=0` ile `k=15` farklı davranırsa?** Beklenen durumdur — erişim adımı `2^k` değişiyor. **En kötü durum** raporlanır, ortalama değil (US3 senaryo 2).
- **C-sim geçiyor ama sentez II'si kötü çıkarsa?** Tam olarak beklenen tuzak. Bu yüzden kabul ölçütü C-sim değil **sentez raporudur** (US3).
- **Q1.15'e daraltınca fidelity düşerse?** Daraltma geri alınır (US1 senaryo 3). Bellek ile doğruluk arasındaki bu takas, fazın merkezi gerilimi.
- **Sentez aracı kurulmadan kod yazılırsa?** Yazılabilir ve yazılmalıdır (US4) — ama sentez ölçütleri araç gelene kadar **doğrulanmamış** sayılır; "muhtemelen sığar" denmez (Prensip II).
- **Referansın genlik sıralaması ters çıkarsa?** Fidelity ≈ 0 ama genlik büyüklükleri doğru — [DG-02](../../docs/risk-register.md)'nin imzası. Doğrulama paketi bunu ayırt edebilmelidir.
- **AXI-Stream yalnızca skaler döndürüyorsa genlik kıyası nasıl yapılır?** Bkz. Assumptions — **iki ayrı yüzey** vardır.

---

## Requirements *(mandatory)*

### Functional Requirements

**Çekirdek işlevi**

- **FR-001**: Çekirdek, `n` kübitlik bir statevector üzerinde kuantum kapıları uygulayabilmelidir.
- **FR-002**: Desteklenecek kapı kümesi **en az**: H, X, RZ, RZZ, CNOT.
- **FR-003**: Kübit sayısı ve paralel şerit sayısı **parametrik** olmalıdır (derleme zamanı parametresi).
- **FR-004**: Statevector **tamamen çip-içi bellekte** kalmalıdır; DDR'a taşma **yasaktır** (Anayasa Prensip III).
- **FR-005**: Üst sınır **16 kübit**; bunun üstü reddedilmelidir.

**Doğrulama**

- **FR-006**: Çekirdek çıktısı, Faz 1'in altın referans genlik vektörüne karşı **genlik düzeyinde** karşılaştırılabilmelidir.
- **FR-007**: Kabul ölçütü olarak **durum fideliteti eşiği** tanımlanmalı ve **ölçülüp raporlanmalıdır**.
- **FR-008**: Doğrulama **karta ihtiyaç duymadan** (C-simülasyon ile) koşabilmelidir.
- **FR-009**: Kübit sıralama konvansiyonu referansın metadata'sından okunmalı, **varsayılmamalıdır**.

**Sentez ve raporlama**

- **FR-010**: Sentez sonrası **gerçek rapordan** şu değerler okunmalıdır: II, gecikme (latency), BRAM/DSP/LUT/FF kullanımı, Fmax.
- **FR-011**: Bu değerler bir belgeye **tablo olarak** yazılmalıdır.
- **FR-012**: Hedef tutturulamadıysa **gizlenmemeli**; nedeni ve bir sonraki deneme yazılmalıdır.
- **FR-013**: `k=0` ve `k=15` uç durumları için II **ayrı ayrı** raporlanmalıdır.
- **FR-014**: Raporlanan hiçbir sayı tahmini olamaz (Anayasa Prensip II).

**Arayüz**

- **FR-015**: Dağıtılan çekirdek, aşağı yönde yalnızca **devre parametrelerini** almalı, yukarı yönde **tek skaler beklenen değer** döndürmelidir (NFR-02).
- **FR-016**: Doğrulama yüzeyi (C-sim/cosim testbench) iç genlik dizisine **doğrudan erişebilmelidir** — FR-006'nın ön koşulu.

**Akış**

- **FR-017**: Sentez, cosim ve IP export **komut satırından** uçtan uca çalıştırılabilmelidir.
- **FR-018**: Kart erişimi **hiçbir modülde derleme koşulu olamaz** (Anayasa Prensip V).

### Key Entities

- **Statevector**: `2^n` karmaşık genlik. Nitelikleri: kübit sayısı, sayı formatı, bankalama şeması, tamponlama (yerinde/ping-pong).
- **Kapı**: Tip (H/X/RZ/RZZ/CNOT), hedef kübit(ler), parametre (açı). Uygulandığı kübit `k`, erişim adımını `2^k` belirler.
- **Bankalama şeması**: Genlik indeksini fiziksel banka+ofsete eşleyen fonksiyon. Başarı ölçütü: tüm `k` için çakışmasızlık.
- **Sentez raporu**: II, latency, BRAM/DSP/LUT/FF, Fmax. **Bu fazın asıl kanıtıdır** — C-sim değil.
- **Doğrulama sonucu**: Fidelity değeri + kullanılan referans dosyası + kübit konvansiyonu.

---

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Altın referansa karşı durum fideliteti **≥ 0,99** (M eşiği), 8/12/16 kübit için ayrı ayrı ölçülmüş.
- **SC-002**: Sentez raporunda **BRAM ≤ %85** ve statevector tamamen çip-içi.
- **SC-003**: Sentez raporunda **II ≤ 4**, `k=0` ve `k=15` için ayrı ayrı raporlanmış.
- **SC-004**: Doğrulama zinciri kart bağlı **değilken** uçtan uca koşar ve başarıyla tamamlanır.
- **SC-005**: Sentez akışı tek komutla çalışır; iki ardışık koşum **aynı** II ve kaynak sayılarını verir.
- **SC-006**: Raporda tahmini (ölçülmemiş) tek bir sayı **bulunmaz**.
- **SC-007**: Bankalama denemesi sayısı **3'ü aşmaz**; her denemenin sentez verisi kayıtlıdır.
- **SC-008**: Hedef tutturulamadıysa, rapor bunu **açıkça** belirtir ve bir sonraki denemeyi yazar.

---

## Assumptions

- **Donanım hedefi**: Zynq-7020 (XC7Z020), PYNQ-Z2 üzerinde. BRAM toplamı ~630 KB (140 × BRAM36 = 280 × BRAM18K). **URAM yoktur** — Zynq-7000'de UltraRAM bulunmaz ([memory-budget.md](../../docs/memory-budget.md) §1'de not edildi; Anayasa Prensip III metni "BRAM/URAM" diyor, bu çipte tek seçenek BRAM).
- **Bankalama ve format seçimi**: Bilinçli olarak **boş bırakıldı**. `/speckit-plan` aşamasında kombinasyon olarak sunulacak (bkz. "bağımsız değil" bulgusu).
- **Fidelity eşiği**: M için ≥0,99, H için ≥0,999 — Faz 1'de sabitlenen değerlerle aynı ([001 spec](../001-veri-hatti-altin-referans/spec.md)).
- **II tabanı**: ≤4 kabul edilebilir; **II=1 hedef değil, İ etiketli** ([K-04](../000-kapsam-takvim/cut-plan.md)) — kovalanması yasak değil ama zorunlu da değil.
- **Test vektörleri**: Faz 1'in ürettiği `docs/measurements/reference_20260913_*_p{1,2}_n5.npy` dosyaları (16 kübit, complex128, norm 1,0, `qubit_order` metadata'da yazılı).
- **Referans formatı dönüşümü**: Kıyas, referansı **donanımın formatına indirgeyerek** yapılır (complex128 → float32/Q1.15), tersi değil ([001 research.md R-5](../001-veri-hatti-altin-referans/research.md)).

### ⚠️ NFR-02 ile genlik kıyası arasındaki görünür çelişki — çözümü

Prompt, dağıtılan arayüzün **yalnızca tek skaler beklenen değer** döndürmesini istiyor (NFR-02). Ama Faz 1, genlik-genlik kıyası için tam genlik vektörü üretti ([001 spec SC-008](../001-veri-hatti-altin-referans/spec.md)). Bu bir çelişki gibi görünüyor.

**Çözüm: iki ayrı yüzey vardır.**

| Yüzey | Ne döndürür | Ne zaman kullanılır |
|---|---|---|
| **Dağıtım arayüzü** (AXI4-Stream) | Tek skaler beklenen değer | Kartta koşum, Faz 5/10 kıyası |
| **Doğrulama yüzeyi** (C-sim/cosim testbench) | İç genlik dizisine doğrudan erişim | Faz 2 doğrulaması (FR-006, FR-016) |

Testbench, çekirdeğin iç belleğine erişebilir; dağıtılan IP erişemez. Bu ayrım FR-015 ve FR-016'da ayrı ayrı yazıldı ki ileride "genlik kıyası imkânsız" yanılgısı doğmasın.

---

## Dependencies

| Bağımlılık | Durum |
|---|---|
| Faz 1 altın referansı | ✅ Tamamlandı — `docs/measurements/reference_*.npy` hazır |
| [memory-budget.md](../../docs/memory-budget.md) bellek analizi | ✅ Tamamlandı (Faz 0 S-3) |
| **Vitis HLS kurulumu** | 🔴 **YOK** — [SK-04](../../docs/risk-register.md), karar tarihi H1 sonu. Sentez ölçütleri (SC-002, SC-003, SC-005) bu kurulmadan doğrulanamaz |
| **PYNQ-Z2 kartı** | 🟡 Teslim 14 Eylül ([DT-00](../../docs/risk-register.md)) — ama bu faz için **gerekmez** (US4) |
| Faz 5 (kartta koşum) | ⬅️ **Bu faza bağımlı** |

### Bu spec yazıldığında ne yapılabilir, ne yapılamaz

| Yapılabilir (kart/Vitis gerekmez) | Yapılamaz (Vitis gerekir) |
|---|---|
| Çekirdek C++ kodunu yazmak | Sentez raporu üretmek (SC-002, SC-003) |
| Bankalama şemasını kağıt üstünde çıkarmak | II ölçmek |
| Standart C++ derleyiciyle mantık doğrulaması | Cosim koşmak |
| Altın referansı okuyup kıyas kodunu yazmak | IP export |

Bu ayrım Anayasa Prensip V'in fiilen uygulanmasıdır: **Vitis gelene kadar duracak iş yok, sadece doğrulanamayacak ölçüt var.**

## Onay kapısı

Anayasa Prensip I gereği: bankalama şeması ve sayı formatı seçimi, iki karşılaştırma tablosu sunulup **yazılı onay** alınmadan koda dökülemez. Bu spec o seçimleri **bilinçli olarak boş bırakır**.
