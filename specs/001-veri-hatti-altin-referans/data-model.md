# Phase 1 — Veri Modeli

**Faz**: 1 — Veri Hattı ve Altın Referans · **Tarih**: 2026-09-13

> Bu fazda veritabanı **yok**. Varlıklar dosya sistemi ve bellek içi yapılar olarak yaşar.
> Kalıcı olanların hepsi determinizm gereği (Prensip II) içerik-adresli veya damgalıdır.

---

## 1. DurakListesi (Stops)

Sıralı koordinat kümesi. **Sıra anlamlıdır** — matris indekslerini belirler.

| Alan | Tip | Kural |
|---|---|---|
| `points` | `list[(lat, lon)]` | 2 ≤ N ≤ 30. lat ∈ [−90, 90], lon ∈ [−180, 180] |
| `order_sensitive` | — | Aynı noktalar farklı sırada **farklı** bir DurakListesi'dir |

**Doğrulama**: N < 2 ise hata. N > 30 ise hata (spec FR-003 üst sınırı). Koordinat aralık dışıysa hata.

**Önbellek anahtarı**: `sha256(json(points) + osm_md5)`. Sıra anahtara dahildir — spec edge case'i ("aynı liste farklı sırayla gelirse yanlış önbellek isabeti") bu şekilde kapatılır.

---

## 2. MesafeMatrisi (DurationMatrix)

| Alan | Tip | Kural |
|---|---|---|
| `durations` | `np.ndarray[float64] (N,N)` | Saniye. Köşegen = 0 |
| `osm_md5` | `str` | Üretildiği OSM dökümünün sağlaması (R-3) |
| `engine` | `str` | `"osrm"` + sürüm |
| `created_at` | ISO 8601 | |

**Değişmezler**:
- **Asimetrik olabilir** ve olmalıdır — `durations[i][j] ≠ durations[j][i]` beklenen durumdur (gerçek yol ağı; ölçümde 434/435 çift asimetrik çıktı).
- **`None`/`inf` yasak**: Ulaşılamayan çift varsa matris **üretilmez**, hata döner (spec FR-007 — "tanımsız değer uydurulmaz").

**Kalıcılık**: `data/matrices/<anahtar>.npy` (sayısal) + `<anahtar>.json` (metadata). **Git'e commit edilir** — ölçüm girdisinin sabit kalması için ([data-governance.md](../../docs/data-governance.md) §2.3 ile aynı gerekçe).

---

## 3. QUBOProblemi

One-hot TSP formülasyonu. Başlangıç şehri sabit → değişken sayısı `(N−1)²`.

| Alan | Tip | Kural |
|---|---|---|
| `Q` | `np.ndarray[float64] (V,V)` | V = (N−1)². Simetrik |
| `penalty_A` | `float` | `(1+ε)·max(matris)`, ε=0,1 (R-6). **Türetilir, gömülmez** |
| `n_stops` | `int` | Kaynak durak sayısı |
| `var_map` | `dict[(city,time) → index]` | Çözümü tura geri çevirmek için |

**Değişmezler**:
- Geçerli turların enerji sıralaması = gerçek tur uzunluğu sıralaması (spec FR-010).
- Kısıt ihlal eden **her** atama, geçerli **her** turdan yüksek enerjili (spec SC-003).

**Boyut kontrolü** — Anayasa Prensip III bağlantısı:

| N (durak) | V = (N−1)² | 16 kübit tavanı |
|---:|---:|---|
| 4 | 9 | ✅ |
| **5** | **16** | ⚠️ tam tavanda |
| 6 | 25 | 🔴 aşıyor — **reddedilir** |

Altın referans N > 5 için **hata verir**; matris servisi N ≤ 30'u destekler (iki farklı ölçek, spec'te bilinçli).

---

## 4. ReferansSonucu (ReferenceResult)

Faz 2'nin karşılaştıracağı çıktı. **Bu fazın asıl ürünü.**

| Alan | Tip | Kural |
|---|---|---|
| `amplitudes` | `np.ndarray[complex128] (2^16,)` | **Ham genlikler.** `‖ψ‖ = 1` (tolerans 1e-9) |
| `probabilities` | `np.ndarray[float64] (2^16,)` | `|amp|²`, toplam 1 |
| `best_tour` | `list[int]` | Bulunan en iyi tur |
| `best_energy` | `float` | |
| `p` | `int` | QAOA derinliği (1 veya 2) |
| `seed` | `int` | Tohum — tekrarlanabilirlik için zorunlu |
| `qubit_order` | `str` | **`"little"` / `"big"`** — DG-02 riskine karşı açık kayıt (R-5) |
| `backend` | `str` | `"aer_simulator_statevector"` + sürüm |

**Kalıcılık**: `docs/measurements/reference_<tarih>_<githash>_p<N>.npy` + eşlenik `.json`. Damgalama [risk-register.md VR-03](../../docs/risk-register.md)'ün gereği.

**Neden complex128**: Faz 2 float32/Q1.15 üretecek; kıyas referansı donanım formatına **indirgeyerek** yapılır. complex128 her dar formata kayıpsız indirgenir (R-5).

---

## 5. KabaKuvvetSonucu (BruteForceResult)

Mutlak gerçek. Referansın doğruluğunu bağımsız ölçer.

| Alan | Tip | Kural |
|---|---|---|
| `all_tours` | `list[list[int]]` | N=5 için (5−1)! = **24 tur** (başlangıç sabit, dönüşler sayılmaz) |
| `optimal_tour` | `list[int]` | |
| `optimal_length` | `float` | |

**Kullanım**: `reference.best_tour` ile karşılaştırılır. Spec SC-002 bu eşleşmenin %100 olmasını istiyor.

> **Not**: Prompt "5! = 120 tur" diyor. Başlangıç şehri sabitlendiğinde gerçek sayı **4! = 24**'tür (QUBO değişken sayısıyla tutarlı). Uygulama 24 turu sayar; 120 üzerinden dolaşmak aynı turları 5 kez tekrar sayardı. Bu fark `tasks.md`'ye not düşülecek.

---

## Varlık ilişkileri

```
DurakListesi ──(OSRM)──> MesafeMatrisi ──(matrix_to_qubo)──> QUBOProblemi
                                                                  │
                                            ┌─────────────────────┴───────────────┐
                                            ▼                                     ▼
                                    ReferansSonucu                       KabaKuvvetSonucu
                                    (QAOA, N=5)                          (24 tur, N=5)
                                            │                                     │
                                            └──────── doğrulama ──────────────────┘
                                                          │
                                                          ▼
                                              Faz 2'nin kıyas girdisi
```
