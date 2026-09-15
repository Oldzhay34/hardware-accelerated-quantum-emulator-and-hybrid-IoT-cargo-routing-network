# Quickstart — Faz 2 doğrulama ve sentez akışı

**Plan**: [plan.md](plan.md) · **Sözleşmeler**: [contracts/](contracts/)

Bu belge **koşum ve doğrulama** rehberidir; uygulama kodu `/speckit-implement` aşamasına aittir.

---

## Ön koşullar

| Gereksinim | Durum | Gerekli olduğu adım |
|---|---|---|
| Python venv + Qiskit | ✅ kurulu | Adım 0, 1 |
| Faz 1 altın referansı (`docs/measurements/reference_*.npy`) | ✅ var | Adım 2, 3 |
| `g++` (standart C++17) | ✅ kurulu | Adım 2 |
| **Vitis HLS 2025.2** | 🔴 **YOK** — [SK-04](../../docs/risk-register.md) | Adım 4, 5, 6 |
| PYNQ-Z2 kartı | 🟡 var ama **gerekmez** | — |

> **Prensip V**: Adım 0–3 Vitis olmadan koşar ve fazın M kapsamının tamamını kapsar.
> Adım 4–6 araç gelene kadar **doğrulanmamış** sayılır — "muhtemelen sığar" denmez.

---

## Adım 0 — Kararların dayandığı sayıları yeniden üret

Plandaki hiçbir sayı elle yazılmadı. Hepsi yeniden üretilebilir:

```bash
.venv\Scripts\python.exe scripts\banking_analysis.py
```

Beklenen: yerinde şemada en kötü k'de **4 çift/çevrim**, ping-pong'da **16**; üç banka
şeması da aynı. Parçalanma tablosunda F ≤ 64 için israf **yok**.

```bash
.venv\Scripts\python.exe scripts\format_fidelity.py
```

Beklenen: **Q1.17 = 0,999917** (H eşiğini geçen en dar format), Q1.15 = 0,998674 (kalıyor).

```bash
.venv\Scripts\python.exe scripts\memory_budget.py
```

Beklenen: Q1.17 yerinde **64 blok = %45,7**, ping-pong 128 = %91,4.

```bash
.venv\Scripts\python.exe scripts\cpu_reference_time.py
```

Beklenen: Aer (C++) p=2 için ~60–80 ms. **Yayılım geniştir** — tek koşuma güvenme.

Her biri `docs/measurements/` altına damgalı JSON yazar.

---

## Adım 1 — Altın referansın hazır olduğunu doğrula

```bash
.venv\Scripts\python.exe -c "import numpy as np, glob; f=sorted(glob.glob('docs/measurements/reference_*_p2_n5.npy'))[-1]; v=np.load(f); print(f, v.shape, v.dtype, abs(np.linalg.norm(v)-1) < 1e-9)"
```

Beklenen: `(65536,) complex128 True` — 16 kübit, norm 1,0.

Yanındaki `.json` metadata'sında `qubit_order` alanı **bulunmalıdır**. Yoksa doğrulama
yapılamaz (FR-009: konvansiyon varsayılmaz).

---

## Adım 2 — C-sim doğrulaması (Vitis GEREKMEZ) ⭐

Fazın M kapsamının kalbi. Çekirdek standart `g++` ile derlenir ve altın referansa karşı
koşulur:

```bash
g++ -std=c++17 -O2 -DQIR_VERIFICATION -Ihls/src -Ihls/tb hls/tb/tb_kernel.cpp -o build/tb_kernel.exe
```

```bash
build\tb_kernel.exe --reference docs\measurements\reference_20260913_*_p2_n5.npy --n 16
```

**Kabul**: fidelity ≥ 0,99 (M) — beklenen 0,999917.

`n = 8, 12, 16` için ayrı ayrı koşulur (US1 senaryo 4):

```bash
foreach ($n in 8,12,16) { build\tb_kernel.exe --n $n }
```

> Bu adımın geçmesi **SC-001 ve SC-004'ü karşılar** ve kart/Vitis olmadan yapılır.
> Faz 2'nin M sınırı burada tamamlanır.

### Sonuç beklenenden düşükse

[testbench-interface.md](contracts/testbench-interface.md#dg-02-ayırt-etme-kuralı)
tablosuna bak — fidelity ≈ 0 ama büyüklükler doğruysa sorun sayısal değil,
**kübit sıralaması**dır (DG-02).

---

## Adım 3 — Bankalama beklentisini kaydet

Sentez öncesi, aritmetiğin **ne beklediğini** yaz. Sentez sonrası sapma ancak böyle
görülür:

| `k` | Beklenen II (HESAPLANAN) |
|---|---|
| 0–3 | 1 |
| 4–15 | 2 |

Bu tahmin `scripts/banking_analysis.py` çıktısındandır ve **doğrulanmamıştır**.

---

## Adım 4 — Sentez (Vitis HLS gerekir) 🔴

```bash
vitis-run --mode hls --tcl hls\tcl\csynth.tcl
```

Rapordan okunacaklar ve eşikleri:

| Değer | Nereden | Eşik |
|---|---|---|
| **BRAM_18K** | kaynak tablosu | ≤ **238** (= %85 × 280) |
| II (`k=0`) | boru hattı raporu | ≤ 4 |
| II (`k=15`) | " | ≤ 4 |
| DSP48E / LUT / FF | kaynak tablosu | izlenir |
| Fmax | zamanlama özeti | kaydedilir (NC-4) |

> ⚠️ **BRAM birimi tuzağı**: HLS **18Kb** birimiyle raporlar. Bütçe **280**, 140 değil.
> Tahmin: 64 BRAM36 = **128 BRAM_18K** = %45,7. Raporu 140'a bölmek doluluğu iki kat gösterir.

**Sapma varsa gizlenmez** (FR-012) — nedeni ve bir sonraki deneme yazılır.

---

## Adım 5 — Cosim (Vitis HLS gerekir) 🔴

```bash
vitis-run --mode hls --tcl hls\tcl\cosim.tcl
```

RTL'in C ile aynı sonucu verdiğini doğrular. C-sim'in **göremediği** şey budur.

---

## Adım 6 — Uçtan uca tek komut (SC-005) 🔴

```bash
.\hls\run.ps1
```

Sentez → cosim → IP export zincirini elle tıklamadan koşar. **İki ardışık koşum aynı II
ve kaynak sayılarını vermelidir** (SC-005).

---

## Kabul ölçütleri haritası

| Ölçüt | Adım | Vitis gerekir mi |
|---|---|---|
| SC-001 (fidelity ≥ 0,99, n = 8/12/16) | 2 | ❌ |
| SC-002 (BRAM ≤ %85) | 4 | ✅ |
| SC-003 (II ≤ 4, k=0 ve k=15 ayrı) | 4 | ✅ |
| SC-004 (kart olmadan uçtan uca) | 0–2 | ❌ |
| SC-005 (tek komut, tekrarlanabilir) | 6 | ✅ |
| SC-006 (tahmini sayı yok) | hepsi | ❌ |
| SC-007 (≤ 3 bankalama denemesi) | 3–4 | ✅ |
| SC-008 (başarısızlık açıkça yazılır) | 4 | ✅ |

**Vitis olmadan karşılanabilen**: SC-001, SC-004, SC-006 — yani fazın M kapsamı.

---

## Sık karşılaşılacak tuzaklar

| Belirti | Neden | Çözüm |
|---|---|---|
| BRAM raporu beklenenin 2 katı | 140 yerine 280'e bölünmedi | BRAM_18K birimi |
| C-sim geçiyor, II korkunç | `k` çalışma zamanı değişkeni olmuş | `template <int K>` — [R-7](research.md#r-7-çekirdeğin-genelliği--qaoaya-özel-nc-3) |
| Sentezde `m_axi` portu belirdi | `QIR_VERIFICATION` sentez akışında tanımlı | Testbench yolu sentezlenmemeli |
| Fidelity ≈ 0, büyüklükler doğru | Kübit sıralaması ters | DG-02, metadata'yı oku |
| Enerji yanlış ölçekte | `h`/`J` normalize edilmeden verilmiş | [kernel-interface.md](contracts/kernel-interface.md#ölçekleme-uyarısı) |
