# Faz 1 Ölçümleri

**Kaynak**: `specs/001-veri-hatti-altin-referans/` T026-T027, T042 · **Tarih**: 2026-09-13
**Ortam**: Docker 29.5.3, Python 3.13.12, qiskit 2.5.2, qiskit-aer 0.17.2, 6 CPU, 10,4 GB RAM

> Anayasa Prensip II: bu belgedeki her sayı gerçekten ölçüldü. Tahmini değer yok.

---

## Altın referans — QAOA (5 durak, 16 kübit, seed=42)

| | p=1 | p=2 |
|---|---:|---:|
| Toplam süre (optimizasyon dahil) | 23.145,7 ms | 156.190,6 ms |
| Tepe bellek | 17,82 MB | 17,73 MB |
| COBYLA değerlendirme sayısı | 37 | 99 |
| Beklenti değeri (önce → sonra) | 15.191,6 → **-9.799,6** | 300,9 → **-3.950,9** |
| Optimali ölçme olasılığı | 9,0e-6 | 2,4e-5 |
| Kaba kuvvetle eşleşme | ✅ birebir | ✅ birebir |
| Genlik dosyası boyutu | 1,00 MB | 1,00 MB |

`reference_20260913_04f37b8_p1_n5.{npy,json}` ve `..._p2_n5.{npy,json}` olarak `docs/measurements/`'e yazıldı.

## 🔬 Bulgu: optimizasyon çalışıyor ama olasılık yoğunlaşmıyor

COBYLA'nın beklenti değerini gerçekten düşürdüğü açık (p=1'de ~%164 iyileşme, p=2'de ~%1413 iyileşme — pozitiften negatife). Ama bu, olasılık kütlesinin optimal duruma **yoğunlaşması** anlamına gelmedi:

```
p=2 icin en yuksek olasilikli 8 durum (65536 icinden):
  0.000505, 0.000489, 0.000450, 0.000415, 0.000408, 0.000399, 0.000396, 0.000372
  (rastgele/uniform dagilimda beklenen tek-durum olasiligi: 1/65536 = 0.0000153)

Etkin durum sayisi (Shannon entropisi uzerinden): ~2^14.2 ≈ 18.900 durum
```

Olasılık kütlesi, 65536 durumun ~%29'una neredeyse eşit dağılmış — rastgele bir dağılıma **yakın**, tek bir tepe noktasına yoğunlaşmış değil. En yüksek 8 durumun toplamı yalnızca %0,34.

### Yorum (dürüst, abartısız)

Bu bir uygulama hatası değil — objektif fonksiyon gerçekten iyileşiyor, `best_tour` her koşumda doğru bulunuyor (tam statevector taraması sayesinde). Bulgu şu: **16 kübitlik bir arama uzayında, p=1/2 derinlik ve 100 iterasyonluk bütçeyle, QAOA enerjiyi düşürse de olasılığı tek bir bit dizisine yoğunlaştıramıyor.** Bunun olası nedenleri:

1. **Dejenerelik**: Bir turun tersten (saat yönü/tersi) okunması aynı fiziksel rotayı, farklı bit dizisini verir — enerji eşit, olasılık ikiye bölünür. 5 durakta bu tek başına 2x'lik bir bölünme demek, gözlenen dağılımın tamamını açıklamaz ama katkısı var.
2. **Sığ devre**: p=1/2, 16 kübitlik bir kombinatoryal yüzeyi keskin bir tepeye oturtmak için yetersiz kalabilir — literatürde bilinen bir QAOA sınırlaması.
3. **İterasyon bütçesi**: `MAX_QAOA_ITER=100`, COBYLA'nın yakınsaması için sınırlı olabilir.

### Bu Faz 2'yi engelliyor mu?

**Hayır.** Faz 2'nin ihtiyacı ham genlik vektörü + kaba kuvvetle doğrulanmış `best_tour` — ikisi de mevcut ve doğru. Olasılık dağılımının yayık olması, referansın *geçerliliğini* değil, QAOA'nın *bu derinlikte ne kadar etkili* olduğunu gösteriyor — ki bu zaten ölçülmesi istenen bir özellikti (spec FR-016, SC-006: "hedef bir değer dayatılmaz, ölçüm dürüstlüğü esastır").

### Tez için

Bu bulgu **saklanacak bir kusur değil, raporlanacak bir sonuç**. Yöntem bölümüne şu türden bir not düşülebilir: *"p=1 ve p=2 derinliklerinde QAOA, maliyet beklentisini anlamlı ölçüde düşürmesine rağmen (COBYLA, sırasıyla 37 ve 99 değerlendirmede %164 ve %1413 iyileşme sağladı), olasılık kütlesini tek bir optimal duruma yoğunlaştıramamıştır; etkin durum sayısı ~18.900 olarak ölçülmüştür. Bu, sığ-devre QAOA'nın bilinen bir sınırlamasıyla tutarlıdır."*

## Devredilen

| Soru | Nereye |
|---|---|
| Daha yüksek p (p=3, p=4) veya daha fazla iterasyon denenmeli mi? | Kullanıcı kararı — kapsam/takvim etkisi var (14 hafta kısıtı) |
| Dejenerelik payının (tur tersine çevirme) ölçülmesi | İsteğe bağlı, tez zenginleştirmesi |
