# Phase 1 — Veri Modeli: Faz 2 FPGA Statevector Çekirdeği

**Tarih**: 2026-09-15 · **Plan**: [plan.md](plan.md) · **Araştırma**: [research.md](research.md)

> Bu belge **onaylanan** A1 + B4 + C1 kombinasyonunu varsayar. Onay değişirse buradaki
> bit genişlikleri ve blok sayıları yeniden türetilmelidir.

---

## 1. Statevector

Fazın merkezî varlığı. `2^n` karmaşık genlik; çip-içi BRAM'de, **tek dizi** (yerinde
güncelleme — [R-2](research.md#r-2-tamponlama--yerinde-in-place)).

| Alan | Değer | Kaynak |
|---|---|---|
| Kübit sayısı `n` | 16 (derleme zamanı parametresi, ≤16) | FR-003, FR-005 |
| Genlik sayısı | `2^16` = 65.536 | |
| Sayı formatı | `ap_fixed<18, 1>` (Q1.17), reel + sanal ayrı | [R-3](research.md#r-3-sayı-formatı--q117) |
| Genlik genişliği | 36 bit (18 + 18) | |
| Toplam | 2.359.296 bit = 288 KB | |
| BRAM36 blok | **64** (= %45,7 / 140) | HESAPLANAN |
| Tamponlama | Yerinde (tek dizi) | R-2 |
| Bankalama | `cyclic`, F = 16 | [R-1](research.md#r-1-bankalama-şeması) |
| Parça başına kelime | 65.536 / 16 = **4.096 = 4 × 1.024** — israf yok | HESAPLANAN |

```cpp
// hls/src/qir_types.hpp
static constexpr int N_QUBITS = 16;
static constexpr int N_AMP    = 1 << N_QUBITS;   // 65536
static constexpr int BANKS    = 16;              // ARRAY_PARTITION faktörü
static constexpr int LANES    = 8;               // yerinde tavan: BANKS*2/4

using real_t = ap_fixed<18, 1>;                  // Q1.17: 1 işaret + 17 kesir
struct amp_t { real_t re, im; };                 // 36 bit — tam bir BRAM36 kelimesi
```

```cpp
// hls/src/statevector.hpp
amp_t sv[N_AMP];
#pragma HLS ARRAY_PARTITION variable=sv cyclic factor=16 dim=1
#pragma HLS BIND_STORAGE     variable=sv type=RAM_2P impl=BRAM
```

**Değişmezler (invariants)**:
- `‖sv‖₂ = 1` (kuantalama sonrası yeniden normalize edilir)
- Her genlik `[-1, 1)` aralığında — `ap_fixed` doyurma (saturation) ile kırpılır
- DDR'a taşma **yok** (Anayasa Prensip III) — dizi `m_axi` portuna **bağlanmaz**

**Neden F = 16?** Parçalanma uçurumu F > 64'te başlar (parça 1.024 kelimenin altına düşünce
bloğun kalanı israf olur). F = 16 uçurumun rahatça altında ve tam bölünüyor. F'i büyütmek
yerinde şemada verim kazandırmaz: tavan `BANKS × port / 4` olduğu için F = 32 teorik olarak
16 çift/çevrim verirdi, ama bunu sömürmek için 64 erişim/çevrim gerekir ve DSP bütçesi
(220) buna yetmez. **F = 32 sentez sonrası bir İ denemesidir**, M değil.

---

## 2. Kapı (Gate)

İki **ayrı** sınıf. Bu ayrım fazın en önemli tasarım bulgusudur
([R-4](research.md#r-4-kapı-kümesinin-donanım-biçimi--yerleşik-rzz)) — kod da ikiye ayrılır.

### 2a. Köşegen kapılar — eşleme YOK

| Kapı | Etki | Erişim deseni |
|---|---|---|
| RZ(θ, k) | `sv[i] *= exp(±iθ/2)`, işaret `i`'nin k. bitine göre | sıralı |
| RZZ(θ, a, b) | `sv[i] *= exp(±iθ/2)`, işaret `bit_a XOR bit_b`'ye göre | sıralı |
| P(φ, k) | faz çarpımı | sıralı |

**Bankalama sorunu yoktur.** Erişim `i = 0 … N_AMP-1` sıralıdır; `2^k` adımı yoktur.
Köşegen matrislerin çarpımı köşegen olduğundan, maliyet katmanının **100 kapısı tek geçişe
füzyonlanır**.

```cpp
// hls/src/gates_diagonal.hpp — kavramsal imza
void apply_cost_layer(amp_t sv[N_AMP], const cost_terms_t &terms, real_t gamma);
```

### 2b. Eşlemeli kapılar — `(i, i XOR 2^k)`

| Kapı | Etki |
|---|---|
| H(k), X(k), RX(β, k) | `(sv[i], sv[i∨2^k])` çiftine 2×2 matris |
| CNOT(c, t) | `c` biti 1 olan indekslerde `t` üzerinde takas |

Bu sınıf, SK-02'nin geçerli olduğu tek yerdir — ve p=2'de **232 kapının yalnızca 32'si**
buradadır.

```cpp
// hls/src/gates_pairing.hpp
template <int K>                     // K DERLEME ZAMANI sabiti — R-7'nin koşulu
void apply_rx(amp_t sv[N_AMP], real_t beta);
```

> ⚠️ `K`'nin şablon parametresi olması **tesadüf değil, tasarımın kendisidir.** Çalışma
> zamanı değişkeni olsaydı HLS `ARRAY_PARTITION`'ı çözemez ve erişimleri serileştirirdi
> ([R-7](research.md#r-7-çekirdeğin-genelliği--qaoaya-özel-nc-3)).

---

## 3. Devre (QAOA katmanı)

Konaktan **kapı listesi gelmez** — yalnızca parametreler gelir (C1 kararı).

| Alan | Tip | Açıklama |
|---|---|---|
| `p` | derleme zamanı sabiti | QAOA derinliği (1, 2, 3) |
| `gamma[p]` | `real_t` | maliyet katmanı açıları (çalışma zamanı) |
| `beta[p]` | `real_t` | karıştırıcı açıları (çalışma zamanı) |
| `cost_terms` | `{h[16], J[16][16]}` | QUBO'dan türetilen Ising katsayıları |

Devre yapısı sabittir: `p` kez (maliyet katmanı → karıştırıcı katmanı).

Kapı sayısı (yerleşik formülasyon, **ÖLÇÜLEN**): `p × (100 köşegen + 16 eşlemeli)`.

---

## 4. Bankalama şeması

Genlik indeksini fiziksel banka + ofsete eşleyen fonksiyon.

| Alan | Değer |
|---|---|
| Eşleme | `banka(i) = i mod 16` (naif düşük-bit — `cyclic` partition'ın doğal davranışı) |
| Ofset | `ofset(i) = i div 16` |
| Port/banka | 2 (çift portlu BRAM) |
| Çift başına erişim | 4 (oku `i`, oku `i'`, yaz `i`, yaz `i'`) — yerinde güncellemenin bedeli |

**Verim** (HESAPLANAN, `scripts/banking_analysis.py`):

| `k` aralığı | Tepe banka yükü | Çevrim | Verim |
|---|---:|---:|---:|
| 0–3 | 2 | 1 | 8 çift/çevrim |
| **4–15** | **4** | **2** | **4 çift/çevrim** |

`k ≥ 4` için çiftin iki üyesinin de düşük 4 biti aynıdır → aynı bankaya düşerler. Bu
**kaçınılmazdır**: yerinde şemada hiçbir banka eşlemesi bunu düzeltmiyor (üçü de aynı
sonucu veriyor). SC-003 (II ≤ 4) açısından **sorun değil** — II = 2.

---

## 5. Sentez raporu

**Bu fazın asıl kanıtı** — C-sim değil (US2, US3).

| Alan | Nereden | Hedef | Ölçüt |
|---|---|---|---|
| BRAM_18K | `csynth` rapor tablosu | ≤ 238 (= %85 × 280) | SC-002 |
| DSP48E | " | — (izlenir) | — |
| LUT / FF | " | — (izlenir) | — |
| II (`k=0`) | boru hattı raporu | ≤ 4 | SC-003, FR-013 |
| II (`k=15`) | " | ≤ 4 | SC-003, FR-013 |
| Latency | " | — (kaydedilir) | FR-010 |
| Fmax | zamanlama özeti | — (NC-4'ü çözer) | FR-010 |

> ⚠️ **BRAM birimi tuzağı**: Vitis HLS BRAM'i **18Kb birimiyle (BRAM_18K)** raporlar.
> Bütçe **280'dir, 140 değil**. %85 eşiği = **238 BRAM_18K**. Tahmini 64 BRAM36 = 128
> BRAM_18K = %45,7. Raporu 140'a bölmek doluluğu iki kat gösterir.

Beklenen değerden sapma **gizlenmez** (FR-012): nedeni ve bir sonraki deneme yazılır.

---

## 6. Doğrulama sonucu

| Alan | Tip | Açıklama |
|---|---|---|
| `fidelity` | float | `|⟨ref\|out⟩|²`, ikisi de normalize |
| `referans_dosya` | path | `docs/measurements/reference_*.npy` |
| `kubit_konvansiyonu` | str | Referansın metadata'sından **okunur**, varsayılmaz (FR-009) |
| `n_qubits` | int | 8, 12, 16 ayrı ayrı (US1 senaryo 4) |
| `format` | str | `Q1.17` |
| `gecti` | bool | `fidelity ≥ 0,99` (M) / `≥ 0,999` (H) |

**Kıyas yönü**: referans **donanımın formatına indirgenerek** karşılaştırılır
(complex128 → Q1.17), tersi değil ([001 research R-5](../001-veri-hatti-altin-referans/research.md)).

**Beklenen değer** (ÖLÇÜLEN, CPU'da sabit-nokta taklidiyle): Q1.17 için **0,999917**.
C-sim'in bundan anlamlı ölçüde sapması, taklidin yakalamadığı bir donanım davranışına
(taşma, farklı yuvarlama kipi, ara sonuç genişliği) işaret eder — **bu sapma kendi başına
bir bulgudur** ve kaydedilir.

### Ayırt edici durum — DG-02 imzası

Fidelity ≈ 0 **ama** genlik büyüklükleri doğruysa: kübit sıralama konvansiyonu terstir,
sayısal hata değil. Doğrulama takımı bu ikisini ayırt edebilmelidir (spec Edge Cases).

---

## Varlık ilişkileri

```text
Devre (p, gamma[], beta[], cost_terms)
   │
   ├── p kez ──> Maliyet katmanı ──> Köşegen kapılar (100) ──┐
   │                                                          ├──> Statevector (65536 × Q1.17)
   └── p kez ──> Karıştırıcı katmanı ──> Eşlemeli kapılar(16)─┘         │
                                              │                         │
                                              │                    Bankalama şeması
                                              │                    (cyclic F=16)
                                              ▼                         │
                                         SK-02 yalnızca                 ▼
                                         burada geçerli           Sentez raporu
                                                                  (II, BRAM, Fmax)
                                                                        │
Altın referans (.npy) ──────────> Doğrulama sonucu <────────────────────┘
                                   (fidelity, konvansiyon)
```
