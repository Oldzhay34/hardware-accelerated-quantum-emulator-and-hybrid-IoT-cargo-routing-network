# ADR 0003 — Yedekleme hedefleri: OneDrive + D: (uzak git remote yok)

**Tarih**: 2026-09-10 · **Faz**: 0.5 · **Durum**: Kabul edildi — **kısmi**, bkz. Tekrar değerlendirilmeli mi?

## Bağlam

3-2-1 kuralı en az iki farklı yerde, biri fiziksel olarak ayrı yedek istiyor. Depoda şu an uzak git
remote yok (`git remote -v` boş). En doğal çözüm bir GitHub deposu olurdu, ama bu kullanıcının
GitHub hesabına bağlanmayı gerektiriyor — otonom olarak alınabilecek bir karar değil.

## Seçenekler

1. **Uzak git remote (GitHub)** — en sağlam, ama hesap/kimlik doğrulama gerektiriyor.
2. **Yalnızca yerel (D: sürücüsü)** — fiziksel olarak ayrı değil (aynı makine), laptop kaybında işe yaramaz.
3. **OneDrive (bulut) + D: (ikinci disk)** — bugün otonom olarak kurulabilir, kısmi koruma sağlar.

## Karar

**Bugün için: OneDrive + D:.** Uzak git remote sorusu kullanıcıya soruldu, cevap bekleniyor.

## Gerekçe

- OneDrive gerçekten fiziksel olarak ayrı (bulut) — laptop kaybında hayatta kalır.
- D: aynı makinede ama farklı fiziksel disk — "C: diski bozuldu" senaryosunda işe yarar, "laptop çalındı" senaryosunda yaramaz (bkz. risk `BK-00`).
- `scripts/backup.ps1` her çalıştığında kendi kendini doğruluyor (gerçek geri yükleme provası, bkz. [docs/backup.md §4](../backup.md#4-geri-yükleme-provası--yapıldı-atlanamaz-adım)).

## Sonuç

- [scripts/backup.ps1](../../scripts/backup.ps1) — git bundle oluşturur, iki hedefe kopyalar, geri yükleyip doğrular.
- İlk prova 2026-09-10'da geçti: 0.25 saniyede 7 commit, HEAD eşleşti.
- Risk kaydına `BK-00`..`BK-04` eklendi ([docs/risk-register.md](../risk-register.md) §8b).

## Tekrar değerlendirilmeli mi?

**Evet — açık bir eksik.** BK-00 riski `AÇIK` ve "kullanıcı kararı bekliyor" durumunda. Kullanıcı bir
GitHub (veya başka uzak git) deposu eklemeyi onaylarsa bu ADR revize edilir ve BK-00 kapatılır. O ana
kadar OneDrive+D: **tek koruma**dır ve laptop kaybı senaryosunda tam koruma sağlamaz.
