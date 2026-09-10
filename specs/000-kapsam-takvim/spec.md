# Feature Specification: Faz 0 — Kapsam Triyajı, Takvim ve Kesme Planı

**Feature Branch**: `000-kapsam-takvim`

**Created**: 2026-09-10

**Status**: Draft — onay bekliyor

**Input**: User description: "Faz 0 — Kapsam Triyajı, Takvim ve Kesme Planı. Bu faz KOD ÜRETMEZ. Kalan on fazın hangi sırayla, hangi kapsamda koşacağını ve neyin ne zaman kesileceğini bağlar."

**Çıktı belgeleri**: [scope-triage.md](scope-triage.md) · [schedule.md](schedule.md) · [cut-plan.md](cut-plan.md)

> **Bu faz kod üretmez.** Çıktısı üç karar belgesidir. Kabul ölçütleri de bu belgelerin *kullanılabilirliği* üzerinden tanımlanmıştır.

---

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Karar tarihi geldiğinde ne yapılacağını bilmek (Priority: P1)

Proje sahibi, yüksek riskli bir işin karar tarihine geldiğinde belgeyi açar, o riskin ölçütüne bakar, ölçüm sonucunu ölçütle karşılaştırır ve **yazılana uyar**. Karar anında yeni bir muhakeme yapmaz — muhakeme baştan yapılmıştır.

**Why this priority**: Bu, fazın var oluş sebebidir. Panikle kesmek ile planlı kesmek arasındaki farkı yaratan tek şey, kararın *önceden* verilmiş olmasıdır. Diğer tüm çıktılar bunu destekler.

**Independent Test**: Rastgele bir hafta seçilir; o haftaya düşen tetik belgeden bulunur, ölçütü okunur ve "ölçüt tutmazsa ne yapılır" adımı **ek yorum gerektirmeden** uygulanabilir mi diye bakılır.

**Acceptance Scenarios**:

1. **Given** H4 sonuna gelinmiş ve ilk sentez raporu elde, **When** proje sahibi kesme planını açar, **Then** K-02'nin ölçütünü (BRAM ≤ %85) rapordan okunabilir bir sayıyla karşılaştırabilir ve tutmazsa uygulanacak üç adımı sırayla görebilir.
2. **Given** bir tetiğin ölçütü tutmadı, **When** proje sahibi "ölçüt tutmazsa" bölümünü uygular, **Then** hangi kapsamın düştüğü ve proje iddiasının nasıl yeniden yazılacağı belgede yazılıdır; yeni karar üretmesi gerekmez.
3. **Given** deneme sayısı üst sınıra ulaştı (K-03: 3 bankalama denemesi), **When** proje sahibi dördüncü denemeyi yapmak ister, **Then** belge bunu açıkça yasaklar ve alternatif yolu gösterir.

---

### User Story 2 - Hangi işin yapılmayacağını bilmek (Priority: P1)

Proje sahibi, haftalık işi seçerken hangi alt dalın taban planda olduğunu, hangisinin "zaman kalırsa", hangisinin **hiç planlanmadığını** tek tabloda görür. Kapsam genişletme talebi geldiğinde bu tabloyu gösterir.

**Why this priority**: Envanter gerçekte 15 faz ve 67 alt daldır — promptun varsaydığının iki katı. Neyin *yapılmayacağının* yazılı olmaması, 14 haftalık takvimin sessizce taşması demektir.

**Independent Test**: Kaynak belgedeki 67 alt dalın her biri için etiket tablosunda bir satır var mı ve her satırda bir gerekçe cümlesi var mı diye sayılır.

**Acceptance Scenarios**:

1. **Given** proje sahibi Faz 7'ye başlamak ister, **When** triyaj belgesine bakar, **Then** Faz 7'nin tamamının "İ — taban plan dışı" olduğunu ve gerekçesini görür.
2. **Given** yeni bir iş talebi geldi, **When** triyaj belgesi açılır, **Then** "yeni iş eklemek için eşdeğer bir iş çıkarılmalıdır" kuralı yazılıdır.
3. **Given** tampon 1 haftadan fazla yenmiş, **When** kesme planının kesme sırası bölümüne bakılır, **Then** hangi işin **önce** kesileceği numaralı bir sırayla yazılıdır ve sıranın nerede duracağı (M sınırı) işaretlidir.

---

### User Story 3 - Haftalık olarak takvimden sapmayı ölçmek (Priority: P2)

Proje sahibi her Cuma 10 dakikada: o haftanın tetiğini kontrol eder, planlanan çıktı ile eldeki çıktıyı karşılaştırır, tampondan ne kadar yendiğini kaydeder ve gelecek hafta verilecek kararı not eder.

**Why this priority**: Sapma erken görülmezse tampon sessizce tükenir. Ritüel olmadan tampon muhasebesi yapılmaz.

**Independent Test**: Ritüel şablonu bir hafta için doldurulur; 10 dakikada tamamlanabiliyor ve dört sorunun hepsi belgedeki verilerle cevaplanabiliyor mu diye bakılır.

**Acceptance Scenarios**:

1. **Given** hafta sonu geldi, **When** ritüel şablonu doldurulur, **Then** dört başlığın (tetik / sapma / tampon / gelecek hafta) hepsi takvim ve kesme planındaki verilerle cevaplanabilir.
2. **Given** üst üste iki hafta "1 hafta+" sapma var, **When** ritüel doldurulur, **Then** belge o hafta yeni iş açılmamasını ve yalnızca kesme yapılmasını şart koşar.

---

### User Story 4 - Danışman ve jüriye kapsamı gerekçeli anlatmak (Priority: P3)

Danışman "neden bu kadarını yaptın, şunu neden yapmadın?" diye sorduğunda, proje sahibi etiket tablosunu ve kesme kayıtlarını gösterir. Negatif sonuç çıkarsa savunma metni hazırdır.

**Why this priority**: Değerlendirme anında değer yaratır ama projenin yürümesi buna bağlı değildir.

**Independent Test**: "FPGA hiçbir eksende kazanmıyor" senaryosu için belgede hazır bir savunma metni ve kanıt paketi listesi var mı diye bakılır.

**Acceptance Scenarios**:

1. **Given** kıyas sonucu negatif çıktı, **When** kesme planı K-10 açılır, **Then** yeniden yazılmış iddia cümlesi, dört maddelik kanıt paketi ve "hangi koşulda kazanırdı" analizi yazılıdır.
2. **Given** bir faz hiç yapılmadı, **When** danışman sorar, **Then** o fazın etiketi ve tek cümlelik gerekçesi tablodan gösterilir.

---

### Edge Cases

- **Karar tarihi düşük kapasiteli bir haftaya düşerse ne olur?** H7 mihenk taşı vize hazırlık haftasına denk gelir; işin kendisi H6'ya çekilmiş, H7 yalnızca doğrulama haftası yapılmıştır.
- **İki tetik aynı anda ateşlenirse?** Şiddet sütunu sıralamayı verir: Kritik olanlar (K-02, K-03, K-04, K-05, K-10) önce işlenir; Düşük şiddetliler (K-06, K-07, K-08, K-09) zaten taban plan dışı işleri keser ve gecikebilir.
- **Kesme sırası M sınırına dayanırsa?** Kesme durur ve triyaj belgesinin yeniden onaylanması gerekir; M kümesi kendiliğinden kesilemez.
- **Destek (ders/hoca) ihtiyaç anından sonra gelirse?** Triyaj belgesi §1'de "destek geç" durumu tanımlıdır: ders içeriği H6'dan sonra o konuya geliyorsa K-03 sıkı sürümüyle uygulanır ve dış kanal baştan devreye alınır.
- **Ölçüt hiç ölçülemezse (ölçüm yapılamadı)?** Ölçülemeyen ölçüt "tutmadı" sayılır. Anayasa Prensip II gereği tahmini değerle ölçüt geçilmiş sayılamaz.

---

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Fizibilite kapısının iki sorusu (S1 tedarik, S2 destek) belgede **cevaplanmış** olarak yer almalı ve karar kuralının hangi dalının uygulandığı açıkça yazılmalıdır.
- **FR-002**: Kaynak belgedeki **her faz ve her alt dal** M / H / İ etiketlerinden birini ve **tek cümlelik bir gerekçe** taşımalıdır.
- **FR-003**: Etiket dağılımı hem sayıca hem **zamana göre** raporlanmalı; "M kümesi 14 haftanın en fazla yarısı" kuralına uyum veya ihlal **açıkça** belirtilmelidir.
- **FR-004**: Faz 2'nin (FPGA hızlandırıcı) M mi H mi olduğu gerekçeli olarak karara bağlanmalı ve **iki ayrı proje kimliği cümlesi** (donanım çalışıyor / çalışmıyor) yazılmalıdır.
- **FR-005**: Fazlar arası bağımlılıklar bir **Mermaid diyagramı** ile gösterilmeli, kritik yol işaretlenmelidir.
- **FR-006**: Donanım/sentez beklerken paralel koşacak işler, hangi bekleme penceresinde koşacakları ile eşleştirilmiş olarak listelenmelidir.
- **FR-007**: 14 haftalık takvim tablosu her hafta için **gerçek tarih**, ana iş, paralel iş ve **somut/gösterilebilir** hafta sonu çıktısı içermelidir.
- **FR-008**: Takvim, kod yazımının **H11 sonunda** bitmesini, son üç haftanın teslimata ayrılmasını ve en az **iki tam tampon haftası** bulundurmasını sağlamalıdır.
- **FR-009**: Kullanıcının bildirdiği düşük kapasite haftaları (H7, H8, H13, H14) takvimde işaretlenmeli ve kapasite kaybı açıkça muhasebeleştirilmelidir.
- **FR-010**: Takvim, FPGA çekirdeği ve CPU kıyasını öne alma kuralına uymalı; **H7 sonunda en az tek eksende** bir CPU-vs-FPGA kıyas tablosu elde edilmelidir. Sapma varsa gerekçelendirilmelidir.
- **FR-011**: Kesme planı, belirtilen dokuz riskin tamamını ve "FPGA hiçbir eksende kazanmıyor" senaryosunu kapsamalıdır.
- **FR-012**: Her kesme tetiği **RİSK / KARAR TARİHİ / ÖLÇÜT / ÖLÇÜT TUTMAZSA / KAYIP** biçimini eksiksiz taşımalı; ÖLÇÜT **ölçülebilir** olmalıdır.
- **FR-013**: İterasyonla çözülmeye çalışılan riskler (bankalama, II) için **deneme üst sınırı** sayı olarak yazılmalıdır.
- **FR-014**: "FPGA hiçbir eksende kazanmıyor" senaryosu için yeniden yazılmış iddia cümlesi, kanıt paketi ve hazırlık ödevi **şimdiden** yazılmış olmalıdır.
- **FR-015**: Tampon yendiğinde uygulanacak **kesme sırası** numaralı ve M sınırında duracak şekilde tanımlanmalıdır.
- **FR-016**: Haftalık kontrol ritüeli **10 dakikada** tamamlanabilecek, doldurulabilir bir şablon olarak verilmelidir.
- **FR-017**: Belgeler, kullanıcı onayı olmadan bağlayıcı olmadıklarını açıkça belirtmeli ve onay sonrası her `/speckit-plan` adımının bu belgelere karşı denetleneceğini yazmalıdır.
- **FR-018**: Bu faz **hiçbir uygulama kodu üretmemelidir**.

### Key Entities

- **Faz**: Kaynak belgedeki 15 iş kümesinden biri. Nitelikleri: numara, başlık, M/H/İ etiketi, gerekçe, bağımlı olduğu fazlar.
- **Alt dal**: Bir fazın altındaki 67 iş biriminden biri. Nitelikleri: numara, başlık, etiket, gerekçe.
- **Kesme tetiği**: Yüksek riskli bir iş için önceden verilmiş karar. Nitelikleri: kod (K-XX), risk tanımı, karar tarihi (hafta), ölçülebilir ölçüt, tutmazsa uygulanacak adımlar, kayıp, şiddet.
- **Hafta**: Takvimin bir birimi. Nitelikleri: numara, tarih aralığı, kapasite (tam/düşük/tampon), ana iş, paralel iş, somut çıktı.
- **Proje kimliği**: Donanımın çalıştığı ve çalışmadığı senaryolar için projenin ne olduğunu anlatan cümle.

---

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Kaynak belgedeki 15 fazın ve 67 alt dalın **%100'ü** bir etiket ve bir gerekçe cümlesi taşır; etiketsiz kalem sayısı sıfırdır.
- **SC-002**: Yüksek riskli işlerin **%100'ü** için bir karar tarihi ve ölçülebilir bir ölçüt tanımlıdır; ölçütü "ölçülebilir mi?" testinden geçmeyen tetik sayısı sıfırdır.
- **SC-003**: Proje sahibi, rastgele seçilmiş bir karar tarihinde ne yapacağını belgeye bakarak **2 dakikadan kısa sürede** söyleyebilir.
- **SC-004**: Haftalık kontrol ritüeli **10 dakika içinde** tamamlanır ve dört başlığın hepsi belgedeki verilerle cevaplanabilir.
- **SC-005**: Takvim, en az **iki tam tampon haftası** ve düşük kapasite haftalarının açık muhasebesini içerir; tamponsuz hafta sayısı beyan edilenle tutarlıdır.
- **SC-006**: Kod yazımı için ayrılan son hafta **H11**'dir ve teslimat penceresi **üç haftadır** (H12–H14).
- **SC-007**: H7 sonunda en az bir eksende CPU-vs-FPGA kıyas tablosu üretilebilecek şekilde bağımlılıklar sıralanmıştır.
- **SC-008**: "FPGA hiçbir eksende kazanmıyor" senaryosu için savunma metni, kanıt paketi ve hazırlık ödevi belgede **ölçümden önce** yazılıdır.
- **SC-009**: Belgede uygulama kodu (kaynak dosya, betik, konfigürasyon) üretilmemiştir — üretilen dosya sayısı: yalnızca karar belgeleri.

---

## Assumptions

Aşağıdakiler, kullanıcı tarafından belirtilmediği için makul varsayım olarak alınmıştır. Yanlışsa belge güncellenir.

- **Dönem takvimi**: Hafta 1, 14 Eylül 2026 Pazartesi'den başlar (kullanıcı 15 Eylül dedi; 15 Eylül 2026 Salı olduğu için o haftanın Pazartesi'si esas alındı). Hafta 14, 20 Aralık 2026'da biter.
- **Düşük kapasite**: H7, H8, H13, H14 için kapasite **≈%40** varsayılmıştır (kullanıcı bu haftaları bildirdi, oranı bildirmedi).
- **Resmi tatil**: 29 Ekim 2026 (Perşembe) H7 içindedir; başka resmi tatil takvime işlenmemiştir.
- **Fidelity eşiği**: M için ≥0.99, H için ≥0.999 (kullanıcı eşik vermedi; statevector emülasyonu için yaygın kabul). Eşik Faz 10.3'te ölçümden önce nihai olarak sabitlenecektir.
- **BRAM doluluk tavanı**: %85 (yerleştirme/yönlendirme için pay bırakan yaygın pratik).
- **II tabanı**: ≤4 kabul edilebilir; II=1 hedef değil İ etiketli.
- **Kübit alt sınırı**: 12 kübit ve tek şerit; bunun altı fizibil değil sayılır.
- **Depo görünürlüğü**: Depo private varsayılmıştır (0.3 sır denetimi bu yüzden H, M değil).
- **Veri**: Sentetik/demo kargo verisi kullanılacaktır; gerçek kişisel veri işlenmeyecektir (0.4 bu yüzden H).
- **Destek zamanlaması**: Reconfigurable Programming dersinin bellek mimarisi/HLS konusuna ne zaman geleceği bilinmiyor; H1'de öğrenilecek ve H6'dan sonraysa "destek geç" sayılacaktır.
- **Enerji ölçümü**: INA219 ölçümü ESP32'ye bağımlı değildir; gerekirse doğrudan seri okuma ile FPGA güç rayına uygulanır.

---

## Onay kapısı

Anayasa Prensip I gereği bu belge **onay bekliyor**. Onaylanmadan bağlayıcı değildir. Onaylandıktan sonra her fazın `/speckit-plan` adımı [scope-triage.md](scope-triage.md), [schedule.md](schedule.md) ve [cut-plan.md](cut-plan.md)'ye karşı denetlenecektir.
