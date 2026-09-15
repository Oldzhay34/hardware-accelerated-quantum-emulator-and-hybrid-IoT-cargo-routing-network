# Faz 2 — C-simülasyon doğrulama sonuçları

**Tarih**: 2026-09-15 · **Git**: `c6ad872` · **Durum**: US1 + US4 tamamlandı
**Ham çıktı**: `csim-fidelity_*.json`, `compare-amplitudes_*.json` (bu dizinde)

> Bu belgedeki her sayı **ÖLÇÜLMÜŞTÜR**. BRAM, II ve Fmax hakkında **hiçbir sayı
> yoktur** — onlar sentez raporundan okunur ve Vitis HLS henüz kurulu değil
> ([SK-04](../risk-register.md)). Anayasa Prensip II.

---

## 1. Fidelity — altın referansa karşı (SC-001)

Çekirdek: `ap_fixed<18,1,AP_RND_CONV,AP_SAT>` (Q1.17), yerinde, faz 18 bit.

| n | p | Referans | Kapı | **Fidelity** | M (≥0,99) | H (≥0,999) |
|--:|--:|---|--:|---:|:---:|:---:|
| 8 | 2 | sentetik | 209 | **0,999999956** | ✅ | ✅ |
| 12 | 2 | sentetik | 457 | **0,999998968** | ✅ | ✅ |
| 16 | 1 | TSP (Faz 1) | 300 | **0,999989159** | ✅ | ✅ |
| 16 | 2 | TSP (Faz 1) | 584 | **0,999978359** | ✅ | ✅ |

**n = 8 ve 12 neden sentetik**: tek-sıcak TSP formülasyonunda kübit sayısı
`(N-1)²`, yani yalnızca 4, 9, 16 mümkün. 8 ve 12'nin problem karşılığı yoktur.
Aynı **yapıda** (köşegen maliyet + RX karıştırıcı) rastgele katsayılı devreler
üretildi; altın referans yine Qiskit/Aer (Prensip IV). Katsayı ölçeği gerçek
QUBO'dakine yakın tutuldu (~1e3) ki faz akümülatörü asıl zorlanan koşulda
sınansın.

### 🔬 Bulgu: ölçülen fidelity, tahmin edilenden İYİ çıktı

CPU emülasyonu (`format_fidelity.py`) Q1.17 için **0,999917** öngörmüştü;
C-sim **0,999978** verdi. Sapma gerçek ve açıklaması var: emülasyon **584 kapılı
ayrıştırılmış** devreyi kapı kapı kuantalıyordu, çekirdek ise yerleşik
formülasyonu koşuyor ve yalnızca **35 kuantalama noktası** var
(1 başlangıç + 2 maliyet katmanı + 32 RX).

Yani yerleşik formülasyonun kazancı yalnızca eşlemeli kapıyı 12× azaltmak değil:
**kuantalama hatası birikimini de ~17× azaltıyor.** Bu, plan aşamasında
öngörülmemiş ek bir faydadır.

---

## 2. Bit düzeyi çapraz doğrulama

Fidelity tek başına ince hataları gizler — bir kübitin kapısı atlanmış olsa bile
yüksek kalabilir. Bu yüzden C++ çekirdeği, **bağımsız bir NumPy uygulamasına**
(`scripts/compare_amplitudes.py`) karşı genlik genlik kıyaslandı.

| n | Genlik | Bit-birebir | Azami fark |
|--:|--:|:---:|---:|
| 8 | 256 | ✅ | 0,0 |
| 12 | 4.096 | ✅ | 0,0 |
| 16 | 65.536 | ✅ | 0,0 |

### 🔬 Bu kıyas gerçek bir hata yakaladı

İlk denemede fidelity ikisinde de aynıydı (0,999978) **ama genliklerin %75'i
farklıydı**, azami sapma 6,1 LSB. Sebep: C++ `cos`/`sin` çıktısını `real_t`'ye
atadığı için **kuantalıyor**, Python ikizi ise tam duyarlıkta tutuyordu.
Gerçekçi olan C++'tır — donanımda katsayı bir LUT'tan gelir ve sonlu
duyarlıktadır. Python ikizi düzeltildikten sonra üçü de bit-birebir oturdu.

**Ders**: fidelity bir kabul ölçütüdür, bir doğrulama yöntemi değildir.

---

## 3. `ap_fixed` kip seçimi (ÖLÇÜLEN)

Vitis varsayılanları `AP_TRN` + `AP_WRAP`'tır ve **ikisi de kullanılmadı**:

| Kuantalama | Normalizasyon | Fidelity | H |
|---|---|---:|:---:|
| **AP_RND_CONV + AP_SAT** | her kapıda | **0,999917** | ✅ |
| **AP_RND_CONV + AP_SAT** | **yok** | **0,999917** | ✅ |
| AP_TRN + AP_SAT (varsayılan) | her kapıda | 0,997417 | ❌ |
| AP_TRN + AP_SAT (varsayılan) | yok | 0,999607 | ✅ |

**İki karar çıktı:**

1. **Yuvarlama şart.** `AP_TRN` hatayı ~5× büyütüyor; kapı başına
   normalizasyonla birlikte H eşiğinde kalıyor.
2. **Kapı başına yeniden normalizasyon GEREKSİZ** — 0,999917032 → 0,999916819.
   Donanımda tam geçiş + ters karekök maliyeti hiç ödenmeyecek. Gerçek bir
   mimari tasarruf.

`AP_SAT` için ölçüm fark göstermedi, **ama ölçüm tehlikeli durumu uyandırmıyor**:
emülasyon başlangıç durumunu kuantalamıyor, donanım ise onu belleğe yazar.
`|0…0⟩`'ın genliği tam 1,0 ve Q1.17 aralığı `[-1, 1)`. Çözüm iki katlı:
`AP_SAT` kullanıldı **ve** başlangıç doğrudan düzgün süperpozisyona kuruldu
(2⁻⁸, tam temsil edilebilir) — H katmanı hiç uygulanmıyor.

---

## 4. Faz akümülatörü bit genişliği (ÖLÇÜLEN)

`E(i)` ~1e4 mertebesinde olduğu için `γ·E` doğrudan sabit noktada tutulamaz.
Faz **tur** cinsinden tutulur; terim başına mod 1'e indirgenir ve toplama
taşması zaten mod 2π verir.

| Faz biti | Çözünürlük (rad) | Fidelity |
|--:|---:|---:|
| 12 | 1,53e-03 | 0,999950 |
| 16 | 9,59e-05 | 0,9999999 |
| **18** | **2,40e-05** | **0,999999995** |
| 24 | 3,74e-07 | 1,000000 |

**18 bit seçildi** — `real_t` ile aynı genişlik. Faz darboğaz değil; baskın hata
kaynağı genlik kuantalamasıdır.

---

## 5. Kart ve araç bağımsızlığı (SC-004)

| Koşul | Durum |
|---|:---:|
| PYNQ-Z2 kartı bağlı değil | ✅ koştu |
| Vitis HLS kurulu değil | ✅ koştu |
| Standart `g++` ile derlendi (`-DQIR_NO_VITIS`) | ✅ |
| Windows ikilisi ile WSL ikilisi aynı sonucu verdi | ✅ birebir |

Anayasa Prensip V fiilen kanıtlandı.

---

## 6. Doğrulanmamış olanlar — açıkça

| Ölçüt | Durum | Neden |
|---|---|---|
| SC-002 (BRAM ≤ %85) | ⏳ **doğrulanmadı** | Vitis yok |
| SC-003 (II ≤ 4) | ⏳ **doğrulanmadı** | Vitis yok |
| SC-005 (tek komut, tekrarlanabilir) | ⏳ **doğrulanmadı** | Vitis yok |
| `ap_fixed` mock'unun gerçeğiyle uyumu (T040) | ⏳ **doğrulanmadı** | Vitis yok |
| `trig.hpp` sentezlenebilirliği | ⏳ **sentez borcu** | LUT/CORDIC gerekli |

⚠️ **T040 kritik**: yukarıdaki fidelity sayılarının tamamı `ap_fixed` mock'una
dayanıyor. Mock gerçeğinden sessizce farklı davranırsa bu sayılar yanıltıcı olur.
Vitis gelene kadar **bütün C-sim sonuçları KOŞULLUDUR**.
