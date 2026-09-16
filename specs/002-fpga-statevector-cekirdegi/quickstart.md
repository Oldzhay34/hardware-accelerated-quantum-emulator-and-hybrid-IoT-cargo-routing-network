# Quickstart — Faz 2 doğrulama ve sentez akışı

**Plan**: [plan.md](plan.md) · **Sözleşmeler**: [contracts/](contracts/)

Bu belge **koşum ve doğrulama** rehberidir; uygulama kodu `/speckit-implement` aşamasına aittir.

---

## Ön koşullar

| Gereksinim | Durum | Gerekli olduğu adım |
|---|---|---|
| Python venv + Qiskit | ✅ kurulu | Adım 0, 1 |
| Faz 1 altın referansı (`docs/measurements/reference_*.npy`) | ✅ var | Adım 2, 3 |
| Sentetik referanslar (`synthref_*_n8/_n12`) | ✅ var | Adım 2 |
| `g++` (standart C++17) — **WSL içinde** | ✅ kurulu | Adım 2 |
| **Vitis HLS 2025.2** | ✅ **kurulu — WSL/Ubuntu, `/opt/Xilinx/2025.2`** | Adım 4, 5, 6 |
| PYNQ-Z2 kartı | 🟡 var ama **gerekmez** | — |

> ⚠️ **Vitis Windows'ta ÇALIŞMAZ.** `vitis-run.exe` imzasız ve Smart App Control
> engelliyor ([SK-05](../../docs/risk-register.md)). Windows kurulumu kaldırıldı;
> `hls/run.ps1` artık **çalışmaz**, yerine `hls/run.sh` kullanılır.
>
> ⚠️ Her Vitis çağrısında **`LC_ALL=en_US.UTF-8` şart**. Yoksa `vitis-run` çöker:
> `locale::facet::_S_create_c_locale name not valid`.

> **Prensip V**: Adım 0–3 Vitis olmadan koşar ve fazın M kapsamının tamamını kapsar.

---

## Adım 0 — Kararların dayandığı sayıları yeniden üret

Plandaki hiçbir sayı elle yazılmadı. Dördü de **2026-09-16'da koşuldu ve doğrulandı**:

```bash
.venv\Scripts\python.exe scripts\banking_analysis.py
```
✅ Yerinde şemada en kötü k'de **4 çift/çevrim**, ping-pong'da **16**; üç banka şeması
da aynı. Betiğin kendi yorumu, Tur 17'nin aylar sonra ölçümle bulduğu şeyi zaten
söylüyordu: *"Ping-pong'un üstünlüğü bankalamadan değil, PORT SAYISINI ikiye
katlamasından geliyor."*

```bash
.venv\Scripts\python.exe scripts\format_fidelity.py
```
✅ **Q1.17 = 0,999917032** (H eşiğini geçen en dar format), Q1.15 = 0,998674120.

```bash
.venv\Scripts\python.exe scripts\memory_budget.py
```
✅ Q1.17 yerinde **64 blok = %45,7**, ping-pong 128 = %91,4.
⚠️ Bu **birinci dereceden bir tahmindir**. Sentezde ölçülen: `sv` 4 diziye bölündü
(2 banka × re/im) ve **144 BRAM_18K** tuttu; toplam **187 = %66**. Betiğin kendi
uyarısı doğruydu: *"kesin sayı yalnızca sentez raporundan okunur"*.

```bash
.venv\Scripts\python.exe scripts\cpu_reference_time.py
```
⚠️ **Tek koşuma güvenme — bu uyarı ciddidir.** İki koşum, p=2, Aer (C++):

| Koşu | min | **medyan** | max |
|---|---:|---:|---:|
| 2026-09-15 | 58,07 | 77,57 | 120,99 ms |
| 2026-09-16 | 78,95 | **92,66** | 111,42 ms |

Yayılım **±%60**. Proje uzun süre "~58 ms" kullandı — o, 15 Eylül koşusunun *en iyi*
değeriydi ve karşılaştırmayı bozdu. Düzeltme:
[faz2-sentez.md](../../docs/measurements/faz2-sentez.md) §15. Teze girecek sayı
**medyan + yayılım** olmalıdır.

⚠️ Betiğin sonunda bastığı "FPGA TAHMINI ... 33,2x / 113,4x" satırları **sentez
öncesi aritmetiktir** ve ölçülenden 16–54 kat sapmıştır. Gerçek p=2: 3.728.217 çevrim.

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

Fazın M kapsamının kalbi. **Tek komut**, dört durumu birden koşar:

```bash
wsl -d Ubuntu -e bash /mnt/c/Users/olcay/IdeaProjects/qir-engine/hls/build_and_run.sh
```

**2026-09-16'da ölçülen** (hepsi H eşiğini geçti):

| Durum | Fidelity | Eşik |
|---|---:|:---:|
| n=16, p=2 (TSP) | 0,999978179 | ✅ H |
| n=16, p=1 (TSP) | 0,999989167 | ✅ H |
| n=12, p=2 (sentetik) | 0,999998860 | ✅ H |
| n=8, p=2 (sentetik) | 0,999999871 | ✅ H |

> ⚠️ **Neden WSL, neden elle `g++` değil**: derleme `-DQIR_NO_VITIS` bayrağını
> (mock `ap_fixed` için) ve **üç** kaynak dosyayı ister (`tb_kernel.cpp` +
> `qir_kernel_debug.cpp` + `qir_kernel.cpp`). Eksik bayrakla derleme
> `fatal error: ap_fixed.h: No such file or directory` verir. Ayrıca `n`
> **derleme zamanı** parametresidir (`-DQIR_N_QUBITS`): tek bir ikili ile
> `--n 8` ve `--n 16` koşulamaz, testbench bunu açıkça reddeder.
> Windows'ta üretilen `.exe` ayrıca Smart App Control tarafından engellenir.

> Bu adımın geçmesi **SC-001 ve SC-004'ü karşılar** ve kart/Vitis olmadan yapılır.

### Sonuç beklenenden düşükse

[testbench-interface.md](contracts/testbench-interface.md) tablosuna bak — fidelity
≈ 0 ama büyüklükler doğruysa sorun sayısal değil, **kübit sıralamasıdır** (DG-02).

---

## Adım 3 — Bankalama beklentisi ve ne çıktığı

Sentez öncesi aritmetiğin **ne beklediğini** yazmak, sapmayı görmenin tek yoluydu:

| `k` | Beklenen II (HESAPLANAN) | **Ölçülen** |
|---|---|---|
| 0–3 | 1 | **2** |
| 4–15 | 2 | **2** |

**Beklenti niteliksel olarak yanlıştı** ve öğretici biçimde: `k`'ye göre değişen bir
II yok, çünkü mikser **paylaşılan tek birimdir** (çalışma zamanı `k`) ve HLS hangi
bankaya düşüldüğünü kanıtlayamadığı için her `k` için en kötü durumu varsayıyor.
II'yi belirleyen bankalama değil **bellek portu** çıktı: `RAM_2P` ile 3, `RAM_T2P`
ile 2. Bkz. [ADR 0009](../../docs/decisions/0009-paralellik-turu-kapatildi.md).

---

## Adım 4 — Sentez

```bash
wsl -d Ubuntu -e bash /mnt/c/Users/olcay/IdeaProjects/qir-engine/hls/run.sh csynth
```

**2026-09-16'da ölçülen**:

| Değer | Eşik | **Ölçülen** | |
|---|---|---:|:---:|
| BRAM_18K | ≤ 238 (%85×280) | **187** (%66) | ✅ SC-002 |
| II, `cost_amp_loop` | ≤ 4 | **1** | ✅ SC-003 |
| II, `rx_dyn_pair_loop` | ≤ 4 | **2** | ✅ SC-003 |
| DSP48E | izlenir | 36 (%16) | |
| FF | izlenir | 49.839 (%46) | |
| LUT | izlenir | 45.164 (**%84**) | ⚠️ dar |
| Zamanlama | kaydedilir (NC-4) | **7,195 ns** (Fmax 138,98 MHz) | ✅ |
| Gecikme, p=2 | — | 3.728.217 çevrim = **37,3 ms** | |
| Gecikme, p=3 (max) | — | 5.375.324 çevrim = 53,8 ms | |

> ⚠️ **BRAM birimi tuzağı**: HLS **18Kb** birimiyle raporlar. Bütçe **280**, 140 değil.
>
> ⚠️ **p tuzağı**: rapordaki `max` gecikme `P_MAX = 3` içindir. CPU referansı ve
> fidelity testleri **p=2** koşar — karşılaştırırken aynı `p`'yi kullan.

**Sapma varsa gizlenmez** (FR-012) — nedeni ve bir sonraki deneme yazılır.

---

## Adım 5 — Cosim

```bash
QIR_N=8 wsl -d Ubuntu -e bash /mnt/c/Users/olcay/IdeaProjects/qir-engine/hls/run.sh cosim
```

RTL'in C ile aynı sonucu verdiğini doğrular — C-sim'in **göremediği** şey budur
(örneğin `BIND_STORAGE` seçimi C-sim'de hiç görünmez).

**2026-09-16'da ölçülen**: `C/RTL co-simulation finished: PASS`, fidelity
0,999999871, süre **4 dk 31 sn**.

> ⚠️ **`QIR_N=8` bilinçlidir.** n=16 cosim'i 5,4 milyon çevrim simüle etmek zorunda
> ve **11,5 saat** sürüyor (ölçüldü; darboğaz hesap değil, `/mnt/c` üzerine yazılan
> 87 MB'lık bağımlılık uyarısı log'u). Doğrulanan yapı — `RAM_T2P`, `DEPENDENCE`,
> boru hattı — `n`'den bağımsızdır.
>
> ⚠️ xsim yüz binlerce `Critical WARNING ... dependence access` basar. **Yanlış
> pozitiftir**; cosim geçtiği için pragmanın sağlam olduğu kanıtlanmıştır.

---

## Adım 6 — Uçtan uca (SC-005)

```bash
wsl -d Ubuntu -e bash /mnt/c/Users/olcay/IdeaProjects/qir-engine/hls/run.sh csim csynth
```

**İki ardışık koşum aynı II ve kaynak sayılarını vermelidir** (SC-005).

> ⚠️ `hls/run.ps1` **çalışmaz** — Windows PATH'inde `vitis-run` arıyor, o kurulum
> Device Guard yüzünden kaldırıldı. Yerine `hls/run.sh` yazıldı.

---

## Kabul ölçütleri haritası

| Ölçüt | Adım | Durum (2026-09-16) |
|---|---|---|
| SC-001 (fidelity ≥ 0,99, n = 8/12/16) | 2 | ✅ dördü de H eşiğinde |
| SC-002 (BRAM ≤ %85) | 4 | ✅ %66 |
| SC-003 (II ≤ 4) | 4 | ✅ 1 ve 2 |
| SC-004 (kart olmadan uçtan uca) | 0–2 | ✅ |
| SC-005 (tek komut, tekrarlanabilir) | 6 | ✅ `run.sh` |
| SC-006 (tahmini sayı yok) | hepsi | ✅ §15 düzeltmesiyle |
| SC-007 (≤ 3 bankalama denemesi) | 3–4 | ✅ **sıfır** deneme harcandı |
| SC-008 (başarısızlık açıkça yazılır) | 4 | ✅ [dead-ends.md](../../docs/decisions/dead-ends.md) |

---

## Sık karşılaşılacak tuzaklar

| Belirti | Neden | Çözüm |
|---|---|---|
| `ap_fixed.h: No such file or directory` | `-DQIR_NO_VITIS` verilmemiş | `build_and_run.sh` kullan |
| `vitis-run` çöküyor, `_S_create_c_locale` | locale üretilmemiş | `LC_ALL=en_US.UTF-8` |
| `vitis-run.exe ... Device Guard policy` | Windows, imzasız ikili | WSL kullan (SK-05) |
| `COSIM 212-40` sentez bulunamadı | `open_solution -reset` DB'yi siliyor | `cosim.tcl` önce `csynth_design` çağırır |
| `COSIM 212-330` top çağrılmamış | tb yalnızca `qir_kernel_debug` çağırıyordu | tb `qir_kernel`'i de çağırır |
| Cosim saatlerce bitmiyor | n=16, 5,4M çevrim | `QIR_N=8` |
| BRAM raporu beklenenin 2 katı | 140 yerine 280'e bölünmedi | BRAM_18K birimi |
| CPU karşılaştırması tutarsız | farklı `p`, veya medyan yerine en iyi durum | §15 |
| Sentezde `m_axi` portu belirdi | testbench yolu sentezlenmiş | `add_files -tb` |
| Fidelity ≈ 0, büyüklükler doğru | Kübit sıralaması ters | DG-02, metadata'yı oku |
