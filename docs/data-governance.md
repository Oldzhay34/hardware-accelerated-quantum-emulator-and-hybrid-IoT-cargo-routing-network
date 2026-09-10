# Veri Yönetişimi — Kişisel Veri, Saklama ve Demo Verisi

**Kaynak**: Faz 0 alt dal 0.4 · **Oluşturma**: 2026-09-10 · **Durum**: Karar verildi

> Bu bir veri yönetişimi kararıdır ve **şemayı etkiler**, o yüzden Faz 7.2'den (veri modeli) ÖNCE koşuldu.
> İlgili: [secrets-audit.md](secrets-audit.md) (0.3, log maskeleme) · [backup.md](backup.md) (0.5, yedek şifreleme) · [risk-register.md](risk-register.md)

---

## 1. Veri envanteri

Servisler henüz yazılmadı (`services/` boş), bu yüzden "servis/tablo" sütunu **planlanan** yapıyı gösterir — kesinleşmesi Faz 3.2 (servis sözleşmeleri) ve Faz 7.2 (veri modeli) işidir. **Ama "Gerekli mi?" kararı bugün verilir**, çünkü şema doğduktan sonra alan çıkarmak, hiç eklememekten pahalıdır.

| Veri sınıfı | Planlanan servis / tablo | Kim erişebilir | Saklama | Neden gerekli | **Gerekli mi?** |
|---|---|---|---|---|---|
| Şoför kimliği (ad-soyad) | `fleet` / `drivers` | Mühendis, admin | Hesap aktif + 30 gün | Panelde rota atamasını okunabilir kılmak | 🟡 **Kısmen** — ID yeterli olurdu; ad yalnızca arayüz okunabilirliği için. Sentetik olduğu için risk yok. |
| Şoför iletişim (telefon) | `fleet` / `drivers` | Admin | — | Sevkiyat bildirimi | 🔴 **HAYIR — TOPLANMAZ.** Bu projede sevkiyat/bildirim akışı yok. Alan şemaya hiç girmiyor (bkz. §1.1). |
| Teslimat adresi (metin) | `routing` / `deliveries` | Mühendis, şoför | Teslimat + 90 gün | Rota noktasını insana göstermek | 🟡 **Kısmen** — algoritma yalnızca koordinat kullanıyor; metin adres sadece arayüz/demo için. |
| Teslimat koordinatı (lat/lon) | `routing` / `deliveries` | Mühendis, şoför | Teslimat + 90 gün | **QUBO mesafe matrisinin girdisi** — algoritmanın çalışması buna bağlı | 🟢 **EVET, çekirdek** |
| Alıcı adı | `routing` / `deliveries` | Şoför, admin | Teslimat + 90 gün | Teslimat doğrulaması | 🟡 **Kısmen** — kıyas ölçümü için gereksiz; yalnızca demo gerçekçiliği. |
| Araç konumu / hareket geçmişi (telemetri) | `telemetry` / `vehicle_positions` | Mühendis | **30 gün** | ESP32 saha katmanı (Faz 4), enerji/gecikme ölçümü | 🟡 **Kısmen** — enerji ölçümü için gerekli, ama **kişiye bağlanabilir konum izi** en hassas kalem. Şoför ID yerine araç ID ile tutulur. |
| Kullanıcı hesapları (e-posta, parola özeti) | `auth` / `users` | Admin | Hesap aktif + 30 gün | Panel girişi (Faz 6.2) | 🟡 **Kısmen** — Faz 6.2 taban planda **İ** ([scope-triage](../specs/000-kapsam-takvim/scope-triage.md)); kimlik doğrulama hiç yapılmayabilir. |
| Denetim kaydı (kim, ne zaman, ne yaptı) | `audit` / `audit_log` | Admin | **1 yıl** | Değiştirilemez eylem izi (Faz 6.5) | 🟡 **Kısmen** — Faz 6.5 taban planda **İ**. Yapılırsa aktör **ID** ile tutulur, ad ile değil (bkz. §5.4). |

### 1.1 Uygulanan kural: telefon alanı şemaya girmiyor

> *"En güvenli veri, hiç toplanmayan veridir."*

Bu kural yazıp geçilmedi, **uygulandı**: `scripts/generate_synthetic_data.py` ilk sürümünde şoför telefonu üretiyordu; bu alan bu kararla üreticiden **kaldırıldı**. Gerekçe: projenin kapsamında sevkiyat bildirimi, SMS veya arama akışı yok — telefon hiçbir ölçüm eksenine veya demo senaryosuna hizmet etmiyor. Faz 7.2 veri modeline de eklenmeyecek.

---

## 2. 🎯 Asıl karar: Gerçek mi, sentetik mi?

### Seçeneklerin karşılaştırması

| Kriter | (a) Tamamen sentetik | (b) Anonimleştirilmiş gerçek | (c) Gerçek veri |
|---|---|---|---|
| Hukuki risk (KVKK) | **Sıfır** — ortada kişisel veri yok | Düşük ama sıfır değil — yeniden kimliklendirme riski gerçektir (konum verisi özellikle) | Yüksek — açık rıza, aydınlatma metni, veri sorumlusu yükümlülükleri |
| Elde etme maliyeti | Sıfır (üretici yazıldı) | Yüksek — böyle bir veri kümesi elde yok, bulunması/izin alınması haftalar | Çok yüksek — bir kargo firmasıyla anlaşma gerekir |
| 14 hafta kısıtına etkisi | Yok | 1–2 hafta kayıp | Muhtemelen dönem içinde bitmez |
| Tezde savunulabilirlik | Açıkça belirtilirse tam savunulabilir | Anonimleştirme yönteminin ayrıca savunulması gerekir | Etik kurul sorusu gündeme gelir |
| Jüri odasında görünürlük riski | Yok | Var (maskeleme gerekir) | Yüksek |

### Karar: **(a) Tamamen sentetik veri**

Bu, [Faz 0 spec'inde varsayım](../specs/000-kapsam-takvim/spec.md) olarak yazılmıştı; burada gerekçelendirilmiş **karara** dönüştürülüyor. Gerçek teslimat adresi ve gerçek şoför bilgisi **kullanılmayacaktır**.

### 2.1 Ölçüm gerçekçiliği — sentetik veri yeterli mi?

Bu, kararın en ciddi sorusu: *gerçek adres dağılımı kümeleme sonucunu anlamlı biçimde değiştirir mi?*

**Cevap: Gerçekçilik iki ayrı kaynaktan gelir ve kritik olanı sentetik değil.**

| Gerçekçilik bileşeni | Kaynak | Sentetik veriden etkilenir mi? |
|---|---|---|
| **Yol ağı topolojisi** — mesafe matrisinin gerçek değerleri, tek yönlü yollar, Boğaz geçişleri, asimetrik seyahat süreleri | **OSM/OSRM — gerçek veri** (Faz 1.1) | ❌ **Hayır.** Adresler sentetik olsa da mesafeler *gerçek yol ağı* üzerinden hesaplanıyor. Bu, problemin zorluğunu belirleyen asıl yapıdır. |
| **Nokta kümelenme deseni** — noktaların tekdüze mi yoksa yoğunlaşmış mı dağıldığı | Sentetik üretici | ⚠️ **Evet — ve bu yüzden üretici uniform rastgele DEĞİL.** |

**Kritik tasarım kararı**: Tekdüze rastgele koordinat üretmek, problemi yapay olarak **kolaylaştırırdı** — simetrik, kümesiz bir örnek, gerçek bir kargo probleminin karakterini taşımaz. Bu yüzden üretici, İstanbul'un 20 ilçe merkezinin etrafında **ağırlıklı Gauss dağılımı** kullanıyor.

Üretilen 200 noktalık örnekte ölçülen sonuç:

```
En yoğun ilçe / en seyrek ilçe oranı : 5.7x   (tekdüze dağılımda ~1x olurdu)
Lat aralığı                          : 40.847 – 41.170
Lon aralığı                          : 28.623 – 29.283   (Boğaz'ın iki yakası da kapsanıyor)
```

Boğaz'ın iki yakasına da nokta düşmesi önemli: OSRM gerçek yol ağını kullandığı için bu, köprü/tünel darboğazlarından geçen **gerçekten asimetrik** rota maliyetleri üretiyor — kümeleme ve rotalama algoritmasının en çok zorlandığı yapı.

**Sonuç**: (a) yeterlidir. Gerçek adres kümesi kullanmak, mesafe matrisinin istatistiksel karakterini anlamlı biçimde değiştirmezdi, çünkü mesafeler zaten gerçek yol ağından geliyor.

### 2.2 Sentetik verinin **yakalayamadığı** şey (dürüst sınır)

Gerçek kargo verisinde bulunup burada olmayan: **zamansal desenler** — teslimat zaman pencereleri, tekrar eden müşteriler, saat bazlı trafik yoğunluğu. Taban plandaki QUBO formülasyonu (Faz 1.2) zaman penceresi modellemiyor, dolayısıyla bu eksiklik ölçümü etkilemiyor. **Ama tezde belirtilecek** (bkz. §6) — çünkü kapsam genişletilip zaman pencereli bir varyant denenirse bu sınır devreye girer.

### 2.3 Üretici

[`scripts/generate_synthetic_data.py`](../scripts/generate_synthetic_data.py) yazıldı ve çalıştırıldı.

- **Deterministik**: aynı `--seed` aynı veriyi üretir. İki ardışık koşumun MD5'i karşılaştırılarak doğrulandı (Anayasa Prensip II — ölçüm tekrarlanabilirliği; ayrıca risk [VR-02](risk-register.md) ile aynı disiplin).
- `data/synthetic/MANIFEST.json` seed'i ve **Faker sürümünü** kaydeder — kütüphane sürümü çıktıyı değiştirebileceği için köken bilgisi ölçümle birlikte saklanmalıdır.
- Üretilen veri git'e commit edilir: sentetik olduğu için gizlilik riski yok, küçük, ve **ölçümlerin dayandığı girdinin sabit kalmasını** garanti eder.

---

## 3. Saklama süreleri ve otomatik temizlik

| Veri sınıfı | Saklama | Gerekçe |
|---|---|---|
| Araç konumu / telemetri | **30 gün** | En hızlı büyüyen sınıf (Faz 4'te 10 Hz örnekleme öngörülüyor — ayda milyonlarca satır). Ölçüm analizi için özetlenmiş biçim yeterli; ham iz uzun tutulmaz. |
| Süreç izi (Faz 9) | **30 gün** | Aynı gerekçe. Faz 9 zaten taban planda **İ**. |
| Teslimat kaydı (adres, alıcı, koordinat) | **Teslimat + 90 gün** | Kıyas koşumlarının tekrar edilebilmesi için bir dönemlik pencere; sonrasında koordinat dışındaki alanlar silinir. |
| Şoför / kullanıcı hesabı | **Hesap aktif + 30 gün** | Silme talebi sonrası kısa bir geri alma penceresi. |
| Denetim kaydı | **1 yıl** | Değiştirilemez, ama **süresiz değil**. Bir bitirme projesi için bir yıl fazlasıyla yeterli; sonrasında toplu silinir. |
| Ölçüm verisi (`docs/measurements/`) | **Süresiz** | ⚠️ Bu **kişisel veri değildir** — anonim performans sayılarıdır. Aksine kaybedilmemesi gereken kalem ([backup.md §1](backup.md)). |

### Otomatik temizlik işi

Veritabanı henüz yok, dolayısıyla **çalışan bir temizlik işi yazılmadı** — olmayan tabloya karşı kod yazmak spekülatif olurdu. Bunun yerine Faz 3'ün uygulayacağı sözleşme burada sabitleniyor:

```sql
-- Faz 3'te bir zamanlanmış işe (günlük) bağlanacak sözleşme.
DELETE FROM vehicle_positions WHERE recorded_at < now() - interval '30 days';
DELETE FROM process_traces   WHERE created_at  < now() - interval '30 days';
DELETE FROM audit_log        WHERE created_at  < now() - interval '1 year';

-- Teslimat: kayıt silinmez, kişisel alanlar boşaltılır (koordinat ölçüm için kalır).
UPDATE deliveries
   SET address_line = NULL, recipient_name = NULL
 WHERE delivered_at < now() - interval '90 days';
```

Bu işin **yedeklerle hizalanması** gerekiyor: [backup.md §3](backup.md) veritabanı yedeklerini 30 gün tutuyor. Yani silinen bir kayıt en fazla 30 gün daha yedeklerde yaşar ve sonra kendiliğinden düşer (bkz. §5.4).

---

## 4. Demo ve tez görünürlüğü — "demo kipi"

**Kural: jüri odasında projeksiyonda gerçek bir adres veya kişi adı GÖRÜNMEZ. Tezdeki ekran görüntülerinde de aynı kural geçerlidir.**

Bu projede veri zaten sentetik olduğu için risk teorik — **ama kural yine de uygulanır**, çünkü:
1. Sentetik bir isim bile gerçek bir kişiyle rastlantısal olarak çakışabilir (Faker gerçek Türkçe ad/soyad havuzundan üretiyor).
2. Kapsam ileride genişler ve gerçek veri girerse, koruma zaten yerinde olur.

### Gereksinim: `DEMO_MODE`

| | |
|---|---|
| Açılma biçimi | Tek bir ortam değişkeni: `DEMO_MODE=true` (sunucu tarafında okunur, istemciden değiştirilemez) |
| Maskelediği alanlar | `full_name` → `Şoför A`, `Şoför B`… · `recipient_name` → `Alıcı #1234` · `address_line` → yalnızca ilçe adı (`Kadıköy`) · varsa `plate` → `34 XX 000` |
| Maskelemediği | Koordinatlar, mesafeler, ölçüm sayıları — demo bunları göstermek için var |
| Nerede uygulanır | **Sunucu tarafında, yanıt üretilirken.** İstemcide CSS ile gizlemek yeterli değildir; ağ sekmesinde veri görünür. |

**Faz 12.4'ün kurulum kontrol listesine eklenecek satır** (Faz 12 henüz yazılmadı, devir olarak kayıtlı — §7):

```
- [ ] DEMO_MODE=true mu? (sunucu yanıtında bir kişi adı görünmediği elle doğrulandı)
```

Aynı satır [backup.md §6](backup.md) altın kopya prosedürüne de eklendi — altın kopya savunmadan hemen önce alındığı için doğal bir kontrol noktası.

---

## 5. Teknik önlemler

### 5.1 Loglama
Kişisel veri içeren alanlar **hiçbir logda görünmez**. Bu, [0.3'te kurulan](secrets-audit.md) log maskeleme filtresinin kapsamına dahildir — filtre yalnızca token/parola değil, `full_name`, `recipient_name`, `address_line`, `phone` alanlarını da maskeler. Faz 3'te filtre yazıldığında **testle kanıtlanacak** (0.3 §4.9 devir tablosunda kayıtlı).

### 5.2 Yedeklerin şifrelenmesi
Veritabanı dump'ları kişisel veri içerir → [backup.md §3](backup.md) uyarınca `age -e` ile şifrelenir. Git bundle'ları şifrelenmez çünkü içlerinde kişisel veri yok (yalnızca kod + sentetik veri).

### 5.3 Dışa aktarma (CSV) uçları
Bir CSV export ucu yazılırsa (Faz 6/8): **yetki denetimi zorunlu** (yalnızca admin) **ve her export denetim kaydına yazılır** (kim, ne zaman, kaç satır, hangi filtre). Export, kişisel veriyi sistemden dışarı çıkaran en kolay yoldur; izsiz bırakılamaz.

### 5.4 Silme talebi — düşünülmesi gereken köşe

Bir kişi verisinin silinmesini isterse, `DELETE FROM drivers` yetmez. Üç iz daha vardır:

| İz | Sorun | Çözüm |
|---|---|---|
| **Outbox tablosu** | Olay yükleri (payload) kişisel alan kopyası taşıyabilir; ana tablodan silmek bunları temizlemez | **Önleyici tasarım**: outbox olayları kişisel alan **taşımaz**, yalnızca ID referansı taşır. Bu, Faz 7.3'e (outbox/olay sözleşmeleri) bağlayıcı bir kısıt olarak devredildi. |
| **Denetim kaydı** | Değiştirilemez olmalı — ama içinde kişi adı varsa silinmesi gerekir; çelişki | **Çözüm**: denetim kaydı aktörü **ID ile** tutar, ad ile değil. Kişi silindiğinde ID yetim bir işaretçiye dönüşür: eylem izi (kim-ne-zaman-ne) korunur, kimlik kaybolur. Değiştirilemezlik bozulmadan silme hakkı karşılanır. |
| **Yedekler** | Şifreli arşivden geriye dönük satır silinemez | **Kabul edilen cevap**: silinmez, **eskitilir**. Yedek saklama süresi 30 gün olduğu için (§3) veri en fazla 30 gün sonra kendiliğinden düşer. Bu, yaygın ve savunulabilir bir yaklaşımdır; tezde de böyle yazılır. |

---

## 6. Tez bölümü taslağı (Yöntem)

> Aşağıdaki paragraf Faz 12.1'in birikim hattına düşürüldü; tezin Yöntem bölümüne girecek.

> **Veri kaynağı.** Bu çalışmada kullanılan teslimat noktaları ve şoför kayıtları **tamamen sentetiktir**; gerçek bir kargo firmasının müşteri, adres veya personel verisi kullanılmamıştır. Sentetik veri, İstanbul'un yirmi ilçe merkezi etrafında ağırlıklı Gauss dağılımıyla üretilmiştir. Tekdüze rastgele üretim bilinçli olarak tercih edilmemiştir: gerçek kargo taleplerinin mekânsal kümelenme karakterini korumak, problemin zorluk yapısını temsil etmek açısından gereklidir. Üretilen örnekte en yoğun ve en seyrek ilçe arasındaki teslimat sayısı oranı 5.7 kat olarak ölçülmüştür. Noktalar arası mesafe ve seyahat süresi matrisi ise sentetik değil, **OpenStreetMap tabanlı gerçek yol ağı** üzerinden hesaplanmıştır; dolayısıyla tek yönlü yollar, köprü darboğazları ve Boğaz geçişlerinden kaynaklanan asimetrik maliyetler modelde korunmuştur. Veri üretimi deterministiktir: sabit bir tohum (seed) ve kaydedilmiş kütüphane sürümü ile aynı veri kümesi yeniden üretilebilir, bu da ölçümlerin tekrarlanabilirliğini garanti eder. Sentetik verinin yakalamadığı tek yapı zamansal desenlerdir (teslimat zaman pencereleri, saat bazlı trafik yoğunluğu); bu çalışmanın problem formülasyonu zaman penceresi içermediğinden bu sınırlama sonuçları etkilememektedir.

---

## 7. Devredilenler

| Devredilen | Hedef |
|---|---|
| Telefon alanı veri modeline **eklenmeyecek** (§1.1) | Faz 7.2 |
| Outbox olayları kişisel alan taşımayacak, yalnızca ID referansı (§5.4) | Faz 7.3 |
| Denetim kaydı aktörü ID ile tutulacak, ad ile değil (§5.4) | Faz 6.5 (İ) |
| Log maskeleme filtresine kişisel alanların eklenmesi + testle kanıt (§5.1) | Faz 3 |
| Otomatik temizlik işinin gerçek tabloya bağlanması (§3) | Faz 3 |
| CSV export yetki denetimi + denetim kaydı (§5.3) | Faz 6/8 |
| `DEMO_MODE` uygulaması (§4) | Faz 6.3 |
| `DEMO_MODE` kontrol satırının kurulum listesine eklenmesi (§4) | Faz 12.4 |
| Yöntem paragrafının teze işlenmesi (§6) | Faz 12.1 / 12.2 |
