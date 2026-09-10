# qir-engine

Kuantum-esinli rota optimizasyonu için statevector emülasyon çekirdeğini PYNQ-Z2 üzerinde HLS ile
donanımda hızlandıran, Qiskit altın referansına karşı doğrulayan ve CPU'ya karşı gecikme/enerji
ekseninde gerçek ölçümle kıyaslayan bir bitirme projesi.

**Şu anki faz**: Faz 0 — Kapsam Triyajı (alt dal 0.7 çalışıyor). Bkz. [specs/000-kapsam-takvim/](specs/000-kapsam-takvim/).

## Anayasa — altı ilke (tam metin: [.specify/memory/constitution.md](.specify/memory/constitution.md))

1. **Onay kapısı**: karşılaştırma raporu + açık onay olmadan hiçbir teknoloji/mimari karar kodlanmaz.
2. **Ölçüm dürüstlüğü**: enerji/gecikme gerçek ölçüme dayanır; tahmini değer rapora yazılmaz.
3. **Donanım bütçesi önce**: statevector çip-içi bellekte kalmalı (BRAM/URAM), DDR'a taşamaz. Üst sınır 16 kübit.
4. **Altın referans**: her hızlandırıcı çıktısı Qiskit'e karşı doğrulanmadan "çalışıyor" sayılmaz.
5. **Donanımsız süreklilik**: kart yokken de C-sim/cosim/mock ile geliştirme sürer; donanım erişimi derleme koşulu değil.
6. **14 hafta kısıtı**: her öneri kalan takvime karşı değerlendirilir; kapsam M/H/İ etiketlenir.

## Kırmızı çizgiler

- Onaysız migration yok.
- Sır düz metin olarak repoya **asla** girmez. Tek kaynak: `secrets.enc.yaml` (SOPS+age ile şifreli, commit edilir). Düzenleme: `.\scripts\secrets.ps1 edit`. Ayrıntı: [docs/secrets-audit.md](docs/secrets-audit.md).
- Türkçe locale tuzağı: string büyütmede `ToUpper()` değil **`ToUpperInvariant()`** kullan (`i` → `İ` geçersiz tanımlayıcı üretir).
- Ölçüm rakamı (fidelity, II, BRAM %, gecikme, enerji) elle sabitlenmez — [docs/measurements/](docs/measurements/) altına damgalı (tarih+git hash+konfig) yazılır.
- Domain kodunda çerçeve anotasyonu yok (hexagonal — bkz. aşağı).

## Hexagonal paket iskeleti (servisler için — Faz 3.1'de kesinleşecek)

```
domain/          saf iş mantığı, dış bağımlılık YOK
application/      use-case'ler, domain'i çağırır
adapters/
  in/              HTTP/MQTT/CLI giriş noktaları — application'ı çağırır
  out/             DB/HTTP/queue çıkış adaptörleri — application'ın tanımladığı port'u uygular
```

**Bağımlılık yönü**: `adapters → application → domain`. Ok her zaman içe doğru; `domain` hiçbir şeyi import etmez.

## Depo haritası

| Dizin | İçerik | Detay |
|---|---|---|
| `specs/00X-.../` | spec.md, plan.md, tasks.md — her fazın kalıcı hafızası | |
| `services/`, `firmware/`, `hls/`, `agent/`, `web/` | uygulama kodu | [docs/repo-conventions.md](docs/repo-conventions.md) §2 |
| `infra/` | docker/k8s/railway | |
| `docs/` | risk kaydı, kararlar, tez, ölçümler | [docs/README.md](docs/README.md) |
| `artifacts/` | bitstream/overlay/model — **git'e girmez** | |

## Sık kullanılan komutlar

```bash
# Python (Qiskit altın referans, ölçüm analizi)
.venv\Scripts\activate

# C derleyici doğrulama (HLS C-sim öncesi)
gcc --version

# spec-kit şablon çözümleme
.specify\scripts\powershell\resolve-template.ps1 <template-name> -Json
```

Derleme/sentez/test komutları ilgili faz kurulduğunda buraya eklenecek (şu an `hls/`, `services/` boş).

## Kalıcı hafıza dosyaları

- [docs/decisions/](docs/decisions/) — kesinleşmiş kararlar, ADR biçiminde. Şablon: `ADR-TEMPLATE.md`.
- [docs/decisions/dead-ends.md](docs/decisions/dead-ends.md) — denenip elenen yollar. Boş kalıyorsa yanlış kullanılıyordur.
- Her `specs/<faz>/tasks.md` bir **SIRADAKİ** bloğuyla başlar — standart: [docs/siradaki-standardi.md](docs/siradaki-standardi.md).
- Faz bitince: [docs/faz-sonu-kontrol.md](docs/faz-sonu-kontrol.md) — kararlar ADR'ye yazıldı mı, SIRADAKİ güncellendi mi.

Bu dosya bir arşiv değil, hatırlatmadır. Ayrıntı `docs/` altına gider; burası 100 satırı geçmez.
