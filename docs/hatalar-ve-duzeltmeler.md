# Bulunan Hatalar ve Düzeltmeleri

**Amaç**: bitirme raporunun *doğrulama* ve *tartışma* bölümleri için kaynak.
Burada yalnız **yanlış sonuç üreten ya da üretecek olan** hatalar durur —
denenip elenen tasarım yolları [dead-ends.md](decisions/dead-ends.md)'de,
ölçümle çürüyen tahminler [olculen-degerler.md §8](olculen-degerler.md)'de.

Her kayıt aynı biçimdedir ve rapora doğrudan taşınabilir:

| Alan | Soru |
|---|---|
| **Belirti** | Ne görüldü? |
| **Nasıl yakalandı** | Hangi mekanizma gösterdi? |
| **Kök neden** | Gerçek sebep ne? |
| **Yakalanmasaydı** | Hangi sonuç yanlış raporlanırdı? |
| **Düzeltme** | Ne değişti? |
| **Kanıt** | Nerede kayıtlı? |
| **Rapor için ders** | Tek cümle |

**Yeni kayıt ekleme kuralı**: hata *bulunduğu gün* buraya yazılır, sonra değil.
Sayılar kaynağından (ölçüm dosyası, rapor, yazmaç) alınır, hafızadan değil.

---

## Özet

| # | Tarih | Hata | Tür | Yakalayan | Yakalanmasaydı |
|---|---|---|---|---|---|
| 1 | 27 Eyl | FCLK0 100 yerine **62,5 MHz** | donanım yapılandırması | koruma kodu (FCLK doğrulaması) | bütün gecikmeler **%60 uzun** |
| 2 | 20 Eyl | `cost` katsayıları **sessizce doyuyor** | sayısal | konak kodlayıcıyı yazarken veriye bakmak | doymuş operatörün değeri "enerji" sanılırdı |
| 3 | 16 Eyl | iki karşılaştırma hatası **birbirini maskeledi** | ölçüm yöntemi | `quickstart.md`'yi uçtan uca koşmak | yanlış yönde hızlanma sonucu |
| 4 | 19 Eyl | CPU tabanı **kirli** (arka plan yükü + turbo penceresi) | ölçüm yöntemi | teşhis deneyi (4 koşul) | CPU 1,85–2,21× yavaş görünürdü |
| 5 | 21 Eyl | CPU tabanı **farklı algoritma** (Qiskit Aer, 12× kapı) | ölçüm yöntemi | aynı kodu CPU'da zamanlamak | *"başabaş"* sonucu |
| 6 | 21 Eyl | ARM tabanı **taklit aritmetikle** 18,8× şişik | ölçüm yöntemi | float varyantını da ölçmek | **sahte 42× hızlanma** |
| 7 | 19 Eyl | cosim'in 13 saat sürmesi — **iki kez yanlış teşhis** | araç zinciri | süreç tablosu (hangi süreç CPU yiyor) | n=16 RTL eşdeğerliği hiç gösterilemezdi |
| 8 | 20 Eyl | I2C pinleri (INA219 için) **ses çipinin** pinlerine atanacaktı — kâğıt üzerinde | donanım tasarımı (pin ataması) | kart kısıt dosyasını satır satır okumak | sensöre hiç ulaşılamaz; yeni bitstream + bütün ölçümlerin tekrarı |
| 9 | 27 Eyl | besleme gerilimi **"0,0 V"** göründü | ölçüm yorumu | dört rayın aynı anda 0 olması | yanlış "USB beslemesi yetmiyor" sonucu |
| 10 | 27 Eyl | *"18 bit iki kısıtın kesişimi"* — **iki yarısı da yanlış** | tasarım gerekçesi (model ≠ çekirdek) | genişliği gerçekten tarayıp sentezlemek (6C) | tezin ana bulgularından biri yanlış raporlanırdı |
| 11 | 28 Eyl | Aer CPU tabanı **16 iş parçacığıyla** — sanal makinede aşırı abonelik | ölçüm yöntemi (taban yapılandırması) | ilk serinin kuyruğu (p99 525 ms) + ön kayıtlı tarama | CPU/GPU oranı GPU lehine çarpık |

**Desen**: 11 hatanın **6'sı ölçümde** (yöntem, taban, yorum: 3, 4, 5, 6, 9, 11),
5'i tasarım, gerekçe, yapılandırma ve araç zincirinde (1, 2, 7, 8, 10). Hiçbiri çekirdeğin hesabında değil — çekirdek her aşamada
altın referansla bit bit karşılaştırıldığı için. Hatalar, karşılaştırmanın
**olmadığı** yerlerde birikti.

---

## 1. FCLK0 100 yerine 62,5 MHz — kristal frekansı yanlış (2026-09-27, Faz 5 T032)

**Belirti**: Bitstream karta yüklenince konak kodu durdu:
`FCLK0 = 62.500 MHz, beklenen 100.000 MHz (sapma %37.50)`. Aynı kart
açılışta 100 MHz gösteriyordu (20 Eylül'de ölçülmüş ve kaydedilmişti).

**Nasıl yakalandı**: `agent/board.py` her yüklemeden sonra PL saatini okuyup
%1 toleransla doğruluyor ve sapmada **istisna atıyor**. Bu kontrol 20 Eylül'de,
kart görülmeden, "çalışma zamanındaki saati bitstream değil kart belirler"
gerekçesiyle yazılmıştı. İlk gerçek yüklemede tetiklendi.

**Kök neden**: Blok tasarım betiği `fpga/bd/qir_bd.tcl`, kart ön ayarı
(board preset) olmadığı için PS7'yi elle yapılandırıyor ve PS referans
kristalini **33,333 MHz** veriyordu. PYNQ-Z2'ninki **50 MHz**. Zincir:

```
.hwh (Vivado'nun sandığı) : IO PLL 1600 MHz, FCLK0 bölenleri 4×4 → 1600/16 = 100 MHz
kart (gerçek)             : IO PLL 1000 MHz  (boot'ta ps7_init kurar)
PYNQ Overlay yüklerken    : PLL'e DOKUNMAZ, bölenleri .hwh'den YAZAR
sonuç                     : 1000 / 16 = 62,5 MHz
```

Kartın saat yazmaçlarından (SLCR) doğrulandı: IO / ARM / DDR PLL çarpanları
20 / 26 / 21 → **×50 MHz** ile 1000 / 1300 / 1050 MHz, yani 650 MHz
Cortex-A9 ve 525 MHz DDR3 ile birebir. 33,333 MHz ile hesaplanınca hiçbiri
anlamlı çıkmıyor.

**Yakalanmasaydı**: Hesap sonuçları **doğru** çıkardı — 20 izdüşümün
hepsi C modeliyle bit bit tutardı, çünkü mantık saatten bağımsızdır. Ama
bütün gecikme ölçümleri sessizce **1,6× (%60) uzun** olurdu: p=2 için
37,28 ms yerine ~59,6 ms. PS↔PL hızlanması 2,26× yerine ~1,4× raporlanır;
koşum başına enerji de yanlış saatte ölçülmüş olurdu. Sonuçlar "makul" göründüğü için fark
edilmezdi.

**Düzeltme**:
- `agent/board.py` frekansı artık önce **ayarlıyor** (`Clocks.fclk0_mhz = 100`;
  PYNQ bölenleri gerçek PLL'den hesaplar → 1×10 = tam 100,000 MHz), sonra
  **doğruluyor**. Ayar öncesi değer ölçüm dosyasına yazılıyor
  (`fclk_yukleme_sonrasi_mhz: 62.5`) — hangi koşumun ayar gerektirdiği
  sonradan görülebilsin.
- 3 birim testi: sapma varsa ayarlanır ve kaydedilir; tolerans içindeyse
  yazılmaz; ayar tutmazsa sessiz geçilmez.
- `qir_bd.tcl`'ye uyarı notu. Kristal bir **sonraki derlemede** düzeltilecek
  ve `.hwh`'deki bölenlerle doğrulanacak — kristal tek başına değişince
  Vivado IO PLL'i yine 1000'den farklı kurabilir.
- Bitstream **yeniden üretilmedi**: PL mantığı kristale bağlı değil ve
  zamanlama 100 MHz'e göre kapandı (WNS +0,776 ns).

**Kanıt**: [kart-dogrulama p2](measurements/kart-dogrulama_20260927_67165a7_n16_p2.json)
(`fclk` alanı), [SIRADAKI.md](../specs/003-zynq-ps-kartta-kosum/SIRADAKI.md)
donanım tablosu.

**Neden daha önce görülmedi**: 20 Eylül'de FCLK0 **açılışta** ölçüldü —
bitstream yüklenmeden. G0 uyumluluk denemesi de yalnız `.hwh`'yi ayrıştırdı,
karta indirmedi. İkisi de doğruydu ama ikisi de hatanın oluştuğu anı
(yükleme) kapsamıyordu.

**Rapor için ders**: *Doğru sonuç, doğru ölçüm demek değildir: işlevsel
doğrulama saat hatasını göremez, çünkü mantık saatten bağımsızdır — ölçüm
koşulları (saat, besleme) ayrıca doğrulanmalıdır.*

---

## 2. `cost` katsayıları sessizce doyuyor (2026-09-20, Faz 5 öbek 3)

**Belirti**: C testbench'inin ürettiği beklenen değer `-0,442401439`
fiziksel olarak anlamsızdı.

**Nasıl yakalandı**: Konak kodlayıcıyı yazarken referans dosyasının ham
Ising katsayılarına bakıldı: `max|h| = 7512,61`, `max|J| = 1253,07`.
Q1.17'nin aralığı `[-1, 1)`.

**Kök neden**: Testbench katsayıları `real_t`'ye (Q1.17, `AP_SAT`) düz
atıyordu. `AP_SAT` aralık dışını **uyarısız** kırpar: **16/16 `h`** ve
**84/120 `J`** girdisi `±1`'e doydu.

**Yakalanmasaydı**: Doymuş bir maliyet operatörünün beklenen değeri tezde
enerji olarak raporlanabilirdi. Fidelity ve C/RTL eşdeğerliği bu hatayı
**göremez** — ikisi de `cost`'tan bağımsız yoldan gelir (fidelity yalnız
fazlardan, eşdeğerlik iki tarafın aynı doymuş fonksiyonu hesaplamasından).

**Düzeltme**: `agent/encoder.py` ölçekleme protokolünü uygular ve aralık
dışı girdide **istisna atar** (madde H-3: sessiz kırpma yasak). Testle
sabitlendi (`test_kodlayici_doyurmak_yerine_atar`).

**Kanıt**: [faz2-sentez.md §21](measurements/faz2-sentez.md).

**Rapor için ders**: *Bir doğrulama ölçütü yalnız ölçtüğü yolu korur;
fidelity mükemmelken çıkışın fiziksel anlamı yanlış olabilir.*

---

## 3. İki karşılaştırma hatası birbirini maskeledi (2026-09-16, Faz 2 T054)

**Belirti**: FPGA ↔ CPU karşılaştırması *"CPU 1,2× önde"* gibi makul bir
sonuç veriyordu.

**Nasıl yakalandı**: `quickstart.md` baştan sona, sıfırdan koşulunca.

**Kök neden**: İki bağımsız hata, **ters yönde**:
1. FPGA tarafı sentez raporunun `max` gecikmesiydi — o **p=3** içindir
   (53,75 ms); CPU tarafı **p=2** koşuyordu. Farklı devreler kıyaslanıyordu.
2. CPU'nun "~58 ms"si bir **medyan değil, en iyi durumdu** (aynı koşunun
   medyanı 77,57 ms).

FPGA olduğundan büyük, CPU olduğundan küçük alınınca sonuç makul göründü.

**Yakalanmasaydı**: Yanlış yönde bir sonuç tezde kalırdı.

**Düzeltme**: Karşılaştırmada aynı `p` zorunlu; gecikme p'ye göre
ayrıştırıldı (init + p × katman + beklenen değer). Tek koşum yerine dağılım.

**Kanıt**: [faz2-sentez.md §15](measurements/faz2-sentez.md). (§15'in
sonuçları da sonradan §18 ve §22'yle geçersiz oldu — bkz. 4 ve 5.)

**Rapor için ders**: *Tek bir sayıya bakarak yakalanamayacak hatalar vardır;
iki hata birbirini götürdüğünde sonuç "makul" görünür — uçtan uca yeniden
üretim bunu yakalar.*

---

## 4. CPU tabanı kirli — arka plan yükü ve turbo penceresi (2026-09-19, Faz 2)

**Belirti**: CPU tabanı iki kayıtta 77,57 ve 92,66 ms'ydi; aynı devre
başka bir anda 35,51 ms ölçüldü.

**Nasıl yakalandı**: Dört koşullu teşhis deneyi (temiz-soğuk, benchmark
sonrası, sürdürülen, soğuk tekrar). *"Soğuk tekrar"ın düzelmemesi* suçlunun
termal doyum olduğunu gösterdi.

**Kök neden**: İki ayrı kirlenme:
1. 16 Eylül ölçümü alınırken arka planda **n=16 cosim koşuyordu**.
2. Betik `TEKRAR = 15` ile ~0,6 sn ölçüyordu — tam **turbo penceresi**.
   İşlemci ısınınca yavaşlıyor ve orada kalıyor.

**Yakalanmasaydı**: CPU platonun **1,85×** ve **2,21×** yavaşı görünür,
FPGA haksız yere "önde" raporlanırdı.

**Düzeltme**: Süre tabanlı ölçüm (7474 koşum / 300 sn, prizde, sessiz
makine); turbo (32,75 ms) ve plato (41,93 ms) **ayrı** raporlanır.

**Kanıt**: [faz2-sentez.md §18](measurements/faz2-sentez.md).

**Rapor için ders**: *Sabit tekrar sayısıyla alınan kısa ölçüm, işlemcinin
sürdürülen değil kısa süreli en iyi hâlini ölçer.*

---

## 5. CPU tabanı farklı bir algoritmaydı — Qiskit Aer (2026-09-21, Faz 5)

**Belirti**: Temiz CPU tabanıyla sonuç *"gecikmede başabaş"*tı (FPGA
37,28 ms, Aer 32,75–41,93 ms).

**Nasıl yakalandı**: Aynı çekirdek kodu (`hls/tb/bench_kernel.cpp`)
doğrudan CPU'da zamanlandı: **3,273 ms**.

**Kök neden**: Aer, RZZ kapısını CX-RZ-CX olarak ayrıştırıp p=2'de
**384 kapı** uyguluyor; bizim çekirdek köşegen operatörü **32 geçişe**
füzyonluyor. **12× algoritmik fark** — donanım farkı değil.

**Yakalanmasaydı**: *"Başabaş"* bir **taban artefaktı** olarak tezde kalırdı;
adil tabanla dizüstü CPU FPGA'dan **11,4× hızlı**.

**Düzeltme**: Gecikme tabanı her zaman **aynı algoritmanın** aynı
platformdaki hâli. SoC için doğru taban aynı çipteki ARM'dır (PS↔PL).

**Kanıt**: [faz2-sentez.md §22](measurements/faz2-sentez.md),
[adil-cpu-tabani](measurements/adil-cpu-tabani_20260921_c504294.json).

**Rapor için ders**: *Bir hızlanma sayısı, tabanı söylenmeden anlamsızdır;
taban aynı algoritmayı koşmuyorsa ölçülen şey donanım değil algoritma farkıdır.*

---

## 6. ARM tabanı taklit aritmetikle 18,8× şişik (2026-09-21, Faz 5 T045b)

**Belirti**: Kartın ARM'ında, donanımla **aynı** Q1.17 aritmetiğiyle
çekirdek **1579 ms** sürdü.

**Nasıl yakalandı**: Aynı kodun yerel `float` varyantı da ölçüldü:
**84,1 ms**.

**Kök neden**: Taklit sınıf (`ap_fixed_mock`) her işlemi `double`'da yapıp
kuantalıyor; Cortex-A9'un NEON birimi **çift duyarlık desteklemiyor**.
18,8× fark mimarinin değil taklit sınıfın artefaktı.

**Yakalanmasaydı**: *"Donanımla aynı aritmetik"* en adil taban gibi
göründüğü için yalnız o ölçülürdü ve **42× hızlanma** raporlanırdı. Gerçek
sayı **2,26×** (21 Eyl, FPGA tarafı tahmin); FPGA kartta ölçülünce **2,30×**
(27 Eyl, [kart-gecikme p2](measurements/kart-gecikme_20260927_201475a_n16_p2.json)).

**Düzeltme**: `QIR_REAL_FLOAT` bayrağı (yalnız taban ölçümü için, sentezde
kullanılmaz); taban, hedef platformda **yetkin bir gerçeklemenin** yapacağı şey.

**Kanıt**: [dead-ends.md](decisions/dead-ends.md),
[ps-pl-hizlanma](measurements/ps-pl-hizlanma_20260921_c504294.json).

**Rapor için ders**: *"Adil" görünen taban, hedef platformda kötü
gerçeklenmişse hızlanmayı bir mertebe şişirebilir.*

---

## 7. Cosim'in 13 saat sürmesi — iki kez yanlış teşhis (2026-09-19, Faz 2)

**Belirti**: n=16 C/RTL eşdeğerlik simülasyonunun tahmini ~13 saatti ve
giderek yavaşlıyordu (0,885 → 0,036 ms/dk).

**Nasıl yakalandı**: Süreç tablosu: asıl simülatör (`xsimk`) **%5,1 CPU**
ile açlık çekerken Tcl süreci (`vitis-run`) **%97,9 CPU** ve 685 MB
kullanıyordu.

**Kök neden**: Aracın ürettiği `run_sim.tcl`, simülatörün her çıktı
satırını Tcl kanal katmanından geçiriyordu (`| tee temp2.log >&@ stdout`);
tasarım yüz binlerce uyarı satırı bastığı için Tcl darboğaz oldu. Önceki
teşhis (*"`/mnt/c` disk köprüsü yavaş"*) **iki kez** çürütülmüştü ama betik
yorumunda kalmıştı.

**Yakalanmasaydı**: n=16 RTL eşdeğerliği pratikte hiç gösterilemezdi;
makine çökmeleri (sürücü) 13 saatlik bir koşuyu bitirtmiyordu.

**Düzeltme**: Simülasyonun 2. ve 3. aşaması doğrudan kabuktan koşuldu —
aynı RTL, aynı uyaran. **15 dk 48 sn, 76× hızlı**. Sonuç: çıkış portu C ile
bit bit aynı (`0xbee28271`).

**Kanıt**: [faz2-sentez.md §20](measurements/faz2-sentez.md).

**Rapor için ders**: *Çürütülen hipotezi yazan yorum da güncellenmeli;
güncellenmeyen yorum bir sonraki turu aynı yanlış yola sokar.*

---

## 8. I2C pinleri ses çipinin pinlerine atanacaktı (2026-09-20, Faz 5 öbek 2)

⚠️ **Fiziksel bir bağlantı hatası DEĞİLDİR.** INA219 o tarihte (ve bu kayıt
yazılırken) karta hiç takılmamıştı. Hata, bitstream'in **pin tanımında**,
kâğıt üzerinde yakalandı.

**Belirti**: Yok — bitstream üretilmeden **önce** yakalandı.

**Nasıl yakalandı**: Blok tasarım için FPGA'nın I2C sinyallerinin hangi
fiziksel pinlerden çıkacağı seçilirken, PYNQ-Z2'nin resmî pin dosyası
(`base.xdc`) satır satır okundu: dosyada **üç ayrı I2C pin çifti** var.

**Kök neden**: Adı en doğal görünen `IIC_1` (pinler U9/T9) kartın devresinde
**üzerine lehimli ses çipine** (ADAU1761) gidiyor; dışarıdan erişilebilir
değil. Sensörün takılacağı yer Arduino başlığının SDA/SCL'si
(`arduino_direct_iic`, P15/P16).

**Yakalanmasaydı**: Bitstream I2C denetleyicisini ses çipine yönlendirirdi.
INA219 Arduino başlığına takıldığında FPGA onu **hiç göremezdi** — ve bu,
bugün değil, enerji ölçümüne (US3) geçilen gün ortaya çıkardı. Düzeltmek yeni
bir bitstream, yeni bitstream de karar K2 gereği o güne kadar bu bitstream'le
alınmış **bütün** ölçümlerin tekrarı demekti.

**Düzeltme**: EMIO I2C0 → P15/P16. Seçim, kaynak dosya ve gerekçe kısıt
dosyasının başlığında.

**Kanıt**: [fpga/bd/qir_constraints.xdc](../fpga/bd/qir_constraints.xdc)
(başlık yorumu).

**Rapor için ders**: *Pin ataması addan değil, kart şemasından yapılır.*

---

## 9. Besleme gerilimi "0,0 V" göründü (2026-09-27, Faz 5 US1)

**Belirti**: Kart USB'den beslenirken koşum boyunca gerilim izlendi; dört
rayın **hepsinin** en düşük değeri 0,0 V çıktı. Ortalamalar ise normaldi
(VCCINT 1,0202 V).

**Nasıl yakalandı**: Dört rayın **aynı anda** 0 olması. İşlemciyi besleyen
ray (VCCPINT) gerçekten 0 olsaydı Linux çökerdi, ama SSH bağlantısı hiç
kopmadı.

**Kök neden**: Gerilim algılayıcısı (XADC) PL tarafında yaşıyor; bitstream
yüklenirken PL yeniden programlandığı için birkaç örnek 0 okuyor.

**Yakalanmasaydı**: *"USB beslemesi yük altında çöküyor"* sonucu çıkar,
JP5 yanlış gerekçeyle değiştirilir ve enerji ölçüm düzeni boşuna bozulurdu.

**Düzeltme**: `agent/xadc_izle.py` yeniden programlama örneklerini ayrı
sayıyor. Düzeltilmiş ölçüm: 50 sn, 78.988 örnek, **VCCINT ≥ 1,0151 V**
(çalışma aralığı 0,95–1,05 V) — düşüş yok.

**Kanıt**: [kart-dogrulama p2](measurements/kart-dogrulama_20260927_67165a7_n16_p2.json)
(`besleme` alanı).

**Rapor için ders**: *Bir ölçüm aracının kendi çalışma koşulları vardır;
aykırı değer önce aracın o anki durumuyla açıklanmaya çalışılmalı.*

---

## 10. "18 bit iki kısıtın kesişimi" — iki yarısı da yanlış (2026-09-27, Faz 5 6C)

**Belirti**: Belgelerde (neden-fpga §2.2b, mimari-gerekçe, banking-research
§4, memory-budget) ve tez cümlesinde bir **bulgu** olarak duruyordu:
*"Q1.17 H eşiğini geçen en dar formattır; 19+ bit BRAM36'nın 36-bit
kelimesini aşar ve BRAM ikiye katlanır — 18, iki bağımsız kısıtın tam
kesişimidir."* Genişlik gerçekten tarandığında (aynı çekirdek, 14–24 bit):

| W | Fidelity p=2 (çekirdek) | Model | BRAM_18K (toplam) | Statevector BRAM |
|---:|---:|---:|---:|---:|
| 14 | 0,994508 ❌ H | 0,978861 ❌ | 152 | 112 |
| 16 | **0,999656** ✅ H | 0,998674 ❌ | 169 | 128 |
| 18 | 0,999978 | 0,999917 | 187 | 144 |
| 20 | 0,9999985 | 0,999995 | 204 | 160 |
| 24 | 0,9999999 | 0,99999998 | 238 | 192 |

**Nasıl yakalandı**: 6C görevinin kendisi — tasarım parametresini gerçekten
süpürüp her noktayı sentezlemek. Kriterler (K1–K4) koşudan **önce** yazıldı.

**Kök neden** (iki ayrı):
1. **Doğruluk yarısı modelden geliyordu, çekirdekten değil.** Format Faz 2'de
   `format_fidelity.py` ile seçildi; model her kapıdan sonra yuvarlıyor.
   Çekirdek ise çift genişlikli `acc_t`'de biriktirip bir kez yuvarlıyor →
   hata ~3,8× az. Modelde kalan Q1.15, çekirdekte H'yi ~3× payla geçiyor.
2. **Donanım yarısı hesaplanmıştı, sentezlenmemişti.** Hesap, genliğin re+im
   olarak tek 36-bit kelimeye paketlendiğini varsaydı. Sentez raporunun
   bellek tablosu başka bir şey gösteriyor: statevector **4 ayrı bellek ×
   32.768 kelime × W bit** (re ve im ayrı), her biri **2W** blok →
   statevector BRAM'i tam **8W** (112/128/144/160/192). Kelimeye hizalama hiç
   devreye girmiyor; maliyet bit başına doğrusal, uçurum yok. DSP48'in 18-bit
   B portu argümanı da tutmadı (DSP 36/36/30/33).

**Yakalanmasaydı**: Tezin *"18-bit hassasiyet noktası"* katkısı ve savunmanın
*"FPGA'ya özgü değer"* argümanı yanlış bir mekanizmaya dayanırdı. Jüride
tek bir soruyla (*"16 bitle denediniz mi?"*) çökerdi.

**Düzeltme**: Kod değişmedi (18 bit çalışıyor ve doğru). Değişen **iddia**:
18 bir seçimdir; genişlik, ölçülmüş maliyet/doğruluk eğrisi olan serbest
bir parametredir. Eski cümleler ilgili belgelerde ⛔ ile işaretlendi; tez
cümlesi kararı kullanıcıda. İlginç yan bulgu (doğrulanmadı): HLS BRAM'in
parite bitlerini kullanmıyor; 18 bitte 1K×18 düzeni 144 yerine 128 blok
verebilirdi.

**Kanıt**: [genislik-pareto_20260927_dfe3eff.json](measurements/genislik-pareto_20260927_dfe3eff.json)
(`BRAM_statevector` alanı), figür
[genislik-pareto_20260927_dfe3eff.svg](figures/genislik-pareto_20260927_dfe3eff.svg)
— panel (b) Faz 2 hesabını ölçümün yanında gösterir,
`qir_hls_prj_W<n>/solution1/syn/report/qir_kernel_csynth.rpt` (Memory
tablosu), [olculen-degerler.md §2.2, §8 #5–6](olculen-degerler.md).

**Rapor için ders**: *Bir tasarım noktasının "optimum" olduğu, komşu
noktalar gerçekten üretilip ölçülmeden iddia edilemez — model ve el hesabı
yalnız hangi noktaların ölçülmeye değer olduğunu söyler.*

---

## 11. Aer CPU tabanı 16 iş parçacığıyla — sanal makinede aşırı abonelik (2026-09-28, Faz 5 6B)

**Belirti**: GPU tabanı protokolünün (v1.0) ilk serisi A-CPU'da, medyan
normal görünüyordu (42,66 ms) ama kuyruk patlamıştı: p99 **525 ms**, en kötü
**1.338 ms**, 4.214 koşumun 264'ü 200 ms'yi aştı, ilk 50 koşumun medyanı
137,7 ms.

**Nasıl yakalandı**: Kuyruğun kendisi, ve 6 iş parçacığıyla yapılmış duman
testinde en kötü koşumun 51 ms olması. Sonra **ön kayıtlı bir tarama**
(T = 1…16, seçim kuralı taramadan önce yazıldı) nedeni ölçtü: T=4 medyanı
31,7 ms, T=16'nın p99'u 249,7 ms (taramanın en kötüsü).

**Kök neden**: Protokolün K1 kararı WSL'e ana makinenin **tüm** 16 mantıksal
işlemcisini verdi ve Aer varsayılan olarak hepsini kullandı. Windows da
işlemci istediğinde sanal işlemciler askıya alınıyor, OpenMP iş parçacıkları
birbirini bekliyor. K1'in gerekçesi ("6 iş parçacığı GPU lehine şişirir")
ölçümde **ters** çalıştı: 16 iş parçacığı CPU'yu kötü, dolayısıyla GPU'yu iyi
gösteriyordu.

**Yakalanmasaydı**: Aer içinde CPU/GPU oranı 42,66 / 29,94 = 1,42× diye
raporlanırdı; doğru yapılandırmayla 1,21×. Fark GPU'nun değil **tabanın
yanlış yapılandırılmasının** ürünü olurdu — hata #5'in ("taban farklı bir
algoritma") akrabası.

**Düzeltme**: Protokol v1.1 (§12, "sonuç görüldükten sonra" diye beyan
edildi): iş parçacığı sayısı ön kayıtlı taramayla seçildi (T=4), dört seri
baştan koşuldu, v1.0 serisi silinmedi, ayrı satır olarak kaldı.

**Aynı turda iki araç hatası daha (sonucu bozmadı, ölçüm dışı)**: kirli ağaç
kontrolü önce **fazla katıydı** (bir önceki serinin çıktı dosyasını "kirli"
sayıp ikinci seriyi reddetti), düzeltilince **fazla gevşek** oldu (eklenmemiş
yeni bir betiği "temiz" saydı, bir deneme ölçüm dizinine yazdı — dosya
silindi). Son kural: izlenen her değişiklik + ölçüm dizini dışındaki her yeni
dosya kirlidir; altı durumla sınandı.

**Kanıt**: [v1.0 A-CPU](measurements/cpu-yuk-dongu_20260927_20f1c5c_seriA-CPU_p2.json),
[tarama ve seçim](measurements/aer-is-parcacigi-secimi_20260930_14a59ee.json),
[protokol §12](measurements/gpu-taban-olcum-protokolu.md),
[olculen-degerler §6.1](olculen-degerler.md).

**Rapor için ders**: *Taban, kendi en iyi yapılandırmasıyla ölçülmelidir; o
yapılandırma varsayılarak değil, önceden yazılmış bir kuralla ölçülerek
seçilir.*

---

## Hataları ne yakaladı — rapor için çapraz bakış

| Mekanizma | Yakaladığı |
|---|---|
| **Çalışma koşulunu doğrulayan koruma kodu** (istisna atan) | 1 |
| **Altın referansla bit düzeyinde karşılaştırma** | çekirdekte hata kalmadı — 20/20 izdüşüm, cosim, fidelity |
| **Ham veriye bakmak** (katsayı aralığı, süreç tablosu) | 2, 7 |
| **Uçtan uca yeniden üretim** (`quickstart.md`) | 3 |
| **Kontrollü teşhis deneyi** (koşul değiştirip ölçmek) | 4 |
| **Tabanı değiştirip aynı şeyi yeniden ölçmek** | 5, 6 |
| **Kaynak belgeyi satır satır okumak** | 8 |
| **Fiziksel tutarlılık kontrolü** (bu değer mümkün mü?) | 9 |
| **Komşu tasarım noktalarını gerçekten üretip ölçmek** (parametre taraması) | 10, 11 |
| **Kuyruğa bakmak** (medyan değil p99/maks) | 11 |

**Rapora girecek genel sonuç**: Çekirdeğin kendisinde hata kalmadı, çünkü
her aşamada (C-sim → RTL → kart) bir altın referansa **bit düzeyinde**
bağlandı. Hataların hepsi bu zincirin **dışında** kalan yerlerde çıktı:
ölçüm koşulları, karşılaştırma tabanı, sayısal aralık, pin ataması. Tez
açısından bu, doğrulama stratejisinin nerede işe yaradığını ve nerede ek
kontrol gerektiğini gösteren somut bir kanıttır.
