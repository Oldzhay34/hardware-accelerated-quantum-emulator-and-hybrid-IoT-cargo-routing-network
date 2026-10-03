# Prizde / Pilde Gecikme Kontrol Ölçümü Protokolü (6B ek, T069 öncesi)

| | |
|---|---|
| **Durum** | 📝 **TASLAK — onay bekliyor.** Onaylanıp dondurulmadan ölçüm koşulmaz |
| **Sürüm** | v1.0 (taslak) — kayıtlar `priz-pil-kontrol-protokolu v1.0` taşır |
| **Onaylanan metin** | — (dondurulunca commit ve git içerik özeti buraya) |
| **Görev** | T069'un girdisi: §6.1'deki GPU (0,997 ms → 36,7×) ve CPU (3,273 ms → 11,2×) değerleri prizde yeniden üretiliyor mu |
| **Dayanak** | FR-011, SC-009 · [gpu-taban-olcum-protokolu v1.1](gpu-taban-olcum-protokolu.md) (aynı iş yükü, aynı istatistik) · [olculen-degerler §6.2](../olculen-degerler.md) açık gözlem |
| **Yürütücü** | `scripts/priz_pil_kontrol.ps1` (**kullanıcı çalıştırır** — fiş uyarılarını görmesi gerekir), özet `scripts/priz_pil_kontrol_ozet.py`; karar kuralları **kodda**, protokolle birlikte donar |

**Kural (FR-011, SC-009)**: ölçümden **önce** onaylanıp dondurulur.

---

## 1. Soru

3 Eki enerji ölçümünde (pilde) iş yükleri, 30 Eyl'deki T067 gecikme
ölçümünden (prizde) belirgin hızlı çıktı. Hangisi doğru çalışma noktası?

| İş yükü | T067 / 21 Eyl (prizde) | 3 Eki (pilde) | Dayandığı iddia |
|---|---:|---:|---|
| GPU aynı algoritma FP32 p=2 | **0,997 ms** (300 sn) | 0,555 ms (170 sn) | "GPU FPGA'dan **36,7×** hızlı" |
| CPU `bench_kernel` float, tek iş parçacığı | **3,273 ms** (10 tekrar!) | 2,91 ms (59.408 koşum) | "CPU FPGA'dan **11,2×** hızlı" |

İki açıklama yarışıyor: **(a) güç kaynağı** (prizde/pilde farklı davranış) ya
da **(b) oturum koşulu** (T067'de GPU sıcak başladı — 75 °C, seri içinde
0,62 → 1,10 ms yavaşladı, arka planda bilinmeyen GPU kullanımı not edilmişti;
3,273 ms ise yalnız 10 tekrardan). Bu ölçüm ikisini ayırır.

---

## 2. Önceden bilinenler — ön kayıt beyanı

| Bilinen | Değer |
|---|---|
| T067 G32-2 (prizde, 30 Eyl 23:42, 300 sn) | medyan 0,997 ms, IQR 0,98; ilk 50 koşum 0,617 → son 60 sn 1,103 ms; GPU başta 75 °C / sonda 80 °C, 1470 → 1845 MHz |
| 3 Eki E3 (pilde, 170 sn) | medyan 0,555 ms, IQR 0,25; GPU başta 58 °C |
| 3 Eki geçersiz koşu E3 (pilde, 170 sn) | medyan 0,5325 ms |
| `bench_kernel` 21 Eyl (prizde?, 10 tekrar) | 3,273 ms, min 2,901 |
| 3 Eki E4 (pilde, 175 sn) | 2,911 ms |
| Güç planı | iki tarihte de "Yüksek performans" + AC ve DC overlay "En iyi performans" (kayıtlardan) |
| Ekran/uyku | **prizde de** ekran 180 sn, uyku 180 sn (3 Eki ön denetimi) → çalıştırıcı engeller |
| Kod | T067'den bu yana ölçüm kodunda yalnız çıktı yazımı ve `bench_kernel --saniye` değişti; zamanlanan bölge aynı |
| ⚠️ **Akış denemesi** (3 Eki 16:08, `-Deneme`, fiş **hep takılı**, G 8 sn, K 5 sn — ölçüm değil, ama gerçek iş yükü) | G medyanları 0,44 / 0,47 / 0,46 / 0,43 ms; K 3,48 / 3,31 / 3,29 / 3,83 ms. **§6'daki beklentiler bu denemeden ÖNCE yazıldı ve değiştirilmedi**; K2 ve K5 bu yüzden tam kör değil, raporda belirtilir |

---

## 3. Tasarım — ABAB

```
[AC1] -> fişi çek -> [DC1] -> fişi tak -> [AC2] -> fişi çek -> [DC2]
blok = [istenen güç durumu] -> 180 sn bekleme -> G (300 sn) -> K (120 sn)
```

| Seri | İş yükü | Ayar |
|---|---|---|
| **G** | `gpu_ayni_algoritma.py --hassasiyet 32 --p 2 --saniye 300` | T067 G32-2 ile **aynı** (300 sn, ısınma 3, başta doğrulama, sonda bit bit) |
| **K** | `bench_kernel --saniye 120 --isinma 3` (float, tek iş parçacığı) | T068 E4 ile aynı ikili kaynağı |

- ABAB: güç kaynağının etkisi (AC↔DC) zamanla kaymadan (AC1↔AC2) ayrılır.
- Ortam: WSL `/root/qir-gpu-venv`, `processors=16` (T067 ve T068 ile aynı);
  ölçüm boyunca **WSL açık**, **ekran/uyku engelli** (T068 v1.1 ile aynı
  düzenek); parlaklık %0; harici monitör yok; klavye/fare kullanılmaz —
  kullanıcı yalnız fişi takar/çeker (betik bip ve mesajla ister).
- Toplam ~45 dk. DC bloğu başında batarya ≥ %30 olmalı.

---

## 4. Ölçülen büyüklükler

Her G serisi için gecikme protokolünün istatistikleri (`agent/measure_latency.py`,
aynı kod): medyan, IQR, p99, ilk 50 koşum / son 60 sn medyanı, pencere
medyanları, GPU sıcaklık/saat/güç (başta, sonda, her 10 sn). K için medyan,
IQR, koşum sayısı, `beklenen_deger`. Her blok için güç durumu (başta ve sonda).

Türetilen:
- **R_kaynak** = DC/AC medyan oranı, iki çift ayrı ayrı (DC1/AC1, DC2/AC2)
- **R_kayma** = AC2/AC1
- **R_T067** = AC medyanı / 0,997 ms (G); **R_21Eyl** = AC medyanı / 3,273 ms (K)

---

## 5. Karar kuralları (koşudan önce; kodda `karar()`)

Ayrı ayrı G ve K için:

| Durum | Karar |
|---|---|
| İki çiftte de DC/AC < 0,90 (ya da > 1,10), aynı yönde | **güç kaynağı etkisi VAR** |
| İki çiftte de 0,90 ≤ DC/AC ≤ 1,10 | güç kaynağı etkisi **yok** |
| Diğer | belirsiz |
| İki AC medyanı da tabanın [0,85, 1,15] katı içinde | taban (T067 / 21 Eyl) **yeniden üretildi** |
| İki AC medyanı da tabanın < 0,85 katı | taban **yeniden üretilemedi** (bugün daha hızlı) |
| Diğer | belirsiz |

**Sonuç → yapılacak** (otomatik değil, kullanıcıya öneri):
- Taban yeniden üretildi → §6.1 değerleri (36,7×, 11,2×) **prizde geçerli**
  kalır; pil ayrı bir çalışma noktası olarak yazılır.
- Taban yeniden üretilemedi → §6.1'in ilgili değeri **bu oturum koşuluna
  özgü**; 36,7× / 11,2× gözden geçirilir — gecikme protokolünün ilgili
  serilerini yeni sürümle yeniden koşmak **kullanıcı kararı**. Bu kontrol
  ölçümü §6.1'in yerine **geçmez**.

---

## 6. Ön kayıtlı beklentiler (ölçümden ÖNCE)

| # | Beklenti | Gerekçe |
|---|---|---|
| K1 | G'de güç kaynağı etkisi **yok** (iki çift de 0,90–1,10) | Plan ve overlay iki durumda aynı; fark oturumdan |
| K2 | G'nin iki AC medyanı da **≤ 0,75 ms** (T067'nin 0,997'si yeniden üretilmez) | T067'deki sıcak başlangıç / arka plan kullanımı |
| K3 | Dört G serisinin hepsinde son 60 sn / ilk 50 koşum **< 1,3** | Soğuk başlangıçta T067'deki seri içi yavaşlama (1,79) görülmez |
| K4 | K'de güç kaynağı etkisi **yok** | Aynı gerekçe |
| K5 | K'nin iki AC medyanı da **≤ 3,0 ms** (3,273 yeniden üretilmez) | 3,273 yalnız 10 tekrardan |

⛔ Tutmayan beklenti için sonradan ölçüt değiştirilmez; sonuç yazılır.

---

## 7. Geçerlilik

| Durum | Karar |
|---|---|
| Ağaç kirli | betik başlamaz |
| Bir blok içinde güç durumu değişti (başta/sonda ya da iş yükünün kendi kaydında `sebekede`) | o blok **geçersiz**, ölçüm durur |
| İş yükü doğrulaması kaldı (G: fidelity / sonda bit bit; K: `beklenen_deger` = −3950,989990234) | blok **geçersiz**, ölçüm durur |
| DC bloğu başında batarya < %30 | ölçüm durur |
| Zamana/değere bakarak koşum ayıklama | ⛔ yapılmaz |

---

## 8. Çıktı

- `gpu-ayni-algoritma_<tarih>_<git>_kontrol{AC1,DC1,AC2,DC2}_fp32_p2.json` (+ `.ham.json.gz`)
- `bench-kontrol_<tarih>_<git>_{AC1,DC1,AC2,DC2}.txt`
- `priz-pil-kontrol-kosullar_<tarih>_<git>.json` — blok başı/sonu güç durumu, batarya, zaman
- `priz-pil-kontrol_<tarih>_<git>.json` — özet: medyanlar, oranlar, kararlar, K1–K5
- Çalıştırma (temiz ağaç, **kullanıcı**, fiş takılıyken başlar):
  `powershell -ExecutionPolicy Bypass -File scripts\priz_pil_kontrol.ps1`.
  `-Deneme`: kısa süreler, fiş beklenmez, çıktı repo dışına — **ölçüm değildir**.

---

## 9. Kapsam dışı

Aer serileri (Aer CPU/GPU oranı aynı gecede ölçüldü, oran olarak daha
sağlam); p=1; FP64; GPU'nun kendi gücü; sıcaklığın kontrollü değiştirilmesi
(yalnız kaydedilir).
