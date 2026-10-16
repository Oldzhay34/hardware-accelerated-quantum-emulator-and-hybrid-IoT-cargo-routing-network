# Kart seçimi ve donanım sınırları

| | |
|---|---|
| **Oluşturma** | 2026-10-16 · canlı belge |
| **Soru** | Neden ping-pong yok, neden tek kelebek birimi var, neden genlik çifti başına tek çevrimde (II = 1) işleyemiyoruz — ve *"neden Kria KV260 / daha büyük bir kart değil?"* |
| **Kaynak notu** | Kart seçimi için bir ADR yazılmamıştı. Seçim nedeni (bütçe) **proje sahibinin beyanıdır** (16 Eki). Teknik sayılar aşağıdaki etiketlerle kaynağına bağlıdır |
| **İlgili** | [neden-fpga.md](neden-fpga.md) (savunma), [ADR 0009](decisions/0009-paralellik-turu-kapatildi.md) (II tabanı), [memory-budget.md](memory-budget.md), [olculen-degerler.md](olculen-degerler.md) |

**Etiketler**: **[Ö]** ölçüldü / sentez–implementasyon raporu · **[H]** ölçülmüş
sayılardan aritmetik, **sentezlenmedi** · **[T]** tahmin · **[D]** üretici veri
sayfası, **doğrulanmalı** (değerler yaklaşık, bellekten yazıldı).

⛔ [H] ve [T] etiketli hiçbir sayı teze **sonuç** olarak yazılmaz (Anayasa
Prensip II); yalnız gerekçe ve gelecek çalışma tartışmasında, etiketiyle.

---

## 0. Kısa cevap

1. Kart **proje başında bütçeye göre** seçildi: PYNQ-Z2 (XC7Z020, ~4,9 Mb BRAM).
   Projenin bütün sınırları — 16 kübit, 5 şehir — bu bellekten türedi.
2. 16 kübitlik durum vektörü çipin BRAM'inin üçte ikisini alıyor. **İkinci
   kopyası (ping-pong) sığmıyor** — en dar kullanılabilir genişlikte bile.
3. Ping-pong olmadan çift başına tek çevrim (II = 1) ancak çakışmasız
   bankalamayla olur; kübit indeksi çalışma anında seçildiği için HLS bunu
   kanıtlayamıyor. **Ölçülen taban II = 2** — sınır hesap değil, **bellek
   portu**. Birden çok kelebek birimi de aynı nedenle kurulamıyor.
4. Daha büyük bir kart (KV260, Kintex-7, ZCU102) bu sınırları gevşetir ve
   **hızı** artırır; **problem boyutunu artırmaz** (5 şehirden sonraki adım
   25 kübit, hiçbir tek cihaza sığmaz) ve kaba kuvvetle aradaki yapısal
   uçurumu kapatmaz.

---

## 1. Kart nasıl seçildi

- Proje başında, **bütçeye göre**: PYNQ-Z2 (TUL, Zynq-7000 XC7Z020-1CLG400).
  Kart 15 Eylül'de teslim alındı ([risk-register DT-00](risk-register.md)).
- 📝 *Doldurulacak (savunmayı güçlendirir)*: satın alma tarihi ve fiyatı;
  değerlendirilen alternatiflerin (ör. KV260) o tarihteki fiyatı ve temin
  süresi. Fiyat **tahminle yazılmaz**.
- Seçimin sonucu: Anayasa Prensip III ("statevector çip içinde, üst sınır
  16 kübit") **bu kartın belleğinden** türetildi; 5 şehir 16 kübitten seçildi,
  tersi değil ([neden-fpga §0](neden-fpga.md)). Aşağıdaki her tasarım kararı
  bu bütçeye karşı verildi.

---

## 2. Ortak zemin: bir kapı nasıl işleniyor

16 kübitte 65.536 genlik var. k. kübite bir kapı, birbirinden 2^k uzaklıktaki
genlikleri ikişer ikişer günceller (**kelebek**):

```
a[i]  ──┐       ┌──> a'[i]        i ve j = i XOR 2^k   ->   32.768 çift / kapı
        ├─ 2×2 ─┤                 her çift: 2 okuma + 2 yazma = 4 bellek erişimi
a[j]  ──┘       └──> a'[j]        bir BRAM bloğu: 2 port
```

Literatürdeki *"tek çevrimde işleme"* **bir çiftin** bir çevrimde okunup
yazılmasıdır (II = 1) — 16 kübitin bir çevrimde işlenmesi değil. II = 1'de
bile bir kapı 32.768 çevrim sürer.

---

## 3. Neden ping-pong sığmadı

Ping-pong: A kopyasından oku, B kopyasına yaz; her kopya kendi 2 portunu
kullanır → çift başına 4 erişim bir çevrime sığar. Bedeli: **durum vektörünün
iki kopyası**.

| | BRAM_18K | Bütçe 280 içinde | |
|---|---:|---:|---|
| Durum vektörü, Q1.17 (re/im ayrı, 4 bellek × 32.768 × 18 bit) | 144 | | [Ö] |
| Tasarımın tamamı (bugün) | **187** | **%66,8** | [Ö] |
| Ping-pong, Q1.17: yalnız iki kopya | 288 | **%103** — tek başına aşıyor | [H] |
| Ping-pong, 16 bit (çekirdekte H eşiğini geçen en dar genişlik, 0,999656 [Ö, 6C]): 2 × 128 + öteki bellekler ~43 | ~299 | **~%107** | [H] |

**Sonuç**: XC7Z020'de 16 kübitte, H eşiğini (fidelity ≥ 0,999) geçen **hiçbir
genişlikte** ping-pong sığmıyor. Bu yüzden durum vektörü **yerinde**
güncelleniyor — okuma ve yazma aynı diziye.

---

## 4. Neden çift başına tek çevrim (II = 1) yapamadık

Yerinde güncellemede tek dizi, 2 port, çift başına 4 erişim:

| Bellek ayarı | Çevrimde erişim | II | |
|---|---:|---:|---|
| `RAM_2P` (basit çift port: 1 okuma + 1 yazma) | 2 | 3 | [Ö] |
| **`RAM_T2P`** (gerçek çift port) — bugünkü tasarım | 2 | **2** | [Ö] |
| II = 1 için gereken | **4** | — | |

`RAM_T2P` tek kelimelik bir değişiklikle gecikmeyi −%22,6 düşürdü, dört
kaynakta sıfır bedelle ([ADR 0009](decisions/0009-paralellik-turu-kapatildi.md)).
Daha aşağısı için iki yol var: ping-pong (§3 — sığmıyor) ya da çakışmasız
bankalama (§5 — kanıtlanamıyor).

**Bedeli** [H]: `mixer_loop` her kübitte 65.545 çevrim (32.768 çift × 2 + boru
hattı) [Ö]; p = 2'de 2.097.440 / 3.728.217 çevrim = gecikmenin **%56**'sı. II = 1
bunun yaklaşık yarısını, ~1,05 M çevrimi (**~%28**) kazandırırdı — sentezlenmedi.

---

## 5. Neden birden çok kelebek birimi koyamadık

P paralel birim çevrim başına **4P** erişim ister → durum vektörü bankalara
bölünmeli ve aynı çevrimde okunan çiftlerin **hep farklı bankalara** düştüğü
**kanıtlanmalı**.

- Klasik bankalama (alt bitlere göre, `cyclic`) bunu ancak **k derleme anında
  biliniyorsa** kanıtlar. Bizde 16 kübiti **tek ortak birim** işliyor ve k
  çalışma anında seçiliyor. Bu bilinçli bir seçimdi: ortak birim **2.409 LUT**,
  kübit başına özelleştirilmiş sürüm **45.114 LUT** — çipin %85'i [Ö,
  [olculen-degerler §8 #1](olculen-degerler.md)].
- Ölçüldü: `cyclic` 2 / 4 / 8 bankada II **değişmedi** — HLS çakışmayı
  dışlayamıyor ve en kötü durumu varsayıyor [Ö, ADR 0009].
- Fiziksel port sayısı sorun değil — durum vektörü zaten 144 bloğa yayılmış.
  Sorun **erişim deseninin kanıtlanamaması**.
- Çip yönlendirme açısından da dolu: tablo döngülerini boru hattına alan
  varyant gecikmeyi **−%28,5** düşürüyordu ama zamanlama marjı +0,878'den
  **+0,122 ns**'ye indi (yönlendirme tıkanıklığı) ve **reddedildi** [Ö,
  [olculen-degerler §9](olculen-degerler.md)].

**Denenmemiş yol (bu çipte)**: bankayı alt bitlere göre değil, indeks
bitlerinin **paritesine** göre seçmek. i ile i XOR 2^k tam bir bitte farklı →
pariteleri **her k için** farklı → çiftin iki üyesi her zaman ayrı bankada;
2 banka × 2 port = çevrimde 4 erişim, **bellek büyümeden** II = 1. HLS bunu
kendi bulmaz (indeksleme elle yazılmalı). **Ölçülmedi**; ADR 0009'u yeniden
açmak ve yeni bitstream'le bütün kart ölçümlerini (doğrulama, gecikme, enerji)
yinelemek demek — takvim kararı.

---

## 6. Daha büyük kartlarda ne değişirdi

| Çip (kart) | BRAM | URAM | DSP | LUT | Sert işlemci | |
|---|---:|---:|---:|---:|---|---|
| **XC7Z020 (PYNQ-Z2)** — bu proje | 140 × 36 Kb ≈ 4,9 Mb (280 BRAM_18K) | — | 220 | 53.200 | 2 × Cortex-A9 | [D] DS190 |
| XCK26 (Kria **KV260**) | 144 ≈ 5,1 Mb | 64 × 288 Kb ≈ 18 Mb | 1.248 | 117.120 | 4 × A53 + 2 × R5F | [D] DS987 |
| XC7K325T (**Kintex-7**, KC705) | 445 ≈ 16 Mb | — | 840 | 203.800 | **yok** | [D] DS180 |
| XCZU9EG (**ZCU102**) | 912 ≈ 32 Mb | — | 2.520 | 274.080 | 4 × A53 + 2 × R5F | [D] DS891 |

Ping-pong (bizim ölçülmüş 288 BRAM_18K'lık iki kopya) ne kadar yer tutardı [H]:

| Kart | Ping-pong | Ne açılır [T] | Ne kaybedilir / değişmez |
|---|---|---|---|
| **KV260** | BRAM'in **%100**'ü → durum vektörü **URAM'a** taşınmalı: iki genlik bir 72 bitlik kelimeye paketlenirse 2 × 8 = 16 URAM (%25), paketlenmezse 64 URAM'in tamamı (tasarım işi) | II = 1 ve birkaç kelebek birimi (DSP 5,7×, LUT 2,2×); A53'ler konak tarafı kodlamayı hızlandırır. KV260 için PYNQ desteği var (Kria-PYNQ) | BRAM neredeyse **aynı** — kazanç bellekten değil URAM'dan. AMARETTO 16 kübiti KV260'ta göstermiş (§7) |
| **Kintex-7** | BRAM'in ~%32'si | Aynı 7-serisi BRAM mimarisi → HLS pragmaları neredeyse olduğu gibi taşınır; ping-pong + çoklu birim | **Sert işlemci yok**: PS↔PL kıyası (2,30×) ve "Linux'lu tek kutu / G/Ç göbeği" mimarisi ([sistem-mimarisi](sistem-mimarisi.md)) kurulamaz; konak PCIe ya da MicroBlaze gerekir |
| **ZCU102** | BRAM'in ~%16'sı | II = 1, çok sayıda birim, daha yüksek saat (UltraScale+); 17–18 kübit sığar (FQsun ZCU102'de 17–18 kübit bildirmiş). Kartta ray başına akım ölçerler var → PL'nin gücü ayrı ölçülebilir (UG1182'den doğrulanmalı) | Geliştirme kartının boştaki gücü PYNQ-Z2'nin (1,45 W, 5 V girişi [Ö]) **kat kat** üstünde [T] → "5 W zarfı" kart düzeyinde kaybolur |

ZCU102 için kaba gecikme senaryoları [T] (çapa: bugünkü 36,6 ms, dizüstü CPU
tek iş parçacığı 3,3 ms, GPU 1,0 ms [Ö]):

| Senaryo | Çekirdek | Yorum |
|---|---:|---|
| Kodu taşı, ~200 MHz + ping-pong | ~10–18 ms | CPU hâlâ ~3–5× hızlı |
| + ~8 kelebek birimi + paralel tablolar | ~1–3 ms | tek iş parçacıklı CPU ile eşit ↔ FPGA ~3× hızlı |
| Araştırma düzeyinde tasarım (≥ 32 birim) | ~0,3–1 ms | GPU ile **başabaş** civarı |

Uçtan uca gecikmede bugün çağrının ~13 ms'si ARM'daki Python kodlaması + 1.095
yazma [Ö]; çekirdek 1 ms'ye inince **baskın kalem bu olur** — kodlamanın da
C'ye/DMA'ya taşınması gerekir. Belirlenimcilik (p99/medyan ≈ 1) her kartta
korunur.

**Hiçbir kartta değişmeyen**:
- **Problem boyutu**: tek-sıcak TSP'de 16 kübitten (N = 5) sonraki adım
  **25 kübit** (N = 6) → 33,5 M genlik, ~151 MB — tek cihazın çip içi belleğine
  sığmaz. Daha büyük kart **daha hızlı 5 şehir** demektir, daha çok şehir değil.
- **Kaba kuvvet** N = 5'i 43,2 µs'de kesin çözüyor [Ö] — en iyi senaryoda bile
  emülasyon mertebe olarak yavaş kalır.
- Ölçülmeyen iki rakip FPGA'nın aleyhine: çok iş parçacıklı CPU ve gece toplu
  işinde bağımsız alt problemleri **toplu (batch)** koşan GPU.

---

## 7. Savunma: *"Neden Kria KV260'ı seçmedin?"*

**Cevabın sırası**:

1. **Seçim nedeni — bütçe.** Kart proje başında bütçeye göre seçildi. ⚠️ Jüri
   KV260'ın fiyatını PYNQ-Z2'ye yakın biliyor olabilir; bu yüzden cevap **yalnız
   bütçeye dayanmamalı** — §1'deki fiyat ve temin bilgisi doldurulmalı, ve 2–3
   eklenmeli.
2. **KV260'ın farkı BRAM değil, URAM.** BRAM neredeyse aynı (5,1 Mb ↔ 4,9 Mb
   [D]). 16 kübit iki kartta da sığar — AMARETTO bunu KV260'ta göstermiş.
   KV260'ın açacağı şey **hız** (URAM'da ping-pong, birkaç kelebek birimi),
   **kübit sayısı değil**; TSP'de 16'dan sonraki adım zaten 25.
3. **Sonradan görülen değer — seçimin nedeni değil.** Bu proje tasarım
   uzayının **en küçük ucunu** ölçtü: AMARETTO'nun "düşük segment" dediği
   KV260'ın da altındaki sınıf. Bellek-portu bağlı II tabanı tam olarak bu
   kısıtta ortaya çıkan, ölçülmüş bir bulgu; aynı kısıt PS↔PL'nin **aynı
   SoC'de** kıyasına (2,30×) ve 1,45 W'lık kart zarfına da imkân verdi.
4. **Bedeli açıkça**: II = 2, tek kelebek birimi; dizüstü CPU 11,2×, GPU 36,7×
   hızlı [Ö].

**Kullanılmayacak argümanlar**:

| ❌ Argüman | Neden çöker |
|---|---|
| *"KV260 16 kübiti sığdıramaz"* | Yanlış — AMARETTO KV260'ta 16 kübit emüle etti |
| *"PYNQ-Z2 bu iş için daha uygun"* | Hiçbir eksende değil; KV260'ta her kaynak eşit ya da fazla |
| *"En küçük kartı bilerek seçtik"* | Seçimin nedeni bütçeydi; "küçük cihaz ucunu karakterize ettik" bir **sonuçtur**, gerekçe olarak geriye yazılmaz |
| *"Büyük kartla daha çok şehir çözerdik"* | Hayır — 25 kübit hiçbir tek cihazın çip içi belleğine sığmaz |

---

## 8. Tez için — "Gelecek çalışma" paragrafı (taslak, rakamsız)

> Bu çalışma, kuantum devre emülasyonunun tasarım uzayını küçük bir SoC-FPGA
> ucunda karakterize etmektedir. Ölçülen bellek-portu bağlı başlatma aralığı
> tabanı, daha büyük çip içi belleğe sahip cihazlarda iki yolun açılacağını
> öngörür: durum vektörünün iki kopyasıyla (ping-pong) genlik çifti başına tek
> çevrim, ve çakışmasız bankalamayla birden çok kelebek biriminin paralel
> çalışması. Aynı çipte de denenmemiş bir yol vardır: indeks paritesine göre
> bankalama, kübit indeksi çalışma anında seçilse bile çiftin iki üyesini
> ayrı bankalara düşürür. Bu yolların kazancı ölçülmemiştir ve hiçbiri
> problem boyutunu değiştirmez: tek-sıcak TSP kodlamasında beş şehirden
> sonraki boyut 25 kübit gerektirir ve tek bir cihazın çip içi belleğine
> sığmaz. Daha büyük bir kartın asıl yanıtlayacağı soru, emülatörün aynı
> problemde tek ve çok iş parçacıklı CPU ile ve toplu koşan GPU ile gecikme,
> belirlenimcilik ve koşum başına enerji eksenlerinde nerede durduğudur; bu
> ölçüm, programlanabilir mantığın gücünü ayrıca ölçmeye izin veren bir kartta
> yapılmalıdır.

---

## Kaynaklar

- C. Conti, D. Volpe, M. Graziano, M. Zamboni, G. Turvani, *AMARETTO: Enabling
  Efficient Quantum Algorithm Emulation on Low-Tier FPGAs*, IEEE ICECS 2024 —
  [arXiv:2411.09320](https://arxiv.org/abs/2411.09320). KV260'ta 16 kübit.
  ⚠️ "BRAM'in ~%100'ü" ifadesi makalenin kaynak tablosundan doğrulanmalı.
- T. H. Vu ve diğ., *FQsun: A Configurable Wave Function-Based Quantum Emulator
  for Power-Efficient Quantum Simulations*, IEEE Access 2025 —
  [arXiv:2411.04471](https://arxiv.org/abs/2411.04471). ZCU102, çoklu
  hassasiyet; karşılaştırma tablosunda 17–18 kübit.
- AMD/Xilinx veri sayfaları [D]: DS190 (Zynq-7000), DS987 (Kria K26 SOM),
  DS180 (7-serisi), DS891 (Zynq UltraScale+ MPSoC); kart kılavuzları UG1089
  (KV260), UG810 (KC705), UG1182 (ZCU102).
- Bu depo: [ADR 0009](decisions/0009-paralellik-turu-kapatildi.md),
  [memory-budget.md](memory-budget.md),
  [olculen-degerler §2–§9](olculen-degerler.md),
  [hatalar #10](hatalar-ve-duzeltmeler.md) (BRAM eşlemesi),
  [neden-fpga.md](neden-fpga.md).
