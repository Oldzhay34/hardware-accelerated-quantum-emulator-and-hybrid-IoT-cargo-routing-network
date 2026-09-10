# Faz Sonu Kontrol Listesi

**Kaynak**: Faz 0 alt dal 0.7 · **Oluşturma**: 2026-09-10

Haftalık ritüelden ([schedule.md §4](../specs/000-kapsam-takvim/schedule.md)) farklı: bu liste **bir fazın/alt dalın işi bittiğinde**, o iş commit edilmeden hemen önce çalıştırılır. Amaç, kalıcı hafıza dosyalarının fazla iş bittikten sonra "sonra yaparım" denip hiç güncellenmemesini önlemek.

- [ ] Bu fazda verilen kararlar [docs/decisions/](decisions/) altına ADR olarak yazıldı mı? (`ADR-TEMPLATE.md` kullan)
- [ ] Denenip elenen bir yol varsa [docs/decisions/dead-ends.md](decisions/dead-ends.md)'e düştü mü?
- [ ] [CLAUDE.md](../CLAUDE.md) başındaki **"Şu anki faz"** satırı güncellendi mi?
- [ ] İlgili `specs/<faz>/tasks.md` başındaki **SIRADAKİ** bloğu güncellendi mi? (bkz. [docs/siradaki-standardi.md](siradaki-standardi.md))
- [ ] Yeni bir ölçüm üretildiyse [docs/measurements/](measurements/) altına damgalı (tarih+git hash+konfig) yazıldı mı?
- [ ] Commit mesajı faz referansı taşıyor mu (`tip(fazN): özet`)?
- [ ] Bu faz [scope-triage.md](../specs/000-kapsam-takvim/scope-triage.md)'deki etiketiyle (M/H/İ) tutarlı iş yaptı mı — yoksa kapsam sürünmesi mi oldu (bkz. risk TK-03)?

Bu liste her fazın sonunda 2 dakikadan uzun sürmemeli; uzuyorsa fazın kapsamı çok büyük demektir.
