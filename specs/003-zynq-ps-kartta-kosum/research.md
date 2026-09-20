# Faz 0 — Araştırma: Zynq PS + Kartta Koşum

**Tarih**: 2026-09-19 · **Dal**: `003-zynq-ps-kartta-kosum` ·
**Spec**: [spec.md](spec.md)

Anayasa Prensip I her karar noktasında en az iki alternatifin karşılaştırılmasını
şart koşuyor. Aşağıdaki altı başlık, `plan.md`'deki her NEEDS CLARIFICATION'ı
kapatır.

---

## Bu fazın açılışta bulduğu iki sert gerçek

Plan yazılırken depo incelendi ve spec'in varsaydığı iki şeyin **doğru olmadığı**
görüldü. İkisi de plana yapısal olarak giriyor.

### Gerçek 1 — Elde bitstream yok, IP var

`artifacts/ip/qir_kernel_ip_20260917_15931cc.zip`, `export_design -flow impl`
çıktısıdır: **Vivado IP kataloğu paketi**, bitstream değil
([artifacts/ip/README.md](../../artifacts/ip/README.md) bunu zaten yazıyor).
Faz 2'nin "implementasyon koşuldu" dediği şey, IP'nin **bağlamdan bağımsız**
(out-of-context) P&R'ıdır — gerçek kaynak sayılarını verir ama karta yüklenecek
bir ikili üretmez.

> **Sonuç**: US1'den önce bir **Vivado blok tasarımı** (Zynq7 PS + qir_kernel +
> AXI ara bağlantı) kurulup sentezlenmeli. Bu, spec'te adı geçmeyen ama US1'in
> ön koşulu olan bir iş kalemidir ve planın ikinci görev öbeğidir.

### Gerçek 2 — Kart genlik vektörünü dışarı vermiyor

`hls/src/qir_kernel.cpp:135` imzası ve Faz 2 sözleşmesi
([kernel-interface.md](../002-fpga-statevector-cekirdegi/contracts/kernel-interface.md))
nettir:

| Yön | İçerik |
|---|---|
| Aşağı (host → kart) | `phases`, `cos_beta`, `sin_beta`, `cost`, `p` |
| Yukarı (kart → host) | **tek `float`: `beklenen_deger`** |

Madde K-1: *"Çekirdek hiçbir koşulda `m_axi` portu açmaz."* Statevector çip-içi
BRAM'de kalır ve **AXI'den görünmez**. 65.536 genliği çekmek zaten 288 KB'dir ve
hızlandırmayı anlamsız kılar.

> **Sonuç**: SC-001'in *"fidelity ≥ 0,99"* ölçütü **kartta doğrudan
> ölçülemez** — fidelity genlik vektörü gerektirir, kart genlik vermez.
> Çözüm §R3'te.

---

## R1 — PYNQ 2.5 ile Vivado 2025.2 `.hwh` uyumluluğu ⚠️ KRİTİK

**Soru**: Kartta PYNQ 2.5 (Glasgow, 2019) var; bitstream Vivado 2025.2 ile
üretilecek. PYNQ'nun `Overlay` sınıfı bu `.hwh` dosyasını ayrıştırabilir mi?

**Bulgu**: Ayrıştıramama riski **yüksek ve belgelenmiş**. PYNQ topluluk
forumunda `.hwh` ayrıştırma hataları **tek bir Vivado alt sürümü farkında bile**
raporlanmış: 2019.1 → 2019.2 geçişi `hwh_parser.py` içinde
`AttributeError: 'NoneType' object has no attribute 'get'` üretmiş; aynı hata
PYNQ 2.4–2.6 ile Vivado 2020.1 kombinasyonunda da görülmüş. Buradaki fark
**altı yıl ve on bir sürüm**. Beklenti: çalışmayacağı yönünde.

**Karar**: `Overlay`'e bel bağlanmaz. İki katmanlı yol izlenir ve **üst katman
başarısız olursa alt katmana düşülür**. Alt katman, `Overlay`'in sunduğu tek
şeyden (`.hwh`'den otomatik IP keşfi) vazgeçer — o da bizde zaten gereksizdir.

| Katman | Yol | Ne gerektirir | Risk |
|---|---|---|---|
| **A (önce denenir)** | `Overlay("qir.bit")` | `.hwh` ayrıştırılabilmeli | Yüksek — R1'in ta kendisi |
| **B (yedek, sağlam)** | `Bitstream("qir.bit").download()` + `MMIO(taban, 0x3000)` | Yalnızca sabit taban adres | **Düşük** |

**Yedek yolun neden sağlam olduğu**: Çekirdeğin **tek** arayüzü `s_axilite`.
`m_axi` yok → DMA yok → `pynq.allocate` yok → sürücü keşfi yok. Gereken tek şey
AXI-Lite taban adresi (blok tasarımda biz atıyoruz, tipik `0x43C0_0000`) ve
register haritası — ki o da IP paketinin içinde **hazır**:
`drivers/qir_kernel_v0_1/src/xqir_kernel_hw.h`. Yani B katmanı, PYNQ'nun
ayrıştırıcısına **hiç dokunmadan** tam işlevsellik verir.

`Bitstream` sınıfı `.hwh` olmadan da `.bit`'i PL'e indirir (PYNQ belgeleri bunu
açıkça bir yol olarak gösterir); `MMIO(taban, uzunluk)` ise adresi elle alan
alt seviye sınıftır.

**Erken uyarı denemesi (planın İLK görevi)**: Tam bitstream'i beklemeye gerek
yok. `.hwh`, blok tasarımın çıktı ürünleri üretilirken yazılır
(`validate_bd_design` + `generate_target all`) — **sentez ve implementasyon
gerekmez**. Kukla BD karta kopyalanıp ayrıştırıcıya tek satırda verilir.
Böylece R1 **saatler yerine bir saatte**, asıl sentez başlamadan cevaplanır.
Sonuç ne olursa olsun plan durmaz — yalnızca A mı B mi kullanılacağı belli olur.

> ⛔ **Kukla BD PS-only OLMAMALI.** İlk taslakta öyle yazılmıştı; **yanlıştır**
> ve testi anlamsız kılar. Gerekçe: `.hwh` ayrıştırıcısının asıl işi IP'leri ve
> register haritalarını çıkarmaktır. PS-only bir dosyada özel IP **yoktur**,
> yani ayrıştırıcı için mümkün olan **en kolay durumdur** ve `ip_dict` boş
> döner. Yukarıda kaynak verilen PYNQ forum hatalarının tamamı IP tarafındadır
> (`MEMORYMAP` / `ADDRESSBLOCK` şeması, arayüz adlandırması, yeni XML
> öznitelikleri) — hiçbiri PS-only dosyada görünmez.
>
> **Kukla BD, PS + gerçek `qir_kernel` IP içermelidir.** Ek maliyet ~5 dakika;
> karşılığında test gerçekten belirleyici olur. Aksi hâlde probe "geçer",
> bütün konak kodu A yoluna göre yazılır ve gerçek bitstream gelince `.hwh`
> ayrıştırılamaz — öbek 0'ın önlemek için var olduğu senaryonun ta kendisi.

> ⚠️ Karta PYNQ 3.x yüklemek **elenmiştir**: yeniden imaj yazmak çalışan tek
> donanımı riske atar, saatler sürer ve PYNQ 3.0 da Vivado 2022.1 tabanlıdır —
> 2025.2 ile arada hâlâ üç yıl kalır. Risk aynı yerde durur, bedeli çok yüksektir.

---

### ✅ SONUÇ — 2026-09-20, kartta ölçüldü: **A YOLU AÇIK**

Tahmin *"çalışmayacağı yönünde"* idi. **Yanlış çıktı.** PYNQ 2.5 (çekirdek
`4.19.0-xilinx-v2019.1`), Vivado 2025.2'nin `.hwh`'sini altı yıllık farka
rağmen sorunsuz ayrıştırdı.

**Deney**: PS7 + **gerçek** `qir_kernel` IP + `axi_interconnect` +
`proc_sys_reset` içeren kukla BD ([probe_hwh.tcl](../../fpga/bd/probe_hwh.tcl)),
sentez koşulmadan `.hwh` üretildi (156.920 bayt), seri konsoldan karta
aktarıldı (md5 `7e5168268ab1604e5d6740781bdc6919` iki tarafta da doğrulandı) ve
[probe_test.py](../../fpga/bd/probe_test.py) koşuldu.

**Sonuç — üç katmanın üçü de okundu:**

| Katman | Beklenen | Okunan |
|---|---|---|
| IP keşfi | `ip_dict` dolu | ✅ 1 IP: `qir_kernel_0`, tip `qir-engine:hls:qir_kernel:0.1` |
| Taban adres | `.hwh`'deki `BASEVALUE` | ✅ `0x40000000`, uzunluk `0x10000` |
| Register haritası | 11 register | ✅ **11/11** doğru ofsetlerle |

Okunan register'lar: `CTRL` +0x000 · `GIER` +0x004 · `IP_IER` +0x008 ·
`IP_ISR` +0x00C · `Memory_cos_beta` +0x020 · `Memory_cost` +0x2000 ·
`Memory_phases` · `Memory_sin_beta` · `p` · `beklenen_deger` ·
`beklenen_deger_ctrl`.

**Karar**: Öbek 4'ün konak kodu **A yoluna** göre yazılır — `Overlay("qir.bit")`.
B yolu (`Bitstream` + `MMIO`) yedek olarak belgede kalır; artık zorunlu değil.

#### ⚠️ Deneyin ortaya çıkardığı iki yeni kısıt

**1. `import pynq` root istiyor.**

```
RuntimeError: Root permission needed by the library.   (pynq/xlnk.py:133)
```

Konak kodu **`sudo` ile koşacak**. Karttaki `sudo` parola istiyor
(`sudo: a password is required`), yani otomatik koşumlar için ya parolasız
sudo kuralı ya da bir servis gerekir — öbek 4 başlamadan çözülmeli.

Sondanın bunu kazara atlatmış olduğu not edilmeli: ilk aday içe aktarma bu
hatayı verdi, `except` yakaladı, ikinci denemede modül `sys.modules`'da yarı
yüklü olduğu için geçti. **Ayrıştırma sonucu geçerlidir** (değerler `.hwh` ile
birebir), ama `Overlay()`'in tam yolu root olmadan uçtan uca denenmedi.

**2. `HWH` diye bir sınıf yok.**

`pynq/pl_server/hwh_parser.py` (PYNQ 2.5) üç sınıf tanımlar:

```
 78: class _HWHABC(metaclass=abc.ABCMeta)
494: class _HWHZynq(_HWHABC)          ← bizim kartımız
547: class _HWHUltrascale(_HWHABC)
```

Belgelerde geçen `pynq.pl_server.hwh_parser.HWH` **bu sürümde mevcut değil**.
Doğrudan sınıf adı kullanılacaksa Zynq-7000 için `_HWHZynq`'tir. `Overlay`
doğru sınıfı kendi seçtiği için konak kodu bundan etkilenmez — ama teşhis
betiği yazan herkes bu tuzağa düşer.

**Elenen alternatifler**

| Alternatif | Neden elendi |
|---|---|
| Karta PYNQ 3.x imajı yazmak | Çalışan donanımı riske atar; açığı kapatmaz (3.0 = Vivado 2022.1) |
| `.hwh`'yi elle yamamak | Kırılgan, belgelenemez, her yeniden sentezde tekrarlanır |
| IP'yi eski Vivado ile üretmek | 2019.1 kurulu değil; 2025.2 çıktısı geri alınamaz |

### 🎁 2026-09-19 — hazır bir 2025.2 `.hwh` bulundu, T001–T005 kısalıyor

Vitis `export_design -flow impl` koşarken implementasyon için **kendi blok
tasarımını kuruyor** ve yan ürün olarak bir `.hwh` bırakıyor. Yani T002'nin
üretmeye çalıştığı dosya **zaten elimizdeydi**:

    qir_hls_prj/solution1/impl/verilog/project.gen/sources_1/bd/bd_0/hw_handoff/bd_0.hwh

İçeriği doğrulandı:

| | |
|---|---|
| `VIVADOVERSION` | **2025.2** ✓ sorgulanan sürüm |
| `MODULE` | `hls_inst` / **`qir_kernel`** ✓ gerçek IP |
| `MEMRANGE` | `s_axi_control`, `Reg`, `0x0000`–`0xFFFF` |
| `REGISTER` | **0** — register düzeyi ayrıntı yok |

⚠️ **`qir_hls_prj/` gitignore'da ve `open_solution -reset` onu siliyor.** Dosya
bu yüzden **`artifacts/ip/bd_0_20260917_15931cc.hwh`** altına kopyalandı.
(2026-09-19'da n=16 cosim başlatılırken son anda kurtarıldı.)

**Ne test eder, ne etmez**

- ✅ PYNQ 2.5'in **2025.2 biçimini** ve **özel IP'li** bir `.hwh`'yi okuyabilmesi
  — R1'in asıl sorusu budur ve bilinen ayrıştırma hatalarının hepsi bu yoldadır
- ❌ **Adres ataması**: bu BD'de PS yok, `BASEVALUE = 0x0`. Gerçek BD'de PS
  olacak ve taban adres gerçek olacak
- ❌ `REGISTER` yok → en iyi ihtimalle **kısmi başarı** çıkar (`ip_dict` dolar,
  `registers` boş kalır). Sorun değil: register haritası
  [contracts/axi-register-map.md](contracts/axi-register-map.md)'de zaten var,
  erişim `MMIO` ile yapılır.

**Sonuç**: T001–T005 yerine tek bir kopyalama + tek komut yeterli. Cevap
**5 dakikada** alınır. T001–T007 yine de yapılmalı (gerçek BD'nin `.hwh`'si PS
ve adres ataması içerecek) ama **hangi yola göre kod yazılacağı bugünden
bilinebilir**.

**Koşulacak** (kart açıkken):

    scp artifacts/ip/bd_0_20260917_15931cc.hwh xilinx@<KART-IP>:/home/xilinx/probe.hwh
    # sonra seri konsoldan fpga/bd/probe_test.py

---

## R2 — Bitstream nasıl üretilecek (board files yok)

**Bulgu (yerinde doğrulandı)**: WSL/Ubuntu'da `/opt/Xilinx/2025.2/Vivado`
**kurulu** ve `xc7z020` parça verisi mevcut (284 MB, `parts/xilinx/zynq/`).
Ancak `data/boards/board_files` **boş** — PYNQ-Z2 board dosyası yok.

**Karar**: Board dosyası indirmek yerine **Zynq7 PS'i Tcl ile elle
yapılandırmak**. Board preset'inin sağladığı şey DDR modeli, PS saat referansı
ve FCLK ayarlarıdır; üçü de Tcl'de birkaç satırdır ve **depoya commit edilebilir
metindir** — board dosyası ise harici, sürümsüz bir bağımlılıktır.

| Seçenek | Artı | Eksi | Karar |
|---|---|---|---|
| **Tcl ile elle PS preset** | Depoda metin, yeniden üretilebilir, bağımlılık yok | DDR/saat ayarları elle yazılır | ✅ **seçildi** |
| Board files indir | Preset hazır | Harici indirme, 2025.2 uyumu belirsiz, sürümsüz | ✗ |
| Vivado GUI'de elle kurmak | Görsel | WSL'de GUI zahmetli, **yeniden üretilemez** | ✗ |

Blok tasarım **minimum** tutulur: `processing_system7` + `qir_kernel` +
`axi_interconnect` (veya `smartconnect`) + `proc_sys_reset`. FCLK0 = 100 MHz
(Faz 2 sentezinin hedef saati).

> Blok tasarımı üreten Tcl betiği **git'e girer** (`fpga/bd/qir_bd.tcl`, karar K3).
> Üretilen `.bit`/`.hwh` girmez — [repo-conventions §3](../../docs/repo-conventions.md)
> gereği `artifacts/` altında kalır, depoda yalnızca **üretim komutu ve
> SHA-256 özeti** bulunur. FR-016 böyle karşılanır (§R6).

---

## R3 — Genlik olmadan doğrulama: çoklu izdüşüm

**Soru**: Kart yalnız skaler döndürüyorsa fidelity nasıl raporlanır?

**Karar (onaylandı 2026-09-19, K1)**: **Çoklu izdüşümlü beklenen değer
eşdeğerliği.** Tek skalerle yetinilmez — aynı statevector, **N farklı `cost`
vektörüyle** okunur.

### Anahtar gözlem: `cost` bir AXI girişidir

`cost`, `run_circuit`'e hiç girmez; yalnızca `expectation_scaled`'i besler
(`qir_kernel.cpp:157-158`). Yani aynı devre — aynı `phases`, `cos_beta`,
`sin_beta`, `p` — sabit tutulup **yalnız `cost` değiştirilerek** yeniden
koşulursa, kart **aynı statevector'ün farklı bir izdüşümünü** döndürür.

Çekirdek durumsuz (madde K-4) ve belirlenimci olduğundan her koşum aynı
statevector'ü yeniden üretir. Dolayısıyla N koşum = **aynı vektörün N bağımsız
doğrusal izdüşümü**.

> **Tasarım değişmez. Yeniden sentez yok. Kaynak/zamanlama sayıları geçerli
> kalır.** Bedeli yalnızca N × ~37 ms koşum süresidir.

### Protokol

| | |
|---|---|
| İzdüşüm sayısı | **en az 20** rastgele `cost` vektörü |
| Tohum | Sabit ve kaydedilir (yeniden üretilebilirlik) |
| Geçme ölçütü | **Hepsi** kart ile C-sim arasında **birebir** tutmalı |
| Yazma maliyeti | İzdüşüm başına yalnız `cost` (272 word); `phases` bir kez yazılır |

### ⚠️ Bu yöntemin görmediği şey: faz

`expectation_scaled`, **olasılık ağırlıklı** bir toplamdır:

```
return Σ(olasilik_i · E_i) / Σ(olasilik_i)
```

`olasilik_i = |ψ_i|²`. Yani izdüşümler genlik **büyüklüklerini** kısıtlar,
**fazları görmez**. Yirmi rastgele `cost` vektörünün hepsinde aynı anda
yanlış bir olasılık dağılımının doğru sonuç vermesi pratikte beklenmez — ama
faz ekseni bu yöntemle **hiç** sınanmaz.

**Faz tarafı ayrıca kanıtlanmıştır**: n=8 cosim PASS verdi (Faz 2) — RTL'in
faz davranışı orada doğrulandı. Rapor bu iş bölümünü **açıkça yazar**:

| Eksen | Kanıt | Nerede ölçüldü |
|---|---|---|
| Genlik büyüklükleri | 20 bağımsız izdüşüm, kart ↔ C-sim birebir | **Bu fazda, kartta** |
| Faz | n=8 cosim PASS | Faz 2, RTL simülasyonunda |
| Genlik ↔ altın referans fidelity | ≥0,99997 (n=8/12/16) | Faz 2, C-sim'de |

### Doğrulama zinciri

```
Qiskit altın referans  ←(fidelity, ÖLÇÜLDÜ: ≥0,99997)→  C-sim
                                                          ↕  (aynı kaynak: run_circuit)
                                                        KART   ←(20 izdüşüm, bu fazda)
```

Zincirin gücü: `run_circuit` **başlıkta `inline`** tanımlıdır
(`qir_kernel.hpp:41`) ve C-sim ile sentez yolu **birebir aynı kodu** derler
(Faz 2 sözleşme maddesi T-1).

### Ne iddia edilebilir / edilemez (Prensip II, SC-008)

| İddia | Geçerli mi |
|---|---|
| "Kartın 20 izdüşümü de C-sim ile birebir tutuyor" | ✅ doğrudan ölçülür (SC-003) |
| "Kartın beklenen değeri altın referansla uyuşuyor" | ✅ doğrudan ölçülür |
| "Kartın olasılık dağılımı C-sim'inkiyle aynıdır" | ✅ 20 bağımsız kısıt — güçlü |
| "Kartın **fazları** doğrudur" | ⚠️ bu fazda **ölçülmez**; n=8 cosim'den gelir |
| "Kartın **genlik vektörünün** fidelity'si ≥0,99" | ⚠️ **devralınan çıkarım** — rapora böyle yazılır, ölçülmüş gibi değil |

**Elenen alternatifler**

| Alternatif | Neden elendi |
|---|---|
| Tek `cost` vektörüyle tek skaler | Tek kısıt; hatanın gizlenme ihtimali gereksiz yere açık kalır |
| Çekirdeği `m_axi` ile yeniden sentezlemek | Madde K-1 ve Prensip III ihlali; ölçülen tasarım ≠ raporlanan tasarım olur |
| Genlik penceresi portunu **peşinen** eklemek | Yeniden sentez + implementasyon; Faz 2'nin kaynak/zamanlama sayılarını geçersiz kılar |

> **Teşhis yolu açık tutulur**: 20 izdüşüm ayrışır **ve** ayrışma deseni nedeni
> göstermezse — ve yalnız o zaman — genlik penceresi varyantı devreye alınır.
> Peşinen bedeli ödenmez (Prensip VI). Çoklu izdüşümün teşhis değeri de tek
> skalerden yüksektir: hangi `cost` vektörlerinde saptığı, hatanın `h` mi `J`
> yolunda mı olduğunu daraltır.

### R3b — Devralınan borç: ölçekleme

Faz 2 sözleşmesi bunu açıkça Faz 5'e bırakmış:

> *"Konak tarafı `h` ve `J`'yi `[-1, 1)` aralığına ÖLÇEKLEMEK ZORUNDADIR…
> Bu, Faz 5'e devredilen açık bir borçtur."*

Ham katsayılar ~1e4 mertebesinde; `ap_fixed` doyurması onları **sessizce**
kırpar ve sonuç yanlış çıkar — üstelik hata donanıma yıkılır. Ölçek çarpanı
`beklenen_deger`'e geri uygulanmalıdır.

**Karar — konak kodlayıcı önce kartsız doğrulanır.** Host tarafındaki
kodlayıcı/çözücü (ölçekleme + sabit-nokta paketleme) **C-sim'e karşı, kart
olmadan** doğrulanır (Prensip V). Ancak geçtikten sonra karta gidilir.

> Bu sıralama planın en önemli tasarım kararıdır: kodlayıcı önceden
> doğrulanmazsa, kartta çıkan her uyuşmazlık **"donanım mı, kodlayıcı mı"**
> belirsizliğinde kalır. Önce doğrulanırsa, uyuşmazlık **donanıma izole olur**.

---

## R4 — Gecikme nasıl ölçülür ve kapsamı ne

**Karar**: PS tarafında `time.perf_counter()`; ek zamanlayıcı IP'si **yok**.

Gerekçe: Hedef büyüklük ~37 ms. ARM A9'da `perf_counter` çözünürlüğü ~µs —
bağıl hata %0,003. Ayrı bir AXI Timer IP'si blok tasarımı büyütür, MMIO ile
ayrıca bulunması gerekir ve **bu ölçekte hiçbir şey kazandırmaz**.

**Üç kapsam ayrı ayrı ölçülür** (FR-007 bunu şart koşuyor):

| Sembol | Kapsam | Nasıl |
|---|---|---|
| `T_cekirdek` | `ap_start` yazımı → `ap_done` görülmesi | Yoklama döngüsü çevresinde sayaç |
| `T_yazma` | 1.095 register yazımı | Yazma döngüsü çevresinde sayaç |
| `T_uctan_uca` | Kodlama + yazma + koşum + okuma | Tüm çağrı çevresinde sayaç |

1.095 rakamı register haritasından gelir (§ contracts): `phases` 816 +
`cost` 272 + `cos_beta` 3 + `sin_beta` 3 + `p` 1. Bu, ölçüm kapsamını
**akademik bir ayrıntı olmaktan çıkarıp** raporlanması zorunlu bir kalem yapar:
CPU tarafında böyle bir aktarım maliyeti yok, dolayısıyla `T_cekirdek` ile
`T_uctan_uca` kıyasta **farklı sonuç verir** ve ikisi de yazılır.

> ⚠️ `ap_done` yoklaması Python'dan yapılır; yoklama aralığı `T_cekirdek`'e
> **üst taraftan** hata ekler. Yoklama periyodu ölçülüp kaydedilir.

---

## R5 — Enerji: INA219'u kim okuyacak? (bitstream'den ÖNCE karar)

**Bu başlık US3 için ama kararı ŞİMDİ alınmalı.** Sebep: karar blok tasarımı
etkiliyor ve bitstream yeniden üretmek saatler sürüp FR-016 izlenebilirliğini
bozuyor.

**Sorun**: PYNQ-Z2'de PMOD ve Arduino/RPi başlıklarının I2C hatları **PL
pinlerine** bağlı. Hazır `base.bit` bunları Pmod IOP ile sürer — ama **bizim
özel bitstream'imiz base overlay'i değiştirir ve o IOP ortadan kalkar.**
Yani "kart kendi INA219'unu okusun" demek, blok tasarımda I2C yolu açmak demek.

| Seçenek | Artı | Eksi | Karar |
|---|---|---|---|
| **PS I2C0'ı EMIO ile dışarı vermek** | Birkaç LUT; kart kendi gücünü okur; delta yönteminde okuyucunun maliyeti **iki tarafta da sadeleşir** | BD'ye kısıt + blok eklenir | ✅ **seçildi — ilk bitstream'e dahil** |
| Dizüstüden USB-I2C köprüsüyle okumak | Karta hiç dokunmaz, tedirginlik yok | Elde olduğu **doğrulanmadı**; tedarik riski | 🔸 yedek |
| Sonra eklemek | Şimdi iş yok | Bitstream'i yeniden üretir; SHA değişir, ölçümler yeniden alınır | ✗ |

**Gerekçe (on dakika şimdi, üç saat sonra)**: EMIO I2C eklemenin maliyeti
neredeyse sıfırdır ve zamanlamaya dokunmaz; eklemeyip sonra ihtiyaç duymanın
maliyeti tam bir sentez turu **artı** US1/US2 ölçümlerinin yeniden alınmasıdır
(çünkü ölçülen ikili değişmiş olur).

**Yöntem her iki tarafta aynı kalır (FR-009c)**: boş güç ve yük altındaki güç
ayrı okunur, koşum enerjisi **farktan** hesaplanır. CPU tarafı batarya sayacıyla
ölçüldü (0,644 J/koşum); kart tarafı INA219 ile ölçülecek. Alet farklı, **yöntem
aynı** — spec bunu açıkça serbest bırakıyor.

**Tek koşum görünmez (FR-009d)**: ~37 ms hiçbir güç ölçerde ayırt edilemez.
İş yükü en az 60 sn döngüye alınır, toplam enerji koşum sayısına bölünür —
CPU tarafında kullanılan yöntemin aynısı (`scripts/cpu_load_loop.py`).

---

## R6 — Bitstream saklama (FR-016 / SC-010)

**Bulgu**: Karar zaten var. [repo-conventions §3](../../docs/repo-conventions.md):
büyük ikililer git'e **hiç** girmez; depoda yalnızca **üretim komutu ve SHA-256
özeti** durur. `artifacts/bitstream/` ve `artifacts/overlay/` mevcut ve
`.gitignore`'da (satır 46–47).

**Karar** — üç parçalı, `artifacts/ip/` için zaten işleyen kalıbın aynısı:

| Parça | Nerede | Git'e girer mi |
|---|---|---|
| Blok tasarım Tcl'i (asıl kaynak) | `fpga/bd/qir_bd.tcl` | ✅ evet |
| `.bit` + `.hwh` | `artifacts/bitstream/qir_<tarih>_<hash>.{bit,hwh}` | ✗ hayır |
| SHA-256 + üretim komutu + araç sürümü | `artifacts/bitstream/README.md` | ✅ evet |

Adlandırma `artifacts/ip/` ile aynı: `<tarih>_<git-hash>`. Böylece hangi kod
sürümünden üretildiği **dosya adında** taşınır (SC-010).

---

## Çözülen bilinmeyenlerin özeti

| # | Soru | Karar |
|---|---|---|
| R1 | PYNQ 2.5 `.hwh`'yi okur mu? | Belirsiz → **önce denenir**; yedek `Bitstream`+`MMIO` (sağlam) |
| R2 | Bitstream nasıl üretilir? | Vivado 2025.2 (WSL, kurulu), PS preset **Tcl ile elle** |
| R3 | Genlik yokken doğrulama? | **≥20 `cost` vektörüyle çoklu izdüşüm**; faz n=8 cosim'den gelir; fidelity **devralınır** |
| R3b | Ölçekleme borcu? | Konak kodlayıcı **önce kartsız** C-sim'e karşı doğrulanır |
| R4 | Gecikme ölçümü? | `perf_counter`, üç kapsam ayrı ayrı |
| R5 | INA219'u kim okur? | Kart okur → **EMIO I2C ilk bitstream'e dahil** |
| R6 | Bitstream saklama? | Tcl git'te, ikili `artifacts/`'ta, SHA-256 depoda |
| R7 | Donanım kodu nereye? | **Yeni `fpga/` üst dizini** — aşağıda |

**NEEDS CLARIFICATION kalmadı.**

---

## R7 — Donanım kaynağı için yeni `fpga/` üst dizini

**Karar (onaylandı 2026-09-19, K3)**: Vivado blok tasarımı `hls/` altına
**konmaz**; yeni bir `fpga/` üst dizini açılır.

**Gerekçe**: [repo-conventions §2](../../docs/repo-conventions.md) `hls/`'i
*"Vitis HLS kaynakları, C-sim, Tcl akışı (Faz 2)"* diye tanımlıyor. Vivado
blok tasarımı HLS değildir; oraya konması o tanımla çelişir. Ayrıca araç
zinciri **zaten bölünmüş** durumda — devir noktası `artifacts/ip/`'tir:
HLS orada biter, Vivado orada başlar.

```
fpga/
├── README.md        # yeni
├── bd/              # Vivado blok tasarım: probe_hwh.sh, qir_bd.tcl, build.sh
└── rtl/             # ŞİMDİDEN AYRILDI — elle yazılacak Verilog için
```

`fpga/rtl/` şimdiden ayrılır: elle yazılan RTL `hls/` altına konamaz ve
ileride gerekirse dizin tartışması yeniden açılmaz.

**Aynı değişikliğe dahil edilecekler** (dizin eklemenin bedeli budur):

| Dosya | Değişiklik |
|---|---|
| `docs/repo-conventions.md` §2 | Dizin listesine `fpga/` satırı |
| `CLAUDE.md` Depo haritası | Aynı satır |
| `fpga/README.md` | Yeni — dizinin kapsamı ve `hls/` ile sınırı |

Bitstream çıktısı **`artifacts/bitstream/`'e gitmeye devam eder** — `fpga/`
kaynak dizinidir, yapıt dizini değil.

## Kaynaklar

- [Vivado 2019.2 HWH parser issue — PYNQ forum](https://discuss.pynq.io/t/vivado-2019-2-hwh-parser-issue/1381)
- [Parse hwh file failed — PYNQ forum](https://discuss.pynq.io/t/parse-hwh-file-failed/2975)
- [Error Loading Overlays made with Vivado 2023 — PYNQ forum](https://discuss.pynq.io/t/error-loading-overlays-made-with-vivado-2023-not-reading-the-tcl-correctly/6414)
- [Overlay — PYNQ belgeleri](https://pynq.readthedocs.io/en/v3.1/pynq_libraries/overlay.html)
- [Allocate — PYNQ 2.5 belgeleri](https://pynq.readthedocs.io/en/v2.5/pynq_libraries/allocate.html)
