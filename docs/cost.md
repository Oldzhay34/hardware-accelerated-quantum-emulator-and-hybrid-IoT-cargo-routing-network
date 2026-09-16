# Maliyet Takibi ve Ücretsiz Katman Limitleri

**Kaynak**: Faz 0 alt dal 0.6 · **Oluşturma**: 2026-09-13

> Bir bitirme projesinde beklenmedik fatura veya limit aşımı, teknik bir sorun kadar can yakar. Bu belge, henüz hiçbir servis kurulmadan (Faz 0'dayız) önleyici standardı sabitliyor.

**Kullanıcı kararları (2026-09-13)**:
- Bütçe tavanı: **0 TL** çoğu dönem boyunca; **son 1-2 ayda Railway Hobby planı (~$5/ay) kabul edilebilir**.
- Ödeme yöntemi: **hiçbir serviste kart bağlı değil** — otomatik faturalama riski şu an sıfır.
- Elektrik: kart+makine **yalnızca çalışırken açık** — sürekli açık kalmayacak.

---

## 1. Maliyet envanteri

Bugünkü gerçek durum: **hiçbir dış servis henüz kurulu değil.** `git remote -v` boş, `infra/railway/` boş iskelet, Cloudflare/veritabanı/nesne depo hiç yok. Tablo bu yüzden iki katmanlı: **bugün** (fiilen çalışan) ve **planlanan** (Faz 3+ doğacak).

| Servis | Durum | Ücretsiz katman limiti | Mevcut kullanım | Aşınca ne olur | Aylık tahmini maliyet |
|---|---|---|---|---|---|
| **GitHub Actions (CI)** | 🟢 **AKTİF (2026-09-16)** — `secrets-scan` + `csim-regression`, ikisi de yeşil | Private repo: 2.000 dk/ay (Linux). **ARM64/macOS işleri 10x çarpanla sayılır.** | **~1,2 dk/push** (csim 1 dk + gitleaks 8 sn) | Dakika biter, iş kuyruğa girmez / kart istenir | 0 TL. ~1.600 push/ay'a kadar bedava — gerçekçi kullanımın çok altında |
| **Railway** | 🟡 **Hobby planı var, ~12 Eki 2026'da bitiyor** (H5) | Hobby ~$5/ay | **Hiçbir şey dağıtılmadı** — dağıtılacak uygulama henüz yok | Kredi biterse servis **durur** (silinmez, ama çalışmaz) | **0 TL** şimdilik; H10'da (~16 Kas) yeniden alınacak — panel işi o hafta başlıyor |
| **Cloudflare (Tunnel + WAF + Turnstile)** | ⚪ Henüz hesap yok | Tunnel: ücretsiz sınırsız. WAF: 5 kural (ücretsiz plan). Turnstile: sınırsız doğrulama, ücretsiz. CDN: sınırsız bant genişliği (ücretsiz plan, "makul kullanım" şartı var) | — | Kural sayısı aşılırsa **yeni kural eklenemez** (var olanlar çalışmaya devam eder) | 0 TL — Faz 13 zaten taban planda **İ** ([scope-triage.md](../specs/000-kapsam-takvim/scope-triage.md)), muhtemelen hiç kurulmayacak |
| **Yönetilen veritabanı** | ⚪ Henüz yok | Railway içinde PostgreSQL eklentisi Railway'in kendi kotasına dahil, ayrı ücretsiz katmanı yok | — | Railway kotasına dahil olduğu için ayrı aşım yok | Railway'e dahil |
| **Nesne depo** | ⚪ Planlanmıyor | — | — | — | Taban planda yok; büyük ikili dosyalar OneDrive+G: SSD'de ([backup.md](backup.md)) |
| **OSRM (kamuya açık demo sunucusu)** | ⚪ Henüz kullanılmadı — Faz 1.1'de başlayacak | **Maliyet değil, KOTA**: proje.osrm.org "makul kullanım" politikası, agresif istekte IP engellenir | 0 istek | Engellenirsen **para kaybetmezsin, veri kaybedersin** — ölçüm turunun ortasında bloklanma riski | 0 TL |
| **Nominatim (kamuya açık)** | ⚪ Henüz kullanılmadı — Faz 1.1 | **KOTA**: 1 istek/saniye politikası (resmi kullanım şartı) | 0 istek | Aynı — IP engeli, para değil | 0 TL |
| **Alan adı** | ⚪ Planlanmıyor | — | — | — | Taban planda yok — Railway'in verdiği `*.up.railway.app` alt alan adı yeterli |
| **Elektrik** | 🟢 Bugün gerçek | — | Günlük birkaç saat, yalnızca çalışırken (kullanıcı kararı) | — | Önemsiz düzeyde (~10-20 TL/ay tahmini, PC+kart günlük birkaç saat) — **izlenmeyecek**, kullanıcı bunu bilinçli kabul etti |

---

## 2. En büyük risk kalemleri — hangisi beklenmedik biçimde patlayabilir

Sıralama: gerçekleşme olasılığı × sürpriz olma ihtimali.

| # | Kalem | Neden patlayabilir | Erken uyarı işareti |
|---|---|---|---|
| **1** | 🔴 **CI dakikaları — ARM64/çoklu-platform işler** | Her PR'da tetiklenen bir CI matrisi (ör. birden fazla Python sürümü × işletim sistemi) dakikaları hızla tüketir; ARM64 runner'lar **10x çarpanla** sayılır — bunu bilmeden bir iş eklemek limiti sessizce eritir. | `secrets-scan.yml`'e yeni bir iş eklenirken runner tipi kontrol edilmeli; `ubuntu-latest` dışına çıkmadan önce bu belgeye bakılır. |
| **2** | 🔴 **Railway çalışma saati — servisler 7/24 açık unutulursa** | Railway ücretsiz/Hobby kotası **saat bazlı**; bir servisi "deploy edip unutmak" günler içinde krediyi tüketir. | Haftalık ritüelde ([schedule.md §4](../specs/000-kapsam-takvim/schedule.md)) "Railway'de unutulmuş servis var mı?" kontrolü — bkz. §3. |
| **3** | 🟡 **Telemetri veri hacmi** | Faz 4'te öngörülen 10 Hz örnekleme, aylarca birikirse disk/veritabanı boyutu büyür — Railway'in kalıcı disk kotası aşılabilir. | [data-governance.md §3](data-governance.md)'teki 30 günlük saklama süresi bunu **önlüyor** — risk teoride var, disiplin uygulanırsa gerçekleşmez. |
| **4** | 🟢 CDN bant genişliği (video/büyük varlık) | Demo videosu veya büyük statik dosyalar CDN üzerinden servis edilirse ücretsiz katmanın "makul kullanım" sınırını zorlayabilir. | Faz 13 taban planda **İ** — muhtemelen hiç gerçekleşmeyecek durumda. |
| **5** | ⚪ OSRM/Nominatim IP engeli | Para kaybı değil ama **veri/zaman kaybı**: ölçüm turunun ortasında engellenmek, tekrarlanabilirliği bozar (Prensip II). | [Faz 1.1'e devredildi](#4-devredilenler): istek hızı sınırlaması (rate limiting) istemci tarafında baştan uygulanmalı. |

---

## 3. İzleme — Faz 14'e bağlanan gereksinim

Faz 14 (Gözlemlenebilirlik: Prometheus/Grafana) taban planda **İ** ([scope-triage.md](../specs/000-kapsam-takvim/scope-triage.md)) — muhtemelen hiç kurulmayacak. Bu yüzden maliyet izleme, ağır bir gösterge panosuna **bağımlı bırakılmıyor**; iki katmanlı tanımlanıyor:

| Katman | Ne zaman | Nasıl |
|---|---|---|
| **Bugünden itibaren — manuel** | Her hafta ([schedule.md §4](../specs/000-kapsam-takvim/schedule.md) ritüeline eklendi, bkz. §6) | Railway/Cloudflare/GitHub panelinden kullanım elle kontrol edilir. Servis yokken bu adım "N/A" geçilir. |
| **Faz 14 gerçekleşirse — otomatik** | Faz 14 açılırsa | Railway ve GitHub Actions kullanım API'lerinden çekilen bir Grafana paneli + limitin **%70'ine** yaklaşınca alarm. |

**Limit aşımı sessizce gerçekleşmeyecek** kuralı, Faz 14 olmasa bile haftalık manuel kontrolle karşılanıyor — otomatik panonun yokluğu bu kuralı geçersiz kılmıyor, sadece daha ucuz bir uygulaması var.

---

## 4. Tasarruf kararları

| Karar | Gerekçe |
|---|---|
| Railway servisleri **yalnızca aktif geliştirme/demo sırasında** ayakta tutulur; gece/hafta sonu kapatılır (geliştirme dışı dönemde) | Çalışma-saati bazlı kotayı doğrudan azaltır (risk #2) |
| Ağır CI işleri (tam entegrasyon testi, HLS C-sim) yalnızca **ana dala push'ta** koşar; her PR'da değil | Dakika kotasını (risk #1) korur — [Faz 11.5](../specs/000-kapsam-takvim/scope-triage.md) donanımsız CI kurulduğunda uygulanacak |
| Telemetri saklama süresi **30 gün** | [data-governance.md §3](data-governance.md) ve [backup.md §3](backup.md) ile zaten hizalı — üçüncü kez aynı sayı, tek karar |
| Elektrik: kart+makine yalnızca çalışırken açık | Kullanıcı kararı (2026-09-13) — izlenmeyecek kadar küçük, ayrı bir disiplin gerekmiyor |
| `ubuntu-latest` dışında runner **kullanılmaz** (ARM64/macOS yasak, gerekçesiz) | Risk #1'in kökünü kurutuyor — istisna gerekirse bu belgeye bakılıp bilinçli karar verilir |

---

## 5. Bütçe ve tavan

| | |
|---|---|
| **Aylık tavan** | **0 TL** (yalnızca ücretsiz katmanlar) — **H12–H14 döneminde** (son 1-2 ay, teslimat penceresi) Railway Hobby planı **~$5/ay** kabul edilebilir. |
| **Neden son aya saklanıyor** | Demo/kıyas koşumlarının canlı ve kesintisiz kalması gereken tam da o dönem; ücretsiz katmanın kredi tükenmesi riski en pahalıya bu haftalarda patlar. |
| **Ödeme yöntemi** | Hiçbir serviste kart bağlı değil (2026-09-13 itibariyle) — **otomatik faturalama riski sıfır**. Hobby planına geçilirse kart o an eklenir, harcama limiti (varsa) o an ayarlanır. |
| **Tavan aşılırsa** | Kart bağlı olmadığı sürece aşım **fiziksel olarak imkânsız** — servisler durur, fatura kesilmez. Kart eklendiğinde: Railway'in kendi "usage alert" e-posta bildirimi açılır (ücretsiz), tavanın %80'inde uyarı. |

---

## 6. Savunma günü — kotalar kontrol edildi

**Faz 12.4'ün kurulum kontrol listesine eklenecek** (Faz 12 henüz yazılmadı, devir olarak kayıtlı — §7 ve [backup.md §6](backup.md) altın kopya prosedürüyle aynı yere):

```
- [ ] Railway kredisi/plan durumu kontrol edildi — demo günü boyunca yetiyor mu?
- [ ] Cloudflare/domain aktif mi (kullanılıyorsa)?
- [ ] Kotalar kontrol edildi: hiçbir servis limitten dolayı durmuş değil.
```

Bu satır [backup.md §6](backup.md)'daki `DEMO_MODE` kontrolüyle **aynı anda**, altın kopya alınırken (H13 sonu, 13 Aralık) çalıştırılacak — iki ayrı kontrol listesi yerine tek bir "savunma öncesi" ritüeli.

---

## 7. Devredilenler

| Devredilen | Hedef |
|---|---|
| CI matrisine yeni platform eklenirken bu belgeye bakılması (ARM64/macOS yasağı) | Faz 11.5 (donanımsız CI) |
| OSRM/Nominatim istemci tarafı rate limiting | Faz 1.1 |
| Railway kullanım API'sinden otomatik gösterge/alarm | Faz 14 (gerçekleşirse — taban planda İ) |
| "Kotalar kontrol edildi" + `DEMO_MODE` ortak savunma-öncesi kontrol listesi | Faz 12.4 |
| Railway Hobby planına geçiş kararı (H12-H14 civarı) | Kullanıcı — o dönem geldiğinde hatırlatılacak (haftalık ritüel) |


---

## Railway zamanlaması — 2026-09-16 kararı

Mevcut Hobby planı **~12 Ekim**'de (H5) bitiyor. Panelin dağıtılacağı iş
(**6.3** mühendis konsolu + **8.1** gateway) takvimde **H10**'da, yani
**16 Kasım**. Aradaki boşluk **35 gün**.

**Karar: mevcut plan dağıtım için kullanılmayacak, bitmesine izin verilecek.**

Gerekçe:

1. **Dağıtılacak bir şey yok.** Faz 3 (backend) başlamadı, panel yazılmadı.
2. Şimdi harcanırsa **ona ihtiyaç duyulan işten bir ay önce** biter ve zaten
   yeniden alınması gerekir.
3. Deneme amaçlı bir dağıtımın Kasım'daki gerçek dağıtım hakkında öğreteceği
   şey sınırlı.
4. Geri dönüş yolu zaten planlı ve bedava — [K-08](../specs/000-kapsam-takvim/cut-plan.md):
   panel Railway'den yerele taşınır, `docker compose up`, jüri demosu yerelde.

**Domain**: satın alınmasına gerek yok. Kullanıcının elinde zaten bir alan adı
var (başka bir uygulama çalışıyor); sırası gelince **alt alan adı**
(`qir.<mevcut-domain>`) yeterli — mevcut uygulamaya hiç dokunmadan, tek DNS
kaydıyla. Railway ve Cloudflare Tunnel ayrıca ücretsiz alt alan adı da veriyor.

⚠️ Ölçüm eksenlerinin **hiçbiri** tünelden veya dağıtımdan geçmiyor
([cut-plan.md](../specs/000-kapsam-takvim/cut-plan.md) K-07). Domain ve Railway
bir **sunum** meselesidir, tez iddialarının koşulu değildir.
