# docs/

| Alt dizin | İçerik | Hangi fazda büyür |
|---|---|---|
| **`olculen-degerler.md`** | **tez/makale için tek referans** — bütün ölçülen değerler, deney koşulları, iddia sınırları | Faz 2+ |
| `measurements/baseline-fidelity.json` | CI regresyon kapısının referans değerleri — elle değil ölçümle güncellenir | 11.5 |
| `decisions/` | ADR'ler (kesinleşmiş kararlar) + `dead-ends.md` (elenen yollar) | 0.7, sürekli |
| `thesis/` | Tez metni, bölüm bölüm | 12.2 |
| `figures/` | Ölçüm şekilleri, sentez raporu grafikleri | 12.1, sürekli birikir |
| `measurements/` | Ham ölçüm verisi (gecikme, enerji, fidelity) — damgalı (tarih + git hash + konfig) | Faz 1, 2, 4, 5, 10 |
| `runbooks/` | Operasyonel prosedürler (geri yükleme, felaket provası, demo kurulumu) | 0.5, 12.4 |

Kök seviyedeki dosyalar (`risk-register.md`, `repo-conventions.md`, `cost.md`, `secrets-audit.md`, `data-governance.md`, `backup.md`, `siradaki-standardi.md`, `faz-sonu-kontrol.md`) Faz 0 alt dallarının çıktılarıdır ve tek dosya olarak kalır.
- [neden-fpga.md](neden-fpga.md) — *"GPU varken neden FPGA?"* savunması; kullanılacak ve **kullanılmayacak** argümanlar
- [sistem-mimarisi.md](sistem-mimarisi.md) — uçtan uca mimari, iki çalışma kipi, kapasite ve gerçek sınır (alt problem başına 4 durak)
- [mimari-gerekce.md](mimari-gerekce.md) — hızlandırıcı seçiminin derin teknik gerekçesi; her iddia [Ö]/[T]/[?] etiketli
- [hizlandirici-kiyas-gunlugu.md](hizlandirici-kiyas-gunlugu.md) — 21 Eylül kıyas turunun **akışı**: soru zinciri, üç taban/üç cevap, düşen varsayımlar
