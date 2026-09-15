# `hls/` — FPGA statevector çekirdeği (Faz 2)

**Onaylanan mimari**: [ADR 0008](../docs/decisions/0008-statevector-cekirdek-mimarisi.md) —
**A1** (naif `cyclic` F=16 + yerinde) + **B4** (Q1.17) + **C1** (QAOA'ya özel).

> ⚠️ **Buradaki hiçbir kaynak sentezlenmedi.** Vitis HLS kurulu değil
> ([SK-04](../docs/risk-register.md)). C-simülasyon doğrulaması geçti, ama
> **BRAM, II ve Fmax hakkında hiçbir iddia yoktur** — o sayılar yalnızca sentez
> raporundan okunur (Anayasa Prensip II, SC-002/SC-003).

## Dizin düzeni

| Dizin | İçerik | Sentezlenir mi |
|---|---|:---:|
| `src/` | Çekirdek kaynağı — tipler, kapılar, üst seviye | ✅ |
| `tb/` | Testbench, `.npy`/JSON okuyucular, `ap_fixed` mock | ❌ |
| `tcl/` | Vitis HLS akış scriptleri (csim/csynth/cosim/export) | — |
| `build/` | Derleme çıktısı — **git'e girmez** | — |

### `src/`

| Dosya | Ne yapar |
|---|---|
| `qir_types.hpp` | `real_t = ap_fixed<18,1,AP_RND_CONV,AP_SAT>`, sabitler, faz tipi |
| `statevector.hpp` | Başlangıç durumu, çift indeksleme (`pair_index`) |
| `gates_diagonal.hpp` | **Köşegen** kapılar — eşleme yok, bankalama sorunu yok |
| `gates_pairing.hpp` | **Eşlemeli** kapılar — `template <int K>`, SK-02 burada |
| `trig.hpp` | Tur → (cos, sin). **Sentez borcu**: LUT/CORDIC gerekir |
| `qir_kernel.cpp` | Üst seviye + iki yüzey (dağıtım / doğrulama) |

## Üç tasarım kararı ve neden böyle

**1. Köşegen ve eşlemeli kapılar AYRI dosyada.** QAOA maliyet operatörünün 100
Pauli teriminin hepsi köşegendir; köşegen kapı genliği yerinde çarpar,
`(i, i XOR 2^k)` eşlemesi yapmaz. Qiskit RZZ'yi `CX–RZ–CX`'e ayrıştırdığı için
devrede 384 eşlemeli kapı görünür — ama bu Qiskit'in kapı kümesinin kısıtıdır.
Yerleşik uygulamayla p=2'de **384 → 32**, yani 12× azalma.

**2. `K` şablon parametresidir, çalışma zamanı değişkeni değil.** HLS
`ARRAY_PARTITION`'lı bir diziye hangi parçadan erişildiğini derleme zamanında
çözemezse **bütün erişimleri seri hale getirir**. Plandaki II aritmetiğinin
tamamı `K`'nin sabit olmasına bağlıdır ([research.md R-7](../specs/002-fpga-statevector-cekirdegi/research.md)).

**3. Faz TUR cinsinden tutulur.** `E(i)` bu problemde ~1e4 mertebesinde; `γ·E`'yi
sabit noktada tutmak ~44 bitlik akümülatör isterdi. Terim başına faz konakta
mod 1'e indirgenir, çekirdekteki toplama taşması **zaten mod 2π** demektir.
Burada sarma hata değil, istenen davranıştır.

## Derleme ve koşum

Kart ve Vitis GEREKMEZ (Anayasa Prensip V):

```bash
wsl -e bash /mnt/c/Users/olcay/IdeaProjects/qir-engine/hls/build_and_run.sh
```

> **Neden WSL?** Bu makinede Windows **Smart App Control açık** ve yeni üretilen
> her imzasız `.exe`'yi dosya özetine göre engelliyor. SAC'ı kapatmak **geri
> alınamaz** bir sistem güvenlik değişikliğidir; derleme Linux tarafına alındı.
> Aynı kaynak, aynı standart C++17 — Windows'ta koşabilen ilk ikili ile WSL
> ikilisi **birebir aynı** fidelity'yi verdi. Bkz. [BK-04](../docs/risk-register.md).

Elle derlemek için:

```bash
g++ -std=c++17 -O2 -DQIR_VERIFICATION -DQIR_NO_VITIS -DQIR_N_QUBITS=16 -Ihls/src -Ihls/tb hls/tb/tb_kernel.cpp hls/src/qir_kernel.cpp -o hls/build/tb_kernel_n16
```

Kübit sayısı **derleme zamanı** parametresidir (FR-003) — n=8/12/16 ayrı ikili ister.

## Ölçülen sonuçlar

[docs/measurements/faz2-csim.md](../docs/measurements/faz2-csim.md)
