# Yedekleme, Geri Yükleme ve Felaket Provası

**Kaynak**: Faz 0 alt dal 0.5 · **Oluşturma**: 2026-09-10

> Savunmadan bir hafta önce diskin bozulması senaryosuna hazırlıksız yakalanmak, projeyi bitirmiş olmana rağmen kaybetmek demektir. Bu belge o senaryoyu bugün, maliyeti sıfırken önlüyor.

---

## 1. Envanter — neyi kaybedersem proje biter

| Kalem | Yeniden üretilebilir mi? | Neden |
|---|---|---|
| Kıyas koşumlarının ham ölçüm verisi (`docs/measurements/`) | 🔴 **HAYIR** | Yeniden koşmak donanım zamanı + gerçek saat ister; üstelik bağlam (git commit, konfigürasyon) değişmiş olabilir — [VR-03 riski](risk-register.md) zaten bunu "damgasız koşum geçersiz" diye işaretliyor. |
| Sentez raporları + bitstream/overlay (`artifacts/bitstream/`, `artifacts/overlay/`) | 🔴 **HAYIR** | Yeniden sentez saatler sürer (bkz. [cut-plan.md K-02/K-03/K-04](../specs/000-kapsam-takvim/cut-plan.md) — sentez turlarının kendisi haftalarca risk kaynağı). |
| INA219 kalibrasyon kayıtları | 🔴 **HAYIR** | Fiziksel donanımla tekrar kalibrasyon gerekir; ölçüm günü koşullarına (sıcaklık, kablo direnci) bağlı, tam tekrar edilemez. |
| Tez metni ve şekiller (`docs/thesis/`, `docs/figures/`) | 🔴 **HAYIR** | Haftalarca yazım emeği; şekiller ham veriden üretiliyor ama ham veri de kritikse zincir kırılır. |
| Sunum destesi, poster, demo videosu | 🔴 **HAYIR** | Video özellikle — yeniden çekim için donanım + zaman + o anki durum gerekir. |
| Eğitilmiş ML modeli ve eğitim verisi (`artifacts/models/`) | 🔴 **HAYIR** *(varsa)* | [VR-01 riski](risk-register.md) zaten bu verinin üretiminin kendisinin riskli olduğunu gösteriyor — kaybedilirse üretim süreci baştan başlar. Not: Faz 3.3 taban planda **İ** ([scope-triage.md](../specs/000-kapsam-takvim/scope-triage.md)), yani bu kalem gerçekleşmeyebilir de. |
| 🔴 **age özel anahtarı** (`%APPDATA%\sops\age\keys.txt`) | 🔴 **HAYIR** | [ADR 0002](decisions/0002-sops-age-sir-yonetimi.md) uyarınca kaybolursa `secrets.enc.yaml` içindeki her şey kalıcı olarak kurtarılamaz. Bu envantere resmen giriyor — 0.3'ün bıraktığı bağlayıcı iş burada kapanıyor. |
| Kaynak kod, `specs/`, `docs/` (metin dosyaları) | 🟢 EVET | Git'te; bkz. §2 — ama **bugüne kadar tek kopyaydı**, bkz. §5 BK-00. |
| Docker imajları | 🟢 EVET | `Dockerfile`'dan yeniden build edilir (henüz `Dockerfile` yok — Faz 3+). |
| Veritabanı şeması | 🟢 EVET | Migration dosyalarından (henüz veritabanı yok — Faz 3+). |
| Grafana panoları (JSON) | 🟢 EVET *(varsa)* | Repoda tutulacak. Not: Faz 14 taban planda **İ**, muhtemelen hiç yapılmayacak. |

**Gözlem**: Kritik (yeniden üretilemez) kalemlerin **hiçbiri henüz mevcut değil** — proje Faz 0'da. Bu, yedekleme planını kurmak için en ucuz an: kaybedilecek bir şey yokken süreç test edilebiliyor.

---

## 2. Yedek planı (3-2-1 kuralı, bu ölçeğe uyarlanmış)

**Kural**: en az iki farklı yerde, biri fiziksel olarak ayrı.

| Hedef | Tür | Neyi kapsıyor | Sıklık |
|---|---|---|---|
| `%OneDrive%\yedekler\qir-engine\` | Bulut, fiziksel olarak ayrı | Git bundle (kod+specs+docs, metin) | Her `scripts/backup.ps1` çalıştığında |
| `D:\yedekler\qir-engine\` | İkinci sabit disk, aynı makinede | Git bundle (aynısı) | Her `scripts/backup.ps1` çalıştığında |
| — | **Uzak git barındırma (GitHub vb.)** | — | 🔴 **YOK — bkz. §5 BK-00, en kritik açık madde** |

### ⚠️ Bilinçli sınırlama — neden "uzak git" yok

Bu depo şu an **hiçbir uzak sunucuya bağlı değil** (`git remote -v` boş). Bir GitHub deposu eklemek en doğal çözüm olurdu, ama bu **senin GitHub hesabını** kullanmayı gerektiriyor — hesap/kimlik doğrulama işlemleri benim tek başıma alabileceğim bir karar değil. Bunun yerine bugün elimdeki araçlarla (OneDrive + D: sürücüsü) gerçek bir 3-2-1 kurdum ve BK-00'ı riske açıkça yazdım. **Bu konuşmanın sonunda sana soracağım.**

### Büyük ikili dosyalar (bitstream, video, model)

[ADR 0001](decisions/0001-monorepo.md) ve [repo-conventions.md §3](repo-conventions.md) kararı gereği bu dosyalar git'e **hiç girmiyor** — dolayısıyla `git bundle` onları **kapsamaz**. Bu tür dosyalar doğduğunda (Faz 2+ sentez raporları, Faz 12 video):

- `scripts/backup.ps1`'e bir **ikinci adım** eklenecek: `artifacts/` ve `docs/figures/`, `docs/thesis/` içindeki büyük dosyaları da aynı iki hedefe (OneDrive + D:) kopyalayan bir `robocopy /MIR`.
- Bu genişletme **Faz 0.5'in kapsamı dışında bırakıldı** çünkü bugün `artifacts/` boş — olmayan dosyayı yedekleme kodu yazmak spekülatif olurdu. Genişletme görevi aşağıda §6'da devredildi.

### Otomatikleştirme

**Elle yapılan yedek yapılmayan yedektir.** [scripts/backup.ps1](../scripts/backup.ps1) yazıldı ve çalıştırıldı (bkz. §4). Windows Görev Zamanlayıcı'ya bağlamak için hazır komut:

```powershell
# HAFTALIK OTOMATİK YEDEK — bunu kaydetmek için (sistem değişikliği, onayın gerekiyor):
$action = New-ScheduledTaskAction -Execute "powershell.exe" -Argument '-NoProfile -File "C:\Users\olcay\IdeaProjects\qir-engine\scripts\backup.ps1"'
$trigger = New-ScheduledTaskTrigger -Weekly -DaysOfWeek Friday -At 18:00
Register-ScheduledTask -TaskName "qir-engine-backup" -Action $action -Trigger $trigger -Description "Faz 0.5 haftalık git yedek"
```

Bu komut **çalıştırılmadı** — Görev Zamanlayıcı'ya kalıcı bir görev eklemek sistem durumunu değiştiriyor, onayın soruluyor (bkz. konuşmanın sonu).

---

## 3. Veritabanı yedeği (henüz yok — standart şimdiden yazıldı)

Henüz hiçbir servis veya veritabanı kurulmadı (`services/` boş). Bu bölüm, Faz 3+ bir veritabanı doğduğunda **tekrar düşünülmemesi** için standardı şimdiden sabitliyor:

| Karar | Değer |
|---|---|
| Araç | `pg_dump` (varsayılan PostgreSQL kararı — Faz 3.1'de servis çatısı kesinleşince teyit edilecek) |
| Sıklık | Günlük, zamanlanmış iş (yukarıdaki Görev Zamanlayıcı deseniyle aynı) |
| Şifreleme | **Zorunlu** — dump kişisel veri içerir ([docs/data-governance.md](data-governance.md), Faz 0.4 ile bağlı, henüz yazılmadı). SOPS+age ile değil (o küçük yapılandırma sırları için), ayrı bir şifreli arşiv (`age -e` doğrudan dump dosyasına) kullanılacak. |
| Saklama süresi | 30 gün, sonra otomatik silinir (kişisel veri saklama disiplini, 0.4 ile hizalanacak) |
| Yer | Aynı iki hedef: OneDrive + D: |

---

## 4. Geri yükleme provası — ✅ YAPILDI (atlanamaz adım)

**Test edilmemiş yedek, yedek değildir.** Bugün gerçek bir prova koşuldu:

```
Tarih: 2026-09-10 12:40:16
Komut: scripts/backup.ps1

1) git bundle oluştur     → 95.6 KB, 7 commit
2) iki hedefe kopyala     → OneDrive\yedekler\qir-engine\ VE D:\yedekler\qir-engine\ — ikisi de doğrulandı
3) BOŞ bir dizine sıfırdan geri yükle (git clone --quiet <bundle>)
   → Geri yükleme süresi: 0.247 saniye
   → Geri yüklenen commit sayısı: 7 / 7
   → HEAD karşılaştırması: EŞLEŞTİ (orijinal ile birebir aynı hash)

SONUÇ: GEÇTİ
```

**Bugünkü süre (0.25 sn) küçük depo boyutundan (896 KB) kaynaklanıyor** — `artifacts/` büyüdükçe bu süre değişmeyecek çünkü bundle yalnızca git-tracked içeriği kapsıyor (büyük ikili dosyalar zaten dışarıda, §2). Kod+specs+docs tarafı için geri yükleme süresi projenin sonuna kadar saniyeler mertebesinde kalacaktır.

**Prova ritüeli**: Bu script her çalıştığında §3 doğrulaması otomatik koşuyor (`.\scripts\backup.ps1` içinde adım 3) — yani her yedek, alındığı anda kendi kendini test ediyor. Ayrıca [faz-sonu-kontrol.md](faz-sonu-kontrol.md)'ye bir madde eklendi (§6).

---

## 5. Felaket senaryoları ve geri dönüş süresi

| Senaryo | Geri dönüş süresi | Nasıl |
|---|---|---|
| 🔴 **BK-00: Laptop çalındı/bozuldu VE OneDrive/D: senkron olmamış** | **Belirsiz — bugünkü en büyük açık** | D: aynı makinede olduğu için laptop kaybında **o da gider**; yalnızca OneDrive kalır. OneDrive senkronu gecikmişse son commit'ler kaybolabilir. **Kalıcı çözüm: uzak git remote (§2 BK-00 notu, onayın bekleniyor).** |
| Laptop çalındı/bozuldu (OneDrive güncel) | Dakikalar | Yeni makinede OneDrive'dan bundle indir → `git clone` → age anahtarını ayrı yedekten geri yükle. |
| microSD bozuldu (PYNQ) | ~1 saat | Yeni SD karta PYNQ imajını tekrar yaz (imaj zaten yerel diskte duruyor, [risk kaydı DT-03](risk-register.md)). Kod/overlay git'ten veya `artifacts/` yedeğinden. |
| k3s düğümü çöktü | Değişken, ~30 dk – birkaç saat | Manifestler git'te (`infra/k8s/`); küme yeniden kurulur, `kubectl apply -f`. Kalıcı veri varsa (henüz yok) ayrı ele alınır. |
| Railway projesi silindi/limit aştı | ~1 saat | `infra/railway/` konfigürasyonundan yeniden dağıtım; ortam değişkenleri `secrets.enc.yaml`'den (`secrets.ps1 env`). |
| Git deposu bozuldu (lokal) | **Dakikalar** ✅ | `scripts/backup.ps1` ile en son bundle'dan `git clone` — bugün provası geçti. |
| ESP32'lerden biri yandı | Saatler (yedek kart varsa) / günler (sipariş) | [risk kaydı DT-02](risk-register.md) zaten bunu kapsıyor; firmware git'te, sadece donanım tedariki sorunu. |
| 🔴 FPGA kartı bozuldu | **Geri dönüşü yok — savunma stratejisi devreye girer** | Donanım kaybı geri döndürülemez ama proje kaybolmaz: `docs/measurements/` (ölçüm verisi), `artifacts/` yedekleri (sentez raporları, overlay), ve demo videosu **arşivlenmiş** olduğu için savunma bunlarla yapılır. Bu tam olarak [cut-plan.md K-01](../specs/000-kapsam-takvim/cut-plan.md)'in öngördüğü Senaryo B'dir — burada teyit ediliyor: **evet, arşivlenmiş koşumlar + video savunma için yeterlidir**, çünkü jüri canlı donanım değil, sonucu ve metodolojiyi değerlendirir. |
| 🔴 age özel anahtarı kayboldu | **Geri dönüşü yok, sırlar dahil** | [§1](#1-envanter--neyi-kaybedersem-proje-biter)'de kritik envantere eklendi. Tek önlem: anahtarı **bugün** ikinci bir yere (parola yöneticisi) elle kopyala — bu script'in otomasyon kapsamı dışında, çünkü otomatik kopyalamak anahtarı git'e yakın tutma riski taşır. |

---

## 6. Savunma öncesi dondurma — "altın kopya"

Jüri gününden **N gün önce**, o anki kod, veri, overlay, panolar, tez, deste, video alınır ve **dokunulmaz**. [schedule.md](../specs/000-kapsam-takvim/schedule.md) takvimine göre:

- Teslim/savunma penceresi **H14** (14–20 Aralık 2026).
- **Altın kopya tarihi: H13 sonu — 13 Aralık 2026 (Pazar).** Yani H14 (jüri haftası) başlamadan önce, H13'ün "sunum destesi + poster" işi bittiğinde.
- Bu tarih [schedule.md](../specs/000-kapsam-takvim/schedule.md)'ye ve H13/H14 satırlarına işlenecek (bkz. §7 devir).

**Altın kopya prosedürü** (H13 sonunda çalıştırılır):
```powershell
.\scripts\backup.ps1              # normal yedek
git tag altin-kopya-2026-12-13    # o anki commit'i etiketle, asla silinmez/taşınmaz
git bundle create altin-kopya.bundle --all
# + artifacts/, docs/thesis/, docs/figures/ içeriğinin ayrı, dokunulmayan bir kopyası
```

---

## 7. Devredilenler

| Devredilen | Hedef |
|---|---|
| `scripts/backup.ps1`'e büyük ikili dosya (`artifacts/`) yedekleme adımı ekle | İlk gerçek `artifacts/` içeriği doğduğunda (Faz 2 sentez raporları) |
| Veritabanı `pg_dump` + şifreleme scriptini gerçek servis koduna bağla | Faz 3.1/3.2 |
| Kişisel veri saklama süresiyle veritabanı yedek saklama süresini hizala | Faz 0.4 |
| Altın kopya tarihini (13 Aralık 2026) schedule.md'ye işle | Bu commit'te yapılıyor (§8) |
| Görev Zamanlayıcı'ya haftalık otomatik yedek kaydı | **Onayın gerekiyor** — konuşmanın sonunda soruluyor |
| Uzak git remote (GitHub) ekleme | **Onayın gerekiyor** — §2 BK-00, en kritik açık madde |
