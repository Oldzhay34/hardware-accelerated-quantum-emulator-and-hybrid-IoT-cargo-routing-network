# Feature Specification: Faz 1 — Veri Hattı ve Altın Referans

**Feature Branch**: `001-veri-hatti-altin-referans`

**Created**: 2026-09-13

**Status**: Draft — araştırma/onay döngüsü bekliyor

**Input**: User description: "Faz 1 — Veri Hattı ve Altın Referans. OpenStreetMap İstanbul verisinden N×N gerçek sürüş-süresi mesafe matrisi üreten konteynerli bir servis ve 5 duraklı TSP için yazılmış, sonraki tüm donanım çıktılarının karşılaştırılacağı bir 'altın referans' QAOA çözücüsü."

**Kapsam dışı**: FPGA çekirdeği (Faz 2), ESP32 saha katmanı (Faz 4), panel (Faz 6/8).

> ⚠️ **Bu spec kod üretmez ve teknoloji seçimi yapmaz.** Prompt'un çalışma kuralı (ARAŞTIR → KIYASLA → ONAY BEKLE → KODLA) ve Anayasa Prensip I gereği, rotalama motoru ve kuantum kütüphanesi seçimi `/speckit-plan` aşamasında karşılaştırma tablosuyla sunulup **kullanıcı onayı** alındıktan sonra kesinleşir.

---

## Neden bu faz kritik yolda

[Faz 0 bağımlılık grafiğinde](../000-kapsam-takvim/schedule.md) Faz 1, kritik yolun ilk halkası ve **en kırılgan geçiş** olarak işaretlendi: Faz 2 (HLS çekirdeği) bu fazın altın referansı olmadan doğrulanamaz (Anayasa Prensip IV). Risk kaydındaki [TK-01](../../docs/risk-register.md) bu yüzden "H2 sonunda altın referans koşmuyorsa zincirin tamamı kayar" diyor.

### Problem boyutu donanımdan türetilmiştir

"5 durak" keyfi bir sayı değildir. One-hot TSP kodlamasında başlangıç şehri sabitlendiğinde kübit sayısı `(N−1)²` olur:

| Durak sayısı | Gereken kübit | Anayasa tavanı (16) |
|---:|---:|---|
| 4 | 9 | ✅ rahat |
| **5** | **16** | ⚠️ **tam tavanda** |
| 6 | 25 | 🔴 %56 aşıyor |

Yani 5 duraklı problem, Faz 2'nin **en zor** konfigürasyonunu hedefler. [Bellek bütçesi analizi](../../docs/memory-budget.md) 16 kübitin PYNQ-Z2'de "sığıyor" değil **"sınırda"** olduğunu gösterdiği için, bu fazın ürettiği referansın 16 kübitte çalışması bir kolaylık değil, bir gerekliliktir.

### İki farklı ölçek

| Bileşen | Ölçek | Neden |
|---|---|---|
| Mesafe matrisi servisi | **N ≤ 30 durak** | Klasik çözücü kıyası (Faz 10) bu ölçekte anlamlı olur |
| Altın referans QAOA | **N = 5 durak** | 16 kübit tavanı (yukarıdaki tablo) |

Servis daha büyük problemleri üretebilmelidir; kuantum referansı üretemez. Bu asimetri bilinçlidir.

---

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Donanım çıktısını doğrulayacak bir referansa sahip olmak (Priority: P1)

Proje sahibi, Faz 2'de ürettiği HLS çekirdeğinin çıktısını karşılaştıracak, doğruluğundan emin olduğu bir referans sonuca ihtiyaç duyar. Referans, aynı problemi bağımsız ve güvenilir bir yolla çözer; ayrıca **genlik düzeyinde** karşılaştırmaya izin verecek kadar ayrıntılı çıktı verir.

**Why this priority**: Anayasa Prensip IV'ün doğrudan karşılığı — bu olmadan hiçbir hızlandırıcı çıktısı "çalışıyor" sayılamaz. Faz 2 bu çıktı olmadan doğrulanamaz, dolayısıyla kritik yolun ilk halkasıdır.

**Independent Test**: 5 duraklı bir problem verilir; referans çözücü çalıştırılır; ürettiği en iyi tur, aynı problemin kaba kuvvetle (5! = 120 tur) bulunan optimaliyle karşılaştırılır. Eşleşiyorsa referans güvenilirdir.

**Acceptance Scenarios**:

1. **Given** 5 duraklı bir mesafe matrisi, **When** altın referans çözücü çalıştırılır, **Then** bulduğu en iyi tur kaba kuvvet optimaliyle **birebir aynıdır**.
2. **Given** aynı problem ve aynı ayarlar, **When** çözücü iki kez çalıştırılır, **Then** iki koşumun sonucu aynıdır (rastgelelik varsa tohum sabitlenir).
3. **Given** çözüm süreci tamamlandı, **When** çıktı incelenir, **Then** yalnızca en iyi tur değil, **tüm durumların olasılık dağılımı** da erişilebilir — Faz 2'nin genlik-genlik karşılaştırması buna bağlıdır.

---

### User Story 2 - Tekrarlanabilir ve gerçekçi mesafe verisi (Priority: P1)

Proje sahibi, ölçümlerinin girdisi olacak mesafe matrisini üretir. Matris, İstanbul'un **gerçek yol ağından** türeyen sürüş sürelerini içerir ve aynı girdiyle her zaman aynı sonucu verir.

**Why this priority**: Anayasa Prensip II (ölçüm dürüstlüğü) tekrarlanabilirlik olmadan sağlanamaz. Risk kaydındaki [VR-02](../../docs/risk-register.md) bunu "aynı sorgu iki kez farklı sonuç veriyorsa ölçüm tekrarlanamaz" diye işaretliyor; kıyas verisinin tamamı bu matrise dayanacağı için sonradan fark edilen bir kayma tüm ölçümleri çöpe atar.

**Independent Test**: Aynı durak listesi iki kez gönderilir; dönen iki matris bayt düzeyinde karşılaştırılır. Ayrıca sistem çevrimdışıyken (ağ kesikken) önbellekten aynı matris üretilebilmelidir.

**Acceptance Scenarios**:

1. **Given** sabit bir durak listesi, **When** matris iki kez üretilir, **Then** iki çıktı **bit-birebir aynıdır**.
2. **Given** matris bir kez üretilmiş ve önbelleğe alınmış, **When** ağ bağlantısı kesilir ve aynı istek tekrarlanır, **Then** matris önbellekten döner ve sonuç değişmez.
3. **Given** 30 duraklık bir liste, **When** matris istenir, **Then** servis sonucu döndürür (ölçülen süre rapora yazılır — tahmin edilmez).
4. **Given** temiz bir makine, **When** kurulum talimatı izlenir, **Then** aynı veri sürümünden aynı matris üretilir (veri kaynağı sürümü sabitlenmiştir).

---

### User Story 3 - Hem kuantum hem klasik çözücünün ortak girdisi (Priority: P2)

Proje sahibi, mesafe matrisini her iki çözücünün de kabul ettiği ortak bir problem formuna dönüştürür. Aynı form, Faz 2'nin donanım çekirdeğine ve Faz 10'un klasik çözücüsüne girdi olur.

**Why this priority**: Kıyasın **adil** olması buna bağlı. İki çözücü farklı problem formülasyonlarıyla çalışırsa, aradaki fark algoritma farkı değil formülasyon farkı olur ve kıyas geçersizleşir.

**Independent Test**: Üretilen problem formu için, geçerli her turun "enerjisi" hesaplanır ve o turun gerçek uzunluğuyla tutarlı olduğu doğrulanır. Geçersiz turlar (bir şehri iki kez ziyaret eden vb.) geçerli turlardan **her zaman** daha yüksek enerji almalıdır.

**Acceptance Scenarios**:

1. **Given** bir mesafe matrisi, **When** problem formuna dönüştürülür, **Then** geçerli turların enerji sıralaması, gerçek tur uzunluğu sıralamasıyla aynıdır.
2. **Given** kısıt ihlali içeren bir aday çözüm, **When** enerjisi hesaplanır, **Then** enerjisi **her** geçerli turdan yüksektir (ceza katsayısı yeterince büyük seçilmiştir).
3. **Given** ceza katsayısı belirlenirken, **When** matristeki en büyük mesafe değişir, **Then** katsayı da buna göre ayarlanır (sabit bir sayıya gömülmez).

---

### User Story 4 - Tek komutla yeniden kurulabilirlik (Priority: P3)

Proje sahibi veya danışman, temiz bir makinede tek bir komutla tüm veri hattını ayağa kaldırıp altın referansı üretebilir.

**Why this priority**: 14 hafta boyunca bu hat defalarca kurulacak; ayrıca [donanımsız süreklilik](../../.specify/memory/constitution.md) (Prensip V) ve felaket senaryoları ([backup.md](../../docs/backup.md)) bunu gerektirir. Değer yaratır ama ölçüm eksenini taşımaz.

**Independent Test**: Depo temiz bir dizine klonlanır, README'deki tek komut çalıştırılır, altın referans çıktısı üretilir. Süre ölçülür ve yazılır.

**Acceptance Scenarios**:

1. **Given** temiz bir makine ve klonlanmış depo, **When** README'deki tek komut çalıştırılır, **Then** veri hattı ayağa kalkar ve altın referans sonucu üretilir.
2. **Given** kurulum tamamlandı, **When** aynı komut tekrar çalıştırılır, **Then** önbellek kullanılır ve ilk koşumdan hızlı tamamlanır.

---

### Edge Cases

- **Ceza katsayısı çok küçük seçilirse?** Geçersiz turlar geçerli turlardan düşük enerji alır ve çözücü kısıt ihlal eden "çözümler" üretir. US3 kabul senaryosu 2 bunu yakalar; katsayı matristeki en büyük mesafeden **büyük** olacak şekilde türetilir.
- **QAOA derinliği (p) yetersizse?** Referans optimali bulamayabilir. Bu bir **hata değil, ölçülecek bir özelliktir**: kaç tekrarda optimali bulduğu oranı raporlanır. Kaba kuvvet doğrulaması her durumda mutlak gerçeği verir.
- **İki durak arasında yol yoksa (ada, kesik ağ)?** Matris sonsuz/tanımsız değer içerir. Bu durum tespit edilmeli ve durak listesi reddedilmelidir — sessizce büyük bir sayıyla doldurulmamalıdır (Prensip II: uydurma değer yok).
- **Kamuya açık rotalama servisi istek sınırı uygularsa?** Ölçüm turunun ortasında engellenme, tekrarlanabilirliği bozar. [cost.md](../../docs/cost.md) bunu kota riski olarak işaretledi; çözüm önbelleğin kalıcı ve commit'lenebilir olması.
- **Aynı koordinat listesi farklı sırayla gelirse?** Matris satır/sütun sırası girdi sırasına bağlıdır; önbellek anahtarı bunu hesaba katmalıdır, yoksa yanlış önbellek isabeti oluşur.

---

## Requirements *(mandatory)*

### Functional Requirements

**Mesafe matrisi (FR-01 karşılığı)**

- **FR-001**: Sistem, verilen koordinat listesinden **N×N sürüş-süresi matrisi** üretmelidir.
- **FR-002**: Matris değerleri **gerçek yol ağından** türemelidir — kuş uçuşu mesafe kabul edilmez (asimetrik maliyetler, tek yönlü yollar ve Boğaz geçişleri korunmalıdır).
- **FR-003**: Sistem en az **30 duraklık** listeleri işleyebilmelidir.
- **FR-004**: Matris üretimi **deterministik** olmalıdır: aynı girdi + aynı veri sürümü → bit-birebir aynı çıktı.
- **FR-005**: Kullanılan harita verisinin sürümü **sabitlenmeli** ve kayıt altına alınmalıdır; "en güncel veriyi indir" davranışı yasaktır.
- **FR-006**: Üretilen matris **diske önbelleklenmeli** ve çevrimdışı tekrar kullanılabilmelidir.
- **FR-007**: Ulaşılamayan durak çifti tespit edilirse sistem **açık bir hata** vermelidir; tanımsız değer uydurulmamalıdır.

**Problem formülasyonu (FR-02 karşılığı)**

- **FR-008**: Sistem, mesafe matrisini **one-hot TSP** formülasyonuna dönüştürmelidir.
- **FR-009**: Kısıt ihlallerinin cezası, matristeki **en büyük mesafeden büyük** olacak şekilde matristen **türetilmelidir** (sabit değer gömülmez).
- **FR-010**: Geçerli bir turun enerjisi ile gerçek tur uzunluğu arasındaki ilişki **doğrulanabilir** olmalıdır.
- **FR-011**: Aynı formülasyon hem kuantum referansı hem de ileride klasik çözücü (Faz 10) tarafından kullanılabilmelidir.

**Altın referans (FR-03 / NFR-03 karşılığı)**

- **FR-012**: Sistem, **5 duraklı** TSP problemini kuantum-esinli bir yaklaşımla çözen bir referans üretmelidir.
- **FR-013**: Referans, en az **iki farklı derinlik** (p=1 ve p=2) için çalıştırılabilmelidir.
- **FR-014**: Referans çıktısı yalnızca en iyi turu değil, **tüm durumların olasılık dağılımını** da içermelidir — Faz 2'nin genlik düzeyinde karşılaştırma yapabilmesi için zorunludur.
- **FR-015**: Referans sonucu **kaba kuvvetle** (5! = 120 tur) bağımsız olarak doğrulanmalıdır.
- **FR-016**: Referansın optimali bulma **oranı** ölçülmeli ve raporlanmalıdır (bulamaması hata değil, ölçülecek bir özelliktir).
- **FR-017**: Çözücünün ham durum vektörüne (genliklere) **doğrudan erişim** sağlanmalıdır.

**Tekrarlanabilirlik ve raporlama**

- **FR-018**: Tüm rastgelelik kaynakları **tohumlanabilir** olmalı; sabit tohumla sonuçlar tekrarlanmalıdır.
- **FR-019**: Sistem **tek komutla** ayağa kaldırılabilmelidir.
- **FR-020**: Raporlanan her sayı (süre, bellek, başarı oranı) **gerçek ölçümden** gelmelidir; tahmini değer yazılamaz (Anayasa Prensip II).

### Key Entities

- **Durak listesi**: Sıralı koordinat kümesi. Sıra anlamlıdır (matris indekslerini belirler).
- **Mesafe matrisi**: N×N sürüş süresi tablosu; asimetrik olabilir. Kimliği: durak listesi + harita veri sürümü.
- **Problem formu (QUBO)**: Mesafe matrisinden türeyen ikili optimizasyon problemi. Nitelikleri: değişken sayısı `(N−1)²`, ceza katsayısı.
- **Referans çözüm**: En iyi tur + tüm durumların olasılık dağılımı + kullanılan derinlik (p) + tohum.
- **Kaba kuvvet doğrulaması**: 5 durak için tüm turların tam listesi ve gerçek optimal.

---

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Aynı durak listesi iki kez işlendiğinde üretilen matrisler **bit-birebir aynıdır** (fark sayısı: 0).
- **SC-002**: 5 duraklı problemde referansın bulduğu en iyi tur, kaba kuvvet optimaliyle **%100 oranında** eşleşir.
- **SC-003**: Kısıt ihlali içeren aday çözümlerin **tamamı**, geçerli turların tümünden yüksek enerji alır (ihlal sayısı: 0).
- **SC-004**: Sistem çevrimdışıyken önbellekten matris üretimi **%100** başarılıdır.
- **SC-005**: Temiz bir makinede tek komutla kurulum, altın referans çıktısını üretecek şekilde **tamamlanır** (süre ölçülür ve raporlanır).
- **SC-006**: Referansın optimali bulma oranı p=1 ve p=2 için **ölçülmüş** ve raporlanmıştır (hedef bir değer dayatılmaz; ölçüm dürüstlüğü esastır).
- **SC-007**: Raporda tahmini (ölçülmemiş) tek bir sayı **bulunmaz**.
- **SC-008**: Referans çözücünün ham genliklerine erişim, 16 kübitlik bir durum için **doğrulanmıştır** (Faz 2 karşılaştırmasının ön koşulu).

---

## Assumptions

- **Problem boyutu**: 5 durak = 16 kübit, Anayasa Prensip III tavanına birebir oturuyor. Daha büyük problemler (6+ durak) kuantum referansı için **kapsam dışıdır**.
- **Matris ölçeği**: Servisin hedef üst sınırı 30 duraktır (prompt'un araştırma kriterinden türetildi); bu, Faz 10'un klasik kıyası için yeterli kabul edilmiştir.
- **Harita verisi**: İstanbul'u kapsayan, sürümü sabitlenmiş bir OpenStreetMap dökümü kullanılacaktır. Tam kaynak ve sürüm `/speckit-plan` aşamasında kesinleşir.
- **Sürüş süresi**: Trafik modeli **yoktur** — serbest akış (free-flow) süreleri kullanılır. Zamana bağlı trafik, [data-governance.md §2.2](../../docs/data-governance.md)'de sentetik verinin yakalamadığı sınır olarak zaten kayıtlıdır.
- **Kuantum kütüphanesi**: Anayasa Prensip IV **Qiskit'i adıyla bağlayıcı kılıyor** (bkz. aşağıdaki not). Karşılaştırma yine de yapılacak, ancak Qiskit'in dışına çıkmak anayasa değişikliği gerektirir.
- **Rastgelelik**: Çözücüdeki tüm rastgelelik tohumlanabilir varsayılmıştır; değilse bu bir kısıt olarak raporlanacaktır.
- **Test verisi**: 5 duraklık test problemleri [sentetik veri üreticisinden](../../scripts/generate_synthetic_data.py) (Faz 0.4) alınabilir — gerçek adres kullanılmaz.

### ⚠️ Anayasa ile gerilim: kuantum kütüphanesi seçimi

Prompt, "Qiskit Aer vs PennyLane" karşılaştırması istiyor. Ancak [Anayasa Prensip IV](../../.specify/memory/constitution.md) şunu diyor:

> *"Her hızlandırıcı çıktısı, **Qiskit** referans simülasyonuna karşı doğrulanmadan 'çalışıyor' olarak kabul edilemez."*

Yani seçim **kısmen kapalı**: karşılaştırma yapılabilir ve yapılmalıdır (gerekçe belgelenir), fakat sonuç Qiskit dışında çıkarsa anayasanın **değiştirilmesi** gerekir — bu da `plan.md` Complexity Tracking tablosunda gerekçelendirilmeyi gerektirir. Bu gerilim `/speckit-plan` aşamasında kullanıcıya açıkça sunulacaktır.

---

## Dependencies

| Bağımlılık | Durum |
|---|---|
| Faz 0 kapsam/takvim/kesme planı | ✅ Tamamlandı |
| Sentetik veri üreticisi (test problemleri için) | ✅ Tamamlandı ([Faz 0.4](../../docs/data-governance.md)) |
| Konteyner çalıştırma ortamı (yerel) | ⚪ Kurulum durumu `/speckit-plan` aşamasında doğrulanacak |
| Faz 2 (HLS çekirdeği) | ⬅️ **Bu faza bağımlı** — tersi değil |

## Onay kapısı

Anayasa Prensip I gereği: rotalama motoru ve kuantum kütüphanesi seçimi, karşılaştırma tabloları sunulup **yazılı onay** alınmadan koda dökülemez. Bu spec o seçimleri **bilinçli olarak boş bırakır**.
