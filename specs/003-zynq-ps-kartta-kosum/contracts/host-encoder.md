# Sözleşme: Konak Kodlayıcı (ölçekleme + sabit-nokta paketleme)

**Uygular**: FR-002, FR-003 · **Devralınan borç**:
[kernel-interface.md §Ölçekleme uyarısı](../../002-fpga-statevector-cekirdegi/contracts/kernel-interface.md)

> Faz 2 sözleşmesi: *"Bu, Faz 5'e devredilen açık bir borçtur."*

Bu, fazın **en olası sessiz hata kaynağıdır**. Ham QUBO katsayıları ~1e4
mertebesinde; `ap_fixed` doyurması onları uyarı vermeden kırpar ve sonuç
yanlış çıkar — üstelik hata **donanıma yıkılır**.

---

## Kural sıfır — kartsız doğrulanmadan karta gidilmez

Bu kodlayıcı, **kart olmadan** C-sim'e karşı doğrulanır (Anayasa Prensip V).
Ancak geçtikten sonra karta bağlanır.

> Gerekçe: Kodlayıcı önceden doğrulanmazsa, kartta çıkan her uyuşmazlık
> *"donanım mı, kodlayıcı mı"* belirsizliğinde kalır ve teşhis edilemez.
> Önce doğrulanırsa, uyuşmazlık **donanıma izole olur**.

---

## Tipler

| C tipi | Temsil | Aralık | Konak dönüşümü |
|---|---|---|---|
| `real_t = ap_fixed<18,1,AP_RND_CONV,AP_SAT>` | Q1.17, işaretli, ikiye tümleyen | `[-1, 1)` | `round(x * 2**17)`, `[-2**17, 2**17-1]`'e kırp |
| `phase_t = ap_uint<18>` | TUR (turn) cinsinden, işaretsiz | `[0, 1)` | `round((açı/(2π)) mod 1 * 2**18) mod 2**18` |
| `beklenen_deger` | IEEE-754 `float` | — | `struct.unpack('<f', word)` |

Her değer **kendi 32-bit word'üne** yazılır, düşük bitlere hizalı:

```
word = deger_18bit & 0x3FFFF     # üst bitler ayrılmış (reserved), sıfırlanır
```

> ⚠️ İşaretli değerler için **işaret genişletmesi yapılmaz**; ikiye tümleyen
> 18-bit deseni maskelenir. Üst 14 bit donanımda okunmuyor, ama maskelemek
> tek belirlenimci davranıştır.

---

## Ölçekleme protokolü

```
1. S = max(|h_k|, |J_ab|)  üzerinden bir ölçek seçilir
2. h'_k  = h_k / S ,  J'_ab = J_ab / S        → hepsi [-1, 1) içinde
3. Kartın döndürdüğü beklenen_deger_ham, ölçeklenmiş birimdedir
4. beklenen_deger = beklenen_deger_ham * S     → ham birime geri dönülür
```

**Madde H-1**: `S` her koşumla birlikte **kaydedilir**. Kaydedilmezse
`beklenen_deger_ham` yorumlanamaz hâle gelir.

**Madde H-2**: Ölçekten sonra `max(|h'|, |J'|)` **1'e eşit olmamalıdır** —
Q1.17'nin üst sınırı `1 - 2^-17` ve `AP_SAT` tam `1,0`'ı kırpar. Kenar payı
bırakılır (ör. `S = 1.001 * max|·|`).

**Madde H-3**: Kırpma **sessiz olamaz**. Kodlayıcı, aralık dışı bir değer
görürse istisna fırlatır; sessizce doyurmaz.

**Madde H-4**: Faz `h`, `J` katsayılarından `gamma` ile üretilir ve
**konakta mod 1'e indirgenir** (`gates_diagonal.hpp:23`):
`h[k] = round(mod(-gamma*h_k/(2π), 1) * 2**18)`. Çekirdek fazları toplarken
taşma zaten mod 2π demektir — **burada sarma hata değil, istenen davranıştır**.

---

## Kartsız doğrulama kapısı

Kodlayıcı, aynı girdiyi iki yoldan geçirir ve sonuçları karşılaştırır:

```
girdi (h, J, gamma, beta, p)
   ├──> konak kodlayıcı ──> word dizileri ──> C-sim (aynı paketleme okunarak)
   └──> Qiskit altın referans ──> beklenen değer
```

**Geçme ölçütü**: C-sim'in beklenen değeri ile altın referansın beklenen
değeri arasındaki bağıl fark, Faz 2'de ölçülmüş fidelity bütçesiyle tutarlı
olmalı. Bu kapı geçilmeden `agent/` kart yoluna bağlanmaz.

---

## Sözleşme maddeleri özeti

| # | Madde |
|---|---|
| H-1 | Ölçek `S` her koşumla kaydedilir |
| H-2 | Ölçek sonrası `max\|·\| < 1` (kenar payı bırakılır) |
| H-3 | Kırpma sessiz olamaz — istisna fırlatılır |
| H-4 | Fazlar konakta mod 1'e indirgenir |
| H-5 | Kodlayıcı, **kart olmadan** C-sim'e karşı doğrulanır (Prensip V) |
| H-6 | `beklenen_deger_ham` ve ölçek geri uygulanmış `beklenen_deger` **ayrı** saklanır |
| H-7 | İzdüşüm `cost` vektörleri **sabit tohumlu** RNG'den üretilir ve tohum kaydedilir |

---

## İzdüşüm `cost` vektörleri (madde H-7)

Doğrulama, aynı statevector'ü **≥20 farklı `cost` vektörüyle** okur
([research.md](../research.md) §R3). Bu vektörler de aynı ölçekleme
protokolünden geçer — gerçek QUBO katsayıları değil, **rastgele** olmaları
kodlayıcı açısından hiçbir şeyi değiştirmez.

| Kural | |
|---|---|
| Üretim | Sabit tohumlu RNG; tohum `IzdusumSerisi.tohum`'a yazılır |
| Aralık | Doğrudan `[-1, 1)` içinde üretilir — ölçekleme yine de uygulanır (yol aynı kalsın) |
| Bağımsızlık | Vektörler birbirinden bağımsız; hepsi sıfır olan veya birbirinin katı olan vektörler **elenir** |
| `J` simetrisi | Yalnız `a < b` okunur; üretim de yalnız o üçgeni doldurur, gerisi sıfır |

> ⚠️ Birbirine bağımlı `cost` vektörleri **bağımsız kısıt üretmez** — 20 vektör
> yazılır ama doğrulama gücü 1 vektörünki kadar kalır. Bağımsızlık kontrolü
> kodlayıcının değil, üreticinin sorumluluğudur ve testle sabitlenir.
