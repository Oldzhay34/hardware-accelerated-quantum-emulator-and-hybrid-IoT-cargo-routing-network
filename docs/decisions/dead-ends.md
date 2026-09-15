# Elenen Yollar (Dead Ends)

**Kaynak**: Faz 0 alt dal 0.7 · **Oluşturma**: 2026-09-10

Bu dosya **sıkıştırmada en çok kaybedilen bilgiyi** tutar: denenip işe yaramayan yollar. Bağlam
sıkıştığında "bunu zaten denedim, olmadı" bilgisi ilk kaybolan şeydir — burada yaşar.

**Boş kalıyorsa yanlış kullanılıyordur.** Her başarısız deneme (bir sentez stratejisi, bir kütüphane,
bir mimari yaklaşım) buraya bir satır olarak düşmeli — "bir dahaki sefere neden aynı şeyi tekrar
denemeyeceğim" sorusuna cevap olacak şekilde.

## Biçim

```
### <Ne denendi> — <tarih>, Faz <N.M>

**Neden denendi**: <motivasyon>
**Neden olmadı**: <somut başarısızlık nedeni, ölçülebilirse ölçüm>
**Tekrar denenmeli mi**: Evet, şu koşulda: <...> / Hayır, çünkü <...>
```

---

### GraphHopper (açık kaynak) matris motoru olarak — 2026-09-13, Faz 1

**Neden denendi**: OSRM/Valhalla ile birlikte üç aday rotalama motorundan biriydi; Docker imajı çekilip
gerçekten koşuldu (`israelhikingmap/graphhopper`, resmî imaj yok).

**Neden olmadı**: Açık kaynak GraphHopper'ın `/matrix` ucu **yok** — ampirik olarak doğrulandı:
`/route` → 200, `/matrix` → **404**. Matrix API, GraphHopper'ın ticari/lisanslı sürümünün özelliği.
N=30 durak için 900 ayrı `/route` çağrısı gerekirdi; spec FR-001'i makul maliyetle karşılayamaz.

**Tekrar denenmeli mi**: Hayır, çünkü OSRM (BSD-2, resmî imaj, ölçülen matris gecikmesi 0,383 sn
medyan) her ölçülen eksende üstün çıktı. Yalnızca GraphHopper'ın ticari Matrix API lisansı alınırsa
yeniden gündeme gelebilir — taban planda yok. Bkz. [ADR 0006](0006-osrm-ve-qiskit-aer.md).

### Valhalla kurulumu — sırasız komutlar — 2026-09-13, Faz 1

**Neden denendi**: `valhalla_build_tiles`'ı doğrudan `valhalla_build_config` çıktısıyla çalıştırmak.

**Neden olmadı**: `admin.sqlite` ve `tz_world.sqlite` önceden üretilmemişti (`valhalla_build_admins`,
`valhalla_build_timezones` atlanmıştı). Sonuç anlaşılır bir hata değil, **segmentation fault**
oldu (graf kurulumu 17 saniyede başarıyla bitmiş, "Enhancing local graph" aşamasında çökmüştü).

**Tekrar denenmeli mi**: Evet — doğru sıra biliniyor artık: `config → timezones → admins → tiles`.
Bu proje Valhalla'yı seçmedi (bkz. ADR 0006) ama sıra bilgisi genel olarak değerli.

### Rastgele parametreli QAOA (optimizasyonsuz) — 2026-09-13, Faz 1

**Neden denendi**: İlk sürüm, tohumlu rastgele parametrelerle QAOA devresini bir kez koşuyordu —
"altın referans" için yeterli görünmüştü çünkü tam statevector taraması `best_tour`'u zaten doğru
buluyordu.

**Neden olmadı**: "QAOA" adına sadık değildi — gerçek QAOA parametreleri **optimize eder**. Kullanıcı
sorguladı, kabul edildi ve COBYLA optimizasyon döngüsü eklendi (bkz. commit `6e0e3e5`).

**Tekrar denenmeli mi**: Hayır, mevcut sürüm (COBYLA + tohumlu başlangıç) daha doğru. Not: optimizasyon
eklendikten sonra bile olasılık kütlesi tek duruma yoğunlaşmadı (bkz.
[faz1-olcumler.md](../measurements/faz1-olcumler.md)) — bu ayrı, meşru bir bulgu, "olmadı" değil.

### Docker healthcheck — `curl` ile OSRM sağlık kontrolü — 2026-09-13, Faz 1

**Neden denendi**: `docker-compose.yml`'de `osrm` servisinin hazır olmasını beklemek için standart
yaklaşım: `healthcheck: test: ["CMD", "curl", "-f", "http://localhost:5000/..."]` + `depends_on:
condition: service_healthy`.

**Neden olmadı**: **`osrm/osrm-backend` imajında `curl` da `wget` de YOK** (`docker exec ... which
curl` → bulunamadı; `/usr/bin` içinde yalnızca `runcon`, `truncate` gibi birkaç araç var). Docker
healthcheck komutu konteynerin **kendi dosya sisteminde** çalıştığından hiçbir zaman başarılı
olamazdı — servis sonsuza dek "unhealthy" kaldı ve `matrix` servisi hiç başlamadı.

Ayrıca ikinci bir yanlış varsayım: `osrm-routed`'in **`/health` ucu yoktur** (400 döner); gerçek bir
`/route` veya `/table` sorgusu kullanılmalıdır.

**Tekrar denenmeli mi**: Hayır — bu imaj için healthcheck kaldırıldı, hazır olma kontrolü `matrix`
servisinin kendi `/health` ucuna (host'tan HTTP ile) bırakıldı. Genel ders: **minimal imajlarda
healthcheck yazmadan önce imajda HTTP istemcisi olup olmadığını kontrol et.**
