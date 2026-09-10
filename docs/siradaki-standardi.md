# SIRADAKİ Bloğu Standardı

**Kaynak**: Faz 0 alt dal 0.7 · **Oluşturma**: 2026-09-10

Her `specs/<faz>/tasks.md` dosyası, `/speckit-tasks`'ın ürettiği görev listesinin **üstüne**, aşağıdaki
bloğu taşır. Amaç: bir oturum bittiğinde, bir sonraki oturumun (bağlam sıfırlanmış olsa bile) 30
saniyede nerede kaldığını anlaması.

## Biçim

```markdown
## SIRADAKİ

**Hedef (tek cümle)**: <şu an yapılmaya çalışılan tek şey>
**Dokunulacak dosyalar**: <yol1>, <yol2>
**Bilinen tuzak**: <varsa — daha önce burada takılınan veya takılınması beklenen nokta>
**Son güncelleme**: <tarih>, Faz <N.M>

---
```

## Kurallar

- **Tek cümle.** "Faz 2'yi bitir" değil, "2.2'de II=4 hedefiyle ikinci pipeline turu deneniyor" gibi somut.
- **Dosya yolları gerçek olmalı** — "ilgili dosyalar" değil, çalışan komple yol.
- **Bilinen tuzak boşsa boş bırakılır**, uydurulmaz.
- **Her oturum sonunda güncellenir.** Güncellenmeyen SIRADAKİ, yanlış yönlendirir — hiç olmamasından kötüdür.
- Faz sonu kontrol listesinde (bkz. [CLAUDE.md](../CLAUDE.md)) bu satırın güncellendiği doğrulanır.

## Örnek

```markdown
## SIRADAKİ

**Hedef**: 2.2'de ilk sentez raporu alındı, II=9 çıktı; bankalama şeması 2/3 deneniyor.
**Dokunulacak dosyalar**: hls/src/statevector_kernel.cpp, hls/tb/testbench.cpp
**Bilinen tuzak**: pragma HLS ARRAY_PARTITION cyclic factor değişince testbench'te false-positive
geçiş görülüyor — sonucu csim değil sentez raporundan doğrula (bkz. alt dal 2.0, csim körlüğü).
**Son güncelleme**: 2026-10-14, Faz 2.2

---
```

Bu standart, ilk gerçek uygulama fazı (Faz 1) `tasks.md`'sini ürettiğinde uygulamaya konur.
