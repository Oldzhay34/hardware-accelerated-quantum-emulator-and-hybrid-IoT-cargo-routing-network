# ADR 0003 — Yedekleme hedefleri: OneDrive + G: (harici SSD), uzak git remote yok

**Tarih**: 2026-09-10 · **Faz**: 0.5 · **Durum**: Kabul edildi (kullanıcı onayladı, 2026-09-10)

## Bağlam

3-2-1 kuralı en az iki farklı yerde, biri fiziksel olarak ayrı yedek istiyor. Depoda şu an uzak git
remote yok (`git remote -v` boş). En doğal çözüm bir GitHub deposu olurdu, ama bu kullanıcının
GitHub hesabına bağlanmayı gerektiriyor — otonom olarak alınabilecek bir karar değil.

## Seçenekler

1. **Uzak git remote (GitHub)** — en sağlam, ama hesap/kimlik doğrulama gerektiriyor.
2. **Yalnızca yerel disk** — fiziksel olarak ayrı değil (aynı makine), laptop kaybında işe yaramaz.
3. **OneDrive (bulut) + harici SSD** — bugün otonom olarak kurulabilir, gerçek fiziksel ayrılık sağlar.

## Karar

**OneDrive + G: (harici SSD).** Kullanıcıya uzak git remote sorusu soruldu; kullanıcı kendi harici
SSD'sini bağlayıp bunu kalıcı ikinci hedef olarak belirledi. Uzak git remote **ertelendi**, GitHub
hesabı gerektirdiği için otonom kurulamadı.

## Gerekçe

- OneDrive gerçekten fiziksel olarak ayrı (bulut) — laptop kaybında hayatta kalır.
- G: harici bir SSD — takılı değilken laptopla birlikte kaybolmuyor (D: sürücüsünün aksine, ilk
  taslakta önerilen D: aynı makinede sabit disktir ve laptop kaybında işe yaramazdı).
- Tek zayıf nokta: SSD, yedek alınacağı an (Cuma 18:00, otomatik) **takılı olmayabilir** — bu durumda
  o haftanın ikinci kopyası eksik kalır, ama OneDrive yine de bir kopya sağlar.
- `scripts/backup.ps1` her çalıştığında kendi kendini doğruluyor (gerçek geri yükleme provası, bkz. [docs/backup.md §4](../backup.md#4-geri-yükleme-provası--yapıldı-atlanamaz-adım)) ve script artık bir hedef erişilemezse (SSD takılı değilse) hata vermeden diğerine yazıp devam ediyor.

## Sonuç

- [scripts/backup.ps1](../../scripts/backup.ps1) — git bundle oluşturur, erişilebilir hedeflere kopyalar, geri yükleyip doğrular. SSD takılı değilse uyarır ve atlar, başarısız olmaz.
- İki prova geçti (2026-09-10): önce D:'ye (95.6 KB, 7 commit), sonra G:'ye geçildikten sonra (106.8 KB, 9 commit) — ikisinde de 0.2-0.3 saniyede geri yükleme ve HEAD eşleşmesi doğrulandı.
- Risk kaydına `BK-00`..`BK-04` eklendi ([docs/risk-register.md](../risk-register.md) §8b).
- Windows Görev Zamanlayıcı'ya `qir-engine-backup` görevi kaydedildi: her Cuma 18:00, batarya kısıtı olmadan, kaçırılan çalıştırma bilgisayar açılınca telafi ediliyor (`StartWhenAvailable`).

## Tekrar değerlendirilmeli mi?

Evet, şu koşulda: SSD birkaç hafta üst üste takılı unutulursa (haftalık ritüelde fark edilir, bkz.
[risk-register.md BK-00](../risk-register.md)) veya kullanıcı bir GitHub hesabı eklemeye karar
verirse. O zaman bu ADR revize edilir ve uzak git remote üçüncü, en güçlü kat olarak eklenir.
