# Sır Denetimi

**Kaynak**: Faz 0 alt dal 0.3 · **Tarama tarihi**: 2026-09-10 · **Durum**: Bölüm 1-2 tamamlandı, **Bölüm 4 (uygulama) onay bekliyor**

> Bu alt dal iki aşamalıdır: önce tara+rapor+karşılaştır (bu belge), sonra **kullanıcı onayı**, sonra uygulama.
> Aşağıdaki Bölüm 1 ve 2 tamamlanmıştır. **Bölüm 3'te durulmuştur** — Anayasa Prensip I gereği.

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

## 3. 🚦 ONAY BEKLİYOR

Yukarıdaki tavsiye (**SOPS + age**) uygulanmadan önce onayın gerekiyor (Anayasa Prensip I — onay kapısı, pazarlıksız).

Onaylarsan Bölüm 4'te şunlar yapılacak:
- `sops` + `age` kurulumu (winget/scoop).
- Kök `.sops.yaml` konfigürasyonu.
- `age` anahtar çifti üretimi + özel anahtarın **git dışı** saklanma talimatı (Faz 0.5 ile bağlı).
- Örnek şifreli `secrets.enc.yaml` iskeleti (henüz gerçek sır yok, ama biçim hazır olur).
- Yerel + Railway + k8s için çözme (decrypt) komutlarının `scripts/` altına yazılması.
- CI kapısı zaten var ([.github/workflows/secrets-scan.yml](../.github/workflows/secrets-scan.yml), Faz 0.2'den).

**Onaylamazsan veya farklı bir seçenek istersen** (platform-native veya harici kasa), söyle — Bölüm 2'deki tabloyu senin tercihine göre uygularım.

---

## 4. Uygulama

*Bölüm 3'teki onay alınmadan bu bölüm doldurulmaz.*
