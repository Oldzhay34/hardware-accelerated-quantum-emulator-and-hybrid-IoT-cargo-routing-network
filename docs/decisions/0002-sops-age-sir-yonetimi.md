# ADR 0002 — Sır yönetimi: SOPS + age

**Tarih**: 2026-09-10 · **Faz**: 0.3 · **Durum**: Kabul edildi

## Bağlam

Proje ilerledikçe veritabanı parolası, JWT imza anahtarı, MQTT cihaz parolaları, Railway/Cloudflare
token'ları ve PYNQ SSH kimlik bilgisi doğacak. Dağıtım hedefleri iki farklı platform: Railway ve
(muhtemelen) k8s. Sırların nerede saklanacağı, servis kodu yazılmadan **önce** kararlaştırılmalı —
sonradan taşımak, sızmış sır ve rotasyon maliyeti demek.

Faz 0.3 taraması depoda hâlâ sır olmadığını gösterdi, bu yüzden karar bugün sıfır maliyetle verilebilir.

## Seçenekler

1. **Platform-native** (Railway env değişkenleri + k8s Secret) — ek araç yok, ama iki ayrı arayüzde elle senkron gerekir ve **k8s Secret varsayılan olarak base64'tür, şifreli değildir**.
2. **Harici kasa** (Vault / Infisical / Doppler) — merkezi, rotasyon desteği iyi; ama yeni bir servis/hesap ve [cost.md](../cost.md)'a yeni bir izlenecek kalem.
3. **SOPS + age** — sırlar git'te şifreli dosya olarak, tek doğruluk kaynağı.

## Karar

**SOPS + age.**

## Gerekçe

- **Yeni hesap/servis yok** — 14 hafta kısıtı (Prensip VI) altında her yeni bağımlılık bir yüktür.
- **Git iş akışıyla aynı yerde** — sır değişikliği bir commit'tir, PR şablonundaki denetim kutuları doğrudan uygular.
- **k8s Secret'ın "şifreli değil" tuzağını otomatik çözer** — SOPS dosyası zaten şifreli olduğu için etcd şifrelemesini açmayı unutma riski ortadan kalkar.
- **Yerel geliştirme deneyimi iyi** — `secrets.ps1 env` ile tek komutta `.env` üretilir, Railway/k8s'e ihtiyaç duymadan.

## Sonuç

- Kökte `.sops.yaml` ve `secrets.enc.yaml` (şifreli, commit edilir).
- `scripts/secrets.ps1` — `edit` / `env` / `check`.
- age özel anahtarı `%APPDATA%\sops\age\keys.txt`, repoda değil, dosya izni kısıtlı.
- **Faz 0.5'e bağlayıcı devir**: özel anahtar "yeniden üretilemez" yedekleme envanterine girecek.
- Faz 5'te PYNQ (Linux) tarafı için `secrets.ps1`'in bash karşılığı yazılacak.

Ayrıntı: [docs/secrets-audit.md](../secrets-audit.md).

## Tekrar değerlendirilmeli mi?

Evet, şu koşulda: Railway + k8s dışına üçüncü bir dağıtım hedefi eklenirse veya projeye ikinci bir
geliştirici katılırsa (o zaman anahtar paylaşımı sorunu doğar ve harici kasa avantajlı hale gelir).
