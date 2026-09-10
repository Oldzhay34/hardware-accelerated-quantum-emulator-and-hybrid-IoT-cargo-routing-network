# Depo Kuralları

**Kaynak**: Faz 0 alt dal 0.2 · **Oluşturma**: 2026-09-10

Bu belge, sonraki 14 fazın yazacağı iskeletin kurallarını taşır. Yanlış kurulursa her fazda yeniden düzenleme maliyeti çıkar — bu yüzden burada karar gerekçeli yazılıdır, sadece kural değil.

---

## 1. Monorepo mu, çoklu depo mu — KARAR: Monorepo

**Karar: tek depo (monorepo).**

Gerekçe:

- **Tek geliştirici.** Çoklu depo, bağımlılık senkronizasyonu (submodule/paket sürümü) yönetimi getirir; bu, tek kişi için katma değersiz bir yük çıkarır.
- **Fazlar arası sürekli çapraz referans var.** Faz 1'in QUBO çıktısı Faz 2'nin girdisi, Faz 2'nin sentez raporu Faz 5'in agent'ına, Faz 4'ün enerji verisi Faz 10'un kıyasına giriyor ([schedule.md](../specs/000-kapsam-takvim/schedule.md) bağımlılık grafiği). Bunlar ayrı depolarda olsaydı her entegrasyon bir sürüm eşleştirme sorunu olurdu.
- **spec-kit zaten monorepo varsayıyor.** `specs/00X-.../` yapısı tek depo kökünde yaşıyor; çoklu depo bu yapıyı ya kırar ya da tekrarlar.
- **Tek CI, tek sır tarayıcı, tek risk kaydı.** Denetim yüzeyi tek yerde kalır (0.1, 0.3, 0.5, 0.6 hepsi tek depoya yazıyor).

**Karşı senaryo nerede düşünülmeli**: Firmware (`firmware/`) tamamen bağımsız bir derleme zinciri (PlatformIO/ESP-IDF) kullanacağı için "ayrı depo mu olmalı" sorusu akla gelebilir. Karar: hayır — firmware küçük, nadiren değişiyor, ve ayrı depo tek kazandığı şeyi (bağımsız CI hızı) Faz 11.5'in donanımsız CI'sı zaten karşılıyor.

---

## 2. Dizin düzeni

```
qir-engine/
├── specs/              spec-kit fazları: spec.md, plan.md, tasks.md (her faz kendi 00X-.../ altında)
├── services/           L2 mikroservisleri (Faz 3, 6, 8)
├── firmware/            ESP32 (Faz 4)
├── hls/                 Vitis HLS kaynakları, C-sim, Tcl akışı (Faz 2)
├── agent/                PYNQ fpga-agent (Faz 5)
├── web/                 React arayüzü (Faz 6, 8, 9, 10.2)
├── infra/               docker/, k8s/, railway/ (dağıtım tanımları)
├── scripts/             Tek satırlık yardımcı betikler
├── docs/                thesis/, figures/, measurements/, runbooks/, decisions/ + Faz 0 çıktı dosyaları
├── artifacts/            bitstream/, overlay/, models/ — GİT'E COMMIT EDİLMEZ
├── .specify/             spec-kit motoru (specify-cli tarafından yönetilir)
├── .claude/              Claude Code skill/config (git'e girmez)
└── .github/               PR şablonu, CI iş akışları
```

Her dizinin kendi `README.md`'si vardır — o dizine ilk kez yazacak fazın önce okuması beklenir.

---

## 3. Büyük ikili dosyalar — KARAR: harici depo, LFS değil

**Karar: bitstream/overlay/video gibi büyük ikili dosyalar git'e hiç girmez; `artifacts/` `.gitignore`'dadır.**

Gerekçe: Git LFS, GitHub'ın ücretsiz katmanında (1 GB depolama + 1 GB/ay bant genişliği) bu proje ölçeğinde hızla dolar ve tek geliştirici için ekstra bir araç zinciri (`git lfs install`, sürüm takibi) getirir. Alternatif: büyük dosyalar [docs/backup.md](backup.md) (Faz 0.5) içinde tanımlanacak harici depoda (harici disk + bulut) tutulur; depoda yalnızca bu dosyaların **üretildiği komut** ve **SHA-256 özeti** bulunur.

Bu karar [cost.md](cost.md) (Faz 0.6) ile ve [backup.md](backup.md) (Faz 0.5) ile hizalıdır — orada yeniden açılmaz, buraya referans verilir.

---

## 4. Commit mesajı biçimi

```
<tip>(faz<N>): <kısa özet, emir kipi, Türkçe veya İngilizce tutarlı>

[opsiyonel gövde — neden, ne değişti]

[opsiyonel: Kesme tetiği: K-XX etkilendi / Ölçüm değişti: <hangi>]
```

**Tipler**: `feat` (yeni yetenek) · `fix` (hata düzeltme) · `docs` (belge) · `refactor` · `test` · `chore` (araç/konfig).

**Faz referansı zorunlu** — `feat(faz3): karar motoru servis iskeletini ekle` gibi. Faz 0 alt dalları için `faz0.X` kullanılır: `docs(faz0.1): risk kaydını güncelle`.

Örnek (bu commit'in kendisi):
```
docs(faz0.2): depo iskeletini kur
```

---

## 5. Dal stratejisi

**Karar: faz bazlı kısa ömürlü dallar, tek geliştirici için hafif model.**

- `master` her zaman **koşan** durumdadır (donanımsız CI yeşil).
- Her faz/alt dal için `faz<N>-<kisa-ad>` dalı açılır (örn. `faz1-altin-referans`), iş bitince `master`'a **fast-forward veya squash merge** ile birleşir.
- Kritik yoldaki fazlar (0, 1, 2, 10, 12 — bkz. [scope-triage.md](../specs/000-kapsam-takvim/scope-triage.md)) için dal ömrü kısa tutulur (birkaç gün); İ etiketli işler için dal ömrü önemsizdir çünkü zaten taban planda değildir.
- Uzaktan depo (GitHub) eklendiğinde bu strateji değişmez; PR şablonu (§6) o an devreye girer.

**Şu an durum**: Uzak depo yok (`git remote -v` boş), tek dal `master`. Bu bölüm uzak depo eklendiğinde geçerli olacak biçimde yazılmıştır.

---

## 6. PR şablonu

[.github/PULL_REQUEST_TEMPLATE.md](../.github/PULL_REQUEST_TEMPLATE.md) dosyasına kondu. Kapsamı: hangi faz/alt dal, hangi kesme tetiği etkilendi, hangi ölçüm değişti, onay kapısı gerekiyor mu.

---

## 7. Sır yönetimi — SOPS + age

**Karar Faz 0.3'te verildi ve onaylandı** (2026-09-10). Tam gerekçe ve karşılaştırma: [docs/secrets-audit.md](secrets-audit.md).

- **Tek doğruluk kaynağı**: [`secrets.enc.yaml`](../secrets.enc.yaml) — SOPS+age ile şifreli, **git'e commit edilir**. Şifreli olduğu için güvenlidir; YAML anahtar adları düz kaldığından `git diff` "hangi değişken değişti"yi gösterir, değeri sızdırmadan.
- **age özel anahtarı repoda DEĞİL**: `%APPDATA%\sops\age\keys.txt`. Kaybolursa sırlar kurtarılamaz — Faz 0.5 yedekleme envanterine dahildir.
- **Komutlar**: `.\scripts\secrets.ps1 edit | env | check`
- Her servis/bileşen ayrıca **kendi** `.env.example` dosyasını taşır (gerçek değer yok, her değişkenin açıklaması var) — servis kodu doğduğunda, Faz 3'ten itibaren.
- Kök `.gitignore` tüm `.env` dosyalarını (örnek hariç), sertifika/anahtar uzantılarını (`.pem`, `.p12`, `.jks`) ve age anahtar desenlerini hariç tutar.
- CI'da sır tarayıcı kapısı: [.github/workflows/secrets-scan.yml](../.github/workflows/secrets-scan.yml) — yerelde kullanılan gitleaks ile aynı araç. Uzak depo bağlanınca devreye girer; yerel karşılığı `secrets.ps1 check`.

---

## 8. .editorconfig ve dil karışıklığı

Proje üç dil barındırıyor: Python (venv, Qiskit), C/C++ (HLS), muhtemelen TypeScript/Java (web/services — Faz 3.1'de kesinleşecek). [.editorconfig](../.editorconfig) bu üçü için ortak girinti/satır sonu kuralını sabitler; dil bazlı linter kararları ilgili fazda verilir.

---

## 9. README (kök)

Kök [README.md](../README.md), projenin bir paragraflık tanımını, mimari şemasını, hangi fazın nerede olduğunu ve tek komutla yerel ayağa kaldırmayı taşır. Bu dosya her fazın sonunda güncellenmelidir — özellikle "tek komutla ayağa kaldırma" kısmı, `infra/docker/docker-compose.yml` hazır olana kadar dürüstçe "henüz yok" der.
