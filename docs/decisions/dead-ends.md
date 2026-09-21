# Elenen Yollar (Dead Ends)

**Kaynak**: Faz 0 alt dal 0.7 · **Oluşturma**: 2026-09-10

Bu dosya **sıkıştırmada en çok kaybedilen bilgiyi** tutar: denenip işe yaramayan yollar. Bağlam
sıkıştığında "bunu zaten denedim, olmadı" bilgisi ilk kaybolan şeydir — burada yaşar.

**Boş kalıyorsa yanlış kullanılıyordur.** Her başarısız deneme (bir sentez stratejisi, bir kütüphane,
bir mimari yaklaşım) buraya bir satır olarak düşmeli — "bir dahaki sefere neden aynı şeyi tekrar
denemeyeceğim" sorusuna cevap olacak şekilde.

## Biçim

```
### <Ne denendi> — <tarih>, Faz <N.M>

**Neden denendi**: <motivasyon>
**Neden olmadı**: <somut başarısızlık nedeni, ölçülebilirse ölçüm>
**Tekrar denenmeli mi**: Evet, şu koşulda: <...> / Hayır, çünkü <...>
```

---

### GraphHopper (açık kaynak) matris motoru olarak — 2026-09-13, Faz 1

**Neden denendi**: OSRM/Valhalla ile birlikte üç aday rotalama motorundan biriydi; Docker imajı çekilip
gerçekten koşuldu (`israelhikingmap/graphhopper`, resmî imaj yok).

**Neden olmadı**: Açık kaynak GraphHopper'ın `/matrix` ucu **yok** — ampirik olarak doğrulandı:
`/route` → 200, `/matrix` → **404**. Matrix API, GraphHopper'ın ticari/lisanslı sürümünün özelliği.
N=30 durak için 900 ayrı `/route` çağrısı gerekirdi; spec FR-001'i makul maliyetle karşılayamaz.

**Tekrar denenmeli mi**: Hayır, çünkü OSRM (BSD-2, resmî imaj, ölçülen matris gecikmesi 0,383 sn
medyan) her ölçülen eksende üstün çıktı. Yalnızca GraphHopper'ın ticari Matrix API lisansı alınırsa
yeniden gündeme gelebilir — taban planda yok. Bkz. [ADR 0006](0006-osrm-ve-qiskit-aer.md).

### Valhalla kurulumu — sırasız komutlar — 2026-09-13, Faz 1

**Neden denendi**: `valhalla_build_tiles`'ı doğrudan `valhalla_build_config` çıktısıyla çalıştırmak.

**Neden olmadı**: `admin.sqlite` ve `tz_world.sqlite` önceden üretilmemişti (`valhalla_build_admins`,
`valhalla_build_timezones` atlanmıştı). Sonuç anlaşılır bir hata değil, **segmentation fault**
oldu (graf kurulumu 17 saniyede başarıyla bitmiş, "Enhancing local graph" aşamasında çökmüştü).

**Tekrar denenmeli mi**: Evet — doğru sıra biliniyor artık: `config → timezones → admins → tiles`.
Bu proje Valhalla'yı seçmedi (bkz. ADR 0006) ama sıra bilgisi genel olarak değerli.

### Rastgele parametreli QAOA (optimizasyonsuz) — 2026-09-13, Faz 1

**Neden denendi**: İlk sürüm, tohumlu rastgele parametrelerle QAOA devresini bir kez koşuyordu —
"altın referans" için yeterli görünmüştü çünkü tam statevector taraması `best_tour`'u zaten doğru
buluyordu.

**Neden olmadı**: "QAOA" adına sadık değildi — gerçek QAOA parametreleri **optimize eder**. Kullanıcı
sorguladı, kabul edildi ve COBYLA optimizasyon döngüsü eklendi (bkz. commit `6e0e3e5`).

**Tekrar denenmeli mi**: Hayır, mevcut sürüm (COBYLA + tohumlu başlangıç) daha doğru. Not: optimizasyon
eklendikten sonra bile olasılık kütlesi tek duruma yoğunlaşmadı (bkz.
[faz1-olcumler.md](../measurements/faz1-olcumler.md)) — bu ayrı, meşru bir bulgu, "olmadı" değil.

### Docker healthcheck — `curl` ile OSRM sağlık kontrolü — 2026-09-13, Faz 1

**Neden denendi**: `docker-compose.yml`'de `osrm` servisinin hazır olmasını beklemek için standart
yaklaşım: `healthcheck: test: ["CMD", "curl", "-f", "http://localhost:5000/..."]` + `depends_on:
condition: service_healthy`.

**Neden olmadı**: **`osrm/osrm-backend` imajında `curl` da `wget` de YOK** (`docker exec ... which
curl` → bulunamadı; `/usr/bin` içinde yalnızca `runcon`, `truncate` gibi birkaç araç var). Docker
healthcheck komutu konteynerin **kendi dosya sisteminde** çalıştığından hiçbir zaman başarılı
olamazdı — servis sonsuza dek "unhealthy" kaldı ve `matrix` servisi hiç başlamadı.

Ayrıca ikinci bir yanlış varsayım: `osrm-routed`'in **`/health` ucu yoktur** (400 döner); gerçek bir
`/route` veya `/table` sorgusu kullanılmalıdır.

**Tekrar denenmeli mi**: Hayır — bu imaj için healthcheck kaldırıldı, hazır olma kontrolü `matrix`
servisinin kendi `/health` ucuna (host'tan HTTP ile) bırakıldı. Genel ders: **minimal imajlarda
healthcheck yazmadan önce imajda HTTP istemcisi olup olmadığını kontrol et.**

### `template<int K>` ile 16 ayrı RX örneği — 2026-09-16, Faz 2

**Neden denendi**: Tasarımın kendisiydi ([research.md](../../specs/002-fpga-statevector-cekirdegi/research.md) R-7). Gerekçe: HLS,
`ARRAY_PARTITION`'lı bir diziye hangi parçadan erişildiğini derleme zamanında
çözemezse bütün erişimleri seri hale getirir; `K` sabit olduğu sürece bu risk
oluşmaz. Gerekçe mantıklıydı ama bir **hipotezdi ve hiç sınanmamıştı**.

**Neden olmadı**: 16 örnek **45.114 LUT** tutuyor — kalan bütçenin %57'si.
Paylaşılan tek birim (`k` çalışma zamanı parametresi) **2.409 LUT**. Ölçülen
bedel yalnızca **+%4 gecikme**. Yani hipotezin korktuğu tam serileştirme
olmadı; 42.000 LUT karşılığında hiçbir şey alınmıyordu.

**Tekrar denenmeli mi**: Hayır. Tur 17 sebebini de gösterdi: `k` sabit olsa
bile II tabanı bellek **portu** ile belirleniyor, bankalamayla değil. Şablon
sürüm `gates_pairing.hpp`'de geri dönüş için duruyor ama gerekçesi çürük.

### Bankalamayı artırarak II düşürmek (`cyclic factor` 4, 8, 16) — 2026-09-16, Faz 2

**Neden denendi**: SK-02'nin tamamı bu varsayım üzerine kuruluydu — "2^k
çakışması bankalama ile çözülür". Doğal çözüm daha çok banka.

**Neden olmadı**: Ölçüldü, **hiçbir şey kazandırmıyor**. `rx_dyn_pair_loop`'un
II'si faktör 2, 4 ve 8'de **aynı** kaldı; yalnızca LUT %84 → %86 → %90 çıktı.
Sebep: `k` çalışma zamanı değişkeni olduğu için HLS erişimin hangi bankaya
düştüğünü **kanıtlayamıyor** ve kaç banka olursa olsun en kötü durumu
varsayıyor. Gerçek sınır port sayısıydı: `RAM_2P` (1 okuma + 1 yazma) →
`RAM_T2P` (2 gerçek port) tek kelimeyle II'yi 3'ten 2'ye indirdi.

**Tekrar denenmeli mi**: Hayır — `k` derleme zamanı sabiti yapılmadıkça değil,
ki o da yukarıdaki elenen yol. Bkz. [faz2-sentez.md](../measurements/faz2-sentez.md) §13.

### Ping-pong tamponu (ayrı okuma/yazma dizileri) — 2026-09-16, Faz 2

**Neden denendi**: II=1'e ulaşmanın bilinen yolu; okuma A'dan, yazma B'ye
giderse dizi başına 2 erişim kalır ve port sınırı kalkar.

**Neden olmadı**: `sv`'nin BRAM'ini **144 → 288 blok**a çıkarıyor. Toplam bütçe
280 ve tasarım zaten 187 kullanıyor. **%91,4** ile SC-002'yi aşıyor.

**Tekrar denenmeli mi**: Hayır, 16 kübitte. Kübit sayısı 14'e inerse veya daha
büyük bir parçaya (örn. XC7Z045) geçilirse yeniden hesaplanır. Bkz.
[banking-research.md](../measurements/banking-research.md) §6.

### Tablo kurma döngülerini boru hattına almak / açmak — 2026-09-16, Faz 2

**Neden denendi**: Maliyet tabloları toplam gecikmenin **%23'ü** (1.598.208
çevrim) ve `apply_cost_layer`'ın **%89'u**. Asıl genlik döngüsü yalnızca %11.
Buradaki kazanç gerçek ve büyük görünüyordu.

**Neden olmadı**: Dört varyant ölçüldü, dördü de bütçe dışı:

| Varyant | Gecikme | LUT |
|---|---:|---:|
| Tüm tablolar dış döngü `PIPELINE II=4` | 3.780.845 | **%182** |
| Yalnız `tablo_yuksek` dış döngü `II=4` | 4.333.700 | **%166** |
| `tablo_yuksek` dış döngü `UNROLL factor=2` | 5.378.015 | **%123** |
| Tablo iç döngüleri `UNROLL` | **10.212.635** (2× yavaş) | %53 |

Sebep `gates_diagonal.hpp:62`'de zaten yazılıydı: 256 yinelemelik dış döngüyü
boru hattına almak, iç döngüleri **açmaya zorluyor** (~100 toplayıcı). Son
varyant ise ters tepti — `config_compile -pipeline_loops 0` altında `UNROLL`
boru hattını tamamen kaldırıyor ve açılmış toplayıcı zinciri seri kalıyor.

**Tekrar denenmeli mi**: Yalnızca LUT payı ciddi biçimde açılırsa (örn. Tur 16
geri alınıp %63'e inilirse bile #6 hâlâ %161 olur — yetmez). Asıl çözüm
donanım değil **algoritma** olur: tablo kurma maliyetini azaltmak.

### Zamanlama için yuvarlama kipleri ve çarpıcı gecikmesi — 2026-09-16, Faz 2

**Neden denendi**: Kritik yol 24,799 ns'ydi (hedef 10). İlk iki şüpheli:
`AP_RND_CONV`/`AP_SAT` kiplerinin pahalı olması, ve çarpıcının boru hattına
alınmamış olması.

**Neden olmadı**: İkisi de asıl sebep değildi. `AP_TRN`+`AP_WRAP` 24,8 → 17,2 ns
(yolun %31'i ama yetmez, üstelik doğruluğu bozar). `config_op mul -latency 3`
24,8 → 24,3 ns — **neredeyse hiç**. Partition faktörünü 16 → 2 yapmak 24,3 →
23,0. Asıl sebep raporda yazılıydı: `load`→`store` zinciri tek kombinasyonel
parçadaydı ve çözüm `#pragma HLS DEPENDENCE`'tı (23,0 → **12,7 ns**).

**Tekrar denenmeli mi**: Hayır. Ders: **rapordaki "Cannot meet target clock
period from X to Y" satırını önce oku**; üç tur tahmin yürütmeden önce kritik
yolu adıyla söylüyordu.

### Windows'ta Vitis HLS — 2026-09-16, Faz 2

**Neden denendi**: Doğal kurulum yolu; **15 sentez turu boyunca çalıştı**.

**Neden olmadı**: Smart App Control bir gün aracı engelledi
(`vitis-run.exe was blocked by your organization's Device Guard policy`).
`vitis-run.exe` imzasız (`NotSigned`) ve SAC **itibar tabanlıdır, kararı
zamanla değişir** — "bir kez çalıştı" güvence değildir.

**Tekrar denenmeli mi**: Hayır. SAC'ı kapatmak geri alınamaz bir sistem
güvenlik değişikliğidir ve bir derleme kolaylığı için yapılmaz. WSL/Ubuntu
kurulumu çalışıyor ve **ölçümü bozmadığı kanıtlandı** (Tur 15 birebir yeniden
üretildi). Bkz. [runbook](../runbooks/vitis-hls-kurulum.md).

### Cosim'i `cosim_design` üzerinden koşmak (n=16) — 2026-09-19, Faz 2

**Neden denendi**: Belgelenen yol. n=8'de sorunsuz çalışmıştı.

**Neden olmadı**: n=16'da koşu 13 saate çıkıyordu ve süperdoğrusal yavaşlıyordu
(0,856 → 0,036 ms/dk). Sebep tasarım değil, `run_sim.tcl`'deki tek satır:

```tcl
set ret [catch {eval exec "sh ./run_xsim.sh | tee temp2.log" >&@ stdout} err]
```

`>&@ stdout`, xsim'in yüz binlerce `Critical WARNING` satırını Tcl'in kanal
katmanından geçiriyor. Ölçüm: `xsimk` %5 CPU (aç bekliyor), `vitis-run` %98.

**Tekrar denenmeli mi**: n=16 için hayır. Cosim üç ayrı aşamadır ve 2. aşama
(`verilog/run_xsim.sh`) doğrudan kabuktan koşulabilir — **15 dk 48 sn**, 76×
hızlı, bilimsel olarak eşdeğer (aynı RTL, testbench ve uyaran). Betik:
`/root/cosim-hizli.sh`. Ayrıntı: [§20](../measurements/faz2-sentez.md).

**Yan ders**: Bu yavaşlık iki kez **diske** yıkıldı (`/mnt/c` köprüsü). İkisi de
yanlıştı ve ikisi de ölçümle çürütüldü — ikincisi, koşu zaten yerel diskteyken
aynı eğriyi çizerek. Bir hipotez çürütüldüğünde **onu yazan yorum satırı da
güncellenmeli**; güncellenmeyen yorum bir sonraki turu aynı yanlış yola sokuyor.

### Faz 2'nin CPU tabanı olarak Qiskit Aer — 2026-09-21, Faz 5

**Neden denendi**: Doğal seçim; altın referans zaten Aer ve "CPU'da ne kadar
sürüyor" sorusunun en kolay cevabı.

**Neden olmadı**: Aer, RZZ'yi CX-RZ-CX olarak ayrıştırıyor ve p=2'de **384
kapı** uyguluyor; bizim çekirdek köşegen operatörün tamamını **32 geçişe**
füzyonluyor. **12× algoritmik fark** — donanım farkı değil.

Ölçüldü ([adil-cpu-tabani](../measurements/adil-cpu-tabani_20260921_c504294.json)):
aynı çekirdek kodu konak CPU'da **3,273 ms**, Aer 32,75 ms. Yani Faz 2'nin
*"gecikmede başabaş"* sonucu bir **taban artefaktıydı**; adil tabanla dizüstü
CPU FPGA'dan **11,4× hızlı**.

**Tekrar denenmeli mi**: Hayır. Gecikme karşılaştırmasında taban, **aynı
algoritmanın** aynı platformdaki hâli olmalı. `hls/tb/bench_kernel.cpp` bunun
için var.

### FPGA'yı "gerekli" kılmak için gereksinim aramak — 2026-09-21, Faz 5

**Neden denendi**: *"GPU varken neden FPGA?"* sorusuna uygulama tarafından
cevap bulmak.

**Neden olmadı — sırayla elendi:**

| Yol | Neden düştü |
|---|---|
| **n'i büyütmek** | BRAM tavanı. 16 kübitte %67'deyiz, 17 sığmıyor |
| **Daha çok paralellik** | [ADR 0009](0009-paralellik-turu-kapatildi.md): bankayı 4'e katlamak sıfır kazanç, bellek portu bağlıyor |
| **Çoklu eşzamanlı örnek** | İkinci n=16 statevector BRAM'e sığmaz (%134). LUT %43'te boşta ama bağlayıcı kaynak BRAM |
| **Bulut bağlantısızlık** | Kaba kuvvet de çevrimdışı ve ~85.000× hızlı çalışıyor — gerekçelendirmiyor |
| **n=9'a inip mikrosaniye sınıfı** | **Kötüleşiyor**: 4 şehir = 6 tur, daha da trivial. Küçük N emülasyonu daha saçma kılar |

**Kök sebep** (yapısal, düzeltilemez): statevector `2^((N-1)²)`, çözüm uzayı
`(N-1)!`. Emülatör, **emüle edebildiği her boyutta**, aynı TSP'yi kaba
kuvvetle çözmekten üstel olarak pahalıdır. N=5'te 65.536 genlik, 24 tur için.
Ölçüldü: kaba kuvvet **43,2 µs** (kesin) vs QAOA yolu 3,69 s — **~85.000×**
([kaba-kuvvet-kiyas](../measurements/kaba-kuvvet-kiyas_20260921_c504294.json)).

**Tekrar denenmeli mi**: Hayır, ve arama **kapatıldı**. Hiçbir *uygulama*
gereksinimi bu iş yükü için hızlandırıcıyı gerekçelendiremez. Gerekçe
uygulamada değil, **emülatörün kendisindedir** — proje bir rota optimizasyonu
ürünü değil, bir donanım emülasyon çalışmasıdır
([CLAUDE.md tez çerçevesi](../../CLAUDE.md), [neden-fpga.md §0.5](../neden-fpga.md)).

### ARM tabanını `ap_fixed_mock` ile ölçmek — 2026-09-21, Faz 5

**Neden denendi**: Donanımla **aynı** aritmetiği (Q1.17) koşturuyor; en adil
taban gibi görünüyordu.

**Neden olmadı**: Taklit sınıf her işlemi `double`'da yapıp kuantalıyor ve
Cortex-A9'un NEON'u **çift duyarlık desteklemiyor**. Ölçüldü: ARM'da Q1.17
taklidi **1579 ms**, yerel float **84,1 ms** — **18,8× fark**, ve bu fark bir
mimari gerçek değil taklit sınıfın artefaktı.

Yalnız taklidi ölçseydik **"42× hızlanma"** raporlayacaktık; gerçek sayı
**2,26×**.

**Tekrar denenmeli mi**: Hayır. Taban, hedef platformda **yetkin bir
gerçeklemenin** yapacağı şey olmalı. `QIR_REAL_FLOAT` bayrağı bunun için
eklendi ve **sentezde kullanılmaz**.
