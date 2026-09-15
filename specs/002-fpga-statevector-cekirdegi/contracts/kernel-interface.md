# Sözleşme: Dağıtım Arayüzü (AXI)

**Uygular**: FR-015 · **Karşıtı**: [testbench-interface.md](testbench-interface.md)

Bu, **kartta koşan IP'nin** dışarıya gösterdiği yüzeydir. Faz 5 (PS entegrasyonu) ve
Faz 10 (kıyas) bu sözleşmeye bağlanır.

---

## Temel kural

> Aşağı yönde **yalnızca devre parametreleri**, yukarı yönde **tek skaler beklenen değer**.

Genlik dizisi bu yüzeyden **görünmez**. Bu bilinçlidir: 65.536 genliği AXI üzerinden
çekmek, hızlandırmanın kendisini anlamsız kılacak kadar pahalıdır (Q1.17'de 288 KB).

Genlik kıyası için ayrı bir yüzey vardır — bkz. [testbench-interface.md](testbench-interface.md).
Bu ayrım spec'teki görünür NFR-02 çelişkisinin çözümüdür.

---

## Üst seviye imza

```cpp
// hls/src/qir_kernel.cpp
void qir_kernel(
    const real_t gamma[P_MAX],      // maliyet katmanı açıları
    const real_t beta [P_MAX],      // karıştırıcı açıları
    const real_t h    [N_QUBITS],           // Ising lineer katsayıları
    const real_t J    [N_QUBITS][N_QUBITS], // Ising ikinci derece katsayıları
    int          p,                 // kullanılacak katman sayısı (≤ P_MAX)
    real_t      &beklenen_deger     // ÇIKIŞ: ⟨ψ|H_C|ψ⟩ — tek skaler
);
```

```cpp
#pragma HLS INTERFACE mode=s_axilite port=gamma
#pragma HLS INTERFACE mode=s_axilite port=beta
#pragma HLS INTERFACE mode=s_axilite port=h
#pragma HLS INTERFACE mode=s_axilite port=J
#pragma HLS INTERFACE mode=s_axilite port=p
#pragma HLS INTERFACE mode=s_axilite port=beklenen_deger
#pragma HLS INTERFACE mode=s_axilite port=return
```

---

## Sözleşme maddeleri

| # | Madde |
|---|---|
| K-1 | Çekirdek **hiçbir koşulda** `m_axi` portu açmaz. Statevector DDR'a taşmaz (Anayasa Prensip III). |
| K-2 | `p > P_MAX` veya `p < 1` → çekirdek çalışmaz, `beklenen_deger` değişmez. |
| K-3 | Kübit sayısı derleme zamanı sabitidir; çalışma zamanında değiştirilemez (FR-003). |
| K-4 | Çekirdek **durumsuzdur**: her çağrı `\|0…0⟩` durumundan başlar. Önceki çağrının kalıntısı taşınmaz. |
| K-5 | `beklenen_deger`, `real_t` değil **`float`** döner — konak tarafı sabit-nokta ölçeklemesi bilmek zorunda kalmasın. |
| K-6 | Kart erişimi bu arayüzün **derlenmesi** için koşul değildir (Anayasa Prensip V). |

---

## Ölçekleme uyarısı

`h` ve `J` katsayıları QUBO'dan gelir ve **ham hâlleriyle `[-1, 1)` aralığının dışında
olabilirler** (ceza katsayısı `A = (1+ε)·max(matris)` büyük bir sayıdır). Konak tarafı
bunları çekirdeğe vermeden önce **normalize etmek zorundadır**; çekirdek içinde `ap_fixed`
doyurması sessizce kırpar ve bu **sessiz bir doğruluk hatası** olur.

> Bu, Faz 5'e devredilen açık bir borçtur. Normalizasyon ölçeği `beklenen_deger`'e geri
> uygulanmalıdır, yoksa döndürülen enerji yanlış ölçekte olur.

---

## Kapsam dışı (bu faz)

- AXI4-Stream varyantı — yalnızca skaler döndüğü için `s_axilite` yeterli; stream Faz 5'te
  gerekirse eklenir
- Kesme (interrupt) / DMA — Faz 5
- Çoklu çekirdek örneği — İ
