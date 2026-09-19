# Feature Specification: Faz 5 — Zynq PS + Kartta Koşum

**Feature Branch**: `003-zynq-ps-kartta-kosum`

**Created**: 2026-09-16

**Status**: Draft

**Input**: User description: "Faz 5 — Zynq PS + kartta koşum. Kapsam: 5.1 fpga-agent servisi (PS tarafında çalışan, overlay yükleyen ve çekirdeği koşturan servis) ve 5.3 kıyas koşum matrisi (gecikme + enerji, CPU'ya karşı). 5.2 (tünel, kimlik, uzaktan erişim) kapsam DIŞI — İ etiketli. Girdi: Faz 2'nin IP export'u. Hedef: HLS tahminlerini gerçek kart ölçümüne çevirmek."

## Bu fazın tek cümlelik gerekçesi

Faz 2 sonunda elde olan **her sayı bir tahmindir**: 37,3 ms gecikme sentez
sonrası HLS kestirimi, 9,122 ns zamanlama Vivado kestirimi, enerji ise hiç
ölçülmedi. Anayasa Prensip II tahmini rakamların nihai rapora yazılmasını
yasaklıyor. Bu faz, o yasağı kaldıran tek fazdır.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Çekirdek kartta koşuyor ve çıktısı doğru (Priority: P1)

Araştırmacı, sentezlenmiş çekirdeği PYNQ-Z2 kartına yükler, bir QAOA devresi
koşturur ve çıktının Qiskit altın referansıyla uyuştuğunu görür.

**Why this priority**: Bu doğrulanmadan diğer her şey anlamsızdır. Gecikme ve
enerji ölçümü, **yanlış sonuç üreten** bir çekirdekte de alınabilir; hızlı ama
yanlış bir devrenin hiçbir değeri yoktur (Anayasa Prensip IV). Ayrıca bu tek
başına savunulabilir bir sonuçtur: "16 kübitlik statevector emülatörü FPGA'da
çalışıyor ve doğrulandı."

**Independent Test**: Kart bağlanır, çekirdek yüklenir, n=16 p=2 devresi
koşulur, çıkan genlik vektörü altın referansa karşı fidelity hesaplanır.
Gecikme veya enerji ölçümü gerekmez.

**Acceptance Scenarios**:

1. **Given** kart boot etmiş ve çekirdek yüklenmiş, **When** n=16 p=2 devresi
   koşulur, **Then** çıktının altın referansa karşı fidelity'si ≥ 0,99'dur
2. **Given** aynı çekirdek ve aynı girdi, **When** devre iki kez koşulur,
   **Then** iki çıktı **birebir aynıdır** (belirlenimcilik)
3. **Given** çekirdek kartta koşmuş, **When** çıktı C-simülasyon sonucuyla
   karşılaştırılır, **Then** ikisi de aynı altın referansa karşı **aynı**
   fidelity'yi verir — donanım ile simülasyon ayrışmamıştır
4. **Given** kart yeniden başlatılmış, **When** çekirdek tekrar yüklenir,
   **Then** önceki koşumun kalıntısı sonucu etkilemez (durumsuzluk)

---

### User Story 2 - Gecikme kartta ölçülüyor (Priority: P2)

Araştırmacı, çekirdeğin bir devreyi tamamlamasının **gerçekte** ne kadar
sürdüğünü karttan okur ve HLS tahminiyle karşılaştırır.

**Why this priority**: Projenin adındaki "donanım hızlandırmalı" iddiasının
yarısı budur. US1 olmadan anlamsız, ama US3 (enerji) olmadan da yayımlanabilir
bir sonuçtur.

**Independent Test**: Kartta koşum süresi en az 10 tekrarla ölçülür; medyan ve
yayılım raporlanır. Enerji düzeneği gerekmez.

**Acceptance Scenarios**:

1. **Given** çekirdek kartta koşuyor, **When** aynı devre en az 10 kez
   koşulur, **Then** gecikme **medyan ve yayılımıyla** raporlanır — tek koşum
   rakamı kabul edilmez
2. **Given** ölçülen gecikme, **When** HLS tahminiyle (p=2 için 37,3 ms)
   karşılaştırılır, **Then** sapma **gizlenmeden** kaydedilir ve nedeni
   araştırılır
3. **Given** ölçüm, **When** rapora yazılır, **Then** ölçümün **neyi** kapsadığı
   açıkça belirtilir (yalnız çekirdek mi, veri aktarımı dahil mi)

---

### User Story 3 - Enerji kartta ölçülüyor (Priority: P3)

Araştırmacı, bir devre koşumunun kaç joule tükettiğini ölçer.

**Why this priority**: Prensip II enerji rakamlarının gerçek ölçüme dayanmasını
şart koşuyor ve bu, kıyasın ikinci eksenidir. P3 olmasının sebebi **tedarik**:
ölçüm modülü henüz elde değil (risk DT-02) ve US1/US2 onsuz tamamlanabilir.

**Independent Test**: Ölçüm düzeneği kalibre edilir, boştaki ve yük altındaki
güç ayrı ayrı okunur, bir koşumun joule maliyeti hesaplanır.

**Acceptance Scenarios**:

1. **Given** ölçüm düzeneği kurulmuş, **When** kalibrasyon yapılır, **Then**
   bilinen bir yükte okunan değer beklenen değerden **%5'ten az** sapar
2. **Given** kalibre düzenek, **When** kart boştayken ve devre koşarken güç
   okunur, **Then** ikisi **ayrı ayrı** kaydedilir — koşum enerjisi farktan
   hesaplanır
3. **Given** enerji ölçümü, **When** rapora yazılır, **Then** ölçümün kapsamı
   (tüm kart mı, yalnız çip mi) açıkça belirtilir

---

### User Story 4 - Kıyas matrisi ve nihai rapor (Priority: P3)

Araştırmacı, FPGA ve CPU sonuçlarını aynı problem ve aynı parametreler üzerinde
yan yana koyan bir tablo üretir.

**Why this priority**: Faz 5'in tez çıktısı budur, ama US1–US3'ün verisi
olmadan yazılamaz. Kendi başına bir "iş" değil, **birleştirme** adımıdır.

**Independent Test**: Toplanmış ölçümlerden tablo üretilir; her hücrenin
kaynağı (tarih, koşum sayısı, konfigürasyon) izlenebilir.

**Acceptance Scenarios**:

1. **Given** FPGA ve CPU ölçümleri, **When** karşılaştırma yapılır, **Then**
   iki taraf da **aynı p ve aynı problem** üzerinde koşmuştur
2. **Given** kıyas tablosu, **When** bir hücreye bakılır, **Then** o sayının
   hangi ölçümden geldiği izlenebilir
3. **Given** tamamlanmış kıyas, **When** hızlanma oranı yazılır, **Then** oran
   **ölçülmüş** değerlerden hesaplanmıştır ve yayılım birlikte verilmiştir

---

### Edge Cases

- **Kart koşum sırasında yanıt vermezse** ne olur? Koşum zaman aşımına uğramalı
  ve kısmî/bozuk sonuç **geçerli ölçüm sayılmamalıdır**.
- **Kartta ölçülen gecikme tahminden çok saparsa** (örneğin 2 kat) ne yapılır?
  Sapma gizlenmez; nedeni araştırılır ve bulunamazsa **bulunamadığı yazılır**.
- **Kartta üretilen sonuç C-simülasyondan farklıysa?** Bu, tasarımın değil
  **doğrulamanın** krizidir: hangisinin doğru olduğu altın referansla belirlenir
  ve fark kapanmadan hiçbir hız/enerji rakamı raporlanmaz.
- **Ölçüm modülü gelmezse** (risk DT-02) enerji ekseni düşer; gecikme ekseni
  tek başına raporlanır ve enerjinin **neden** ölçülemediği yazılır.
- **Kart ölçüm sırasında ısınır/kısılırsa** ardışık koşumlar yavaşlayabilir;
  bu yüzden koşumlar arası durum kaydedilmeli, yayılım raporlanmalıdır.
- **Bitstream kaybolursa** ne olur? Yeniden üretimi saatler sürer ve araç
  sürümüne bağlıdır — bu yüzden saklanması bu fazın kapsamındadır.
- **Kart ile ana makine arasındaki veri aktarımı** ölçüme dahil mi? Kapsam
  açıkça yazılmazsa karşılaştırma anlamsızlaşır.

## Requirements *(mandatory)*

### Functional Requirements

**Koşum ve doğrulama (US1)**

- **FR-001**: Sistem, sentezlenmiş çekirdeği karta yükleyebilmeli ve yüklemenin
  başarılı olduğunu **doğrulayabilmelidir** — "yükledim" varsayımı yetmez.
- **FR-002**: Sistem, bir QAOA devresini kartta koşturabilmeli ve sonuç genlik
  vektörünü ana makineye aktarabilmelidir.
- **FR-003**: Sistem, kart çıktısını **altın referansa** karşı doğrulamalı ve
  fidelity'yi raporlamalıdır (Anayasa Prensip IV).
- **FR-004**: Sistem, kart çıktısını **C-simülasyon çıktısıyla** da
  karşılaştırmalıdır; ikisinin ayrışması bir hata işaretidir.
- **FR-005**: Çekirdek **durumsuz** olmalıdır: her koşum bilinen bir başlangıç
  durumundan başlar, önceki koşumun kalıntısı taşınmaz.
- **FR-006**: Koşum **belirlenimci** olmalıdır: aynı girdi aynı çıktıyı verir.

**Ölçüm (US2, US3)**

- **FR-007**: Sistem, bir koşumun süresini ölçebilmeli ve ölçümün **neyi
  kapsadığını** (çekirdek / veri aktarımı / uçtan uca) ayırt edebilmelidir.
- **FR-008**: Her ölçüm **en az 10 tekrar** içermeli; medyan ve yayılım
  birlikte raporlanmalıdır. Tek koşum rakamı rapora giremez.
- **FR-009**: Sistem, **kartın** güç tüketimini boştayken ve yük altında ayrı
  ayrı ölçebilmelidir.
- **FR-009b**: Sistem, **CPU tarafının** enerjisini de ölçebilmelidir.
- **FR-009c**: Her iki taraf da **aynı yöntemle** ölçülmelidir: boştaki güç ve
  yük altındaki güç ayrı ayrı okunur, işin maliyeti **farktan** hesaplanır.
  Alet simetrik olmak zorunda değildir, **yöntem zorundadır**.
- **FR-009d**: Tek bir koşum hiçbir güç ölçeriyle görünmeyecek kadar kısadır
  (~37 ms). Ölçüm, iş yükü bir süre **döngüye alınarak** yapılmalı ve koşum
  başına enerji toplam enerjinin koşum sayısına bölünmesiyle bulunmalıdır.
- **FR-010**: Enerji ölçüm düzeneği, ölçüm alınmadan önce **kalibre edilmeli**
  ve kalibrasyon kaydı saklanmalıdır.
- **FR-011**: Ölçüm protokolü, ölçümler **alınmadan önce** yazılmalıdır
  (ön kayıt) — sonuca bakıp protokol ayarlanamaz.

**Kıyas (US4)**

- **FR-012**: Karşılaştırma, FPGA ve CPU tarafında **aynı problem, aynı p ve
  aynı kübit sayısı** üzerinde yapılmalıdır.
- **FR-013**: Her raporlanan sayı **izlenebilir** olmalıdır: tarih, kod sürümü,
  konfigürasyon ve koşum sayısı kaydedilir.
- **FR-014**: Tahmini hiçbir değer nihai rapora girmemelidir (Prensip II).
  Ölçülemeyen bir eksen varsa **ölçülemediği yazılır**, tahminle doldurulmaz.

**Süreklilik ve saklama**

- **FR-015**: Kart erişilemez olduğunda geliştirme durmamalıdır; kartsız yol
  (C-sim/cosim) çalışır kalmalıdır (Anayasa Prensip V).
- **FR-016**: Karta yüklenen ikili çıktı (bitstream/overlay) **saklanmalıdır**;
  yeniden üretimi saatler sürer ve araç sürümüne bağlıdır. Hangi kod
  sürümünden üretildiği kaydedilmelidir.

### Key Entities

- **Koşum (run)**: Kartta yapılan tek bir devre çalıştırması. Nitelikleri:
  kübit sayısı, p, giriş parametreleri, çıkan genlik vektörü, süre, enerji,
  zaman damgası, kod sürümü.
- **Ölçüm serisi**: Aynı konfigürasyonun en az 10 koşumu. Nitelikleri: medyan,
  min, max, yayılım, koşum sayısı, protokol sürümü.
- **Kıyas satırı**: Bir konfigürasyonun FPGA ve CPU sonuçlarının yan yana
  duran hâli. Her hücre bir ölçüm serisine işaret eder.
- **Donanım yapıtı**: Karta yüklenen ikili (bitstream/overlay) ve onu üreten
  kod sürümü + araç sürümü.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Kartta koşan çekirdeğin çıktısı, altın referansa karşı **fidelity
  ≥ 0,99** verir; n=16 için hem p=1 hem p=2'de ayrı ayrı doğrulanır.
- **SC-002**: Aynı girdiyle iki ardışık kart koşumu **birebir aynı** çıktıyı
  üretir (belirlenimcilik).
- **SC-003**: Kart çıktısı ile C-simülasyon çıktısı **aynı** fidelity'yi verir;
  fark varsa bu fark açıklanmadan faz kapanmaz.
- **SC-004**: Gecikme, konfigürasyon başına **en az 10 koşumun** medyanı ve
  yayılımı olarak raporlanır; tek koşum rakamı hiçbir yerde geçmez.
- **SC-005**: Enerji ölçüm düzeneği, bilinen bir yükte **%5'ten az** sapmayla
  okuma yapar (kalibrasyon ölçütü).
- **SC-006**: Bir devre koşumunun enerji maliyeti **joule cinsinden** ölçülür;
  boştaki tüketim ayrı kaydedilir. Bu, **kıyasın iki tarafı için de** geçerlidir
  — tek taraflı enerji rakamı karşılaştırma üretmez.
- **SC-007**: Kıyas tablosundaki her hücre, üretildiği ölçüm serisine kadar
  **izlenebilir**: tarih, kod sürümü, koşum sayısı.
- **SC-008**: Nihai raporda **tahmini tek bir sayı bile** yoktur; ölçülemeyen
  eksen varsa ölçülemediği ve nedeni yazılıdır.
- **SC-009**: Ölçüm protokolü, ilk ölçüm alınmadan **önce** yazılmış ve
  değişmez biçimde kaydedilmiştir (ön kayıt).
- **SC-010**: Karta yüklenen ikili çıktı saklanmıştır ve hangi kod sürümünden
  üretildiği kayıtlıdır.

## Assumptions

- **Kart elde ve çalışıyor.** 2026-09-15'te doğrulandı: boot logu alındı,
  Jupyter yanıt verdi, örnek overlay yüklendi (risk DT-01 kapalı).
- **Çekirdek sentezden geçti ve zamanlamayı tutturdu.** Vivado implementasyonu
  koşuldu: post-route 9,122 ns, dört kaynak da bütçede (Faz 2, ADR 0009).
- **Karşılaştırma tarafı hazır ve TEMİZ ölçüldü** (2026-09-19): CPU (Qiskit
  Aer, p=2) turbo **32,75 ms**, plato **41,93 ms**; 7474 koşum, plato oturduğu
  doğrulandı. CPU enerjisi de ölçüldü: **0,644 J/koşum** (batarya delta
  yöntemi). ⚠️ Daha önceki 77,6/92,7 ms rakamları arka planda cosim koşarken
  alınmıştı ve **geçersizdir**.
- **Gecikmede FPGA'nın tahmini avantajı YOK**: 37,28 ms, CPU'nun turbo ve
  plato değerlerinin arasına düşüyor (başabaş). Fazın asıl beklenen sonucu
  **enerji ekseninde**; bu US3'ü daha kritik yapar.
- **Altın referanslar depoda.** n=16 (p=1, p=2) gerçek TSP referansları ve
  n=8/12 sentetik referanslar commit edilmiş durumda.
- **Kıyas parametreleri Faz 2 ile aynı tutulur**: n=16, p=1 ve p=2 birincil;
  n=8 ve n=12 ikincil. Bu, ölçümlerin Faz 2 sonuçlarıyla karşılaştırılabilir
  kalmasını sağlar.
- **Uzaktan erişim kapsam dışıdır.** 5.2 (tünel, kimlik, erişim politikası)
  İ etiketlidir ve bu spec'e dahil değildir. Kıyas ölçümlerinin hiçbiri
  ağdan geçmez, dolayısıyla tünelin yokluğu ölçümü etkilemez.
- **Enerji ölçüm modülleri 2026-09-17'de temin edilecek** (risk DT-02).
  Gereken: **3× INA219** — kart (12 V), dizüstü (19 V), yedek.
  ⚠️ **Dizüstü modülü 0,01 Ω ŞÖNTLÜ OLMAK ZORUNDA — bu bir güvenlik
  gereğidir, tercih değil.** Adaptör ölçüldü: **20 V / 6 A / 120 W**.
  - Standart 0,1 Ω şöntte 5 A'de harcanan güç **I²R = 2,5 W**; karttaki tipik
    SMD direnç ~1 W'lık, yani **yanar**.
  - Ayrıca INA219'un şönt girişi **±320 mV** ile sınırlı; 0,1 Ω × 6 A = 600 mV
    → kırpar, okuma anlamsızlaşır.
  - 0,01 Ω'da: 5 A'de 0,25 W (güvenli), çözünürlük 20 V'ta ~20 mW — ölçülecek
    fark 20–80 W olduğu için fazlasıyla yeterli.
  - Bara gerilimi sınırı 26 V; 20 V içinde ama **pay dar** — o modüle 24 V'luk
    başka bir kaynak bağlanmamalı.
  - Karttaki modül standart **0,1 Ω** kalmalı: PYNQ ~0,3 A çeker ve 0,1 Ω
    ~1,2 mW çözünürlük verir; ölçülecek fark yalnızca 0,5–2 W olduğu için
    burada hassasiyet gerekli.
  - ⚠️ Adaptörün orijinal kablosu **kesilmemeli**: namlu jak uzatma kablosu
    araya alınır, ölçüm bitince çıkarılır.
  US3 bu tedarike bağlıdır; **US1 ve US2 bağlı değildir** ve tedariği
  beklemeden başlayabilir.
- **Ölçüm yöntemi kararlaştırıldı (2026-09-16, kullanıcı onayı).** Referans
  makine **dizüstü** olduğu için her iki taraf da **aynı aletle** ölçülür:
  **INA219**, kartta 12 V girişinde, dizüstünde 19 V DC girişinde. Bu, alet
  simetrisini de sağlar ve karşılaştırmanın savunmasını en kolay hâle getirir.
  - Elenen 1 — **duvar prizi ölçeri**: gerekmiyor. (Masaüstü olsaydı CPU
    rayına fiziksel erişim pratik olmadığı için tek seçenek oydu.)
  - Elenen 2 — **multimetre**: AC tarafında P ≠ V×I (anahtarlamalı güç
    kaynağının güç faktörü 1 değil, hata %40'a varabilir) ve şebekede seri
    akım ölçümü güvenli değil. Daha temel sorun: multimetre **integral
    almaz**; gereken büyüklük joule, anlık watt değil.
  - Elenen 3 — **RAPL**: yalnızca işlemci paketini sayar; kart tarafında tüm
    kart ölçülürken bu asimetri karşılaştırmayı savunulamaz kılar. Ayrıca
    WSL2 altında MSR erişimi güvenilir değil.
- **Delta yöntemi bir zorunluluktur, tercih değil.** Dizüstü ekranı ~10 W
  çeker, tüm PYNQ kartı ~3 W; mutlak değerler karşılaştırılsaydı sonucu ekran
  belirlerdi. Fark alınınca ekran, diskler ve boştaki her şey **iki tarafta da**
  sadeleşir.
- **Ölçümler sistem düzeyindedir, bileşen düzeyinde değil.** Kart tarafında
  ölçülen tüm kartın gücüdür (yalnız PL değil); CPU tarafında da benzer şekilde
  bileşen izolasyonu beklenmemektedir. Karşılaştırma bu yüzden *"aynı iş için
  uçtan uca sistem enerjisi"* olarak kurulur ve rapora böyle yazılır.
- **Bitstream saklanması bu fazın kapsamındadır.** Depo kuralları büyük ikili
  dosyaların commit edilmesini yasaklıyor, ama yeniden üretimi saatler sürüyor
  ve araç sürümüne bağlı — dolayısıyla saklama yeri tanımlanmadan faz kapanmaz.

## Dependencies

- **Faz 2 çıktısı**: sentezlenmiş çekirdeğin donanım paketi. ⚠️ Şu an mevcut
  değil — ara bir sentez koşusu sırasında silindi; yeniden üretimi ~15 dakika.
- **Faz 1 çıktısı**: Qiskit altın referansları (depoda).
- **4.3 (güç ölçümü)**: US3'ün ön koşulu. Kendi başına **M** etiketli bir iş.
- **Donanım**: PYNQ-Z2 kartı, güç kaynağı, ölçüm modülü (henüz yok).

## Out of Scope

- **5.2 — tünel, kimlik doğrulama, uzaktan erişim politikası** (İ etiketli)
- **5.4+ / ESP32 saha katmanı** (İ etiketli, Faz 4)
- Panel/gösterge arayüzü (Faz 6)
- Çoklu kart veya ölçekleme senaryoları
- 16 kübitin üzerine çıkma (Anayasa Prensip III üst sınırı)
