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
| **DT-00** | PYNQ-Z2 tedarik edilemiyor | — | — | — | — | Kart elde mi | — | Olcay | ✅ **KAPALI** (2026-09-10, kart elde) |
| **DT-01** | Kart arızalı / boot etmiyor · `K-01` | D | **Y** | İlk güç verişte DONE LED'i yanmıyor **veya** SD karttan boot logu seri portta akmıyor | **H1** (20 Eyl) | Kart boot ediyor, Jupyter ağdan açılıyor, örnek overlay yükleniyor | H2'de 2. SD kart + farklı adaptör; tutmazsa Senaryo B kimliği, Faz 5 düşer | Olcay | AÇIK |
| **DT-02** | ESP32 + INA219 gecikti / gelmedi · `K-07` | O | D | H3 sonunda sipariş hâlâ kargoya verilmemiş | **H5** (18 Eki) | Modüller elde, breadboard'da ilk okuma alınıyor | 4.1/4.2/4.4 düşer (İ); **4.3 düşmez** — INA219 seri üzerinden ESP32'siz okunur | Olcay | AÇIK |
| **DT-03** | microSD bozuldu (PYNQ boot ortamı) | O | O | Boot süresi uzuyor, `dmesg`'de dosya sistemi hatası, Jupyter aralıklı donuyor | Sürekli | Kart 3 ardışık boot'ta sorunsuz kalkıyor | Yedek SD karttan devam; çalışma dizini zaten git'te | Olcay | AÇIK |

---

## 3. Sentez / kaynak

| ID | Risk | Ol. | Etki | Erken uyarı işareti | Karar tarihi | Ölçüt | Tetiklenirse yapılacak | Sahibi | Durum |
|---|---|---|---|---|---|---|---|---|---|
| **SK-01** | Statevector BRAM'e sığmıyor · `K-02` | O | **Y** | **2.1 bellek bütçe tablosu H3'te zaten >%85 gösteriyorsa** — sentezi beklemeye gerek yok, tablo 3 hafta önce söyler | **H4** (11 Eki) | Sentez raporunda BRAM ≤ %85, statevector tamamen çip-içi | Sırayla: kübit 16→14→12 · format çift→tek→Q1.15 · şerit yarıya. Taban: 12 kübit + tek şerit | Olcay | AÇIK |
| **SK-02** | 🔴 Bankalama çözülemiyor (2^k çakışması) · `K-03` | **Y** | **Y** | İlk sentez raporunda II beklenenin 5 katından büyük **ve** bellek çakışma (memory dependency) uyarısı var | **H5** (18 Eki) | 3 denemeden en az biri tüm `k` için çakışmasız erişim gösteriyor | **4. deneme yapılmaz.** Tek banka + seri erişim + yüksek II'ye sabitlenir; iddia "bankalama kısıtının nicel karakterizasyonu"na döner | Olcay + ders hocası | AÇIK |
| **SK-03** | II hedefi tutmuyor · `K-04` | O | O | İlk pipeline turunda HLS raporu "II violation" veriyor ve nedeni loop-carried dependency | **H6** (25 Eki) | II ≤ 4 | En iyi II olduğu gibi kabul edilir, optimizasyon durur. **2.4 (elle Verilog) açılmaz** | Olcay | AÇIK |
| **SK-04** | Vitis HLS kurulum / lisans sorunu | O | **Y** | H1 sonunda kurulum bitmemiş **veya** örnek proje sentezlenemiyor | **H1** (20 Eyl) | Örnek HLS projesi uçtan uca sentezleniyor | Faz 2 hiç başlayamaz → kritik yol yeniden kurulur, acil çözüm (WebPACK sürümü / farklı makine) | Olcay | AÇIK |

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
| **VR-04** | Kişisel veri jüri projeksiyonunda görünüyor | D | O | Panelde gerçek görünümlü ad/adres var ve "demo kipi" yok | **H13** (13 Ara) | Demo kipi açıkken hiçbir kişisel alan görünmüyor | Ekran görüntüleri ve demo sentetik veriyle yeniden alınır (bkz. 0.4) | Olcay | AÇIK |

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

## 9. Ucuz sigortalar

> Kural: **bugün veya bu hafta, yarım günde** yapılabilen; riski *karar tarihinden haftalar önce* görünür kılan iş.
> Yüksek etkili (Etki = **Y**) her risk için bir tane var. Bunlar iş değil, **erken uyarı kurulumudur** — atlanırsa risk sessiz kalır.

| # | Riski kapatır | Ucuz sigorta | Süre | Ne zaman | Kazanç |
|---|---|---|---|---|---|
| **S-1** | DT-01 | **Kartı bugün çıkar, güç ver, boot et.** İmaj zaten indirilmiş | 2 saat | **Bugün** | Arızayı H1'in *sonunda* değil *başında* öğrenirsin; 2. SD kart denemesi için hafta kalır |
| **S-2** | SK-04 | **Vitis HLS'i kur ve örnek projeyi uçtan uca sentezle.** Gerçek tasarımı bekleme | 4 saat | **Bugün–yarın** | Araç zinciri sorununu Faz 2 başlamadan görürsün; en pahalı sürpriz budur |
| **S-3** | SK-01 | **Bellek bütçesini kağıtta çıkar**: 2^16 karmaşık genlik × format genişliği vs. PYNQ-Z2 BRAM kapasitesi. Sentez gerekmez, aritmetik yeter | 3 saat | **H1** | 16 kübitin sığıp sığmadığını H4 sentez raporundan **3 hafta önce** öğrenirsin |
| **S-4** | SK-02 | **k=0 ve k=15 için erişim desenini kağıtta çıkar** — hangi adresler aynı bankaya düşüyor, tabloya yaz | 4 saat | **H1–H2** | Projenin 1 numaralı riskini sentezden 4 hafta önce somutlaştırır; hocaya soracağın soruyu da netleştirir |
| **S-5** | SK-03 | **Mock/küçük çekirdekle (4 kübit) csim→synth akışını uçtan uca koş.** Tasarım doğru olmasın, akış çalışsın | 4 saat | **H2** | Araç akışı ile tasarım problemini ayrıştırır; H4'te "sorun kodumda mı araçta mı" sorusunu sormazsın |
| **S-6** | DG-01, DG-02 | **Doğrulama paketini en küçük durumdan kur**: 1 kübit, 1 kapı, elle hesaplanabilir sonuç. Sonra büyüt | 3 saat | **H2** | Format ve endian hatalarını 16 kübitlik gürültünün içinde değil, tek kapıda yakalarsın |
| **S-7** | VR-02 | **OSM önbelleğini dosya tabanlı ve commit'lenen yap**; ölçüm yolunda canlı API çağrısı bırakma | 3 saat | **H1** | Tekrarlanamayan ölçüm, Prensip II ihlalidir — sonradan fark edilirse tüm kıyas çöper |
| **S-8** | VR-03 | **Ölçüm çıktısına otomatik damga** (tarih + git hash + konfigürasyon JSON'u). İlk ölçümden **önce** | 3 saat | **H3** | Damgasız koşum geçersizdir; donanım zamanını iki kez harcamazsın |
| **S-9** | AA-03 | **Demoyu baştan çevrimdışı tasarla** + yedek video çekme kararını takvime yaz. H12'de değil şimdi karar ver | 1 saat | **H1** | Jüri günü ağ arızası, hazırlıklıysa 30 saniyelik olay; hazırlıksızsa proje kaybı |
| **S-10** | TK-01 | **1.3 altın referansını H2'nin ilk yarısına çek** (zaten takvimde). Kritik yolun en kırılgan halkası burası | — | **H2** | Zincirin tamamının kayma riskini bir haftadan yarım haftaya indirir |
| **S-11** | KS-02 | **Her hafta sonunda çalışan durumu commit'le ve uzağa push'la.** İstisnasız | 30 dk/hafta | **Her Cuma** | Hastalık veya donanım kaybında en fazla 1 haftalık iş kaybedersin |
| **S-12** | KS-03 | **Ders müfredat tarihini H1'de öğren; hocaya bankalama sorusunu H2'de sor** — müfredatın gelmesini bekleme | 1 saat | **H1–H2** | Desteğin geç kalıp kalmayacağını 5 hafta önceden bilirsin |

**Toplam**: ≈ 28 saat, büyük kısmı H1–H3'te. Bu, 14 haftanın **%2'sinden azı** karşılığında on yüksek etkili riski görünür kılar.

---

## 10. Haftalık güncelleme protokolü

[schedule.md §4](../specs/000-kapsam-takvim/schedule.md) ritüelinin **1. adımı** bu dosyayı açmaktır. Her Cuma, 3 dakika:

1. **Karar tarihi bu hafta olan** satırları bul → ölçüte bak → durumu `KAPALI` veya `TETİKLENDİ` yap.
2. **Erken uyarı işareti görülen** satırları `AÇIK` → `İZLENİYOR` yap. İzlenen risk, karar tarihini beklemeden ele alınır.
3. **Gerçekleşemez hale gelen** riskleri `KAPALI` yap ve tarihi yaz (örn. DT-00). Kapalı satır silinmez — kaydın geçmişi de bilgidir.
4. **Yeni risk** çıktıysa ekle: kategorisi, ID'si (sıradaki numara), en az bir erken uyarı işareti. Erken uyarı işareti yazılamayan risk, henüz yeterince anlaşılmamıştır.
5. Bu dosyanın başındaki **"Son güncelleme"** satırını değiştir.

**Kırmızı çizgi**: `TETİKLENDİ` durumuna geçen bir risk için [cut-plan.md](../specs/000-kapsam-takvim/cut-plan.md)'de yazılana uyulur. "Bir hafta daha deneyeyim" demek, hem kesme planını hem bu kaydı geçersiz kılar.

---

## 11. Değişiklik kaydı

| Tarih | Hafta | Değişiklik |
|---|---|---|
| 2026-09-10 | H0 | Kayıt oluşturuldu. 22 risk, 7 kategori. DT-00 (tedarik) kapalı doğdu — kart elde. |
