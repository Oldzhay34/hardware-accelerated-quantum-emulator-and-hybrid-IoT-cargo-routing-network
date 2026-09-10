# Sır Denetimi

**Kaynak**: Faz 0 alt dal 0.3 · **Tarama tarihi**: 2026-09-10 · **Durum**: ✅ Tamamlandı (SOPS+age onaylandı ve uygulandı 2026-09-10)

> Bu alt dal iki aşamalıdır: önce tara+rapor+karşılaştır, sonra **kullanıcı onayı**, sonra uygulama.
> Bölüm 3'te durulmuş, onay alınmış, Bölüm 4 uygulanmıştır.

---

## 1. Tarama — bulgular

### Araç seçimi: **gitleaks**

| Aday | Gerekçe |
|---|---|
| **gitleaks** ✅ | Tek ikili dosya, kurulum sürtünmesi sıfır (winget ile kuruldu), git geçmişini native tarar, [.github/workflows/secrets-scan.yml](../.github/workflows/secrets-scan.yml) zaten `gitleaks-action` kullanıyor (0.2'de hazırlanmıştı) — CI ile aynı araç, sonuç tutarlılığı garanti. |
| trufflehog | Daha fazla doğrulama (canlı API'ye karşı kontrol) yapabiliyor ama tek geliştirici için kurulum/konfig yükü daha yüksek; bu ölçekte fayda-maliyet gitleaks'i geçmiyor. |
| detect-secrets | Baseline dosyası yönetimi (`.secrets.baseline`) gerektiriyor — ekstra bir bakım yükü; CI'ya bağlamak daha fazla adım istiyor. |

**Karar**: gitleaks. Gerekirse detect-secrets ikinci katman olarak eklenir (bugün gerek yok).

### Tarama 1 — çalışma ağacı (gitignore'a uymadan, ham disk)

```
gitleaks detect --source . --no-git
→ 39 bulgu, tamamı .venv/ altında (üçüncü parti kütüphane test sabitleri:
  numpy RNG test vektörleri, tornado'nun kendi test sertifikası, pywin32
  tip tanımları). Hiçbiri bu projeye ait değil, hiçbiri git'e girmiyor.
```

### Tarama 2 — git modu (izlenen dosyalar + **tüm commit geçmişi**)

```
gitleaks detect --source .
→ 5 commit tarandı, 0 bulgu.
```

**Bu, "dosyadan silinmiş ama geçmişte duran sır" sorusunu da kapsıyor** — 5 commit'in tamamı (Faz 0 kurulumu) tarandı, hiçbirinde sır yok.

### Tarama 3 — elle, dosya adına değil **içeriğe** bakan tarama

`password|passwd|secret|api[_-]?key|token|ssh|jwt|private[_-]?key|mqtt.*pass|smtp|admin.*pass|seed.*user` deseniyle tüm depo (`.venv` hariç) tarandı.

7 dosyada eşleşme — **hepsi belge/şablon metni içinde kavram geçişi**, gerçek sır değil:
- `docs/repo-conventions.md`, `CLAUDE.md`, `infra/README.md`, `docs/README.md` → sır yönetimi *kuralından* bahsediyor.
- `.github/workflows/secrets-scan.yml` → `secrets.GITHUB_TOKEN` GitHub Actions'ın kendi mekanizması, değer içermiyor.
- `specs/000-kapsam-takvim/scope-triage.md` → "JWT" kelime geçişi (Faz 8.2 açıklaması).
- `.specify/templates/spec-template.md` → spec-kit'in kendi örnek metni ("reset their password").

### Servis envanteri

| Servis | Konfigürasyon kaynağı | Kendi `.env` yolu var mı | Tanımlı değişken | Sessiz varsayılan |
|---|---|---|---|---|
| — | — | — | — | — |

**Tablo boş — dürüstçe.** `services/`, `firmware/`, `hls/`, `agent/`, `web/`, `infra/` dizinlerinin hepsi henüz yalnızca [0.2](../specs/000-kapsam-takvim/scope-triage.md)'de kurulan README iskeletini taşıyor; hiçbir gerçek servis kodu yazılmadı. **PYNQ SSH kimlik bilgisi, ESP32 Wi-Fi parolası, MQTT cihaz parolası — bunların hiçbiri henüz var olmayan koda gömülemez.**

### Sonuç

🟢 **Depo temiz.** Sızmış sır yok, rotasyon gereken bir şey yok. Bu alt dalın "ACİLDİR" uyarısı, kodda gerçek sır biriktiğinde geçerli olacak — bugün için önleyici bir standart kurmak yeterli.

---

## 2. Karşılaştırma — sır deposu kararı

Henüz gerçek bir sır olmadığı için bu karar **erken ve düşük riskli** verilebilir; yanlış seçilirse bugün geri dönüş maliyeti sıfıra yakın.

| Kriter | Platform-native (Railway env + k8s Secret) | Harici kasa (Vault/Infisical/Doppler) | SOPS + age, git'te şifreli dosya |
|---|---|---|---|
| İşletim maliyeti | Sıfır — platformun kendi arayüzü | Ek servis: kendi barındır (Vault, ağır) veya SaaS'a kaydol (Infisical/Doppler ücretsiz katman var ama [0.6 maliyet takibine](cost.md) yeni bir kalem ekler) | Sıfır — tek ikili araç (`sops`), anahtar yönetimi hariç ek servis yok |
| Tek geliştirici karmaşıklığı | Düşük — ama **iki ayrı yerde** (Railway panel + `kubectl`) elle senkron gerekir | Orta — tek doğruluk kaynağı var ama yeni bir araç/hesap öğrenilir | Düşük-orta — tek dosya, git diff'te görünür (şifreli), ama `age` anahtarının kendisi yeni bir "sır" olur |
| Yerel geliştirme deneyimi | Kötü — yerelde Railway/k8s olmadan değer okunamaz, elle `.env` kopyalanır | İyi — CLI ile yerel ortama enjekte edilebilir | İyi — `sops exec-env` ile yerelde de tek komut |
| Rotasyon | Elle, iki yerde ayrı ayrı | Kolay — merkezi, bazılarında otomatik | Elle — dosya yeniden şifrelenir, redeploy tetiklenir |
| k8s + Railway ikilisiyle uyum | Doğal ama **tutarsız** — iki farklı arayüz, iki farklı kayıt | Infisical'in hem k8s operator'ü hem Railway entegrasyonu var — **tek kaynaktan iki hedefe** | Şifre çözme adımı her iki hedef için de aynı script'ten çağrılabilir — **tek kaynaktan iki hedefe**, ama script'i sen yazarsın |
| ⚠️ Kritik uyarı | **k8s Secret varsayılan olarak base64'tür, ŞİFRELİ DEĞİLDİR.** Bu seçenek tek başına kullanılırsa etcd şifrelemesi ayrıca açılmalı — açılmazsa depoya sır koymamak için harcanan çaba, kümede boşa gider. | — | — |

### Tavsiye: **SOPS + age**

Gerekçe (14 hafta kısıtı ile doğrudan bağlı):

1. **Yeni bir hesap/servis yok.** Infisical/Doppler yeni bir hesap, yeni bir bağımlılık, [docs/cost.md](cost.md)'a (henüz yazılmadı, Faz 0.6) yeni bir izlenecek kalem demek. SOPS bunların hiçbirini getirmiyor.
2. **Git ile aynı iş akışında yaşıyor.** Sır değişikliği bir commit'tir; PR şablonundaki ([`.github/PULL_REQUEST_TEMPLATE.md`](../.github/PULL_REQUEST_TEMPLATE.md)) "sır tarayıcı temiz" kutusu zaten bunu bekliyor.
3. **k8s Secret'ın "şifreli değil" tuzağına otomatik çözüm.** SOPS dosyası zaten şifreli; k8s'e uygularken `sops` ile çözülüp Secret nesnesi oluşturulur — etcd şifrelemesini ayrıca açmayı unutma riski ortadan kalkar.
4. **Tek dezavantaj yönetilebilir**: `age` özel anahtarının kendisi artık en kritik sırdır. Bunun için **tek** önlem yeterli: bu anahtar [Faz 0.5 yedekleme planının](backup.md) "yeniden üretilemez" kategorisine düşürülür ve git'in **dışında**, ayrı bir yerde (parola yöneticisi veya harici disk) tutulur.

**Alternatif senaryo**: Proje ilerledikçe Railway + k8s dışına üçüncü bir hedef eklenirse (örn. gerçek bir Vault ihtiyacı doğarsa) bu karar [ADR olarak](decisions/ADR-TEMPLATE.md) yeniden açılabilir — bugün için erken optimizasyon olur.

---

## 3. ✅ Onay

**SOPS + age onaylandı** (kullanıcı, 2026-09-10). Anayasa Prensip I gereği bu onay alınmadan Bölüm 4'e geçilmemişti.

---

## 4. Uygulama

### 4.1 Kurulan araçlar

| Araç | Sürüm | Kaynak |
|---|---|---|
| gitleaks | 8.30.1 | `winget install Gitleaks.Gitleaks` |
| sops | 3.13.3 | `winget install SecretsOPerationS.SOPS` |
| age | 1.3.1 | `winget install FiloSottile.age` |

### 4.2 age anahtarı — konum ve koruma

| | |
|---|---|
| **Açık anahtar** (repoda, `.sops.yaml` içinde) | `age14tkstls957repyqvaa6xhn73ww4nllrtk32rz939u4tre0l3eddsuuxv55` |
| **Özel anahtar** (repoda **DEĞİL**) | `%APPDATA%\sops\age\keys.txt` |
| Dosya izni | `icacls` ile kısıtlandı: yalnızca `olcay:(R,W)`. `age-keygen`'in "world-readable" uyarısı bu adımla kapatıldı. |

> 🔴 **Bu özel anahtar kaybolursa şifreli sırlar KURTARILAMAZ.**
> Faz 0.5'in ([docs/backup.md](backup.md)) "yeniden üretilemez" envanterine **bu dosya eklenecektir** — bu, 0.5'e devredilen bağlayıcı bir gerekliliktir.
> Anahtar git'in dışında, ayrı bir yerde (parola yöneticisi veya harici disk) yedeklenmelidir.

### 4.3 Kurulan dosyalar

| Dosya | Rol | Git'te? |
|---|---|---|
| [`.sops.yaml`](../.sops.yaml) | Hangi dosya hangi anahtarla şifrelenir | ✅ evet |
| [`secrets.enc.yaml`](../secrets.enc.yaml) | Tek doğruluk kaynağı, şifreli | ✅ evet (şifreli olduğu için güvenli) |
| [`scripts/secrets.ps1`](../scripts/secrets.ps1) | `edit` / `env` / `check` komutları | ✅ evet |
| `.env` | Yerelde üretilen düz dosya | ❌ `.gitignore`'da |
| `%APPDATA%\sops\age\keys.txt` | Özel anahtar | ❌ repoda değil |

**Şifreleme davranışı doğrulandı**: YAML'da anahtar adları düz kalıyor (`database:`, `password:`), yalnızca değerler `ENC[AES256_GCM,...]` oluyor. Yani `git diff` "hangi değişken değişti" sorusunu cevaplıyor, değeri sızdırmadan.

`secrets.enc.yaml` içindeki değerler şu an **yer tutucudur** (`PLACEHOLDER_*`) — Bölüm 1'in bulgusu gereği henüz gerçek sır yok. Biçim hazır; ilk gerçek sır üretildiğinde `sops secrets.enc.yaml` ile yerine yazılır.

### 4.4 Kullanım

```powershell
.\scripts\secrets.ps1 edit    # şifreli dosyayı editörde aç (kaydedince otomatik şifreler)
.\scripts\secrets.ps1 env     # yerel geliştirme için .env üret (gitignore'da)
.\scripts\secrets.ps1 check   # çözme çalışıyor mu + depoda düz sır kaldı mı
```

### 4.5 Doğrulama koşuları

| Test | Sonuç |
|---|---|
| Şifrele → çöz (round-trip) | ✅ 9 değişkenin tamamı doğru çözüldü |
| `.env` üretimi | ✅ 9 değişken yazıldı |
| `.env` gitignore'da mı | ✅ `git check-ignore` doğruladı |
| `secrets.enc.yaml` izlenebilir mi | ✅ ignore edilmiyor |
| `secrets.ps1 check` | ✅ çözme OK + gitleaks temiz (6 commit) |

**Uygulama sırasında yakalanan iki hata** (ikisi de düzeltildi):

1. **Türkçe locale `ToUpper()` tuzağı** — `.env` üretiminde `jwt_signing_key` → `AUTH_JWT_SİGNİNG_KEY` oluyordu (noktalı büyük İ), bu geçersiz bir ortam değişkeni adı. `ToUpperInvariant()` ile düzeltildi ve script'e yorum olarak not edildi. Bu tuzak Türkçe locale'de çalışan her string dönüşümünde tekrar edebilir.
2. **`check` komutunda `--no-git`** — `.gitignore`'u atlayıp `.venv`'deki üçüncü parti test sabitlerini sızıntı sanıyordu (39 yanlış pozitif), yani komut her zaman fail ederdi. Git moduna çevrildi.

### 4.6 Rotasyon

**Şu an rotasyon gerektiren sır yok** — Bölüm 1 taraması temiz çıktı, sızmış sır bulunmadı.

İleride bir sır sızarsa uygulanacak sıra:

| Sır tipi | Rotasyon adımı | Yan etki |
|---|---|---|
| Veritabanı parolası | DB'de değiştir → `secrets.ps1 edit` → redeploy | Kısa kesinti |
| JWT imza anahtarı | Yeni anahtar üret → redeploy | **Tüm oturumlar düşer** — düşük trafikli bir saate planla |
| MQTT cihaz parolası | Broker'da değiştir → **her ESP32'ye yeniden yükleme** | Fiziksel erişim gerekir, bkz. risk `DT-02` |
| PYNQ SSH | Kartta `passwd` → `secrets.ps1 edit` | Yok |
| Railway / Cloudflare token | Panelden iptal + yeni üret | Yok |

**Rotasyon kaydı**: *(boş — henüz rotasyon yapılmadı)*

### 4.7 Git geçmişi temizliği

**Gerekmiyor.** Bölüm 1'deki git modu taraması 5 commit'in tamamını taradı ve hiçbir sır bulmadı; temizlenecek geçmiş yok.

İleride gerekirse: `git-filter-repo` (önerilen) veya BFG kullanılır. **Ama önce rotasyon** — geçmiş temizliği rotasyonun yerine geçmez, çünkü sır zaten görülmüş olabilir (klon, fork, CI logu).

### 4.8 CI kapısı

[.github/workflows/secrets-scan.yml](../.github/workflows/secrets-scan.yml) Faz 0.2'de hazırlanmıştı, `gitleaks-action` kullanıyor — yerelde kullandığımız araçla aynı, sonuç tutarlılığı garanti. Uzak depo (GitHub) bağlandığında otomatik devreye girer.

Yerelde aynı kontrol: `.\scripts\secrets.ps1 check`.

### 4.9 Sonraki fazlara devredilenler

| Devredilen | Hedef |
|---|---|
| age özel anahtarını "yeniden üretilemez" envanterine ekle | **Faz 0.5** ([backup.md](backup.md)) |
| Servis başına `.env.example` yaz (gerçek servis kodu doğduğunda) | **Faz 3** ve sonrası |
| Açılışta zorunlu değişken doğrulaması (eksikse servis çalışmayı reddetsin) | **Faz 3.2** servis sözleşmeleri |
| Log maskeleme filtresi + testle kanıt | **Faz 3** / **Faz 0.4** (kişisel veri) |
| Testlerde Testcontainers'ın geçici kimlik bilgileri | **Faz 11** test stratejisi |
| PYNQ tarafı için `secrets.ps1`'in bash karşılığı | **Faz 5** (agent Linux'ta koşuyor) |
