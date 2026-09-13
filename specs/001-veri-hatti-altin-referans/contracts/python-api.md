# Sözleşme — Python Kütüphane Arayüzleri

**Modüller**: `services/qubo`, `services/reference`

> Bu iki modül **servis değil kütüphanedir**. Faz 10'un klasik çözücüsü `qubo`'yu aynen yeniden kullanacak (spec FR-011) — kıyasın adil olması buna bağlı, o yüzden arayüz burada sabitleniyor.

---

## `qubo.matrix_to_qubo(durations, *, epsilon=0.1) -> QUBOProblem`

One-hot TSP QUBO'su üretir. Başlangıç şehri sabitlenir → `(N−1)²` değişken.

| Parametre | Tip | Kural |
|---|---|---|
| `durations` | `ndarray (N,N) float64` | Köşegen 0, `inf`/`nan` yasak |
| `epsilon` | `float` | Ceza payı. `A = (1+ε)·max(durations)` |

**Döndürür**: `QUBOProblem(Q, penalty_A, n_stops, var_map)`

**Garantiler** (testle kanıtlanır):
1. Geçerli turların enerji sıralaması = gerçek tur uzunluğu sıralaması.
2. Kısıt ihlal eden **her** atama, geçerli **her** turdan yüksek enerjili.
3. `penalty_A` matristen türetilir — sabit gömülü değer **yok**.

**Hata**: `durations` kare değilse, köşegen ≠ 0 ise, `inf`/`nan` içeriyorsa `ValueError`.

---

## `qubo.energy(problem, assignment) -> float`

Bir ikili atamanın QUBO enerjisi. `assignment`: `(V,)` boyutunda 0/1 dizisi.

## `qubo.assignment_to_tour(problem, assignment) -> list[int] | None`

Atamayı tura çevirir. Kısıt ihlali varsa **`None`** döner — sessizce "en yakın geçerli tur" uydurmaz.

---

## `brute_force.solve(durations) -> BruteForceResult`

Tüm turları sayarak mutlak optimali bulur. **Yalnızca N ≤ 8** için (N=5'te 24 tur).

> Tur sayısı `(N−1)!` — başlangıç sabit. N=5 → **24**, `5! = 120` değil (aynı turu 5 kez saymamak için).

---

## `qaoa_reference.run(problem, *, p, seed, shots=None) -> ReferenceResult`

Altın referansı üretir.

| Parametre | Tip | Kural |
|---|---|---|
| `problem` | `QUBOProblem` | **`n_stops > 5` ise `ValueError`** — 16 kübit tavanı (Prensip III) |
| `p` | `int` | QAOA derinliği, 1 veya 2 |
| `seed` | `int` | **Zorunlu.** Aynı tohum → aynı sonuç |
| `shots` | `int \| None` | `None` = tam statevector (varsayılan, tercih edilen) |

**Döndürür**: `ReferenceResult` — ham `amplitudes` (complex128), `probabilities`, `best_tour`, `best_energy`, `p`, `seed`, `qubit_order`, `backend`.

**Garantiler**:
1. `‖amplitudes‖ = 1` (tolerans 1e-9).
2. `len(amplitudes) == 2**problem.n_vars`.
3. `qubit_order` **açıkça** doldurulur — [DG-02 riski](../../../docs/risk-register.md) (endian karışıklığı) için.
4. Aynı `(problem, p, seed)` → bit-birebir aynı `amplitudes`.

---

## `amplitudes.save(result, path) / load(path) -> ReferenceResult`

`<path>.npy` (complex128 genlikler) + `<path>.json` (metadata) yazar. Dosya adı damgalıdır: `reference_<tarih>_<githash>_p<N>`.

**Neden ayrı dosya**: Faz 2'nin genlik-genlik kıyası bu `.npy`'yi doğrudan okuyacak. JSON metadata'sı olmadan hangi tohum/konvansiyonla üretildiği bilinemez → [VR-03](../../../docs/risk-register.md).

---

## Faz 2'nin kullanacağı kıyas yüzeyi

```python
ref = amplitudes.load("docs/measurements/reference_20261013_abc123_p2")
# Faz 2 çıktısı float32/Q1.15 olacak; kıyas referansı donanım formatına İNDİRGEYEREK yapılır
hw = load_hardware_output(...)
fidelity = abs(np.vdot(ref.amplitudes.astype(hw.dtype), hw))**2
```

Bu yön önemli: referans complex128 tutulur, **donanımın formatına indirgenir** — tersi belirsizlik yaratırdı (R-5).
