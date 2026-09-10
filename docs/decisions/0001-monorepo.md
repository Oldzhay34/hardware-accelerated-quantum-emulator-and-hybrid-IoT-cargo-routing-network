# ADR 0001 — Tek depo (monorepo)

**Tarih**: 2026-09-10 · **Faz**: 0.2 · **Durum**: Kabul edildi

## Bağlam

15 faz, 67 alt dal içeren bir bitirme projesi tek geliştirici tarafından yürütülecek. Fazlar arası
sürekli veri akışı var (Faz 1 → 2 → 5 → 10 gibi). Depo yapısı kararı sonraki tüm fazların yazacağı
zemini belirliyor.

## Seçenekler

1. **Monorepo** — tüm bileşenler tek git deposunda.
2. **Çoklu depo** — her bileşen (firmware, hls, services, web, agent) kendi deposunda, submodule veya paket olarak bağlanır.

## Karar

**Monorepo.**

## Gerekçe

- Tek geliştirici için çoklu depo senkronizasyon yükü katma değersiz.
- Fazlar arası çapraz referans yoğun (bkz. [schedule.md](../../specs/000-kapsam-takvim/schedule.md) bağımlılık grafiği).
- spec-kit'in `specs/00X-.../` yapısı zaten tek depo kökü varsayıyor.
- Tek CI, tek sır tarayıcı, tek risk kaydı — denetim yüzeyi dağılmıyor.

## Sonuç

[docs/repo-conventions.md](../repo-conventions.md) §1'de detaylandırıldı. Firmware'in ayrı derleme
zincirine (PlatformIO/ESP-IDF) sahip olması bu kararı değiştirmiyor — donanımsız CI (Faz 11.5) izolasyonu
zaten sağlıyor.

## Tekrar değerlendirilmeli mi?

Yalnızca ikinci bir geliştirici katılırsa veya bir bileşen bağımsız bir açık kaynak proje olarak
ayrılmak isterse.
