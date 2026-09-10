# Faz 0 — Kesme Tetikleri (Cut Plan)

**Oluşturma**: 2026-09-10 · **Durum**: ONAY BEKLİYOR

İlgili belgeler: [scope-triage.md](scope-triage.md) · [schedule.md](schedule.md)

> Bu belgenin varlık sebebi tek cümlede: **sonradan panikle kesmek, baştan planlı kesmekten çok daha pahalıdır.**
> Aşağıdaki her tetiğin karar tarihi geldiğinde ölçüt bakılır ve yazılana **uyulur**. Ölçüt tutmadığında "bir hafta daha deneyeyim" demek, bu belgeyi geçersiz kılar.

---

## 1. Tetik özeti

| # | Risk | Karar tarihi | Şiddet |
|---|------|-------------|--------|
| K-01 | Kart bozuk / yanmış / boot etmiyor | **H1 sonu** | Yüksek |
| K-02 | HLS sentezi BRAM'e sığmıyor | **H4 sonu** | Kritik |
| K-03 | Bankalama çözülemiyor (çakışma kalkmıyor) | **H5 sonu** | Kritik |
| K-04 | II hedefi tutmuyor | **H6 sonu** | Kritik |
| K-05 | Qiskit doğrulaması fidelity eşiğini geçmiyor | **H3 sonu** | Kritik |
| K-06 | Tünel kurumsal ağda çalışmıyor | **H9 sonu** | Düşük |
| K-07 | ESP32 donanımı gecikti / gelmedi | **H5 sonu** | Düşük |
| K-08 | Railway maliyet/limit aşımı | **H10 sonu** | Düşük |
| K-09 | ML karar motoru için veri üretilemiyor | **H9 sonu** | Düşük |
| K-10 | 🔴 **FPGA hiçbir eksende kazanmıyor** | **H9 sonu** | Kritik — kimlik |

---

## 2. Tetikler

### K-01 · Kart bozuk / boot etmiyor

- **RİSK**: PYNQ-Z2 elde ama arızalı; boot etmiyor, JTAG görünmüyor veya güç rayında sorun var.
- **KARAR TARİHİ**: **H1 sonu (20 Eylül 2026)**
- **ÖLÇÜT**: PYNQ imajı yazılmış SD kart ile kart boot ediyor, ağdan Jupyter arayüzü açılıyor ve örnek bir overlay yükleniyor. Evet/hayır.
- **ÖLÇÜT TUTMAZSA**:
  1. H2 içinde ikinci bir SD kart + farklı güç adaptörüyle tekrar denenir (donanım arızası ile imaj arızası ayrıştırılır).
  2. H2 sonunda hâlâ boot etmiyorsa: proje **Senaryo B kimliğine** geçer ([scope-triage.md](scope-triage.md) §2.2). Faz 5 tamamen düşer, Faz 2 C-sim + sentez raporu seviyesinde M olarak devam eder.
  3. Kart tedariki paralel yürütülür ama **takvim buna bağlanmaz**.
- **KAYIP**: Gerçek gecikme ve enerji ölçümü. Kıyas, sentez raporundaki tahmini gecikme + Qiskit/CPU gerçek ölçümü şeklinde asimetrik kalır — ve bu **rapora asimetrik olduğu açıkça yazılır** (Prensip II: tahmini değer gerçek ölçüm gibi sunulamaz).

---

### K-02 · HLS sentezi BRAM'e sığmıyor

- **RİSK**: 16 kübit statevector + çalışma bellekleri PYNQ-Z2'nin BRAM bütçesini aşıyor; tasarım DDR'a taşmadan sentezlenemiyor (Anayasa Prensip III ihlali).
- **KARAR TARİHİ**: **H4 sonu (11 Ekim 2026)** — ilk sentez raporu elde.
- **ÖLÇÜT**: Sentez raporunda **BRAM kullanımı ≤ %85** ve statevector'ün tamamı çip-içi. Ölçülebilir, rapordan okunur.
- **ÖLÇÜT TUTMAZSA** — sırayla, her adım en fazla 3 gün:
  1. **Kübit sayısı düşürülür**: 16 → 14 → 12. (14 kübit statevector'ü 16'nın dörtte biri kadar yer kaplar; genelde tek adımda çözer.)
  2. Yetmezse **sayı formatı daraltılır**: çift duyarlık → tek duyarlık → sabit noktalı Q1.15. Her daraltma sonrası K-05 fidelity ölçütü **yeniden koşulur** — daraltma doğruluğu bozarsa geri alınır.
  3. Yetmezse **şerit (lane) sayısı azaltılır**: paralel işlem hattı sayısı yarıya iner.
- **NİHAİ SINIR**: **12 kübit ve tek şerit.** Bunun altına inilmez; inilmesi gerekiyorsa tasarım bu FPGA sınıfında fizibil değildir → Senaryo B.
- **KAYIP**: 16 kübit iddiası. Rapordaki "16 kübite kadar" ifadesi gerçek sayıyla değiştirilir. Ölçek küçüldüğü için hızlanma oranı da düşer — ve düşük ölçekte CPU'nun kazanma olasılığı artar (bkz. K-10).

---

### K-03 · Bankalama çözülemiyor

- **RİSK**: Projenin bir numaralı teknik riski. Kapının uygulandığı kübit `k` için erişim adımı `2^k` değiştiğinden, tek bir bankalama şeması bütün adımlarda çakışmasız paralellik vermiyor. C-simülasyon bu soruna **kördür** — C kodu doğru çalışır, sentez sonucu on kat yavaş çıkar.
- **KARAR TARİHİ**: **H5 sonu (18 Ekim 2026)**
- **ÖLÇÜT**: **Deneme üst sınırı = 3 farklı bankalama şeması.** Her denemenin sentez raporu ve II sayısı `specs/000-kapsam-takvim/haftalik/` altına kaydedilir. H5 sonunda en az bir şema, tüm `k` değerleri için **çakışmasız erişim** gösteriyor olmalı (sentez raporundaki II ve bellek çakışma uyarıları üzerinden okunur).
- **ÖLÇÜT TUTMAZSA**:
  1. **Dördüncü deneme yapılmaz.** Süre kutusu kapanır.
  2. Tasarım **çakışmayı kabul eden** basit şemaya sabitlenir: tek banka, seri erişim, yüksek II.
  3. Proje iddiası yeniden yazılır: hızlanma iddiası düşer, yerine **"bankalama kısıtının nicel karakterizasyonu"** iddiası geçer — üç denemenin sentez verisi bu iddianın kanıtı olur.
  4. Bu durumda üç deneme **kayıp değil, ana sonuçtur**; tezde "Deneysel Yöntem" değil "Bulgular" bölümüne yazılır.
- **DESTEK KANALI** (tıkanmadan önce kullanılacak): Reconfigurable Programming dersi hocası (soru H2'de sorulmuş olacak) · AMD/Xilinx Community Forums HLS board (soru H4'te açılmış olacak).
- **KAYIP**: Hızlanma iddiası. Proje Senaryo B kimliğine geçer ama **savunulabilir kalır** — ölçülmüş bir sınır, ölçülmemiş bir iddiadan iyidir.

---

### K-04 · II hedefi tutmuyor

- **RİSK**: Pipeline başlatma aralığı (Initiation Interval) hedeflenen değere inmiyor; çekirdek çalışıyor ama yavaş.
- **KARAR TARİHİ**: **H6 sonu (25 Ekim 2026)** — sentez karar haftası.
- **ÖLÇÜT**: **II ≤ 4** (kabul edilebilir taban). `II = 1` **hedef değil, İ etiketlidir** — kovalanmaz.
- **DENEME ÜST SINIRI**: **4 pipeline optimizasyon turu** (pragma/loop yeniden yapılandırma). Turlar kayıtlıdır.
- **ÖLÇÜT TUTMAZSA**:
  1. Ulaşılan en iyi II **olduğu gibi kabul edilir** ve rapora yazılır. Optimizasyon durur.
  2. Kıyas bu II ile koşulur. FPGA yavaş çıkarsa bu bir bulgudur, gizlenmez (Prensip II).
  3. Faz 2.4 (elle Verilog) **kesinlikle açılmaz** — II'yi RTL'e inerek kurtarma denemesi, kalan takvimin tamamını yer.
- **KAYIP**: Hızlanma oranı. "Kaç kat hızlı" sayısı düşer veya 1'in altına iner → K-10 devreye girer.

---

### K-05 · Qiskit doğrulaması fidelity eşiğini geçmiyor

- **RİSK**: HLS çekirdeğinin çıktısı Qiskit altın referansından sapıyor. Anayasa Prensip IV gereği bu durumda çekirdek **"çalışıyor" sayılamaz**.
- **KARAR TARİHİ**: **H3 sonu (4 Ekim 2026)** — C-sim ilk doğrulaması.
- **ÖLÇÜT** (ölçümden **önce** sabitlendi, ön kayıt):
  - **M eşiği: durum fideliteti ≥ 0.99** — bu eşik altında çekirdek kabul edilmez.
  - **H eşiği: ≥ 0.999** — hedeflenen.
  - Test seti: en az 20 rastgele devre × {8, 12, 16} kübit.
- **ÖLÇÜT TUTMAZSA**:
  1. Önce **sayı formatı** şüphelisi kovalanır (sabit noktalı taşma/yuvarlama) — 2 gün.
  2. Sonra **kapı sırası / faz konvansiyonu** karşılaştırılır (Qiskit'in kübit sıralaması ters olabilir) — 1 gün.
  3. 3 gün içinde ≥0.99'a çıkmazsa: kübit sayısı 12'ye düşürülür ve eşik o ölçekte aranır.
  4. Hâlâ tutmazsa **Faz 2 durdurulur**, kritik yol Faz 1 → Faz 10 üzerinden yeniden kurulur (Senaryo B).
- **KAYIP**: Doğrulanmamış bir hızlandırıcı hiçbir şey ifade etmez; bu tetik ateşlenirse hızlandırıcı iddiası tamamen düşer. **Bu yüzden karar tarihi bilinçli olarak erken (H3) tutulmuştur** — geç öğrenmek felakettir.

---

### K-06 · Tünel kurumsal ağda çalışmıyor

- **RİSK**: Üniversite/kurum ağı dışa açılan tüneli (Cloudflare Tunnel vb.) engelliyor; uzaktan FPGA erişimi kurulamıyor.
- **KARAR TARİHİ**: **H9 sonu (15 Kasım 2026)**
- **ÖLÇÜT**: Kampüs ağından kurulan tünel üzerinden `fpga-agent` sağlık ucu dışarıdan 3 ardışık denemede yanıt veriyor.
- **ÖLÇÜT TUTMAZSA**:
  1. **Hiçbir şey yapılmaz** — 5.2 zaten **İ** etiketli ve taban planda yok.
  2. Demo ve tüm ölçümler **yerel ağda** koşulur. Jüri demosu yerel makinede yapılır.
  3. Tezde "uzaktan erişim mimarisi tasarlandı, kurumsal ağ politikası nedeniyle sahada doğrulanamadı" olarak yazılır.
- **KAYIP**: Neredeyse sıfır. Ölçüm eksenlerinin hiçbiri tünelden geçmiyor.

---

### K-07 · ESP32 donanımı gecikti / gelmedi

- **RİSK**: Saha IoT katmanının donanımı (ESP32, OLED, kablolama) zamanında hazır olmuyor.
- **KARAR TARİHİ**: **H5 sonu (18 Ekim 2026)**
- **ÖLÇÜT**: ESP32 + INA219 elde ve breadboard üzerinde ilk ölçüm okunuyor.
- **ÖLÇÜT TUTMAZSA**:
  1. **4.1 / 4.2 / 4.4 düşer** (zaten İ etiketli).
  2. 🔴 **4.3 DÜŞMEZ** — enerji ölçümü M'dir. INA219 modülü ESP32'siz de çalışır: doğrudan USB-seri üzerinden bir Python betiğiyle okunur ve **FPGA kartının güç rayına** uygulanır. ESP32 yalnızca bir okuyucudur, ölçümün kendisi değil.
  3. Telemetri girdisi kaydedilmiş sentetik veriyle beslenir; bu **sentetik olduğu açıkça etiketlenir**.
- **KAYIP**: Saha IoT anlatısı. Enerji ekseni korunur — asıl önemli olan buydu.

---

### K-08 · Railway maliyet/limit aşımı

- **RİSK**: Railway ücretsiz katman limiti doluyor veya ücretli katmana geçiş gerekiyor.
- **KARAR TARİHİ**: **H10 sonu (22 Kasım 2026)**
- **ÖLÇÜT**: Aylık kullanım ücretsiz katman limitinin **%70'inin altında**.
- **ÖLÇÜT TUTMAZSA**:
  1. Panel dağıtımı Railway'den **yerele** taşınır (`docker compose up`). Jüri demosu yerelde yapılır.
  2. 6.2 (Railway dağıtımı) zaten İ; kesilmesi taban planı etkilemez.
- **KAYIP**: "Canlı URL" gösterisi. Akademik değerlendirmede ağırlıksız.

---

### K-09 · ML karar motoru için veri üretilemiyor

- **RİSK**: 3.3'ün eğitim verisi (hangi problemi FPGA'ya, hangisini CPU'ya yönlendir) yeterli örnek sayısına ulaşmıyor.
- **KARAR TARİHİ**: **H9 sonu (15 Kasım 2026)**
- **ÖLÇÜT**: En az **200 etiketli koşum** (problem özellikleri → hangi çözücü kazandı) birikmiş.
- **ÖLÇÜT TUTMAZSA**:
  1. 3.3 tamamen düşer (zaten İ).
  2. Yerine **kural tabanlı yönlendirme** yazılır: "n ≤ X ise FPGA, değilse klasik" — eşik, kıyas verisinden okunur.
  3. Tezde "öğrenmeli karar motoru için veri hacmi yetersiz kaldı, eşik tabanlı yönlendirme uygulandı" olarak yazılır — bu dürüst ve yeterli bir sonuçtur.
- **KAYIP**: ML anlatısı. Kural tabanlı yönlendirme kıyas verisinden türetildiği için aslında **daha savunulabilir**.

---

### K-10 · 🔴 FPGA hiçbir eksende kazanmıyor

> Bu, listenin en önemli maddesidir. Diğer tetikler kapsamı korur; bu tetik **projenin kimliğini** korur.

- **RİSK**: Tüm eksenlerde (gecikme, enerji, enerji×gecikme çarpımı) CPU referansı FPGA'yı yeniyor. Sentez tuttu, doğrulama geçti, kart koşuyor — ama sonuç: FPGA yavaş ve/veya daha çok enerji harcıyor.
- **KARAR TARİHİ**: **H9 sonu (15 Kasım 2026)** — tam kıyas veri seti elde.
- **ÖLÇÜT**: En az bir eksende FPGA'nın CPU'yu yenmesi. Ölçülebilir: gecikme oranı < 1.0 **veya** joule/çözüm oranı < 1.0.
- **ÖLÇÜT TUTMAZSA — proje şu şekilde savunulur** (şimdi yazıldı, o gün panikle değil):

  **1. İddia yeniden yazılır, silinmez.**
  > *"Kuantum-esinli statevector emülasyonunun PYNQ-Z2 sınıfı bir SoC-FPGA üzerinde donanım hızlandırmasına uygunluğunu inceledik. Sonuç negatiftir: bu ölçekte (N kübit) ve bu kaynak bütçesinde FPGA, modern bir CPU'yu hiçbir eksende yenmemektedir. Bu çalışma, **bunun nedenini nicel olarak göstermektedir**."*

  **2. Negatif sonucun kanıt paketi hazırlanır** — bunların hepsi zaten elde olacak:
  - Bellek bütçesi tablosu (2.1): statevector'ün BRAM'i nasıl doldurduğu.
  - Üç bankalama denemesinin sentez verisi (K-03): çakışmanın neden kaçınılmaz olduğu.
  - II ölçümleri (K-04): pipeline'ın nerede tıkandığı.
  - Roofline benzeri bir argüman: bu iş yükü **bellek bağımlı**dır, hesap bağımlı değil — FPGA'nın hesap üstünlüğü burada devreye giremez.

  **3. "Hangi koşulda kazanırdı?" sorusu cevaplanır.** Ölçülen veriden ekstrapolasyon yapılır: kaç kübitten sonra, kaç BRAM ile, hangi bellek bant genişliğiyle eşitlenirdi. Bu **tahmindir ve tahmin olduğu açıkça etiketlenir** (Prensip II) — ölçüm gibi sunulmaz.

  **4. Anayasa'ya sığınılır, savunulur.** Prensip II zaten "kuantum üstünlüğü" iddiasını yasaklamış ve iddiayı "kuantum-esinli hızlandırma" ile sınırlamıştı. Negatif sonuç bu çerçeveyi bozmaz; ölçülmüş bir sınırı raporlar.

- **KAYIP**: "Hızlandırdım" cümlesi. **Kaybedilmeyen**: donanım tasarımı yetkinliği, ölçüm metodolojisi, dürüst mühendislik yargısı — bir bitirme projesinde asıl değerlendirilenler.

- **⚠️ Hazırlık ödevi (H9'a bırakılmaz)**: Tezin "Bulgular" bölümünün **negatif sonuç varyantı H10'da taslak olarak yazılır**, sonuç ne çıkarsa çıksın. Negatif sonuca H12'de hazırlıksız yakalanmak, bu belgenin önlemek için var olduğu tek şeydir.

---

## 3. Kesme sırası (tampon yendiğinde uygulanır)

Tampon 1 (H8) veya Tampon 2 (H11) **1 haftadan fazla** yendiğinde, aşağıdaki sıra **yukarıdan aşağıya** uygulanır. Sıra tartışılmaz.

| Sıra | Kesilen | Neden bu sırada |
|------|---------|----------------|
| 1 | Faz 6/8'in H işleri (6.3 hariç) | Panel yüzeyi; ölçüme sıfır katkı |
| 2 | Faz 3.1 / 3.2 (backend iskeleti) | Kıyas servisi tek bir Python betiğiyle de koşar |
| 3 | Faz 11.1 (katmanlı CI/CD) | 11.5 (M) korunur, gerisi düşer |
| 4 | Faz 10.2 (karşılaştırma ekranı) | Tablo + statik figür M'yi karşılar |
| 5 | Faz 5.1 (fpga-agent servisi) | Kartta koşum elle de tetiklenebilir |
| 6 | Faz 2.3 (Tcl CI akışı) | Sentez elle koşulur |
| 7 | 🔴 **DUR** | Bu noktadan sonrası M'dir. M kesilecekse önce [scope-triage.md](scope-triage.md) yeniden onaylanır. |

---

## 4. Onay

Bu belge **onay bekliyor**. Onaylandıktan sonra:
- Her `/speckit-plan` çalıştırması bu tetiklere karşı denetlenir.
- Karar tarihi gelen her tetik, o haftanın kontrol ritüelinde ([schedule.md](schedule.md) §4) bakılır.
- Tetik ateşlendiğinde yazılana uyulur; sapma ancak `plan.md` Complexity Tracking tablosunda gerekçelendirilerek yapılabilir (Anayasa, Governance).
