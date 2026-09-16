# Risk Kaydı (Canlı Belge)

**Kaynak**: Faz 0 alt dal 0.1 · **Oluşturma**: 2026-09-10 · **Son güncelleme**: 2026-09-10 (H0)
**Bağlı belgeler**: [cut-plan.md](../specs/000-kapsam-takvim/cut-plan.md) · [schedule.md](../specs/000-kapsam-takvim/schedule.md) · [scope-triage.md](../specs/000-kapsam-takvim/scope-triage.md)

> Bu belge **canlıdır**. [schedule.md §4](../specs/000-kapsam-takvim/schedule.md) haftalık kontrol ritüelinin 1. adımı bu dosyayı açmaktır.
> Her hafta: durumlar güncellenir, gerçekleşmeyen riskler kapatılır, yeni riskler eklenir. Güncellenmeyen risk kaydı, risk kaydı değildir.

---

## 1. Nasıl okunur

**Olasılık / Etki**: `D` = Düşük · `O` = Orta · `Y` = Yüksek

**Durum**: `AÇIK` (izleniyor, karar tarihi gelmedi) · `İZLENİYOR` (erken uyarı işareti görüldü, yakın takip) · `TETİKLENDİ` (ölçüt tutmadı, kesme uygulanıyor) · `KAPALI` (risk geçti veya gerçekleşemez oldu)

**Erken uyarı işareti**: Riskin *gerçekleşmesinden önce* görülebilecek somut belirti. Bu sütun kaydın en değerli parçasıdır — karar tarihini beklemeden harekete geçmeyi sağlar.

**K-XX** referansları [cut-plan.md](../specs/000-kapsam-takvim/cut-plan.md)'deki kesme tetiğine bağlanır. K referansı olmayan riskler bu kayıtta yenidir; şiddetleri kesme gerektirecek düzeyde değildir ama izlenirler.

---

## 2. Donanım tedariki

| ID | Risk | Ol. | Etki | Erken uyarı işareti | Karar tarihi | Ölçüt | Tetiklenirse yapılacak | Sahibi | Durum |
|---|---|---|---|---|---|---|---|---|---|
| **DT-00** | PYNQ-Z2 tedarik edilemiyor | D | **Y** | 14 Eylül'de teslim alınamazsa | **H1** (20 Eyl) | Kart fiziksel olarak elde | Teslim gecikirse S-1/DT-01 doğrulaması H2'ye kayar; donanımsız iş (Vitis, bellek bütçesi, Faz 1) etkilenmez (Prensip V) | Olcay | ✅ **KAPALI** (2026-09-15) — kart teslim alındı ve bağlandı. (10 Eylül'de hatalı kapatılmış, 13 Eylül'de yeniden açılmıştı.) |
| **DT-01** | Kart arızalı / boot etmiyor · `K-01` | D | **Y** | İlk güç verişte DONE LED'i yanmıyor **veya** SD karttan boot logu seri portta akmıyor | **H1** (20 Eyl) | Kart boot ediyor, Jupyter ağdan açılıyor, örnek overlay yükleniyor | H2'de 2. SD kart + farklı adaptör; tutmazsa Senaryo B kimliği, Faz 5 düşer | Olcay | ✅ **KAPALI** (2026-09-15) — üç ölçütün hepsi geçti: boot logu (COM3), Jupyter `http://169.254.2.99:9090` (HTTP 200), overlay `OVERLAY_OK` (`base.bit` PL'e yüklendi, `ip_dict` doldu). Ayrıntı: [donanim-dogrulama.md](donanim-dogrulama.md). |
| **DT-02** | ESP32 + INA219 gecikti / gelmedi · `K-07` | O | D | H3 sonunda sipariş hâlâ kargoya verilmemiş | **H5** (18 Eki) | Modüller elde, breadboard'da ilk okuma alınıyor | 4.1/4.2/4.4 düşer (İ); **4.3 düşmez** — INA219 seri üzerinden ESP32'siz okunur | Olcay | AÇIK |
| **DT-03** | microSD bozuldu (PYNQ boot ortamı) | O | O | Boot süresi uzuyor, `dmesg`'de dosya sistemi hatası, Jupyter aralıklı donuyor | Sürekli | Kart 3 ardışık boot'ta sorunsuz kalkıyor | Yedek SD karttan devam; çalışma dizini zaten git'te | Olcay | AÇIK |

---

## 3. Sentez / kaynak

| ID | Risk | Ol. | Etki | Erken uyarı işareti | Karar tarihi | Ölçüt | Tetiklenirse yapılacak | Sahibi | Durum |
|---|---|---|---|---|---|---|---|---|---|
| **SK-01** | Statevector BRAM'e sığmıyor · `K-02` | **Y** ⬆ | **Y** | ✅ **Erken uyarı ATEŞLENDİ (2026-09-13)**: S-3 aritmetiği 16 kübitte tasarım alanının çok dar olduğunu gösterdi — sığan tek seçenekler %81,3'te, granülarite kaybıyla %85'i aşabilirler | **H4** (11 Eki) | Sentez raporunda BRAM ≤ %85, statevector tamamen çip-içi | Düzeltilmiş merdiven: 16+float32-yerinde → 16+Q1.15-ping-pong → 14+float32 → şerit yarıya. Taban: 12 kübit + tek şerit ([K-02](../specs/000-kapsam-takvim/cut-plan.md)) | Olcay | 🟡 **İZLENİYOR** — olasılık O→Y'ye çıkarıldı; bkz. [memory-budget.md](memory-budget.md) |
| **SK-02** | 🔴 Bankalama çözülemiyor (2^k çakışması) · `K-03` | **Y** | **Y** | İlk sentez raporunda II beklenenin 5 katından büyük **ve** bellek çakışma (memory dependency) uyarısı var | **H5** (18 Eki) | 3 denemeden en az biri tüm `k` için çakışmasız erişim gösteriyor | **4. deneme yapılmaz.** Tek banka + seri erişim + yüksek II'ye sabitlenir; iddia "bankalama kısıtının nicel karakterizasyonu"na döner | Olcay + ders hocası | 🟡 **KÜÇÜLDÜ** — bkz. not (aş.) |
| **SK-03** | II hedefi tutmuyor · `K-04` | O | O | İlk pipeline turunda HLS raporu "II violation" veriyor ve nedeni loop-carried dependency | **H6** (25 Eki) | II ≤ 4 | En iyi II olduğu gibi kabul edilir, optimizasyon durur. **2.4 (elle Verilog) açılmaz** | Olcay | AÇIK |
| **SK-04** | Vitis HLS kurulum / lisans sorunu | O | **Y** | H1 sonunda kurulum bitmemiş **veya** örnek proje sentezlenemiyor | **H1** (20 Eyl) | Örnek HLS projesi uçtan uca sentezleniyor | Faz 2 hiç başlayamaz → kritik yol yeniden kurulur, acil çözüm (WebPACK sürümü / farklı makine) | Olcay | AÇIK |
| **SK-05** | 🆕 Windows Smart App Control imzasız derleme çıktısını engelliyor | **Y** (gerçekleşti) | O | Yeni üretilen her .exe "Uygulama Denetimi ilkesi bu dosyayı engelledi" ile açılmıyor | **H1** (20 Eyl) | Vitis HLS'in C-sim/cosim akışı kendi ürettiği ikiliyi koşabiliyor | C-sim WSL'de koşulur; yalnızca sentez Windows'ta yapılır | Olcay | 🟡 **GEÇİCİ ÇÖZÜM VAR** |

---

## 4. Doğruluk

| ID | Risk | Ol. | Etki | Erken uyarı işareti | Karar tarihi | Ölçüt | Tetiklenirse yapılacak | Sahibi | Durum |
|---|---|---|---|---|---|---|---|---|---|
| **DG-01** | Fidelity eşiği geçilmiyor · `K-05` | O | **Y** | **Tek kübitlik H kapısında bile Qiskit'ten sapma varsa** — 16 kübiti beklemeye gerek yok, format/konvansiyon hatası demektir | **H3** (4 Eki) | Fidelity ≥ 0.99 · 20 rastgele devre × {8,12,16} kübit | 3 gün: format → konvansiyon → 12 kübite düş. Tutmazsa Faz 2 durur, Senaryo B | Olcay | AÇIK |
| **DG-02** | Qiskit kübit sıralama konvansiyonu ters | **Y** | O | Fidelity ≈ 0 **ama** genlik büyüklükleri doğru — permütasyon hatası imzası | **H3** (4 Eki) | Bit sıralaması testi geçiyor | Endian çevirisi eklenir; 1 günlük iş, kesme gerektirmez | Olcay | AÇIK |
| **DG-03** | QUBO ceza katsayısı yanlış → geçersiz rota | O | O | **Klasik çözücü de** aynı QUBO'da kısıt ihlal eden çözüm buluyorsa sorun çekirdekte değil QUBO'dadır | **H3** (4 Eki) | 4 düğümlü elle doğrulanabilir örnekte geçerli rota çıkıyor | Ceza katsayısı yeniden kalibre edilir; kıyas verisi geçersiz sayılıp yeniden koşulur | Olcay | AÇIK |

---

## 5. Ağ / altyapı

| ID | Risk | Ol. | Etki | Erken uyarı işareti | Karar tarihi | Ölçüt | Tetiklenirse yapılacak | Sahibi | Durum |
|---|---|---|---|---|---|---|---|---|---|
| **AA-01** | Tünel kurumsal ağda çalışmıyor · `K-06` | O | D | Kampüs ağından 443 dışı giden bağlantılar bloklanıyor | **H9** (15 Kas) | Tünelden sağlık ucu 3 ardışık denemede yanıt veriyor | Hiçbir şey — 5.2 zaten İ. Demo ve ölçümler yerel ağda | Olcay | AÇIK |
| **AA-02** | Railway limit / maliyet aşımı · `K-08` | D | D | Aylık kullanım limitin %70'ini H8'de geçmiş | **H10** (22 Kas) | Kullanım < ücretsiz katmanın %70'i | Panel yerele taşınır (`docker compose`); 6.2 zaten İ | Olcay | AÇIK |
| **AA-03** | 🔴 Jüri gününde demo ortamı çalışmıyor (ağ/servis) | O | **Y** | Provada (12.4) ağa bağımlı **tek bir** adım bile varsa | **H13** (13 Ara) | Demo, ağ kablosu çekiliyken uçtan uca koşuyor | Yedek videoya geçilir; jüriye canlı yerine kayıt gösterilir | Olcay | AÇIK |

---

## 6. Veri

| ID | Risk | Ol. | Etki | Erken uyarı işareti | Karar tarihi | Ölçüt | Tetiklenirse yapılacak | Sahibi | Durum |
|---|---|---|---|---|---|---|---|---|---|
| **VR-01** | ML karar motoru için veri üretilemiyor · `K-09` | **Y** | D | H7'de biriken etiketli koşum sayısı 50'nin altında | **H9** (15 Kas) | ≥ 200 etiketli koşum | 3.3 düşer (İ); yerine kıyas verisinden türetilen eşik tabanlı yönlendirme | Olcay | AÇIK |
| **VR-02** | OSM veri hattı deterministik değil → ölçüm tekrarlanamıyor | O | **Y** | Aynı sorgu iki kez farklı sonuç veriyor (H1'de fark edilir) | **H1** (20 Eyl) | Aynı girdi 3 kez aynı çıktıyı veriyor (hash eşitliği) | Önbellek dosya tabanlı ve commit'lenen hale getirilir; ölçüm sırasında canlı API'ye hiç gidilmez | Olcay | AÇIK |
| **VR-03** | 🔴 Ölçüm verisi karışıyor — hangi koşum hangi konfigürasyona ait belirsiz | **Y** | **Y** | İlk kıyas çıktısında commit hash / konfigürasyon damgası yoksa | **H3** (4 Eki) | Her ölçüm dosyası tarih + git hash + konfigürasyon damgası taşıyor | Damgasız tüm koşumlar **geçersiz sayılır ve yeniden koşulur** — donanım zamanı kaybı | Olcay | AÇIK |
| **VR-04** | Kişisel veri jüri projeksiyonunda görünüyor | D | O | Panelde gerçek görünümlü ad/adres var ve `DEMO_MODE` yok | **H13** (13 Ara) | `DEMO_MODE=true` iken sunucu yanıtında hiçbir kişi adı yok | Ekran görüntüleri ve demo yeniden alınır; kontrol satırı [backup.md §6](backup.md) altın kopya prosedürüne eklendi | Olcay | 🟢 Risk düştü (2026-09-10) — veri zaten sentetik ([ADR 0004](decisions/0004-sentetik-veri.md)); `DEMO_MODE` yine de Faz 6.3'te uygulanacak |
| **VR-05** | Faker sürümü değişince sentetik veri değişiyor → eski ölçümler tekrarlanamıyor | O | O | `data/synthetic/MANIFEST.json`'daki `faker_version` ile kurulu sürüm farklıysa | Her ölçüm turu | Üretilen CSV commit'li ve MANIFEST sürümü kayıtlı | CSV zaten commit'li olduğu için ölçüm girdisi sabit; üretici yeniden koşulmaz | Olcay | ✅ KAPALI (2026-09-10, CSV commit + MANIFEST kaydı) |

---

## 7. Takvim

| ID | Risk | Ol. | Etki | Erken uyarı işareti | Karar tarihi | Ölçüt | Tetiklenirse yapılacak | Sahibi | Durum |
|---|---|---|---|---|---|---|---|---|---|
| **TK-01** | 🔴 Kritik yol kayıyor (Faz 1 → Faz 2 geçişi) | **Y** | **Y** | **H2 sonunda altın referans koşmuyorsa** — zincirin tamamı kayar | **H2** (27 Eyl) | 1.3 altın referansı çalışıyor ve doğrulama paketi yeşil | Faz 2'nin C-sim doğrulaması yapılamaz; H3 tamamen 1.3'e ayrılır, H işleri o hafta askıya alınır | Olcay | AÇIK |
| **TK-02** | Tampon erken yeniyor | **Y** | O | **H4 sonunda tampondan gün yenmişse** — H8'e daha 4 hafta var, bu erken | Sürekli | Tampon 1 (H8) ve Tampon 2 (H11) el değmemiş | Toplam >1 hafta yenmişse [cut-plan §3](../specs/000-kapsam-takvim/cut-plan.md) kesme sırası başlatılır | Olcay | AÇIK |
| **TK-03** | Kapsam sürünmesi — İ işlerine el atma | **Y** | O | Haftalık ritüelde "planda olmayan iş yaptım" satırı doluyorsa | Sürekli | O hafta yapılan işlerin tamamı M veya H etiketli | İş durdurulur; [scope-triage](../specs/000-kapsam-takvim/scope-triage.md) tablosu yeniden okunur; yeni iş için eşdeğer iş çıkarılır | Olcay | AÇIK |
| **TK-04** | H7 mihenk taşı vize haftasına denk geliyor | O | O | H6 sonunda kıyas için gereken veri hazır değilse | **H6** (25 Eki) | Kaba kıyasın **işi** H6'da bitmiş, H7'ye sadece tablo çıkarma kalmış | Mihenk taşı H9'a kayar; danışmana gecikme gerekçesiyle bildirilir | Olcay | AÇIK |

---

## 8. Kişisel

| ID | Risk | Ol. | Etki | Erken uyarı işareti | Karar tarihi | Ölçüt | Tetiklenirse yapılacak | Sahibi | Durum |
|---|---|---|---|---|---|---|---|---|---|
| **KS-01** | Sınav yoğunluğu planlanandan ağır | **Y** | O | Vize takvimi açıklandığında H7-8'e 3'ten fazla sınav düşüyorsa | **H3** (4 Eki) | H7-8'e düşen sınav sayısı ≤ 3 | O iki haftanın kapasitesi %40'tan %20'ye indirilir, takvim yeniden hizalanır, H9'a iş kaydırılır | Olcay | AÇIK |
| **KS-02** | 🔴 Hastalık / 1-2 hafta kayıp | O | **Y** | **Yok — öngörülemez.** Tamponların var olma sebebi budur | Sürekli | — | Tampon yenir; >2 hafta ise kesme sırası doğrudan H kümesinden başlatılır ve danışmana bildirilir | Olcay | AÇIK |
| **KS-03** | Reconfigurable Programming dersi ihtiyaç anından geç geliyor | **Y** | O | **H1'de müfredat tarihi öğrenildiğinde** bellek mimarisi/HLS konusu H6'dan sonraysa | **H1** (20 Eyl) | Ders o konuya H6'dan önce geliyor | "Destek geç" sayılır: K-03 sıkı sürümüyle uygulanır, dış kanal (Xilinx forum) H4'te devreye alınır | Olcay + ders hocası | AÇIK |
| **KS-04** | Tek geliştirici tıkanması — takılınca gün kaybı | O | O | Aynı problem üzerinde 2 saatten fazla ilerlemeden geçirilmişse | Sürekli | "2 saat kuralı" uygulanıyor | Problem forum/hoca kanalına yazılır ve başka bir işe geçilir; beklerken paralel iş koşulur | Olcay | AÇIK |

---

## 8b. Yedekleme / veri kaybı

*Kaynak: Faz 0.5 ([docs/backup.md](backup.md)).*

| ID | Risk | Ol. | Etki | Erken uyarı işareti | Karar tarihi | Ölçüt | Tetiklenirse yapılacak | Sahibi | Durum |
|---|---|---|---|---|---|---|---|---|---|
| **BK-00** | 🟡 Laptop kaybı + OneDrive senkron değil + G: SSD o an takılı değil → tek nokta hatası | D | **Y** | `scripts/backup.ps1` bir haftadan uzun süre çalışmamış (Cuma çalıştığında SSD takılı değildi) | Sürekli izleniyor, uzak remote eklenirse kapanır | Uzak git remote (GitHub) bağlı ve son commit'i tutuyor | Haftalık ritüelde SSD'nin son yedek tarihine bakılır; 2 hafta üst üste eksikse uzak remote sorusu tekrar açılır | Olcay | 🟡 İZLENİYOR — kullanıcı OneDrive+G: ile devam kararı verdi (2026-09-10), uzak remote ertelendi |
| **BK-01** | Yedek script'i sessizce bozuldu (çalışıyor görünüp aslında hata veriyor) | D | **Y** | Script çıktısında "Dogrulama: GECTI" satırı yoksa | Her çalıştırmada | Adım 3 (geri yükleme doğrulaması) her seferinde otomatik koşuyor ve HEAD eşleşmesini kontrol ediyor | Doğrulama FAILED ise script'i düzeltmeden bir sonraki yedeğe geçilmez | Olcay | ✅ KAPALI (2026-09-10, otomatik doğrulama script içine gömülü) |
| **BK-02** | Büyük ikili dosyalar (`artifacts/`) hiç yedeklenmiyor | O | **Y** | İlk gerçek `.bit`/overlay dosyası oluştuğunda `backup.ps1` onu hâlâ kapsamıyorsa | **Faz 2** (ilk sentez çıktısı, ~H4) | `artifacts/` içeriği OneDrive+G:'ye kopyalanıyor | `backup.ps1`'e robocopy adımı eklenir — bkz. [backup.md §7](backup.md) devir maddesi | Olcay | AÇIK (bilinçli — henüz içerik yok) |
| **BK-05** | Otomatik yedek çalıştırılıyor ama kimse çıktısını kontrol etmiyor | O | O | Görev Zamanlayıcı geçmişinde art arda 2 "başarısız" durumu | Her hafta (ritüelin parçası) | `Get-ScheduledTaskInfo qir-engine-backup` son çalıştırma sonucu 0 | Ritüele madde eklendi (bkz. §10) | Olcay | AÇIK (yeni — otomasyon 2026-09-10'da kuruldu) |
| **BK-03** | age özel anahtarı ayrıca yedeklenmedi | O | **Y** | Anahtar üretildiğinden beri (bugün) ikinci bir kopyası yok | **Bugün** | Anahtar parola yöneticisi veya ayrı bir güvenli yerde ikinci kez duruyor | Kayıpsa `secrets.enc.yaml` kurtarılamaz, tüm sırlar sıfırdan üretilir | Olcay | 🟡 İZLENİYOR — masaüstüne geçici kopya (`qir-engine-age-keys-YEDEK.txt`) alındı 2026-09-10, parola yöneticisine taşınıp masaüstünden silinince KAPALI olacak |
| **BK-04** | Savunma öncesi altın kopya alınmayı unutuluyor | D | **Y** | H13 bitiminde (13 Ara) `git tag altin-kopya-*` yok | **H13** (13 Ara) | Etiket ve dondurulmuş kopya mevcut | H14 başında acilen alınır — geç ama hâlâ mümkün | Olcay | AÇIK |

---

## 8c. Maliyet

*Kaynak: Faz 0.6 ([docs/cost.md](cost.md)).*

| ID | Risk | Ol. | Etki | Erken uyarı işareti | Karar tarihi | Ölçüt | Tetiklenirse yapılacak | Sahibi | Durum |
|---|---|---|---|---|---|---|---|---|---|
| **MC-01** | CI dakikaları — yanlışlıkla ARM64/çoklu-platform iş eklenip kota erimesi | D | O | Yeni bir CI job'ı `ubuntu-latest` dışında bir runner kullanıyorsa | Her CI değişikliğinde | Tüm işler `ubuntu-latest` | `runs-on` satırı gözden geçirilir, gerekçesiz farklı runner kaldırılır | Olcay | AÇIK (bilinçli — henüz CI aktif değil, remote yok) |
| **MC-02** | Railway servisi unutulup 7/24 açık kalması | O | O | Haftalık kontrolde "son ne zaman kapatıldı" bilinmiyorsa | Servis kurulduktan itibaren, her hafta | Geliştirme dışı saatlerde servis kapalı | Servis durdurulur, kredi/kota kontrol edilir | Olcay | AÇIK (bilinçli — henüz Railway hesabı yok) |
| **MC-03** | Kart bağlı olmadan tavan aşımı endişesi | — | — | — | — | Hiçbir serviste ödeme yöntemi yok | — | Olcay | ✅ KAPALI (2026-09-13 itibariyle doğrulandı — otomatik faturalama fiziksel olarak imkânsız) |

---

## 9. Ucuz sigortalar

> Kural: **bugün veya bu hafta, yarım günde** yapılabilen; riski *karar tarihinden haftalar önce* görünür kılan iş.
> Yüksek etkili (Etki = **Y**) her risk için bir tane var. Bunlar iş değil, **erken uyarı kurulumudur** — atlanırsa risk sessiz kalır.

| # | Riski kapatır | Ucuz sigorta | Süre | Ne zaman | Kazanç |
|---|---|---|---|---|---|
| **S-1** | DT-01 | ✅ **YAPILDI 2026-09-15** — kart bağlandı, COM3'ten canlı PYNQ Linux boot logu alındı. Arıza riski H1'in ilk günlerinde kapandı | ~0 (kart hazır geldi) | H1 | 2. SD kart denemesi için haftalar kaldı — gerek kalmadı |
| **S-2** | SK-04 | **Vitis HLS'i kur ve örnek projeyi uçtan uca sentezle.** Gerçek tasarımı bekleme | 4 saat | **Bugün–yarın** | Araç zinciri sorununu Faz 2 başlamadan görürsün; en pahalı sürpriz budur |
| **S-3** | SK-01 | ✅ **YAPILDI 2026-09-13** — [memory-budget.md](memory-budget.md). Bulgu: 16 kübit + double **imkânsız** (%162); sığan tek seçenekler float32-yerinde veya Q1.15-ping-pong, ikisi de %81,3 (sınırda). K-02 merdiveni düzeltildi | 20 dk | H1 | Sentezden **4 hafta önce** öğrenildi; ayrıca bankalama riskiyle bellek bütçesinin birbirine bağlı olduğu ortaya çıktı |
| **S-4** ✅ | SK-02 | **k=0 ve k=15 için erişim desenini kağıtta çıkar** — hangi adresler aynı bankaya düşüyor, tabloya yaz | 4 saat | **H1–H2** | Projenin 1 numaralı riskini sentezden 4 hafta önce somutlaştırır; hocaya soracağın soruyu da netleştirir |
| **S-5** | SK-03 | **Mock/küçük çekirdekle (4 kübit) csim→synth akışını uçtan uca koş.** Tasarım doğru olmasın, akış çalışsın | 4 saat | **H2** | Araç akışı ile tasarım problemini ayrıştırır; H4'te "sorun kodumda mı araçta mı" sorusunu sormazsın |
| **S-6** | DG-01, DG-02 | **Doğrulama paketini en küçük durumdan kur**: 1 kübit, 1 kapı, elle hesaplanabilir sonuç. Sonra büyüt | 3 saat | **H2** | Format ve endian hatalarını 16 kübitlik gürültünün içinde değil, tek kapıda yakalarsın |
| **S-7** | VR-02 | **OSM önbelleğini dosya tabanlı ve commit'lenen yap**; ölçüm yolunda canlı API çağrısı bırakma | 3 saat | **H1** | Tekrarlanamayan ölçüm, Prensip II ihlalidir — sonradan fark edilirse tüm kıyas çöper |
| **S-8** | VR-03 | **Ölçüm çıktısına otomatik damga** (tarih + git hash + konfigürasyon JSON'u). İlk ölçümden **önce** | 3 saat | **H3** | Damgasız koşum geçersizdir; donanım zamanını iki kez harcamazsın |
| **S-9** | AA-03 | **Demoyu baştan çevrimdışı tasarla** + yedek video çekme kararını takvime yaz. H12'de değil şimdi karar ver | 1 saat | **H1** | Jüri günü ağ arızası, hazırlıklıysa 30 saniyelik olay; hazırlıksızsa proje kaybı |
| **S-10** | TK-01 | **1.3 altın referansını H2'nin ilk yarısına çek** (zaten takvimde). Kritik yolun en kırılgan halkası burası | — | **H2** | Zincirin tamamının kayma riskini bir haftadan yarım haftaya indirir |
| **S-11** | KS-02, BK-00 | **Her hafta çalışan durumu commit'le.** `scripts/backup.ps1` artık otomatik (Cuma 18:00, Görev Zamanlayıcı) — elle çalıştırmaya gerek yok, ama SSD'nin takılı olduğunu haftalık ritüelde kontrol et | 2 dk/hafta (kontrol) | **Her Cuma** | Hastalık veya donanım kaybında en fazla 1 haftalık iş kaybedersin |
| **S-12** | KS-03 | **Ders müfredat tarihini H1'de öğren; hocaya bankalama sorusunu H2'de sor** — müfredatın gelmesini bekleme | 1 saat | **H1–H2** | Desteğin geç kalıp kalmayacağını 5 hafta önceden bilirsin |
| **S-13** | BK-03 | **age özel anahtarını (`%APPDATA%\sops\age\keys.txt`) bugün parola yöneticisine veya harici bir yere elle kopyala** | 10 dakika | **Bugün** | Bu anahtar olmadan `secrets.enc.yaml` kalıcı olarak kurtarılamaz — en ucuz sigorta en pahalı riski kapatıyor |

**Toplam**: ≈ 28 saat, büyük kısmı H1–H3'te. Bu, 14 haftanın **%2'sinden azı** karşılığında on yüksek etkili riski görünür kılar.

---

## 10. Haftalık güncelleme protokolü

[schedule.md §4](../specs/000-kapsam-takvim/schedule.md) ritüelinin **1. adımı** bu dosyayı açmaktır. Her Cuma, 3 dakika:

1. **Karar tarihi bu hafta olan** satırları bul → ölçüte bak → durumu `KAPALI` veya `TETİKLENDİ` yap.
2. **Erken uyarı işareti görülen** satırları `AÇIK` → `İZLENİYOR` yap. İzlenen risk, karar tarihini beklemeden ele alınır.
3. **Gerçekleşemez hale gelen** riskleri `KAPALI` yap ve tarihi yaz (örn. DT-00). Kapalı satır silinmez — kaydın geçmişi de bilgidir.
4. **Yeni risk** çıktıysa ekle: kategorisi, ID'si (sıradaki numara), en az bir erken uyarı işareti. Erken uyarı işareti yazılamayan risk, henüz yeterince anlaşılmamıştır.
5. Bu dosyanın başındaki **"Son güncelleme"** satırını değiştir.
6. **Otomatik yedek kontrolü** (BK-00, BK-05): `Get-ScheduledTaskInfo qir-engine-backup` ile son çalışma sonucunu kontrol et. Başarısızsa veya SSD o gün takılı değildiyse, elle `.\scripts\backup.ps1` çalıştır.

**Kırmızı çizgi**: `TETİKLENDİ` durumuna geçen bir risk için [cut-plan.md](../specs/000-kapsam-takvim/cut-plan.md)'de yazılana uyulur. "Bir hafta daha deneyeyim" demek, hem kesme planını hem bu kaydı geçersiz kılar.

---

## 11. Değişiklik kaydı

| Tarih | Hafta | Değişiklik |
|---|---|---|
| 2026-09-10 | H0 | Kayıt oluşturuldu. 22 risk, 7 kategori. DT-00 (tedarik) kapalı doğdu — kart elde. |
| 2026-09-10 | H0 | Faz 0.5: Yedekleme kategorisi eklendi (BK-00..BK-04, 5 risk). BK-01 aynı gün kapandı (otomatik doğrulama script'e gömülü). BK-00 (uzak git remote yok) en kritik açık madde — kullanıcı kararı bekliyor. S-13 eklendi (age anahtarı yedekleme). |
| 2026-09-10 | H0 | Kullanıcı kararı: D: yerine harici SSD (G:) kalıcı yedek hedefi; uzak git remote şimdilik ertelendi. BK-00 İZLENİYOR'a çekildi (KAPALI değil). Otomatik haftalık yedek (Görev Zamanlayıcı, Cuma 18:00) kuruldu ve doğrulandı — BK-05 eklendi (otomasyon çıktısını kontrol etme riski). BK-03: age anahtarı masaüstüne geçici kopyalandı, İZLENİYOR. |
| 2026-09-10 | H0 | Faz 0.4: Sentetik veri kararı ([ADR 0004](decisions/0004-sentetik-veri.md)). VR-04 riski düştü (veri zaten sentetik). VR-05 eklendi ve aynı gün kapandı (CSV commit'li + MANIFEST'te Faker sürümü). Telefon alanı "gerekmeyen veri toplanmaz" kuralıyla şemadan çıkarıldı. |
| 2026-09-13 | H0 | **DT-00 YENİDEN AÇILDI** — kart 10 Eylül'de "elde" diye kapatılmıştı, gerçekte arkadaşta; teslim 14 Eylül. Takvime etkisi yok. **S-3 yapıldı** ([memory-budget.md](memory-budget.md)): 16 kübit + double imkânsız çıktı (%162), SK-01 olasılığı O→**Y**'ye yükseltildi ve İZLENİYOR'a alındı; K-02 kesme merdiveni gerçek sayılarla düzeltildi. |
| 2026-09-13 | H0 | Faz 0.6: Maliyet kategorisi eklendi (MC-01..MC-03, [cost.md](cost.md)). MC-03 aynı gün kapandı (hiçbir serviste kart bağlı değil). Bütçe tavanı kararı: 0 TL + son 1-2 ay Railway Hobby (~$5) istisnası ([ADR 0005](decisions/0005-butce-tavani.md)). Faz 0 alt dalları TAMAMLANDI (0.1-0.7). |
| 2026-09-15 | **H1** | 🟢 **KART GELDİ VE BOOT ETTİ.** COM3'ten (FTDI FT2232H, seri no `1234-TULB`) canlı PYNQ Linux boot logu alındı. **DT-00 KAPALI**, **DT-01 büyük ölçüde kapalı** (Jupyter + overlay ölçütleri kaldı), **S-1 sigortası yapıldı**. Faz 1 de tamamlanmıştı — kritik yolun ilk iki halkası sağlam. Kalan tek büyük engel: **SK-04 (Vitis HLS kurulu değil)**, karar tarihi 20 Eylül. |
| 2026-09-15 | **H1** | ✅ **DT-01 TAMAMEN KAPANDI.** PC↔kart doğrudan RJ45 bağlantısıyla üç ölçüt de geçti: boot, Jupyter (HTTP 200), overlay (`OVERLAY_OK`, PL programlandı). USB Wi-Fi dongle yolu **bilinçli olarak kesildi** (sürücü yok + güç resetleri) — bkz. [donanim-dogrulama.md](donanim-dogrulama.md). Yeni izlenecek yan konu: kartın ara ara resetlenmesi, Faz 5'te uzun koşumlar öncesi doğrulanmalı. |

---

## SK-02 güncellemesi — 2026-09-15 (araştırma sonrası)

**Durum: 🔴 → 🟡.** Risk kapanmadı ama **ölçülebilir biçimde küçüldü**. Kanıt:
[docs/banking-research.md](banking-research.md), üretici `scripts/banking_analysis.py`.

Üç bağımsız bulgu riski aşağı çekiyor:

1. **Sorun sanıldığından küçük (ÖLÇÜLEN).** RZZ yerleşik köşegen kapı olarak
   uygulanınca eşlemeli (bankalama gerektiren) kapı sayısı p=2'de 384 → 32'ye
   iniyor, **12× azalma**. Kapıların %86,2'si köşegen ve bankalama sorunu yaşamıyor.
2. **Çift tamponlama sorunu aritmetik olarak çözüyor (HESAPLANAN).** Ping-pong,
   banka başına yükü 4'ten 2'ye indirdiği için **her şema, her k için** teorik
   tavana çıkıyor. XOR eşlemesi ve iki geçişli devrik gereksizleşiyor.
3. **`k` derleme zamanı sabiti.** Karıştırıcı `for k in 0..15` döngüsüdür; HLS'in
   partition'ı çözememe riski, çekirdek QAOA'ya özel tutulduğu sürece oluşmuyor.

**Riskin kalan kısmı yer değiştirdi — artık çakışma değil, DOLULUK:**
ping-pong BRAM'i ikiye katlıyor, Q1.17'de **%91,4**. Geriye AXI tamponu, faz
tablosu ve kontrol için pay kalmıyor. Faz tablosu seçilirse (+64 blok) bütçe
aşılır. Bu, **K-02** kesme ölçütünün alanıdır, K-03'ün değil.

**Ölçüt değişmiyor**: kapanış hâlâ **sentez raporuna** bağlı (H5, 18 Eki).
Yukarıdaki II sayılarının hiçbiri doğrulanmış değildir — Prensip II.

**Yeni izlenecek**: sentez raporunda ilk bakılacak satır BRAM_18K kullanımıdır
(bütçe 280, 140 değil). %91,4 tahmininden sapma varsa önce o araştırılır.

---

## SK-05 — Smart App Control (2026-09-15, uygulama sırasında keşfedildi)

**Belirti**: `g++` ile üretilen her yeni `.exe`, çalıştırılmak istendiğinde
*"Uygulama Denetimi ilkesi bu dosyayı engelledi"* veriyor. İlk üretilen ikili bir
kez koştu, sonrakilerin hepsi engellendi; aynı dosya yoluna yeniden derlemek de
işe yaramadı (SAC dosya ÖZETİNE göre karar veriyor).

**Kök neden**: Windows 11 **Smart App Control açık**
(`HKLM:\SYSTEM\CurrentControlSet\Control\CI\Policy\VerifiedAndReputablePolicyState = 1`).
İmzasız ve itibarı bilinmeyen çalıştırılabilirleri engelliyor.

**Neden kapatılmadı**: SAC bir **sistem güvenlik ayarıdır** ve kapatılması
**geri alınamaz** — yeniden açmak Windows'un temiz kurulumunu gerektirir. Bir
derleme kolaylığı için kalıcı bir güvenlik zayıflatması yapılmadı.

**Geçici çözüm**: C-simülasyon **WSL/Ubuntu** altında derlenip koşuluyor
(`hls/build_and_run.sh`). Hiçbir sistem ayarı değişmedi. Doğrulama: Windows'ta
koşabilen ilk ikili ile WSL ikilisi **birebir aynı** fidelity'yi verdi
(0,999978359), yani geçici çözüm sonucu etkilemiyor.

**Kalan risk — izlenecek**: Vitis HLS'in kendi C-sim/cosim akışı da kaynak
kodu derleyip **çalıştırılabilir üretir**. AMD'nin kendi ikilileri imzalıdır ama
kullanıcı kodundan üretilen geçici ikililer imzasızdır. Vitis kurulduğunda
(SK-04) ilk denenecek şey `csim` koşusudur; engellenirse seçenekler:
1. Vitis'i WSL altında kurmak (Linux sürümü var)
2. Sentezi Windows'ta, C-sim'i WSL'de yapmak (şu anki bölünme zaten bu)

**Yan bulgu**: MSYS2'nin `liblto_plugin.dll`'i de yüklenemiyor; `-fno-lto`
gerekiyordu. Aynı kökten olabilir, ama WSL'e geçince konu kalmadı.

---

## Sentez raporu sonrası risk güncellemesi — 2026-09-15

Kanıt: [docs/measurements/faz2-sentez.md](measurements/faz2-sentez.md).

### SK-04 ✅ **KAPALI**
Vitis HLS 2025.2 kuruldu (`D:\Xilinx\2025.2`), `vitis-run --mode hls` ile csim
ve csynth uçtan uca koştu. Kapanış ölçütü karşılandı.

*Not: 2025.2'de komut `vitis_hls` değil **`vitis-run`**; eski `vitis_hls.bat`
artık yok. Runbook ve `hls/run.ps1` ikisini de destekleyecek şekilde yazıldı.*

### SK-02 ✅ **KAPALI — risk gerçekleşmedi**
Projenin 1 numaralı riskiydi. Sentez raporu **ölçtü**:

| | Tahmin | **Ölçülen** | SC-003 (≤4) |
|---|---:|---:|:---:|
| II, k=0 | 1 | **1** | ✅ |
| II, k=15 | 2 | **3** | ✅ |

Bellek çakışma (memory dependency) uyarısı yok. Aritmetik model yüksek `k`'nin
daha kötü olduğunu doğru öngördü, büyüklüğü bir birim şaşırdı. K-03'ün 3 deneme
bütçesinden **hiçbiri harcanmadı**.

### SK-06 🆕 🔴 **AÇIK — tasarım çipe sığmıyor**
Sentez raporu iki kabul ölçütünü geçti ama:

- **LUT %185** (98.627 / 53.200) — sığmıyor
- **DSP %153** (337 / 220) — sığmıyor
- **Zamanlama 25,039 ns** (hedef 10 ns) — ~40 MHz
- **Gecikme 355M çevrim = 8,9 sn** — aritmetik tahminden **1.495×** fazla;
  CPU'dan (~58 ms) **~150 kat yavaş**

**Kök neden ikisi de ÖNCEDEN BİLİNİYORDU ama bedeli ölçülmemişti:**
1. `hls/src/trig.hpp` çift duyarlıklı `std::cos/sin` kullanıyor → HLS tam bir
   `double` transandantal birim sentezledi (tek örnek **85 DSP**, 6.364 LUT).
2. `apply_cost_layer` genlik başına 136 faz terimini **seri** topluyor.

**Çözüm yolu net ve kapsam içinde**: trig'i sabit-nokta LUT/CORDIC'e çevir,
fazı Gray-kod ile artımlı hesapla (NC-2). İkisi de **M** etiketli.

**Karar tarihi**: H4 sonu (11 Ekim) — K-02 ile aynı. O tarihe kadar iki düzeltme
uygulanıp yeniden sentezlenmezse K-02 merdiveni devreye girer.

⚠️ **Bu risk kapanmadan hiçbir hızlanma iddiası yapılamaz.** Daha önce hesaplanan
"~24× hızlanma" **geçersizdir**.

---

## SK-05 GERÇEKLEŞTİ — Vitis engellendi (2026-09-16)

**Belirti**:
```
vitis-run.bat : 'D:\Xilinx\2025.2\Vitis\bin\unwrapped\win64.o\vitis-run.exe'
was blocked by your organization's Device Guard policy.
```

**Doğrulanan üç şey**:
- Engel tutarlı (art arda iki deneme, aynı sonuç)
- Smart App Control hâlâ açık (`VerifiedAndReputablePolicyState = 1`)
- `vitis-run.exe` **imzasız** (`Get-AuthenticodeSignature` → `NotSigned`) —
  AMD bu ikiliyi imzalamamış

**Zamanlama tuhaf ve öğretici**: aynı komut **15 sentez turu** boyunca sorunsuz
koştu, sonra engellendi. SAC itibar tabanlı çalışır ve kararı zamanla değişir.
Yani "bir kez çalıştı" güvence değildir.

SK-05 kaydında *"Vitis'in kendi C-sim akışı da aynı duvara çarpabilir"* yazıyordu.
Çarptı — ama `csim` adımında değil, **`vitis-run`'ın kendisinde**. Yani öngörü
doğru, ayrıntı yanlıştı: sorun kullanıcı kodundan üretilen ikili değil, AMD'nin
imzasız aracıydı.

**Kaybedilmeyen**: son başarılı sentez sonucu kayıtlı (9.801.215 çevrim,
7,195 ns, dört kaynak da bütçede). Engellenen yalnızca **yeni** sentez.

**Seçenekler** (karar Olcay'ın, hiçbiri tek taraflı uygulanmadı):

| | Yol | Artısı | Eksisi |
|---|---|---|---|
| 1 | Smart App Control'ü kapat | Anında çözer | **GERİ ALINAMAZ** — yeniden açmak Windows temiz kurulumu ister. Kalıcı güvenlik zayıflatması |
| 2 | Vitis'i WSL/Ubuntu'ya kur | Hiçbir güvenlik ayarı değişmez; AMD Ubuntu'yu resmen destekler; C-sim zaten WSL'de | ~40 GB yeniden indirme/kurulum; WSL diski C:'de (46 GB boş, dar) — muhtemelen D:'ye taşımak gerekir |
| 3 | Beklemek | Bedava | SAC itibarı geri dönebilir ama **garantisi yok** |

**Etki**: Faz 2'nin kalan işi (paralellik turu) sentez gerektiriyor. C-sim
doğrulaması WSL'de çalışmaya devam ediyor, yani **SC-001 etkilenmiyor**;
etkilenen SC-002/SC-003'ün yeniden ölçülmesi.
