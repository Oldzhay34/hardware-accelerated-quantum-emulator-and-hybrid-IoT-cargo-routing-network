# qir-engine

Kuantum-esinli rota optimizasyonu için statevector emülasyon çekirdeğini PYNQ-Z2 üzerinde HLS ile
donanımda hızlandıran, Qiskit altın referansına karşı doğrulayan ve CPU'ya karşı gecikme/enerji
ekseninde gerçek ölçümle kıyaslayan bir bitirme projesi.

**Şu anki faz**: Faz 2 — plan onaylandı (A1+B4+C1, [ADR 0008](docs/decisions/0008-statevector-cekirdek-mimarisi.md)). Çekirdek yazıldı, C-sim ile doğrulandı (fidelity ≥0,99997, n=8/12/16), **n=16 cosim geçti** (19 Eyl, çıkış portu C ile bit bit aynı: `0xbee28271` — ama 65536 genliğin tek tek eşitliği değil, bkz. [§20](docs/measurements/faz2-sentez.md)) ve **sentezlendi**: 7,195 ns (100 MHz), BRAM %66, DSP %16, FF %46, **LUT %84**, gecikme **p=2 için 3.728.217 çevrim = 37,3 ms**. **Vivado implementasyonu koşuldu**: LUT gerçekte **22.535 (%42)**, FF **19.466 (%18)**, DSP 33 (%15), BRAM 187 (%67), post-route **9,122 ns** — yani HLS tahmini LUT'u **2× fazla** saymış. SC-002/SC-003 geçti, NC-4 kapandı. CPU tabanı **yeniden ölçüldü** (19 Eyl, temiz): turbo **32,75 ms**, plato **41,93 ms**. FPGA'nın p=2 tahmini (37,28 ms) tam ikisinin arasına düşüyor — **gecikmede başabaş, kazanç yok**. Eski 77,6/92,7 ms rakamları arka planda cosim koşarken alınmıştı, **geçersiz** ([§18](docs/measurements/faz2-sentez.md)). CPU enerjisi ölçüldü: **0,644 J/koşum**; FPGA tarafı henüz ölçülmedi. Vitis 2025.2 **WSL/Ubuntu altında kurulu ve çalışıyor** — Windows'ta Device Guard engellemişti ([SK-05](docs/risk-register.md)), taşınmanın ölçümü bozmadığı Tur 15 yeniden üretilerek kanıtlandı. Kurulum ve sentez komutları: [runbook](docs/runbooks/vitis-hls-kurulum.md). Paralellik arama turu **ölçümle kapandı** ([ADR 0009](docs/decisions/0009-paralellik-turu-kapatildi.md)): satın alınabilir paralellik kalmadı, tek kazanç `RAM_T2P` port düzeltmesiydi; II tabanı bankalama değil **bellek portu** çıktı. Altı sentez riski de kapandı ([risk-register.md](docs/risk-register.md)). **Faz 2 KAPANDI** (54/54 görev). **Şu an Faz 5** — durum ve sıradaki iş: [specs/003-zynq-ps-kartta-kosum/SIRADAKI.md](specs/003-zynq-ps-kartta-kosum/SIRADAKI.md).

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

```bash
# C-sim doğrulaması — Vitis ve kart GEREKMEZ (Prensip V)
wsl -d Ubuntu -e bash hls/build_and_run.sh

# Sentez / implementasyon / cosim (Vitis, WSL)
wsl -d Ubuntu -e bash hls/run.sh csynth
wsl -d Ubuntu -e bash hls/run.sh impl
QIR_N=8 wsl -d Ubuntu -e bash hls/run.sh cosim

# Fidelity regresyon kapısı (CI'ın koştuğu kontrol)
python scripts/ci_fidelity_gate.py "docs/measurements/csim-fidelity_*.json"
```

**Donanımsız CI** (`.github/workflows/csim-regression.yml`, kapsam **M**): her push'ta C-sim'i n=8/12/16 için koşar ve fidelity'yi [baseline-fidelity.json](docs/measurements/baseline-fidelity.json)'a karşı denetler. ⚠️ Testbench yalnızca **M eşiğinde** (0,99) başarısız olur; asıl regresyon kapısı `ci_fidelity_gate.py`'dir (tolerans 1e-7).

**Tez/makale yazarken tek referans**: [docs/olculen-degerler.md](docs/olculen-degerler.md) — bütün ölçülen değerler, deney koşulları, ne iddia edilebilir/edilemez, ve yanlışlanan hipotezler.

## Kalıcı hafıza dosyaları

- [docs/decisions/](docs/decisions/) — kesinleşmiş kararlar, ADR biçiminde. Şablon: `ADR-TEMPLATE.md`.
- [docs/decisions/dead-ends.md](docs/decisions/dead-ends.md) — denenip elenen yollar. Boş kalıyorsa yanlış kullanılıyordur.
- Her `specs/<faz>/tasks.md` bir **SIRADAKİ** bloğuyla başlar — standart: [docs/siradaki-standardi.md](docs/siradaki-standardi.md).
- Faz bitince: [docs/faz-sonu-kontrol.md](docs/faz-sonu-kontrol.md) — kararlar ADR'ye yazıldı mı, SIRADAKİ güncellendi mi.

Bu dosya bir arşiv değil, hatırlatmadır. Ayrıntı `docs/` altına gider; burası 100 satırı geçmez.

