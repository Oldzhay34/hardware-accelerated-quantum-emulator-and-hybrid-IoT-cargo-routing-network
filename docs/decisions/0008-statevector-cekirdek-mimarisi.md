# ADR 0008 — Statevector çekirdek mimarisi: Q1.17 + yerinde + QAOA'ya özel

**Tarih**: 2026-09-15 · **Faz**: 2 · **Durum**: Kabul edildi (kullanıcı onayı, Anayasa Prensip I)

## Bağlam

Faz 2 spec'i bankalama şeması ve sayı formatı seçimlerini **bilinçli olarak boş bıraktı**;
Prensip I bu seçimlerin karşılaştırma tablosu + açık onay olmadan koda dökülmesini yasaklıyor.
Araştırma [docs/banking-research.md](../banking-research.md) ile yapıldı, tablolar
[specs/002/plan.md](../../specs/002-fpga-statevector-cekirdegi/plan.md) §Onay Kapısı'nda sunuldu.

Spec'in çerçevelediği ikilem şuydu:

> "16 kübitte ya **doğruluğu** (Q1.15 → fidelity riski) ya da **bankalama kolaylığını**
> (yerinde → SK-02'nin en zor hali) feda ediyorsun."

## Seçenekler

**Tablo A (bankalama/tamponlama)**: A1 naif+yerinde · A2 naif+ping-pong ·
A3 XOR+yerinde · A4 XOR+ping-pong · A5 iki geçişli devrik
**Tablo B (format)**: B1 Q1.11 … B4 Q1.17 … B7 float32
**NC-3 (genellik)**: C1 QAOA'ya özel · C2 genel kapı motoru

## Karar

**A1 + B4 + C1**: naif `cyclic` partition (F=16) + **yerinde (in-place)** + **Q1.17**
(`ap_fixed<18,1>`) + QAOA'ya özel çekirdek.

## Gerekçe

**İkilem aslında yoktu.** Üç bulgu onu ortadan kaldırdı:

1. **Q1.17 her iki kısıtı da karşılıyor** — fidelity 0,999917 (H eşiğini geçiyor, **ÖLÇÜLEN**)
   *ve* BRAM'in 36-bit kelimesine israfsız sığıyor. Spec'in "yalnızca Q1.15" varsayımı **bayt
   düzeyinde** hesaba dayanıyordu; blok düzeyinde hesap onu çürüttü: Q1.11–Q1.17 *hepsi* aynı
   64 bloğu kullanıyor, yani daralmanın hiçbir karşılığı yok.
2. **Bankalama şeması seçimi anlamsız** — üç şema (naif, XOR-2, XOR-tam) her tamponlama ve her
   `k` için **birebir aynı** verimi veriyor. XOR'un ödettiği pragma karmaşıklığının ölçülebilir
   karşılığı yok.
3. **Bağlayıcı kısıt bankalama değil, SC-002 (BRAM ≤ %85).** Ping-pong II'yi 1'e indiriyor ama
   %91,4 BRAM demek — spec'in kendi eşiğini aşıyor.

**Yerinde şemanın ping-pong'a tercih edilmesinin çekirdek gerekçesi tek cümle**: SC-003 zaten
II ≤ 4'e izin veriyor ve yerinde şema II=2 veriyor; yani ping-pong'un satın aldığı şey projenin
ölçütünde **zaten karşılanmış**, ödediği şey (SC-002 ihlali) karşılanmamış.

**C1'in gerekçesi**: tüm II aritmetiğinin geçerliliği buna bağlı. Aritmetiğin göremediği tek
gerçek başarısızlık kipi, HLS'in `ARRAY_PARTITION`'ı derleme zamanında çözememesi ve erişimleri
serileştirmesidir — ve bu yalnızca `k` çalışma zamanı değişkeniyken olur. C1'de karıştırıcı
`for k in 0..15` döngüsüdür, `k` derleme zamanı sabitidir; maliyet katmanı köşegendir, erişimi
sıralıdır. C2'de `k` runtime'a döner ve SK-02 tam güçte geri gelir.

## Sonuç

| Ölçüt | Değer | Tür |
|---|---:|---|
| BRAM | 64/140 blok = **%45,7** (SC-002 ≤%85 ✅) | HESAPLANAN |
| II | k=0–3 → 1, k=4–15 → **2** (SC-003 ≤4 ✅) | HESAPLANAN |
| Fidelity | **0,999917** (M ✅ H ✅) | **ÖLÇÜLEN** |
| Pay | 55 blok — faz tablosu + AXI tamponları sığar | HESAPLANAN |
| Tahmini hızlanma | ~24× (Aer C++ tabanına karşı, 100 MHz varsayımı) | HESAPLANAN |

Ek kararlar (aynı onayın parçası):
- **RZZ yerleşik köşegen kapı** olarak uygulanır, `CX–RZ–CX`'e ayrıştırılmaz → eşlemeli kapı
  sayısı p=2'de 384 → 32, **12× azalma** (**ÖLÇÜLEN**). SK-02 artık kapıların %13,8'ini etkiliyor.
- **Maliyet katmanı tek köşegen geçişe füzyonlanır** (köşegen çarpımı köşegendir, bedelsiz).
- Faz hesaplama stratejisi (tablo vs Gray-kod) **ertelendi** — H etiketli, sentez raporuna bağlı.
- Ping-pong **İ etiketli yükseltme** olarak saklandı: önce yerinde sentezlenir, gerçek BRAM
  okunur, sonra karar verilir.

### Bu kararın düzelttiği önceki hatalar

Prensip II gereği gizlenmiyor:

| Belge | Yazan | Düzeltme |
|---|---|---|
| [specs/002/spec.md](../../specs/002-fpga-statevector-cekirdegi/spec.md) | "ping-pong'a yalnızca Q1.15 ile para yetiyor" | Yanlış — Q1.11–Q1.17 hepsi aynı 64 bloğu kullanıyor |
| specs/002/spec.md | "float32 yerinde %81,3 🟡 sınırda" | Blok düzeyinde **%91,4** — sınırda değil, **başarısız** |
| [cut-plan.md](../../specs/000-kapsam-takvim/cut-plan.md) K-02 | merdivenin ilk iki basamağı | **İkisi de geçersiz** (ikisi de %91,4). Yeni ilk basamak 16+Q1.17-yerinde ve zaten hedefin altında |
| [banking-research.md](../banking-research.md) §6 | ping-pong'u M önermişti | SC-002 çakışması sonradan görüldü, **yerinde** olarak düzeltildi |

## Tekrar değerlendirilmeli mi?

**Evet, şu üç koşulda:**

1. **Sentez raporu BRAM'i tahminden belirgin ucuz gösterirse** → ping-pong (A2) yeniden açılır.
   Sıra bağlayıcıdır: önce A1 sentezlenir, gerçek sayı okunur.
2. **Sentez raporu II'yi tahminden kötü gösterirse** (II >> 2) → muhtemel neden `k`'nin derleme
   zamanı sabiti olmaması; `template <int K>` uygulaması denetlenir. Bu, aritmetiğin göremediği
   tek başarısızlık kipidir.
3. **Fmax 100 MHz'in belirgin altında çıkarsa** → tüm süre tahminleri yeniden hesaplanır (NC-4).

**Yeniden değerlendirilmeyecek**: XOR banka eşlemesi ve iki geçişli devrik. İkisi de ölçülebilir
karşılık vermeden karmaşıklık ekliyor; K-03'ün 3 denemelik bütçesi onlara harcanmaz.
