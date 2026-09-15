# ADR 0007 — Altın referansa gerçek klasik optimizasyon döngüsü (COBYLA)

**Tarih**: 2026-09-13 · **Faz**: 1 · **Durum**: Kabul edildi (kullanıcı onayı)

## Bağlam

Faz 1'in altın referansı ilk sürümde QAOA devresini **tohumlu rastgele parametrelerle bir kez**
koşuyordu; klasik optimizasyon döngüsü yoktu. Tam statevector taraması sayesinde `best_tour` her
koşumda doğru bulunuyordu, dolayısıyla referansın *işlevi* çalışıyordu.

Ancak bu, "QAOA" adına tam sadık değildi: gerçek QAOA parametreleri **optimize eder**. Bu durum
kullanıcıya açıkça raporlandı ve ne yapılacağı soruldu.

## Seçenekler

1. **Optimizasyonsuz bırak** — referansın amacı (Faz 2'ye ham genlik sağlamak) zaten karşılanıyor;
   sınırlama tezde belirtilir.
2. **COBYLA optimizasyon döngüsü ekle** — beklenti değerini gerçekten minimize et.
3. Daha ağır optimizasyon (SPSA, gradyan tabanlı, çok başlangıçlı) — kapsam büyür.

## Karar

**(2) COBYLA.** `scipy.optimize.minimize(method="COBYLA")`, `MAX_QAOA_ITER = 100` tavanıyla.

## Gerekçe

- Kapsam küçüktü (~30 satır), Phase 5'e göre dakikalar mertebesinde.
- Zaten üretilmiş referans dosyaları optimizasyonsuz haliyle bırakılsaydı, Faz 2 onları kullanmaya
  başladığında "bu gerçek bir QAOA mı, rastgele devre mi" sorusu tekrar açılacaktı.
- **Determinizm bozulmuyor** (Anayasa Prensip II): COBYLA kendi içinde rastgelelik taşımaz;
  başlangıç noktası zaten tohumlu `rng`'den geliyor. Aynı `(problem, p, seed)` → bit-birebir aynı
  genlikler; testle doğrulandı.

## Sonuç

- `services/reference/qaoa_reference.py`: `_beklenti()` objektif fonksiyonu + COBYLA döngüsü.
- `ReferenceResult`'a `optimizer`, `optimizer_iterations`, `cost_before`, `cost_after` alanları eklendi;
  `amplitudes.load()` eski dosyalarla geriye uyumlu (`meta.get` + varsayılan).
- **Ölçülen** (5 durak/16 kübit, seed=42): p=1 → 37 değerlendirme, beklenti 15.191,6 → **-9.799,6**;
  p=2 → 99 değerlendirme, 300,9 → **-3.950,9**.
- **Bedeli**: süre ciddi arttı — p=2 artık 156 sn (öncesinde <1 sn), test paketi 8m33s.

## 🔬 Bulgu: optimizasyon çalışıyor ama olasılık yoğunlaşmıyor

Beklenti değeri gerçekten düştü, fakat olasılık kütlesi tek bir duruma **yoğunlaşmadı**: p=2'de
optimali ölçme olasılığı 2,4e-5; Shannon entropisi üzerinden etkin durum sayısı ~18.900/65536 —
neredeyse uniform.

Bu bir uygulama hatası değil, **sığ-devre (p=1/2) QAOA'nın bilinen bir sınırlaması** (muhtemel
katkı: tur-tersine-çevirme dejenereliği). `best_tour` yine de her koşumda kaba kuvvetle birebir
eşleşiyor — Faz 2'yi engellemiyor. Ayrıntı ve tez için önerilen ifade:
[docs/measurements/faz1-olcumler.md](../measurements/faz1-olcumler.md).

## Tekrar değerlendirilmeli mi?

Evet, şu koşulda: tezde "QAOA optimali %X olasılıkla buluyor" gibi bir iddia gerekirse. O zaman
daha yüksek `p` (3-4) veya daha büyük iterasyon bütçesi denenmeli — ama 14 hafta kısıtı (Prensip VI)
altında bunun getirisi ölçülmeden kapsama alınmamalı.
