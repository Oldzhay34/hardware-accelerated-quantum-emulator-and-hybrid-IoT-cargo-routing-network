# Sözleşme: Doğrulama Yüzeyi (C-sim / cosim testbench)

**Uygular**: FR-006, FR-016 · **Karşıtı**: [kernel-interface.md](kernel-interface.md)

Bu yüzey **sentezlenmez**. Yalnızca testbench'in çekirdeğin iç genlik dizisine erişmesi
için vardır. Dağıtılan IP'de karşılığı yoktur.

---

## Neden iki ayrı yüzey var

Spec'te görünür bir çelişki vardı: NFR-02 "yalnızca tek skaler döndür" diyor, ama FR-006
genlik düzeyinde kıyas istiyor. Çözüm, ikisinin **farklı yüzeyler** olmasıdır:

| | Dağıtım arayüzü | **Doğrulama yüzeyi** |
|---|---|---|
| Ne döndürür | Tek skaler | İç genlik dizisinin tamamı |
| Sentezlenir mi | Evet | **Hayır** |
| Nerede yaşar | `qir_kernel.cpp` | `tb/tb_kernel.cpp` |
| Ne zaman | Kartta koşum (Faz 5/10) | Faz 2 doğrulaması |

---

## İmza

```cpp
// hls/src/qir_kernel.cpp — yalnızca testbench derlemesinde görünür
#ifdef QIR_VERIFICATION
void qir_kernel_debug(
    const real_t gamma[P_MAX], const real_t beta[P_MAX],
    const real_t h[N_QUBITS], const real_t J[N_QUBITS][N_QUBITS],
    int p,
    amp_t sv_out[N_AMP]          // ÇIKIŞ: genlik dizisinin tamamı
);
#endif
```

> `#ifdef QIR_VERIFICATION` zorunludur. Bu fonksiyon sentez akışında **derlenmemelidir**;
> derlenirse `sv_out` bir `m_axi` portu doğurur ve K-1 maddesini (DDR'a taşma yasağı)
> ihlal eder.

---

## Sözleşme maddeleri

| # | Madde |
|---|---|
| T-1 | `qir_kernel_debug`, `qir_kernel` ile **aynı hesaplama yolunu** kullanmalıdır. Ayrı bir uygulama olursa doğrulama hiçbir şey kanıtlamaz. |
| T-2 | Testbench, referans `.npy` dosyasını **ve** yanındaki `.json` metadata'sını okur. Kübit sıralama konvansiyonu metadata'dan **okunur**, varsayılmaz (FR-009). |
| T-3 | Kıyas, referansı **donanımın formatına indirgeyerek** yapılır (complex128 → Q1.17), tersi değil. |
| T-4 | Testbench standart `g++` ile de derlenebilmelidir — Vitis HLS başlıkları olmadan (Anayasa Prensip V, FR-018). `ap_fixed` için mock tip sağlanır. |
| T-5 | Testbench kart **gerektirmez** (FR-008). |
| T-6 | Fidelity **ve** genlik büyüklük vektörü ayrı ayrı raporlanır — DG-02 imzasını ayırt edebilmek için (bkz. aşağı). |

---

## Kabul ölçütü

```text
fidelity = |⟨ref|out⟩|²   (ikisi de normalize)

M eşiği: ≥ 0,99      SC-001
H eşiği: ≥ 0,999
Beklenen (Q1.17): 0,999917   — ÖLÇÜLEN, scripts/format_fidelity.py
```

`n = 8, 12, 16` için **ayrı ayrı** koşulur (US1 senaryo 4).

### DG-02 ayırt etme kuralı

| fidelity | büyüklük vektörü | Teşhis |
|---|---|---|
| ≈ 0 | **doğru** | Kübit sıralaması ters — DG-02. Sayısal hata **değil** |
| ≈ 0 | yanlış | Gerçek hesaplama hatası |
| 0,99–0,9999 | doğru | Sabit-nokta birikimi — beklenen |
| < beklenen (0,999917) ama ≥ 0,99 | doğru | **Bulgu**: CPU taklidinin yakalamadığı bir donanım davranışı (taşma / yuvarlama kipi / ara genişlik). Kaydedilir |

---

## Çıktı biçimi

Testbench, [docs/measurements/](../../../docs/measurements/) altına damgalı JSON yazar
(tarih + git hash + konfig — VR-03):

```json
{
  "fidelity": 0.999917,
  "referans_dosya": "reference_20260913_<hash>_p2_n5.npy",
  "kubit_konvansiyonu": "<metadata'dan okunan>",
  "n_qubits": 16,
  "format": "Q1.17",
  "gecti_M": true,
  "gecti_H": true
}
```

Sayı **elle sabitlenmez** — CLAUDE.md kırmızı çizgisi.
