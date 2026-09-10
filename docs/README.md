# docs/

| Alt dizin | İçerik | Hangi fazda büyür |
|---|---|---|
| `decisions/` | ADR'ler (kesinleşmiş kararlar) + `dead-ends.md` (elenen yollar) | 0.7, sürekli |
| `thesis/` | Tez metni, bölüm bölüm | 12.2 |
| `figures/` | Ölçüm şekilleri, sentez raporu grafikleri | 12.1, sürekli birikir |
| `measurements/` | Ham ölçüm verisi (gecikme, enerji, fidelity) — damgalı (tarih + git hash + konfig) | Faz 1, 2, 4, 5, 10 |
| `runbooks/` | Operasyonel prosedürler (geri yükleme, felaket provası, demo kurulumu) | 0.5, 12.4 |

Kök seviyedeki dosyalar (`risk-register.md`, `repo-conventions.md`, `cost.md`, `secrets-audit.md`, `data-governance.md`, `backup.md`, `siradaki-standardi.md`, `faz-sonu-kontrol.md`) Faz 0 alt dallarının çıktılarıdır ve tek dosya olarak kalır.
