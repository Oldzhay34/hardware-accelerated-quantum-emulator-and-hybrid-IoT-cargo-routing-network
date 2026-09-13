# ADR 0006 — Rotalama motoru OSRM, kuantum kütüphanesi Qiskit+Aer

**Tarih**: 2026-09-13 · **Faz**: 1 · **Durum**: Kabul edildi (kullanıcı onayı, 2026-09-13)

## Bağlam

Faz 1 iki dış bağımlılık seçimi gerektiriyor: N×N sürüş-süresi matrisi üretecek rotalama motoru ve
altın referansı koşacak kuantum kütüphanesi. Anayasa Prensip I, karşılaştırma raporu ve açık onay
olmadan koda dökülmesini yasaklıyor. Faz 1 promptu ayrıca "tahmini rakam yazma" diyor — seçim
gerçek ölçüme dayanmalı.

## Seçenekler

**Rotalama**: OSRM · Valhalla · GraphHopper
**Kuantum**: Qiskit(+Aer) · PennyLane (Cirq/qsim değerlendirilmedi — gerekçe aşağıda)

## Karar

**OSRM** (BSD-2-Clause) ve **Qiskit 2.5.2 + qiskit-aer 0.17.2** (Apache-2.0).

## Gerekçe

Ölçümler bu makinede yapıldı (Docker 29.5.3, 6 CPU, 10,4 GB RAM; İstanbul extract 44,6 MB):

- **GraphHopper ampirik olarak elendi**: açık kaynak sürümünde `/matrix` ucu **yok** — varsayılmadı, test edildi (`/route` → 200, `/matrix` → **404**). N=30 için 900 ayrı rota çağrısı gerekirdi.
- **Valhalla performanstan elendi**: matris çağrısı 12,87 sn medyan, OSRM'in 0,383 sn'sine göre **34 kat yavaş**; ayrıca 900 hücrenin 842'sini doldurabildi ve ön işleme 5,5 kat uzun sürdü (1054 sn vs 192 sn).
- **OSRM** ölçülen her eksende ya birinci ya ikinci; asıl kriter olan matris gecikmesinde açık ara önde. Skor 46/50 (Valhalla 33, GraphHopper 25).
- **Qiskit+Aer**: zorunlu kriteri (ham genliklere erişim) PennyLane de karşılıyor, yani seçim oradan ayrışmadı. Belirleyici: Aer'in **8 kat** hız üstünlüğü (8,9 ms vs 72,3 ms) ve Anayasa Prensip IV'ün Qiskit'i **adıyla** bağlayıcı kılması. PennyLane anayasa değişikliği gerektirirdi; ölçümler bunu haklı çıkarmıyor.
- **Cirq/qsim ölçülmedi**: Qiskit anayasayla zaten sabit ve iki aday da zorunlu kriteri karşıladı; üçüncü bir kütüphaneyi ölçmek 14 hafta kısıtı (Prensip VI) altında getirisiz.

## Sonuç

- Tam ölçüm tabloları ve gerekçeler: [research.md](../../specs/001-veri-hatti-altin-referans/research.md)
- OSM dökümü MD5 (`cb101d92…`) ile pinlenir — spec FR-005.
- Altın referans **complex128** `.npy` yazar; Faz 2 kıyası referansı donanım formatına indirgeyerek yapar.
- Valhalla'nın ilk denemedeki segfault'u **aracın kusuru değildi**, eksik kurulum komutumdandı; doğru sırayla çıkış kodu 0 verdi. Ancak yanlış sırada anlaşılır hata yerine segfault vermesi öğrenme maliyetine yazıldı.

## Tekrar değerlendirilmeli mi?

Evet, şu koşulda: problem ölçeği N=30'un belirgin şekilde üstüne çıkarsa (OSRM'in MLD boru hattı
yeniden ölçülmeli) veya Faz 2'nin genlik kıyası Qiskit'in veremediği bir çıktı biçimi isterse.
GraphHopper yalnızca ticari Matrix API lisansı alınırsa yeniden gündeme gelebilir — taban planda yok.
