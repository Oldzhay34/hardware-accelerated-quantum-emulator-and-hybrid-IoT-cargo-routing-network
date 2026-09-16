# ADR 0009 — Paralellik turu kapatıldı: II tabanı bankalama değil, bellek portu

**Tarih**: 2026-09-16 · **Faz**: 2 · **Durum**: Kabul edildi (kullanıcı onayı, Anayasa Prensip I)

## Bağlam

Tasarım çipe sığdıktan ve zamanlamayı tutturduktan sonra ([ADR 0008](0008-statevector-cekirdek-mimarisi.md),
[faz2-sentez.md](../measurements/faz2-sentez.md) §1–§12) geriye tek bir optimizasyon
başlığı kalmıştı: **paralellik**. Plan şuydu — "kalan LUT payını çevrim başına
birden fazla genlik işlemeye yatır".

İki şey bu planı sorgulanır hâle getirdi:

1. Tur 16, LUT payını %37'den **%16**'ya düşürdü. Yatırılacak pay büyük ölçüde
   harcanmıştı.
2. Gecikme dağılımı ölçüldüğünde en büyük kalem beklenen yerde değildi:
   `mixer_loop` **%67,9**, maliyet tabloları %23,0. `apply_cost_layer`'ın
   içinde asıl genlik döngüsü yalnızca **%11**; kalan %89 tablo kurmak.

Ayrıca SK-02 (bankalama riski) baştan beri şu varsayım üzerine kuruluydu:
*2^k çakışması bankalama ile çözülür.* Bu varsayım hiç sınanmamıştı.

Anayasa Prensip I bu kararın karşılaştırma tablosu + açık onay olmadan koda
dökülmesini yasaklıyor. Prensip II ise seçimin tahminle değil **ölçümle**
yapılmasını gerektiriyor — ve bu fazda bir kez zaten pahalıya mal olmuştu:
bankalama araştırması, toplam işin **%0,4'ünü** optimize etmişti.

## Seçenekler

Dokuz konfigürasyon sentezlendi (kaynak ağacı her denemeden sonra geri alındı).
Hepsinde zamanlama 7,195 ns ve BRAM %66 sabit kaldı:

| # | Konfigürasyon | Gecikme | FF | LUT | rx II |
|---|---|---:|---:|---:|:---:|
| 0 | Tur 16 (mevcut) | 6.948.095 | %46 | %84 | 3 |
| 1–2 | `cyclic factor` 4 / 8 | 6.948.095 | %47/49 | %86/90 | 3 |
| **3** | **`RAM_T2P`** | **5.375.327** | %46 | **%84** | **2** |
| 4–5 | `RAM_T2P` + `cyclic` 4/8 | 5.375.327 | %47/49 | %86/90 | 2 |
| 6 | + tüm tablolar `II=4` | 3.780.845 | %122 | **%182** | 2 |
| 7 | + yalnız `tablo_yuksek II=4` | 4.333.700 | %108 | **%166** | 2 |
| 8 | + `tablo_yuksek UNROLL 2` | 5.378.015 | %71 | **%123** | 2 |
| 9 | + tablo içleri `UNROLL` | 10.212.635 | %26 | %53 | 2 |
| 10 | `RAM_T2P` + Tur 16 geri alınmış | 8.228.447 | %32 | %63 | 2 |

## Karar

**#3 uygulandı ve paralellik arama turu kapatıldı.**

```diff
-#pragma HLS BIND_STORAGE variable = sv type = RAM_2P  impl = BRAM
+#pragma HLS BIND_STORAGE variable = sv type = RAM_T2P impl = BRAM
```

## Gerekçe

**Kazanan paralellik değil, port düzeltmesiydi.** `RAM_2P` *basit* çift porttur
— bir okuma + bir yazma. Yerinde kelebek her çift için 2 okuma + 2 yazma ister;
HLS bu yüzden II=3'e razı olmuştu. `RAM_T2P` *gerçek* çift porttur: 4 erişim /
2 port = **II=2**. 7-serisi BRAM bunu donanımda zaten destekliyor, dolayısıyla
BRAM sayısı artmıyor. −%22,6 gecikme, **dört kaynakta da sıfır bedel**.

**Aranan paralellik satın alınamaz olduğu için kapatıldı** — üçü de ölçümle:

- *Banka sayısı işe yaramıyor* (#1, #2, #4, #5). `k` çalışma zamanı değişkeni
  olduğu için HLS erişimin hangi bankaya düştüğünü **kanıtlayamıyor** ve kaç
  banka olursa olsun en kötü durumu varsayıyor. Bu, SK-02'nin varsayımını
  doğrudan yanlışlar: sınır bankalama değildi.
- *II=1 BRAM'e sığmıyor.* Dizi başına 4 port gerekir; ping-pong `sv`'yi
  144 → 288 BRAM yapar, toplam 187/280 zaten dolu (%91,4, SC-002 ihlali).
- ⚠️ **[2026-09-16'da YANLIŞLANDI — aşağıdaki güncellemeye bak]** *Tablolar
  LUT'a sığmıyor* (#6, #7, #8). 256'lık dış döngüyü boru hattına
  almak iç döngüleri açmaya **zorluyor** (~100 toplayıcı). #6'nın vaat ettiği
  1,6M çevrim gerçek ama bedeli LUT %182.

**Prensip II gereği** hiçbiri tahminle elenmedi; dokuzu da sentezlendi.

## Sonuç

- `hls/src/qir_kernel.cpp:155` — tek kelime değişti.
- Gecikme: **p=2 için 3.728.217 çevrim = 37,3 ms** @100 MHz (p=3 max
  5.375.324 = 53,8 ms). Kaynaklar: BRAM %66, DSP %16, FF %46, LUT %84.
  Zamanlama 7,195 ns.
- SK-02 ve SK-03 kapandı ([risk-register.md](../risk-register.md)).
- Elenen yollar [dead-ends.md](dead-ends.md)'e yazıldı.
- Faz 2'nin optimizasyon işi bitti; kalan iş faz sonu görevleri.

⚠️ **Hızlanma iddiası doğurmaz.** 37,3 ms, CPU tabanının (Aer p=2, medyan
77,6–92,7 ms) altında — ama sentez sonrası bir **HLS tahminidir**:
implementasyon yapılmadı, donanımda koşulmadı. Üstelik CPU tarafı iki koşuda
**±%60 oynadı** (58–123 ms), yani tek koşum taban olamaz. Karşılaştırma ancak
Faz 5'teki kart ölçümüyle ve çoklu koşumla kurulabilir (Prensip II ve IV).
Bkz. [faz2-sentez.md](../measurements/faz2-sentez.md) §15.

## Tekrar değerlendirilmeli mi?

**Evet, üç koşuldan biri oluşursa:**

1. **Vivado implementasyonu LUT %84'ü doğrulamazsa** (sığmama veya zamanlama
   ihlali). Geri dönüş yolu ölçülü: #10, LUT'u %63'e indirir, bedeli
   5.375.327 → 8.228.447 çevrim.
2. **Kübit sayısı düşerse veya daha büyük bir parçaya geçilirse** — ping-pong
   (II=1) yeniden hesaplanır.
3. **Tablo kurma maliyeti algoritmik olarak azalırsa.** Tablolar hâlâ toplamın
   %23'ü ve bu *hazırlık* işi, asıl hesap değil. Çözüm donanımda değil
   formülasyonda aranmalı — #6–#9 donanım yolunun kapalı olduğunu gösterdi.

**Yeniden açılmayacak olan**: banka sayısını artırmak. `k` derleme zamanı
sabiti yapılmadıkça fayda vermediği ölçüldü, o yol da ayrıca elenmiş durumda
([dead-ends.md](dead-ends.md), `template<int K>` maddesi).

---

# Güncelleme — 2026-09-16 akşamı: implementasyon ölçüldü, GEREKÇENİN BİR AYAĞI ÇÖKTÜ

Bu ADR'nin "Tekrar değerlendirilmeli mi?" bölümündeki **1. koşul tetiklendi**
("Vivado implementasyonu LUT %84'ü doğrulamazsa"). Doğrulamadı — ama
**beklenenin tersi yönde**.

## HLS tahmini LUT'ta 2 kata kadar yanılıyor

İlk kez `export_design -flow impl` koşuldu (Vivado sentez + yerleştirme +
yönlendirme):

| | HLS tahmini | **Vivado P&R** | oran |
|---|---:|---:|---:|
| LUT | 45.164 (%84,9) | **22.535 (%42,4)** | 0,50× |
| FF | 49.839 (%46,8) | **19.466 (%18,3)** | 0,39× |
| DSP | 36 (%16,4) | 33 (%15,0) | 0,92× |
| BRAM_18K | 187 (%66,8) | **187 (%66,8)** | 1,00× |

Zamanlama tuttu: post-route **9,122 ns**.

## Bu ADR'nin bir gerekçesi YANLIŞTI

Yukarıdaki **Gerekçe** bölümünde şöyle yazıyor:

> *Tablolar LUT'a sığmıyor (#6, #7, #8) ... Ölçüldü: LUT %182 / %166 / %123.*

Bu yüzdeler **HLS tahminiydi**. #6 ve #7 implementasyona kadar koşuldu:

| | LUT | FF | DSP | Gecikme p=2 | Post-route |
|---|---:|---:|---:|---:|---:|
| mevcut | 22.535 (%42) | 19.466 (%18) | 33 (%15) | 37,28 ms | **9,122 ns** ✅ |
| **#6** | 37.983 (**%71**) | 56.561 (%53) | 137 (%62) | **26,65 ms** | **9,878 ns** ✅ |
| #7 | 39.191 (%74) | 51.468 (%48) | 137 (%62) | 30,34 ms | **10,170 ns** ❌ |

**İkisi de sığıyor.** "Sığmıyor" gerekçesi geçersizdir ve öyle işaretlenmiştir.
HLS→gerçek oranı sabit de değil (0,39× / 0,44× / 0,50×), yani "HLS'i ikiye böl"
diye bir kural çıkarılamaz — her varyant ayrı ölçülmelidir.

## KARAR DEĞİŞMEDİ — ama sebebi değişti

#6 reddedildi. Artık "sığmıyor" diye değil, **zamanlama marjı yetersiz** diye.
Ölçüt, sayı görülmeden önce ilan edildi: *post-route 9,1–9,4 ns ise öner,
9,7+ ise önerme.*

| | post-syn → post-route | Marj |
|---|---|---:|
| mevcut | 9,171 → 9,122 (**iyileşti**) | **+0,878 ns (%8,8)** |
| #6 | 9,171 → 9,878 (**kötüleşti** +0,707) | **+0,122 ns (%1,2)** |

Üç bağımsız işaret aynı yöne bakıyor:

1. Marj **7 kat** daha az.
2. **Yönlendirme zamanlamayı bozdu.** Mevcut tasarımda yönlendirme 0,049 ns
   iyileştiriyor; #6'da 0,707 ns kötüleştiriyor — tıkanıklık işareti.
3. Koşum **3 kat** uzun sürdü (13 → 37 dk); Vivado zorlandı.

Faz 5 buna PS entegrasyonu, AXI ve olası DMA ekleyecek. 0,122 ns o noktada
tükenir ve tasarım **Faz 5'in ortasında** kırılır — geri dönmenin en pahalı
olduğu yerde. #6 ayrıca DSP'yi %15 → %62, FF'i %18 → %53 çıkarıyor.

Belirleyici olan şu: **hızlanma iddiası zaten yapılamadığı için** 26,65 ms ile
37,28 ms arasındaki fark bugün hiçbir kabul ölçütünü değiştirmiyor. Ölçülmüş
bir kazancı, ölçülmüş bir riske tercih etmek için sebep yok.

## #7 elendi — domine ediliyor

#7, #6'nın alt kümesidir (yalnızca `tablo_yuksek` boru hattında) ama her
eksende ondan kötü: daha çok LUT, daha yüksek gecikme, zamanlama tutmuyor.
Yerleştirme-yönlendirme **monoton değildir**; daha az talep eden netlist daha
iyi yerleşmeyebilir. Bu, HLS tahminiyle varyant elemenin neden güvenilmez
olduğunun ikinci kanıtı.

## Bu ADR'den çıkan kalıcı kural

**Kaynak gerekçesiyle bir varyant elenecekse, gerekçe implementasyondan
gelmelidir.** HLS tahmini bir varyantı elemeye yetmez; yalnızca hangi
varyantların ölçülmeye değer olduğunu sıralamaya yarar.

## Yeniden açma koşulları (güncellendi)

1. ~~Vivado implementasyonu LUT %84'ü doğrulamazsa~~ — **tetiklendi ve
   cevaplandı** (2026-09-16).
2. Faz 5 tamamlanıp **gerçek** PS entegrasyonu sonrası marj ölçülürse ve hâlâ
   yer varsa → #6 yeniden değerlendirilir.
3. Saat hedefi 100 MHz'in altına çekilirse → 9,878 ns bol marj olur.
4. Gecikme **gerçekten** bir kabul ölçütü hâline gelirse.
5. Kübit sayısı düşerse veya daha büyük parçaya geçilirse → ping-pong (II=1).

Bütün ölçümler [faz2-sentez.md](../measurements/faz2-sentez.md) §16'da; yeniden
açan sıfırdan koşmak zorunda değil.
