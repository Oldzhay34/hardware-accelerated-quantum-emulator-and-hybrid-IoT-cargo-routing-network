# Kart Gecikme Ölçüm Protokolü (US2)

| | |
|---|---|
| **Durum** | 🔒 **DONDURULDU — 2026-09-27**, kullanıcı onayıyla, **ilk gecikme ölçümünden önce** |
| **Sürüm** | **v1.0** — ölçüm kodu her çıktıya `kart-olcum-protokolu v1.0` yazar |
| **Onaylanan metin** | commit `201475a`, git içerik özeti `fc8c570da02a8285b771d0ea8316878af1552990` (`git rev-parse 201475a:docs/measurements/kart-olcum-protokolu.md`). Dondurmadan sonra yalnız bu üç durum satırı değişti: `git diff 201475a -- <bu dosya>` bunu gösterir |
| **Görev** | T039 (bu belge) → T040–T044 (ölçüm), T045 (HLS kıyası), T045b'nin FPGA tarafı |
| **Dayanak** | FR-007, FR-008, FR-011, FR-013, SC-004, SC-009 · [research.md §R4](../../specs/003-zynq-ps-kartta-kosum/research.md) · [data-model.md §2](../../specs/003-zynq-ps-kartta-kosum/data-model.md) |

**Kural (FR-011, SC-009)**: Bu protokol ilk gecikme ölçümünden **önce** onaylanıp
dondurulur. Dondurulduktan sonra sonuca bakıp değiştirilemez; değişiklik
gerekirse yeni sürüm açılır, gerekçesi yazılır ve eski sürümle alınan
sonuçlar eski sürümün etiketini taşır (§10).

---

## 1. Ne ölçülüyor

Kartta, `qir_kernel`'in bir QAOA devresini tamamlama süresi — üç ayrı kapsamda
(FR-007). Soru: *sentez tahmini (p=2 için 37,28 ms) kartta tutuyor mu, ve
çekirdeği PS'ten PL'e taşımak gerçekte neye değer?*

Ölçülmeyen: enerji (US3, ayrı protokol), CPU/GPU tarafı (Faz 2 §18/§22 ve
Phase 6B'de).

---

## 2. Önceden bilinenler — ön kayıt beyanı

Protokol aşağıdakiler **bilinerek** yazıldı. Hiçbiri ölçüm serisi değildir;
yine de sonuçla karşılaştırmada önyargı kaynağı olabilecekleri için beyan
edilirler.

| Bilinen | Değer | Kaynak |
|---|---:|---|
| HLS çevrim modeli, p=2 | 3.728.217 çevrim = **37,282 ms** @100 MHz | [faz2-sentez.md §15](faz2-sentez.md) |
| HLS çevrim modeli, p=1 | 2.081.110 çevrim = **20,811 ms** | aynı |
| Model ayrıştırması | init 65.538 + p × 1.647.107 + beklenen değer 368.465 | aynı |
| ARM Cortex-A9 (PS), aynı çekirdek, float, p=2 | **84,13 ms** medyan (n=30, IQR 0,210) | [ps-pl-hizlanma](ps-pl-hizlanma_20260921_c504294.json) |
| ⚠️ **Yan üründe görülen** `t_cekirdek`, p=2 | **36,52–36,55 ms** (20 çağrı; modelin ~%2 altı) | G3 koşumu, 27 Eyl ([kart-dogrulama p2](kart-dogrulama_20260927_67165a7_n16_p2.json)) |
| ⚠️ **Yan üründe görülen** `t_cekirdek`, p=1 | **20,33–20,36 ms** (20 çağrı; modelin ~%2 altı) | aynı gün ([kart-dogrulama p1](kart-dogrulama_20260927_67165a7_n16_p1.json)) |
| ⚠️ **Yan üründe görülen** `t_yazma` | ~**1,4 ms** (1.095 yazma, tek çağrı) | aynı |

⚠️ Son üç satır **protokol yazılmadan önce görüldü**: G3 doğrulama kaydı her
çağrının süresini de tutuyordu. Isınmasız, yoklamayla alınmış, izdüşüm kısa
yolunu da içeren değerlerdir ve **hiçbir yere sonuç olarak yazılmaz**. Tekrar
sayısı, dışlama ve istatistik kuralları bunlara göre ayarlanmadı — ama §3'teki
B1 ve B2 bu değerler **bilinerek** yazıldı ve bağımsız tahmin sayılmaz.

---

## 3. Ön kayıtlı beklentiler (ölçümden ÖNCE)

Sonuç geldiğinde bunlarla karşılaştırılır; tutmazsa **bulgudur**, gizlenmez.

| # | Beklenti | Gerekçe |
|---|---|---|
| B1 ⚠️ | 300 sn'lik serinin `T_cekirdek` medyanı, §2'deki yan ürün değerlerinden **%0,5'ten az** farklı | ⚠️ **Bağımsız tahmin değil** — §2 bilinerek yazıldı. Sınanan şey, 20 çağrılık gözlemin ısınmalı, uzun, tam çağrılı seride de tutup tutmadığı |
| B2 ⚠️ | Ölçülen `T_cekirdek` HLS modelinin **~%2 altında** kalır, iki p'de de | ⚠️ **Bağımsız tahmin değil** (§2). HLS raporu `max` gecikmedir. Sebep T045'te **çevrim düzeyinde** açıklanmalı; açıklanamazsa açıklanamadığı yazılır |
| B3 ⚠️ | `T_cekirdek` yayılımı (IQR) **< 0,1 ms** | Çevrim sayısı sabit; yayılımı yalnız yoklama ve Linux zamanlaması üretir. ⚠️ **Kısmen bilinerek**: §2'deki 20 çağrı 0,03 ms içinde kaldı |
| B4 | Kuyruk (p99, maks) medyandan **belirgin uzun** olabilir | PS'te Linux koşuyor; kesme ve zamanlayıcı yoklama döngüsünü geciktirebilir |
| B5 | Termal plato **yok** — ilk ve son pencere aynı | PL saati sabit 100 MHz, PS 650 MHz'de kısılma beklenmiyor (dizüstündeki turbo/plato davranışının karşılığı yok) |
| B6 ⚠️ | Girdi `cost` vektörü süreyi **değiştirmez** | Sabit döngü sınırları; §6 kontrol serisi bunu sınar. ⚠️ **Kısmen bilinerek**: G3'teki 20 farklı vektör aynı süreyi verdi |
| B7 | `T_uctan_uca`'yı **Python kodlaması** domine eder | 816 faz word'ü + ölçekleme ARM'da Python ile; büyüklüğü için tahmin **yok**. Bu kapsam hiç görülmedi — **bağımsız** |

**Bağımsız beklentiler**: B4, B5, B7. Diğerleri §2'deki yan ürün gözlemiyle
şekillendi ve raporda öyle etiketlenir.

---

## 4. Deney koşulları — her seride kaydedilir

| Koşul | Değer / kural |
|---|---|
| Bitstream | `qir_20260920_d350605.bit`, sha256 `d4ca4522…0f6f` — seri başında kartta yeniden hesaplanır |
| FCLK0 | **100,000 MHz**, seri **başında ve sonunda** okunur (`board.py` ayarlar + doğrular). Sonda sapma → seri geçersiz |
| Besleme | JP5 = `USB` (27 Eyl teyidi). Düzen her seride kaydedilir; değişirse ayrı seri |
| Kart yükü | Seri öncesi ve sonrası `uptime` yük ortalaması kaydedilir. Ölçüm sırasında kartta başka iş yok; SSH oturumu boşta bekler |
| Ağ | Zamanlanan yolda **ağ yok** — ölçüm tamamen kartta koşar, sonuç dosyaya yazılır |
| Sıcaklık | XADC çip sıcaklığı her 10 sn'lik pencere sınırında okunur (zamanlanan yolun **dışında**) |
| Zaman damgası | Dizüstü saati (kartın saati NTP'siz ve geride) |
| Yazılım | PYNQ 2.5, Python 3.6.5, `sudo`; kod sürümü = ölçümü alan commit |

---

## 5. Üç kapsam (FR-007, R4)

Zamanlayıcı: `time.perf_counter()` (ARM A9'da ~µs çözünürlük; 37 ms'de
bağıl hata ~%0,003). Ayrı zamanlayıcı IP'si yok (R4).

| Kapsam | Başlar | Biter | İçerir |
|---|---|---|---|
| `T_cekirdek` | `ap_start` yazımından hemen önce | `ap_done` biti **görüldüğünde** | çekirdek + yoklama gecikmesi |
| `T_yazma` | ilk register yazımı | 1.095. yazım | `cost` 272 + `phases` 816 + `cos_beta` 3 + `sin_beta` 3 + `p` 1 |
| `T_uctan_uca` | ham problem (`h`, `J`, `γ`, `β`) elde | sonuç float olarak okunmuş | `kosum_kodla` (kodlama + ölçekleme) + yazma + koşum + okuma |

⛔ **Her koşum TAM çağrıdır.** İzdüşüm kısa yolu (yalnız `cost`, 272 yazma)
gecikme ölçümünde **kullanılmaz** — `T_yazma` olduğundan küçük çıkar.

**Yoklama hatası (T041)**: `ap_done` Python'dan yoklanır; bu, `T_cekirdek`'e
**üst taraftan** en fazla bir yoklama periyodu `δ` ekler. `δ` her seriden önce
ayrıca ölçülür (AP_CTRL arka arkaya 10.000 kez okunur, ortalama okuma süresi)
ve seriyle birlikte raporlanır. Rapor `T_cekirdek`'i `δ` ile birlikte verir.

---

## 6. Seriler

| Seri | p | `cost` | Süre | Amaç |
|---|---|---|---|---|
| **A** | 2 | referans problem, kodlayıcıyla ölçekli | **300 sn** | manşet ölçüm |
| **B** | 1 | aynı | **300 sn** | p'ye göre ölçekleme (SC-001 iki p ister) |
| **K** | 2 | izdüşüm vektörü 0 (tohum 42) | ≥ 30 koşum | kontrol: süre girdiden bağımsız mı (B6) |

**Neden süreye göre (sabit tekrar yerine)**: Faz 2'de CPU tabanı `TEKRAR = 15`
ile ölçülüp yalnız turbo penceresini yakalamıştı ([hatalar-ve-duzeltmeler.md
#4](../hatalar-ve-duzeltmeler.md)). Aynı yöntem kartta da kullanılır ki iki
taraf karşılaştırılabilir olsun ve plato iddiası (B5) veriyle sınansın. 300 sn
≈ 7.500 koşum; seri başına ~5 dk.

**Isınma**: her serinin ilk **3** koşumu atılır (T045b ARM ölçümüyle aynı).
Bu sayı ölçümden önce sabitlenmiştir.

**Doğruluk koşulu**: her koşumun sonucu (IEEE-754 bit deseni) o girdinin
C-sim değeriyle karşılaştırılır. **Tek bir sapma seriyi geçersiz kılar** —
doğrulanmamış bir hesabın hızı ölçülmez. C-sim değerleri seriden önce
`hls/tb/izdusum_ref.cpp` ile üretilir.

---

## 7. Dışlama kuralları

| Durum | Karar |
|---|---|
| Isınma koşumları (ilk 3) | atılır — önceden sabit |
| `ap_done` 5 sn içinde gelmedi (madde A-4) | koşum `gecerli=false`, seriye **girmez**, sayısı raporlanır |
| Sonuç bitleri C-sim'den farklı | **seri geçersiz**, ölçüm durur (§6) |
| FCLK seri sonunda sapmış | **seri geçersiz** |
| Süresi uzun ya da kısa görünen koşum | ⛔ **ATILMAZ.** Zaman değerine bakarak aykırı değer ayıklanmaz; kuyruk p95/p99/maks ile raporlanır |

---

## 8. İstatistik (T043)

Her kapsam için ayrı bir `OlcumSerisi` (data-model §2):

- **medyan** ve **IQR** (p25–p75) birlikte — manşet
- min, maks, p95, p99, jitter (maks − min)
- `kosum_sayisi < 10` → seri **üretilmez, hata verir** (SC-004)
- Tek koşum rakamı hiçbir yere yazılmaz

**Plato (T042)**: seri 10 sn'lik pencerelere bölünür; her pencerenin medyanı
ve sıcaklığı kaydedilir. İlk 50 koşum ile son 60 sn ayrı raporlanır.
**Plato oturdu** ⇔ son 6 pencere medyanının hepsi, bu 6'nın ortalamasının
**±%0,5**'i içinde. Oturmadıysa oturmadığı yazılır; seri uzatılmaz.

---

## 9. Karşılaştırma kuralları (T045, T045b)

- **HLS kıyası (T045)**: `T_cekirdek` medyanı × 100 MHz = ölçülen çevrim;
  model çevrimiyle farkı yüzde olarak, `δ` ile birlikte verilir. Fark,
  işareti ne olursa olsun kaydedilir; nedeni araştırılır, bulunamazsa
  bulunamadığı yazılır (FR-014).
- **PS↔PL (T045b)**: FPGA `T_cekirdek` (seri A) ile ARM float ölçümü
  (84,13 ms) karşılaştırılır; ikisi de **yalnız hesap**. Fark: ARM ölçümü
  C++ içinden, FPGA ölçümü Python yoklamasıyla alındı — FPGA tarafı `δ`
  kadar kötümser. `2,26×` bu ölçümle **yeniden hesaplanır** ve eski değerin
  yerine geçer.
- `T_yazma` ve `T_uctan_uca`'nın ARM ve CPU tarafında **karşılığı yoktur**
  (orada veri zaten bellekte); ayrı raporlanır, hızlanma hesabına girmez.

---

## 10. Çıktı ve sürüm

- `docs/measurements/kart-gecikme_<tarih>_<git-hash>_n16_p{1,2}.json` —
  her kapsam için `OlcumSerisi` + ham koşumlar (sıra, üç süre, bit deseni,
  yoklama sayısı), `protokol_surumu`, §4'teki koşullar, `δ`, pencere
  medyanları ve sıcaklıklar
- Seri K aynı dosyada `kontrol` alanı olarak
- **Dondurma**: onaydan sonra bu tablo `Durum: 🔒 DONDURULDU`, `Sürüm: v1.0`,
  tarih ve dondurma commit'iyle güncellenir. Ölçüm kodu (`measure_latency.py`)
  bu sürüm dizesini her çıktıya yazar
- **Değişiklik**: yeni sürüm (v1.1 …) açılır; gerekçe ve *"sonuç görüldükten
  sonra mı"* sorusunun cevabı yazılır
