# Faz 0 — Kapsam Triyajı (M / H / İ)

**Oluşturma**: 2026-09-10 · **Durum**: ONAY BEKLİYOR · **Bağlayıcılık**: Kullanıcı onayı olmadan bağlayıcı değildir.

İlgili belgeler: [schedule.md](schedule.md) · [cut-plan.md](cut-plan.md) · [spec.md](spec.md)

---

## 0. Envanter düzeltmesi (önce bu okunacak)

Faz 0 promptu "10 faz + yaklaşık 35 alt dal" varsayıyor. Kaynak belgeden çıkarılan **gerçek** envanter:

| Ölçü | Prompt varsayımı | Gerçek |
|------|------------------|--------|
| Faz sayısı | 10 | **15** (Faz 0–14) |
| Alt dal sayısı | ~35 | **67** |
| Ek bölüm (donanım kurulum kılavuzları) | — | 3 |

Kapsam, promptun varsaydığının **yaklaşık iki katı**. Bu, triyajı yumuşatmak için değil, **sertleştirmek** için bir gerekçedir. Aşağıdaki etiketleme bu gerçek envanter üzerinden yapılmıştır.

---

## 1. GÖREV 0 — Fizibilite Kapısı

### S1 — PYNQ-Z2 tedariki
**[CEVAPLANDI 2026-09-10 · DÜZELTİLDİ 2026-09-13]** Kart **erişilebilir ama henüz fiziksel olarak elde değil** — arkadaşta, teslim tarihi **14 Eylül 2026** (H1'in ilk günü). PYNQ imajı indirilmiş durumda.

Tedarik riski *kapalı sayılmıştı*; bu düzeltmeyle [DT-00](../../docs/risk-register.md) **yeniden açıldı** ve 14 Eylül'e bağlandı. Takvime etkisi yok (H1'in ilk günü), ama donanım gerektiren doğrulamalar (S-1 boot testi, DT-01) 14 Eylül'den önce yapılamaz — bu yüzden H1'in ilk günü donanımsız işlere ayrıldı (Prensip V).

### S2 — FPGA/HLS bilgisi olan destek
**[CEVAPLANDI 2026-09-10]** **VAR.** Danışman/bölüm tarafında FPGA bilen kişi mevcut ve öğrenci bu dönem **Reconfigurable Programming** dersini alacak; ders FPGA'i detaylı işleyecek.

### Karar kuralının uygulanması

> Kart VAR + donanımdan anlayan hoca VAR → **FPGA yolu, tereddütsüz.**

**KARAR: FPGA yolu seçildi.** Alternatif (saf yazılım) yol taban plandan çıkarıldı; yalnızca [cut-plan.md](cut-plan.md) K-02/K-03 tetikleri ateşlenirse geri çağrılır.

### ⚠️ Desteğin zamanlaması üzerine bir uyarı (yumuşatılmadı)

Destek **var** ama **ders hızında** geliyor. Projenin bankalama kararına ihtiyacı **3.–5. haftada** doğuyor; tipik bir Reconfigurable Programming müfredatı bellek mimarisi / HLS optimizasyonu konusuna dönem ortasından önce gelmez. Yani ders, sentez tıkandığı anda cebinde hazır olmayabilir.

**Bunun için bağlayıcı önlem** (takvime H2'ye yazıldı):

1. Dersin hocasına **2. hafta içinde**, müfredatın o konuya gelmesini beklemeden, şu somut soru sorulacak: *"2^k adımlı erişim deseni için tek bir BRAM bankalama şeması bütün k değerlerinde çakışmasız paralellik vermiyor. Bu problemin standart çözümü nedir; hangi kaynağa bakmalıyım?"*
2. Ders içeriğinin bu konuya ne zaman geleceği 1. hafta öğrenilecek ve takvime işaretlenecek. Eğer **6. haftadan sonraysa**, destek "geç" sayılır ve K-03 tetiği sıkı sürümüyle uygulanır.
3. Yedek dış kanal baştan belirlendi: AMD/Xilinx Community Forums (HLS board) + `r/FPGA`. Soru sorma ödevi H4'e yazıldı — tıkandıktan sonra değil, ilk sentez raporu çıkar çıkmaz.

**Ayrıca:** dersi almak bir destek olduğu kadar bir **yüktür**. Haftalık kapasite hesabında bu ders diğer dersler kümesinin içindedir; takvim bunu %100 değil, azaltılmış kapasiteyle modellemektedir.

---

## 2. GÖREV 1 — M / H / İ etiketlemesi

**Tanımlar**
- **M (Minimum / Çekirdek)** — olmadan savunmaya girilmez.
- **H (Hedef)** — projeyi iyi bir bitirme projesi yapar. Planlanan varış noktası.
- **İ (İddialı)** — zaman kalırsa. Kesilmesi projeyi zedelemez.

### 2.1 Kritik karar: Faz 2 (FPGA hızlandırıcı) M mi H mi?

**KARAR: Faz 2 = M — ama M'in sınırı yeniden tanımlanarak.**

Bu triyajın en önemli tek kararı budur. Gerekçe:

Faz 2'yi bütünüyle "kartta koşan bitstream" olarak tanımlarsak, tek bir sentez başarısızlığı projenin M kümesini yıkar — bu kırılgan bir plandır. Faz 2'yi bütünüyle H'ye düşürürsek, projenin adındaki "donanım hızlandırmalı" iddiası taban planda karşılıksız kalır — bu dürüst değildir.

Bu yüzden **M sınırı donanımın kendisinden değil, donanım tasarımının kanıtından geçirilir**:

| Seviye | Kapsam | Etiket |
|--------|--------|--------|
| Faz 2 çekirdeği | HLS çekirdeği **C-simülasyonda** Qiskit altın referansına karşı doğrulanıyor **+** sentez raporu kaynak (BRAM/DSP/LUT) ve II sayılarını veriyor | **M** |
| Faz 5 | Bitstream kartta koşuyor, gerçek gecikme/enerji ölçümü var | **H** |
| II=1, elle Verilog (2.4) | — | **İ** |

Bu ayrım **Anayasa Prensip V** (Donanımsız Süreklilik) ile birebir uyumludur: donanıma erişim hiçbir modülde derleme koşulu değildir.

### 2.2 İki senaryo için proje kimliği cümlesi

**Senaryo A — FPGA kartta koşuyor, gerçek ölçüm var (hedeflenen varış):**
> Kuantum-esinli rota optimizasyonunda kullanılan 16 kübite kadar statevector emülasyonunu PYNQ-Z2 üzerinde donanımda koşturan; sonucu Qiskit altın referansına karşı doğrulayan ve CPU referansına karşı gecikme ile enerji eksenlerinde **gerçek ölçümle** karşılaştıran bir donanım hızlandırma çalışması.

**Senaryo B — Sentez tutmuyor veya kartta koşmuyor (kesme sonrası):**
> Kuantum-esinli rota optimizasyonu için bir statevector emülatörünün donanım tasarımını yapan; statevector bankalama kısıtını 16 kübite kadar **nicel olarak karakterize eden**; ve bu tasarımın bu FPGA sınıfında hangi kaynak/II duvarına çarptığını sentez verisiyle gösteren bir **donanım fizibilite çalışması**.

Her iki cümle de savunulabilir. B, dürüst bir mühendislik sonucudur — "başarısızlık" değil, ölçülmüş bir sınırdır. Anayasa Prensip II gereği B senaryosunda da hiçbir rakam tahmin edilmez.

### 2.3 Faz düzeyi etiketler

| Faz | Başlık | Etiket | Gerekçe (tek cümle) |
|-----|--------|--------|---------------------|
| 0 | Kapsam Triyajı, Takvim ve Kesme Planı | **M** | Bu belge olmadan diğer 14 fazın hangi sırayla ve nereye kadar koşacağı belirsiz kalır. |
| 1 | Veri Hattı ve Altın Referans | **M** | Anayasa Prensip IV doğrudan buna dayanır; altın referans yoksa hiçbir hızlandırıcı çıktısı "doğru" sayılamaz. |
| 2 | FPGA / Vitis HLS Hızlandırıcı Çekirdek | **M** | Projenin özgün katkısı budur; §2.1'de tanımlanan C-sim + sentez raporu seviyesinde M. |
| 3 | L2 Backend, Kümeleme ve Karar Motoru | **H** | Çekirdek kıyas onsuz da yapılabilir; projeyi "ürün" gibi gösteren katman. |
| 4 | L0 Saha IoT (ESP32) ve Asenkron Tetikleme | **H** | Yalnızca 4.3 (güç ölçümü) M; saha IoT katmanının kalanı kıyas eksenini taşımıyor. |
| 5 | Zynq PS Entegrasyonu ve Güvenli Tünelleme | **H** | Kartta gerçek ölçüm hedeftir ama M, sentez raporu seviyesinde kapatılmıştır. |
| 6 | L3 Panel: Rol Tabanlı Uygulama | **H** | Demoda gösterilecek tek ekran (6.3) dışında kıyasa katkısı yok. |
| 7 | Mikroservis Tasarım Standardı, Hexagonal Yapı | **İ** | 7 alt dal, tek başına 3–4 hafta; çekirdek kıyas için hiçbiri gerekli değil. |
| 8 | API Gateway, Güvenlik Katmanı ve React | **H** | Panelin ayakta durması için minimum gateway gerekir, gerisi İ. |
| 9 | Mühendis Paneli: Süreç Şeffaflığı, IDE Köprüsü | **İ** | Tamamen anlatı/konfor katmanı; kesilmesi hiçbir ölçümü etkilemez. |
| 10 | Karşılaştırma Paneli ve Klasik Referans Çözücü | **M** | Kıyas ekseninin ta kendisi; bu olmadan "hızlandırma" iddiası ölçülemez. |
| 11 | Katmanlı Test Stratejisi ve CI/CD | **H** | Yalnızca 11.5 (donanımsız CI) M — Prensip V'i fiilen uygulayan tek mekanizma. ✅ **11.5 YAPILDI 2026-09-16** (`.github/workflows/csim-regression.yml` + `scripts/ci_fidelity_gate.py`); gerisi hâlâ H. |
| 12 | Teslimatlar: Tez, Sunum, Poster, Video | **M** | Tez teslim edilmezse ortada bitirme projesi yoktur. |
| 13 | Kenar Güvenliği: Tünel, WAF, Turnstile, CDN | **İ** | Akademik değerlendirmede sıfır ağırlık; operasyonel süs. |
| 14 | Gözlemlenebilirlik: Prometheus, Grafana | **İ** | Ölçüm dürüstlüğü Faz 10.3 protokolüyle sağlanır, Grafana ile değil. |

### 2.4 Alt dal düzeyi etiketler

**Faz 0 — Kapsam ve İşletim**

| Alt dal | Etiket | Gerekçe |
|---------|--------|---------|
| 0.1 Risk kaydı ve karar tarihleri | M | Kesme planının veri tabanı; tetikler burada yaşar. |
| 0.2 Depo iskeleti ve çalışma düzeni | M | Diğer 14 fazın çıktısını yazacağı yer. |
| 0.3 Sır denetimi ve servis bazlı konfigürasyon | H | Depo public olacaksa M'ye yükselir; şu an private varsayımıyla H. |
| 0.4 Kişisel veri (KVKK), saklama ve demo verisi | H | Sentetik/demo veri kullanılacaksa yükümlülük hafif. |
| 0.5 Yedekleme, geri yükleme ve felaket provası | İ | Git remote + haftalık push pratikte yeterli. |
| 0.6 Maliyet takibi ve ücretsiz katman limitleri | H | Railway limiti K-07 tetiğini besliyor. |
| 0.7 CLAUDE.md ve kalıcı hafıza dosyaları | M | 14 haftalık tek geliştirici projesinde bağlam kaybı en büyük verimlilik riski. |

**Faz 1 — Veri Hattı ve Altın Referans** — *3/3 alt dal M*

| Alt dal | Etiket | Gerekçe |
|---------|--------|---------|
| 1.1 OSM veri hattı ve deterministik önbellek | M | Determinizm olmadan tekrarlanabilir ölçüm yapılamaz (Prensip II). |
| 1.2 QUBO derleyicisi ve ceza katsayısı | M | Hem FPGA hem klasik çözücünün ortak girdisi; kıyasın adil olması buna bağlı. |
| 1.3 Altın referans QAOA ve doğrulama paketi | M | Prensip IV'ün doğrudan karşılığı. |

**Faz 2 — FPGA / Vitis HLS Çekirdek**

| Alt dal | Etiket | Gerekçe |
|---------|--------|---------|
| 2.0 Bankalama tuzağı: erken uyarı ve csim körlüğü | M | 2.1'e bu okunmadan geçilmez; projenin bir numaralı teknik riski burada tarif ediliyor. |
| 2.1 Bellek bütçesi ve kaynak hesap tablosu | M | Prensip III'ün uygulama noktası; her tasarım kararı buna karşı doğrulanır. |
| 2.2 HLS pipeline turu: II=1 avı | M | Çalışan pipeline M; **II=1 hedefinin kendisi İ** (bkz. K-04). |
| 2.3 Tcl derleme akışı ve donanımsız CI | H | 11.5 ile örtüşür; tekrarlanabilir sentez için değerli ama savunma şartı değil. |
| 2.4 Elle yazılmış Verilog modülü (RTL yetkinliği) | İ | Saf CV değeri; hiçbir ölçüm eksenini taşımıyor. |

**Faz 10 — Karşılaştırma ve Klasik Referans**

| Alt dal | Etiket | Gerekçe |
|---------|--------|---------|
| 10.1 Klasik çözücü servisi (iki mod) | M | Kıyasın diğer yakası; bu olmadan karşılaştıracak bir şey yok. |
| 10.2 Karşılaştırma ekranı ve ölçüm sunumu | H | Tablo + matplotlib figürü M'yi karşılar; interaktif ekran H. |
| 10.3 Ölçüm protokolü ve ön kayıt | M | Prensip II'nin uygulama mekanizması; eşikler ölçümden **önce** yazılır. |

**Faz 4 — Saha IoT ve Enerji**

| Alt dal | Etiket | Gerekçe |
|---------|--------|---------|
| 4.1 Firmware görev mimarisi (FreeRTOS) | İ | Enerji ekseni ESP32 olmadan da ölçülebilir. |
| 4.2 MQTT konu şeması ve mesaj sözleşmesi | İ | Saha katmanı kesilirse birlikte düşer. |
| 4.3 Güç ölçümü: kalibrasyon ve joule muhasebesi | **M** | Prensip II enerji rakamlarının gerçek ölçüme dayanmasını şart koşuyor; **ESP32'den bağımsız olarak FPGA/CPU güç rayına uygulanır**. |
| 4.4 Hibrit broker + tünel üzerinden L2 köprüsü | İ | Operasyonel bağlantı; ölçüme katkısı yok. |

**Faz 5 — Zynq PS Entegrasyonu**

| Alt dal | Etiket | Gerekçe |
|---------|--------|---------|
| 5.1 fpga-agent servis tasarımı ve durum yönetimi | H | Kartta koşum için gerekli; M sentez seviyesinde kapandı. |
| 5.2 Tünel, kimlik ve erişim politikası | İ | Yerel demo için gerekmiyor; uzaktan erişim konforu. |
| 5.3 Kıyas koşum matrisi ve nihai rapor | H | Senaryo A'nın ana çıktısı. |

**Faz 11 — Test ve CI/CD**

| Alt dal | Etiket | Gerekçe |
|---------|--------|---------|
| 11.1 Altı katman tanımı ve servis bazlı CI/CD | H | Tek geliştiricide altı katman ağır; iki katman (birim + C-sim) M'yi karşılar. |
| 11.2 Çapraz servis senaryo testleri | İ | Servis sayısı taban planda zaten düşük. |
| 11.3 Beyaz kutu: hexagonal, sorgu maliyeti | İ | Faz 7 İ olduğu için dayanağı kalmıyor. |
| 11.4 Kara kutu: React bileşenleri | İ | Panel İ ağırlıklı. |
| 11.5 Firmware, HLS ve donanımsız CI | **M** | Prensip V'i fiilen uygulayan tek mekanizma. |

**Faz 3 / 6 / 8 — Yazılım ve Arayüz (H çekirdeği + İ kuyruğu)**

| Alt dal | Etiket | Gerekçe |
|---------|--------|---------|
| 3.1 Servis çatısı kararı | H | Onay kapısı gerektiren mimari karar (Prensip I); ama çekirdek kıyas onsuz koşar. |
| 3.2 Servis sözleşmeleri ve veri modeli | H | Panel + kıyas servisinin konuşabilmesi için minimum. |
| 3.3 Karar motoru: veri, eğitim, dürüst değerlendirme | İ | Eğitim verisi üretimi başlı başına bir proje (bkz. K-08). |
| 3.4 Kuyruk, idempotency ve geri basınç | İ | Tek kullanıcılı demoda yük yok. |
| 6.1 Rol matrisi ve yetkilendirme | İ | Tek kullanıcılı demoda rol ayrımı gösteriş. |
| 6.2 Kimlik doğrulama ve Railway dağıtımı | İ | Yerel demo yeterli. |
| 6.3 Mühendis konsolu: FPGA durumu, podlar, Grafana | H | Jüri demosunda gösterilecek **tek** ekran. |
| 6.4 Şoför arayüzü (mobil) | İ | Saha katmanı kesilirse dayanağı kalmıyor. |
| 6.5 Admin konsolu ve denetim kaydı | İ | — |
| 8.1 Gateway yönlendirme, CORS, güvenlik başlıkları | H | Panel ayakta duracaksa minimum. |
| 8.2 JWT access/refresh, cookie, iptal | İ | Kimlik doğrulama İ olduğu için birlikte düşer. |
| 8.3 Rate limiting ve global exception handler | İ | — |
| 8.4 Uzak API katmanı: OSM/OSRM/Nominatim | H | 1.1 ile büyük ölçüde örtüşüyor; tekrar iş çıkarmamaya dikkat. |
| 8.5 React mimarisi, güvenlik, durum yönetimi | İ | 6.3 tek ekranla karşılanır. |

**Faz 7 / 9 / 13 / 14 — Tamamı İ**

| Faz | Alt dallar | Etiket | Gerekçe |
|-----|-----------|--------|---------|
| 7 | 7.1 – 7.7 (7 dal) | İ | Hexagonal mimari + outbox + Kafka/RabbitMQ + Elasticsearch: tek geliştirici için 3–4 hafta, kıyasa sıfır katkı. |
| 9 | 9.1 – 9.4 (4 dal) | İ | Süreç şeffaflığı ve IDE köprüsü; ölçüm eksenlerinin hiçbirini taşımıyor. |
| 13 | 13.1 – 13.4 (4 dal) | İ | Kenar güvenliği akademik değerlendirmede ağırlıksız. |
| 14 | 14.1 – 14.4 (4 dal) | İ | Ölçüm dürüstlüğü 10.3 protokolüyle sağlanıyor. |

**Faz 12 — Teslimatlar** — *4/4 alt dal M* (12.1 şekil biriktirme, 12.2 tez, 12.3 sunum+poster, 12.4 video+prova). Gerekçe: teslim edilmeyen proje savunulamaz; 12.1 ayrıca ölçüm verisinin kaybolmasını önler.

---

## 3. Dağılım raporu — ve kuralın ihlali

### Alt dal sayısına göre

| Etiket | Alt dal | Oran |
|--------|---------|------|
| M | 17 | %25 |
| H | 13 | %19 |
| İ | 37 | %55 |
| **Toplam** | **67** | **%100** |

### Zamana göre (asıl önemli olan)

Kodlama penceresi H1–H11'dir. H7 %40 kapasite, H8 ve H11 tampon → **etkin kapasite ≈ 8.4 hafta**.

| Küme | Tahmini efor | Etkin kapasitenin oranı |
|------|-------------|------------------------|
| M (kodlama kısmı) | ≈ 6.9 hafta | **%82** |
| H | ≈ 1.5 hafta | %18 |
| İ | 0 hafta | %0 |

### 🔴 Kural ihlali — açıkça raporlanıyor

> Kural: *"M kümesi 14 haftanın en fazla yarısını almalı."*
> Gerçek: **M ≈ %82.**

Bu ihlal **kapsam küçültülerek düzeltilemez**, çünkü M kümesi zaten Anayasa'nın dayattığı asgari settir:
Prensip IV → Faz 1 zorunlu · Prensip III → Faz 2.1 zorunlu · Prensip II → Faz 10.3 ve 4.3 zorunlu.

**Bunun anlamı, yumuşatılmadan:**

1. **İ kümesi taban planda YOKTUR.** 37 alt dal "zaman kalırsa" değil, **"planda yok"** statüsündedir. Faz 7, 9, 13, 14 tamamen taban plan dışıdır.
2. **H kümesi bir haftalık nefes payına sıkışmıştır.** H işlerinden en az yarısı büyük olasılıkla kesilecektir; hangisinin önce kesileceği [cut-plan.md](cut-plan.md) §3'te sıralanmıştır.
3. **Tamponlar dokunulmazdır.** H8 ve H11 tamponlarına iş yazmak, M kümesini riske atmak demektir. Tampon yenirse kesme İ'den değil doğrudan H'den başlar.
4. **Kapsam genişletme talebi geldiğinde** önce bu tablo gösterilecektir. Yeni bir iş eklemek için önce eşdeğer bir iş çıkarılmalıdır.

---

## 4. Onay

Bu belge **onay bekliyor**. Onaylanana kadar bağlayıcı değildir. Onaylandıktan sonra her fazın `/speckit-plan` adımı bu belgeye ve [cut-plan.md](cut-plan.md)'ye karşı denetlenecektir.
