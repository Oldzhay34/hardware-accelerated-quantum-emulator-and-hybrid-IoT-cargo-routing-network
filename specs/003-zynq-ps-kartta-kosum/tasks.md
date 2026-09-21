---
description: "Faz 5 görev listesi — Zynq PS + Kartta Koşum"
---

# Tasks: Faz 5 — Zynq PS + Kartta Koşum

**Input**: `specs/003-zynq-ps-kartta-kosum/` altındaki tasarım belgeleri

**Prerequisites**: [plan.md](plan.md), [spec.md](spec.md), [research.md](research.md),
[data-model.md](data-model.md), [contracts/](contracts/), [quickstart.md](quickstart.md)

## SIRADAKİ

**Hedef (tek cümle)**: 63 görev üretildi; sıradaki tek iş **T001–T007 (G0)** —
PYNQ 2.5'in Vivado 2025.2 `.hwh`'sini ayrıştırıp ayrıştıramadığını öğrenmek.

**Dokunulacak dosyalar**: `fpga/bd/probe_hwh.tcl`, `fpga/bd/probe_hwh.sh`,
`fpga/bd/probe_test.py`, `artifacts/ip/qir_kernel_ip_20260917_15931cc.zip`

**Bilinen tuzak**: ⛔ Kukla BD **PS-only olmamalı** — PS-only bir `.hwh`'de özel
IP yoktur, `ip_dict` boş döner ve bilinen ayrıştırma hatalarının hiçbiri (hepsi
IP tarafındadır) tetiklenmez. Probe "geçer", bütün konak kodu A yoluna göre
yazılır, gerçek bitstream gelince `.hwh` ayrıştırılamaz — G0'ın önlemek için var
olduğu senaryonun ta kendisi. **Kart şu an kapalı**; açılınca DHCP adresi
değişebilir, seri konsoldan (COM3, 115200) `hostname -I` ile doğrula.

**Son güncelleme**: 2026-09-19, Faz 5.2 (görevler üretildi)

Donanım durumu, ölçülmüş değerler ve onaylanan K1/K2/K3 kararları:
[SIRADAKI.md](SIRADAKI.md)

---

**Testler**: Yalnız konak kodlayıcı için test görevi var (madde H-5 şart koşuyor —
kartsız doğrulama kapısı). Kart tarafı "test" değil **ölçüm**dür.

**Organizasyon**: Görevler plan.md'deki **8 iş öbeğinin sırasını korur**.
Öbek 0 → Faz 1, öbek 1–3 → Faz 2 (temel), öbek 4–7 → Faz 3–6 (US1–US4).

## Format: `[ID] [P?] [Story] Açıklama`

- **[P]**: Paralel koşabilir (farklı dosya, tamamlanmamış göreve bağımlı değil)
- **[Story]**: US1/US2/US3/US4 — yalnız kullanıcı hikâyesi fazlarında

## Yol kuralları

- Donanım **kaynağı**: `fpga/` (yeni üst dizin, karar K3)
- Servis tarafı: `agent/`
- Yapıtlar: `artifacts/bitstream/` — git'e girmez
- Ölçümler: `docs/measurements/` — damgalı JSON

---

## ⚠️ Her kart görevinden önce

**Kart şu an kapalı.** Açıldığında DHCP adresi değişebilir — `192.168.1.2`
bir varsayımdır, sabit değil. Seri konsoldan (COM3, 115200 8N1) `hostname -I`
ile doğrulanmadan hiçbir `ssh`/`scp` komutu koşulmaz.

⛔ **Besleme düzenine dokunulmaz**: adaptör + **JP5 = REG**, boot kaynağı
**JP4 = SD**. Enerji ölçümlerinin karşılaştırılabilirliği buna bağlı.

---

## Phase 1: G0 — `.hwh` uyumluluk denemesi (öbek 0) ⚠️ İLK, BLOKLAYICI

**Amaç**: PYNQ 2.5'in Vivado 2025.2 `.hwh`'sini ayrıştırıp ayrıştıramadığını
öğrenmek — yani öbek 4'ün konak kodunun **A yoluna mı B yoluna mı** göre
yazılacağını.

**Neden ilk**: Cevap sonradan öğrenilirse yazılan konak kodu çöpe gider.
Sentez beklemeye gerek yok — `.hwh`, BD çıktı ürünleri üretilirken yazılır.

> 🎁 **KISAYOL (2026-09-19 bulundu)**: Vitis `-flow impl` koşarken kendi blok
> tasarımını kuruyor ve bir `.hwh` bırakıyor. T002'nin üretmeye çalıştığı dosya
> **zaten var** ve kurtarıldı: `artifacts/ip/bd_0_20260917_15931cc.hwh`
> (`VIVADOVERSION 2025.2`, `MODULE qir_kernel`). Karta kopyalayıp `probe_test.py`
> koşmak **5 dakikada** A/B/kısmi cevabını verir — T001–T005'i beklemeden.
> T001–T007 yine yapılır (gerçek BD'de PS ve adres ataması olacak) ama kod hangi
> yola göre yazılacak, bugünden bilinebilir. Bkz. [research.md](research.md) §R1.
>
> ⚠️ Dosya `qir_hls_prj/` altındaydı; orası gitignore'da ve `open_solution -reset`
> onu siliyor. `artifacts/ip/` kopyası kalıcıdır.

- [X] T001 [P] IP paketini Vivado IP deposuna aç: `artifacts/ip/qir_kernel_ip_20260917_15931cc.zip` → `artifacts/ip/repo/qir_kernel_v0_1/`; BD betikleri buraya `set_property ip_repo_paths` ile bakacak
- [X] T002 [P] `fpga/bd/probe_hwh.tcl` yaz — kukla blok tasarım: `processing_system7` (PS preset **elle**, board files yok) + **gerçek `qir_kernel` IP** + `axi_smartconnect` + `proc_sys_reset`. `validate_bd_design` ve `generate_target all` ile `.hwh` üretilir; `launch_runs`/sentez/implementasyon **KOŞULMAZ**
- [X] T003 [P] `fpga/bd/probe_test.py` yaz — boş `ip_dict`'i **başarı saymaz**: `assert len(h.ip_dict) > 0` ve `assert any('qir' in k.lower() for k in h.ip_dict)`; ayrıca her IP'nin `phys_addr` ve `registers` sayısını yazdırır (register haritası da okunabiliyorsa A yolu **gerçekten** açık)
- [X] T004 [P] Kartı aç; JP4=SD ve JP5=REG doğrula, adaptörle besle. Seri konsoldan (COM3, 115200 8N1) `hostname -I` ile **gerçek IP'yi öğren** ve `specs/003-zynq-ps-kartta-kosum/SIRADAKI.md` donanım tablosuna yaz. DONE LED sönükse önce microSD yuvasına bak (bilinen arıza)
- [X] T005 `fpga/bd/probe_hwh.sh` yaz ve koş (`wsl -d Ubuntu -e bash fpga/bd/probe_hwh.sh`) — `LC_ALL=en_US.UTF-8` şart, `/opt/Xilinx/2025.2/Vivado` kullanılır; çıktı `artifacts/bitstream/probe.hwh`
- [X] T006 `probe.hwh` ve `probe_test.py` dosyalarını karta kopyala (T004'teki doğrulanmış IP ile) ve `probe_test.py`'yi koş. `pynq.pl_server.hwh_parser` içe aktarma yolu PYNQ 2.5'te **doğrulanmalı** — farklıysa `python3 -c "import pynq, os; print(os.path.dirname(pynq.__file__))"` ile modül aranır
- [X] T007 Sonucu [research.md](research.md) §R1'e **tarih damgasıyla** işle: A yolu (ip_dict + register'lar okundu), **kısmi başarı** (ip_dict dolu, register'lar boş → taban adres `.hwh`'den, erişim `MMIO` ile) veya B yolu (ayrıştırıcı hata verdi). `plan.md` öbek 0 satırını da güncelle

**Checkpoint**: A mı B mi belli. Bu bilgi olmadan T025 yazılamaz.

---

## Phase 2: Temel (öbek 1, 2, 3) — tüm kullanıcı hikâyelerini bloke eder

**⚠️ KRİTİK**: Bu faz bitmeden hiçbir kullanıcı hikâyesi başlayamaz.

Öbek 1 ve 3 **donanım gerektirmez** (Prensip V) ve G0 beklerken ilerleyebilir.

### Öbek 1 — `fpga/` dizini ve belge güncellemeleri (karar K3)

Yeni üst dizin açmanın bedeli **aynı değişikliğe dahildir**.

- [X] T008 [P] `fpga/README.md` yaz — dizinin kapsamı ve `hls/` ile sınırı: HLS `artifacts/ip/`'te biter, Vivado orada başlar
- [X] T009 [P] `docs/repo-conventions.md` §2 dizin listesine `fpga/` satırı ekle — "Vivado blok tasarım, kısıtlar, elle yazılan RTL (Faz 5)"
- [X] T010 [P] `CLAUDE.md` Depo haritası tablosuna `fpga/` satırı ekle (§2 ile aynı ifade)
- [X] T011 [P] `fpga/rtl/.gitkeep` oluştur — elle yazılacak Verilog için dizin **şimdiden ayrılır**; RTL `hls/` altına konamaz
- [X] T012 [P] `.gitignore`'a Vivado ara çıktılarını ekle: `fpga/bd/*.log`, `fpga/bd/*.jou`, `fpga/bd/vivado_prj/`. `artifacts/bitstream/*` zaten yok sayılıyor (satır 46) — `fpga/` kaynak dizini olarak **commit edilir**

### Öbek 2 — Blok tasarım ve bitstream (EMIO I2C dahil, karar K2)

- [X] T013 `fpga/bd/qir_bd.tcl` yaz — gerçek BD: `processing_system7` **elle preset** (DDR `MT41J256M16 RE-125`, PS ref saat 33,333 MHz, **FCLK0 = 100 MHz**), `qir_kernel` IP, `axi_smartconnect`, `proc_sys_reset`. AXI-Lite taban adresi **`0x43C0_0000` olarak sabitlenir** (B yolunun tek doğruluk kaynağı)
- [X] T014 `fpga/bd/qir_bd.tcl` içine **PS I2C0'ı EMIO ile** dışarı ver (karar K2) — US3 için; şimdi ~10 dk, sonra bir sentez turu artı US1/US2 ölçümlerinin tekrarı demek
- [X] T015 `fpga/bd/qir_constraints.xdc` yaz — EMIO I2C hatlarını PYNQ-Z2 PMOD pinlerine bağla (`PACKAGE_PIN` + `IOSTANDARD LVCMOS33`)
- [X] T016 `fpga/bd/build.sh` yaz — BD → sentez → implementasyon → `write_bitstream` → `.bit`/`.hwh` dosyalarını `artifacts/bitstream/qir_<tarih>_<git-hash>.{bit,hwh}` olarak kopyalar; WNS değerini stdout'a basar
- [X] T017 `wsl -d Ubuntu -e bash fpga/bd/build.sh` koş ve **WNS ≥ 0 doğrula**. ⛔ Zamanlama tutmazsa **FCLK DÜŞÜRÜLMEZ** — faz durur ve neden araştırılır (100 MHz, Faz 2'nin tüm ölçümlerinin dayanağı)
- [X] T018 `artifacts/bitstream/README.md` yaz — `artifacts/ip/README.md` kalıbıyla: SHA-256, üretim komutu, araç sürümü (`Vivado 2025.2`), kaynak git hash, kullanılan IP paketi adı ve **AXI taban adresi**. FR-016 / SC-010 böyle karşılanır

### Öbek 3 — Konak kodlayıcı (**kart olmadan** doğrulanır, Prensip V)

Sözleşme: [contracts/host-encoder.md](contracts/host-encoder.md)

- [X] T019 [P] `agent/encoder.py` — sabit-nokta paketleme: `real_t` Q1.17 (`round(x * 2**17)`, `[-2**17, 2**17-1]` aralığına kırp, `& 0x3FFFF` ile maskele, **işaret genişletmesi yok**); `phase_t` ap_uint<18> TUR cinsinden (`round((açı/(2π)) mod 1 * 2**18) mod 2**18`)
- [X] T020 [P] `agent/encoder.py` — ölçekleme protokolü (madde H-1, H-2, H-6): `S = 1.001 * max(|h|, |J|)` (kenar payı — `AP_SAT` tam `1,0`'ı kırpar), `h' = h/S`, `J' = J/S`, `beklenen_deger = beklenen_deger_ham * S`. `S` her koşumla **kaydedilir**; ham ve ölçekli değerler **ayrı** saklanır
- [X] T021 [P] `agent/encoder.py` — madde H-3: aralık dışı katsayıda **istisna fırlat**, sessizce doyurma. Sessiz kırpma bu fazın en olası gizli hatasıdır
- [X] T022 [P] `agent/encoder.py` — dizi düzeni ([contracts/axi-register-map.md](contracts/axi-register-map.md)): `cost[0..15] = h[k]`, `cost[16..271] = J[a][b]` (`16 + 16*a + b`); `phases[r*272 + 0..15] = phases[r].h[k]`, `phases[r*272 + 16..271] = phases[r].J[a][b]`, `r = 0..2`. `J`'nin yalnız `a < b` üçgeni okunur ama **256 word'ün tamamı yazılır**, kullanılmayanlar sıfırlanır
- [X] T023 [P] `agent/cost_vectors.py` — madde H-7: **sabit tohumlu** RNG ile ≥20 bağımsız `cost` vektörü üret, `[-1, 1)` içinde, `J`'nin yalnız `a < b` üçgeni doldurulur. Hepsi sıfır olan veya birbirinin katı olan vektörler **elenir** — bağımlı vektörler bağımsız kısıt üretmez
- [X] T024 [P] `agent/tests/test_encoder.py` — paketleme (Q1.17 ve TUR sınır değerleri), ölçekleme geri dönüşü, madde H-3 istisnası, dizi düzeni (816 ve 272 word sayıları), `cost` vektörü bağımsızlığı
- [X] T025 G2 kapısı: `python -m pytest agent/tests/test_encoder.py -v` geçsin, ardından C-sim eşdeğerlik kapısı — aynı girdi kodlayıcıdan ve altın referanstan geçirilir, beklenen değerler Faz 2 fidelity bütçesi içinde uyuşur. **Kart hiç gerekmez**

**Checkpoint**: G1 ve G2 geçti. Artık kartta çıkacak her uyuşmazlık
**donanıma izole** — "donanım mı, kodlayıcı mı" belirsizliği yok.

---

## Phase 3: User Story 1 — Çekirdek kartta koşuyor ve çıktısı doğru (P1) 🎯 MVP

**Goal**: Sentezlenmiş çekirdek PYNQ-Z2'de koşuyor ve çıktısı altın referansa
karşı doğrulanmış durumda. Tek başına savunulabilir bir sonuç: *"16 kübitlik
statevector emülatörü FPGA'da çalışıyor ve doğrulandı."*

**Independent Test**: Kart bağlanır, bitstream yüklenir, n=16 p=2 devresi
≥20 `cost` izdüşümüyle koşulur, hepsi C-sim ile birebir tutar. Gecikme veya
enerji ölçümü gerekmez.

**Bağımlılık**: Phase 1 (T007 — A/B yolu kararı) + Phase 2 tamamı.

- [ ] T026 [US1] `agent/board.py` — register haritası sabitleri (`xqir_kernel_hw.h`'den birebir): `AP_CTRL 0x0000`, `P 0x0048`, `BEKLENEN_DEGER 0x0050`, `BEKLENEN_DEGER_CTRL 0x0054`, `COS_BETA 0x0020` (3), `SIN_BETA 0x0030` (3), `PHASES 0x1000` (816), `COST 0x2000` (272); MMIO uzunluğu `0x10000`. Eleman adresi: `taban_ofset + 4*n`
- [ ] T027 [US1] `agent/board.py` — iki erişim yolu: A (`Overlay`) ve B (`Bitstream(...).download()` + `MMIO(taban, 0x10000)`). **Varsayılan T007'nin sonucuna göre seçilir**, diğeri yedek olarak kalır. Taban adres `artifacts/bitstream/README.md`'den okunur
- [ ] T028 [US1] `agent/board.py` — çağrı sırası (maddeler A-1…A-6): `ap_idle` (bit2) **doğrulanır** → `cost`+`phases`+`cos_beta`+`sin_beta`+`p` yazılır (**1.095 yazma**) → `ap_start` (bit0) ← 1 → `ap_done` (bit1) yoklanır (**5 sn zaman aşımı**) → `0x0050` ham 32-bit okunur ve `struct.unpack('<f', ...)` ile yorumlanır (kesme/cast **yok**, bit deseni korunur)
- [ ] T029 [US1] `agent/board.py` — zaman aşımı davranışı (madde A-4): `ap_done` 5 sn içinde gelmezse koşum `gecerli=false` işaretlenir ve **hiçbir seride sayılmaz**; kısmî sonuç ölçüm sayılmaz
- [ ] T030 [US1] `agent/board.py` — izdüşüm kısa yolu: yalnız `cost` (272 word) yeniden yazılır, `phases`/`cos_beta`/`sin_beta`/`p` yerinde kalır. ⚠️ **Bu kısa yol gecikme ölçümünde KULLANILMAZ** — karıştırılırsa `T_yazma` olduğundan küçük raporlanır
- [ ] T031 [US1] `agent/run_board.py` — `--n 16 --p 2 --izdusum 20 --tohum 42`; `cost_vectors.py`'den vektörleri alır, her biri için koşar, C-sim çıktılarıyla karşılaştırır, `IzdusumSerisi` üretir
- [ ] T032 [US1] Bitstream'i karta yükle ve **yüklemenin başarılı olduğunu doğrula** (FR-001) — `ap_idle` okunabiliyor ve 1 dönüyor mu. "Yükledim, koşuyordur" varsayımı yetmez
- [ ] T033 [US1] G3 koş (p=2): **20 izdüşümün hepsi** kart ↔ C-sim **birebir** tutmalı (SC-003). Biri bile saparsa kapı kapalı — hangi `cost` vektörlerinde saptığı hatayı `h` yoluna mı `J` yoluna mı daralttığını gösterir
- [ ] T034 [US1] Belirlenimcilik (SC-002, madde A-5): aynı girdiyle iki ardışık koşum **bit düzeyinde aynı** çıktı vermeli
- [ ] T035 [US1] Durumsuzluk (FR-005, madde K-4): kart yeniden başlatılıp çekirdek yeniden yüklendiğinde aynı sonuç alınmalı; önceki koşumun kalıntısı taşınmamalı
- [ ] T036 [US1] Sınır davranışı (madde A-3): `p=0` ve `p=4` → çekirdek koşmaz ve `0x0050` **değişmez**. Bu bir hata değil, test edilecek bir davranıştır
- [ ] T037 [US1] Aynı doğrulamayı **p=1** için tekrarla — SC-001 hem p=1 hem p=2 için ayrı ayrı doğrulama istiyor
- [ ] T038 [US1] `docs/measurements/kart-dogrulama_<tarih>_<git-hash>_n16_p{1,2}.json` yaz — `IzdusumSerisi` alanları: `devre` özeti (tüm izdüşümlerde aynı olmalı), `tohum`, `izdusum_sayisi` (**≥20**), `kosumlar`, `csim_degerleri`, `sapan_izdusumler` (**boş olmalı**), `bitstream_sha256`

**Checkpoint**: US1 tamam ve bağımsız savunulabilir. Ölçüm fazları başlayabilir.

> ⚠️ **Uyuşmazlık hâlinde**: Bu bir tasarım krizi değil **doğrulama krizidir**.
> Hangisinin doğru olduğu altın referansla belirlenir; fark kapanmadan
> **hiçbir hız/enerji rakamı raporlanmaz**. Sapma deseni yine de neden
> vermezse — ve yalnız o zaman — genlik penceresi varyantı (kapsam **İ**)
> devreye alınır ([research.md](research.md) §R3).

---

## Phase 4: User Story 2 — Gecikme kartta ölçülüyor (P2)

**Goal**: Faz 2'nin 37,28 ms'lik HLS **tahmini**, kartta alınmış gerçek bir
ölçüme dönüşsün.

**Independent Test**: Kartta koşum süresi ≥10 tekrarla ölçülür; medyan ve
yayılım raporlanır. Enerji düzeneği gerekmez.

**Bağımlılık**: US1 (T033 geçmiş olmalı).

- [ ] T039 [US2] `docs/measurements/kart-olcum-protokolu.md` yaz ve **dondur** — ⚠️ İLK ÖLÇÜMDEN **ÖNCE** (FR-011, SC-009): koşum sayısı, ısınma turu sayısı, üç kapsamın tanımı, termal plato ölçütü, dışlama kuralları. Sonuca bakıp protokol ayarlanamaz
- [ ] T040 [US2] `agent/measure_latency.py` — **üç kapsam ayrı ayrı** (FR-007): `T_cekirdek` (`ap_start` yazımı → `ap_done` görülmesi), `T_yazma` (1.095 register yazımı), `T_uctan_uca` (kodlama + yazma + koşum + okuma). `time.perf_counter()` kullanılır; ayrı zamanlayıcı IP'si yok
- [ ] T041 [US2] `agent/measure_latency.py` — `ap_done` yoklama periyodunu ölç ve **kaydet**: yoklama `T_cekirdek`'e üst taraftan hata ekler ve bu hata raporlanmalı
- [ ] T042 [US2] `agent/measure_latency.py` — **termal plato doğrulaması** (CPU tarafındaki turbo/plato ayrımının kart karşılığı): ilk N koşum ile son N koşum **ayrı** raporlanır, platonun oturduğu gösterilir, koşum sırası kaydedilir. Isınma/kısılma ardışık koşumları yavaşlatabilir
- [ ] T043 [US2] `agent/measure_latency.py` — seri istatistiği: **medyan ve yayılım (IQR) birlikte**; `min`/`max` de saklanır. ⛔ `kosum_sayisi < 10` olan seri **serileştirilmesin, hata versin** (SC-004'ün kod düzeyindeki karşılığı). Tek koşum rakamı hiçbir yere yazılmaz
- [ ] T044 [US2] Ölçümleri koş (n=16, p=2 ve p=1, **≥30 tekrar**) → `docs/measurements/kart-gecikme_<tarih>_<git-hash>_n16_p{1,2}.json`; her kapsam için ayrı `OlcumSerisi`. **Ortalama değil dağılım raporlanır**: p50 / p95 / p99 / maks ve jitter (maks−min). FPGA'da jitter **yapısı gereği sıfırdır** (3.728.217 çevrim, her seferinde); CPU ve GPU'da kuyruk vardır. Gerçek zamanlı bir denetim döngüsünde önemli olan en kötü durumdur — ek ölçüm değil, aynı veriden farklı bir tablo (bkz. [neden-fpga.md §2.3](../../docs/neden-fpga.md))
- [ ] T045 [US2] HLS tahminiyle karşılaştır (p=2 için **37,28 ms**) ve sapmayı **gizlemeden** kaydet; nedeni araştır, bulunamazsa **bulunamadığı yazılır** (FR-014). `T_yazma`'nın CPU tarafında **karşılığı olmadığı** ayrıca not edilir

**Checkpoint**: Gecikme ekseni ölçüldü; US3 olmadan da yayımlanabilir.

---

## Phase 5: User Story 3 — Enerji kartta ölçülüyor (P3)

**Goal**: Bir devre koşumunun joule maliyeti ölçülsün. **Fazın asıl beklenen
sonucu bu eksende** — gecikmede başabaş bekleniyor.

**Independent Test**: Düzenek kalibre edilir, boştaki ve yük altındaki güç
ayrı okunur, koşum başına joule hesaplanır.

**Bağımlılık**: US1 + INA219 (elde) + EMIO I2C (T014'te blok tasarıma girdi).

- [ ] T046 [US3] INA219'u kartın **12 V hattına seri** bağla (standart 0,1 Ω şönt doğru: PYNQ ~0,3 A çeker, ~1,2 mW çözünürlük verir). ⚠️ Adaptörün orijinal kablosu **KESİLMEZ** — namlu jak uzatma kablosu araya alınır, ölçüm bitince çıkarılır. ⛔ JP5=REG ve adaptör beslemesi **değiştirilmez**
- [ ] T047 [US3] EMIO I2C yolunu kartta doğrula: özel bitstream yüklüyken I2C veri yolu görünüyor mu (`i2cdetect`), INA219 adresi (varsayılan `0x40`) okunuyor mu. Base overlay'in Pmod IOP'si bizim bitstream'imizde **yok** — bu yüzden EMIO gerekiyordu
- [ ] T048 [US3] `agent/calibrate_ina219.py` — bilinen bir yükte kalibrasyon; sapma **< %5** olmalı (SC-005). `Kalibrasyon` alanları (`bilinen_yuk_w`, `okunan_w`, `sapma_yuzde`, `zaman_damgasi`) kaydedilir. ⛔ Sapma ≥ %5 ise o aletle alınan **hiçbir** enerji ölçümü geçerli sayılmaz
- [ ] T049 [US3] `agent/measure_energy.py` — delta yöntemi (FR-009c, FR-009d): boş güç ve yük altındaki güç **ayrı ayrı** okunur; iş yükü **≥60 sn** döngüye alınır (tek koşum ~37 ms, hiçbir güç ölçerde görünmez); `enerji_j_kosum = (yuk_guc_w - bos_guc_w) * sure_s / kosum_sayisi`
- [ ] T050 [US3] Ölçümü koş → `docs/measurements/kart-enerji_<tarih>_<git-hash>.json`; kapsam **"tüm kart"** olarak yazılır (yalnız PL değil). CPU tarafının kapsamı "tüm dizüstü" — asimetri değil, **aynı yöntem** (delta), rapora böyle geçer

**Checkpoint**: İki eksen de ölçüldü; kıyas matrisi yazılabilir.

> **Modül gelmez / yanarsa**: Enerji ekseni düşer. Gecikme ekseni tek başına
> raporlanır ve enerjinin **neden** ölçülemediği yazılır (FR-014, SC-008).
> Tahminle doldurulmaz.

---

## Phase 6: User Story 4 — Kıyas matrisi ve nihai rapor (P3)

**Goal**: FPGA ve CPU sonuçlarını aynı problem ve aynı parametreler üzerinde
yan yana koyan, her hücresi izlenebilir bir tablo.

**Independent Test**: Toplanmış ölçümlerden tablo üretilir; her hücrenin
kaynağı (tarih, koşum sayısı, konfigürasyon) izlenebilir.

**Bağımlılık**: US2 + US3.

- [ ] T051 [US4] `scripts/build_comparison_matrix.py` — `KiyasSatiri` üretir. ⛔ Hiçbir hücre elle doldurulamaz; her hücre bir `OlcumSerisi` veya `EnerjiOlcumu` **kimliğine işaret eder** (SC-007)
- [ ] T052 [US4] `scripts/build_comparison_matrix.py` — konfigürasyon denetimi (FR-012): iki taraf da **aynı n, aynı p, aynı problem** üzerinde koşmuş olmalı; değilse satır üretilmez
- [ ] T053 [US4] `scripts/build_comparison_matrix.py` — `hizlanma` yalnız **iki taraf da doluysa** ölçülmüş değerlerden hesaplanır ve yayılımla birlikte verilir; aksi hâlde `null` kalır ve `not` alanı **zorunlu** olur (SC-008)
- [ ] T054 [US4] CPU tarafı referanslarını bağla — **yeniden ölçülmez**: turbo **32,75 ms**, plato **41,93 ms**, enerji **0,644 J/koşum** (batarya delta yöntemi, 2026-09-19 temiz ölçüm). ⚠️ Eski 77,6/92,7 ms rakamları **geçersizdir**
- [ ] T055 [US4] Matrisi üret → `docs/measurements/kiyas-matrisi_<tarih>_<git-hash>.json`. ⚠️ Gecikmede başabaş bekleniyor (FPGA 37,28 ms, CPU turbo 32,75 / plato 41,93 ms) — `hizlanma < 1` çıkması **hata değil bulgudur** ve öyle raporlanır. ⚠️ Bu matris **GPU sütunu olmadan nihai değildir** — bkz. Phase 6B (T069 onu yeniden üretir)

**Checkpoint**: Tüm kullanıcı hikâyeleri tamam.

---

> 🔒 **MVP'den sonra** — kapsam 2026-09-21'de donduruldu; öbek 4 (T026–T038) bitmeden başlanmaz.

## Phase 6B: GPU tabanı (US4 eki) — **2026-09-21'de kapsama alındı**

**Neden eklendi**: Faz 2'de GPU *"kapsam dışı; kıyas tek çekirdekli CPU'ya
karşı"* diye elenmişti — ama gerekçe daireseldi ve **makinede RTX 4060 var**.
Elinde GPU varken onu ölçmeden "FPGA üstün" demek savunulamaz; bilgisayar
mimarisi okuyan bir değerlendiricinin soracağı ilk soru budur.

**Beklenti (ölçülmemiş, bu yüzden görev var)**: GPU hızda muhtemelen iki-üç
kat büyüklük önde olur — n=16 yalnızca 65.536 genlik, ~1 MB, bir L2
önbelleğine sığar. **Enerjide bile önde olabilir.** Bu bir sorun değil, bir
bulgudur; FPGA'nın savunması hız değil **dağıtım zarfıdır** (12 V/2 A uç
cihaz; RTX 4060 o zarfa girmez).

⛔ **Sonuç ne çıkarsa çıksın raporlanır.** "GPU kazandı" çıkması bu öbeğin
başarısızlığı değil, tam da varlık sebebidir.

**Bağımlılık**: US4 (T051–T055). Kart **gerekmez**.

- [ ] T064 WSL2 + CUDA üzerinde `qiskit-aer-gpu` kur ve doğrula: `AerSimulator(method="statevector").available_devices()` çıktısında **`GPU` görünmeli**. ⚠️ `qiskit-aer-gpu` tekerleri Linux'tur, Windows'a doğrudan kurulmaz; `/dev/dxg` mevcut olduğu için WSL yolu açık. **Kurulamazsa uydurma yapılmaz**: `dead-ends.md`'ye yazılır ve öbek burada durur
- [ ] T065 `scripts/cpu_load_loop.py`'ye `--device {CPU,GPU}` ekle. ⛔ **Ayrı betik YAZILMAZ** — farklı koşum hattı rakamları kıyaslanamaz kılar; aynı döngü, aynı zamanlama, aynı turbo/plato ayrımı kullanılmalı (FR-012)
- [ ] T066 **Önce doğruluk**: GPU statevector'ü aynı altın referansa karşı koşulur, fidelity Faz 2 bütçesi içinde olmalı. ⛔ Hızlı ama yanlış bir sonuç taban değildir — doğrulanmadan hiçbir süre kaydedilmez (Anayasa Prensip IV)
- [ ] T067 GPU gecikmesini **CPU ile aynı protokolle** ölç: ≥60 sn döngü, ≥30 koşum, turbo/plato ayrımı, platonun oturduğu doğrulanır (T042/T044 ile aynı ölçütler). Protokol **ölçümden önce** yazılır (FR-011)
- [ ] T068 GPU enerjisini **aynı batarya-delta yöntemiyle** ölç (FR-009c). Alet ve yöntem CPU ölçümüyle birebir aynı olmalı; yalnız iş yükü değişir. ⚠️ Boş güç ölçümü GPU boştayken **yeniden** alınır — CPU'nunki kullanılamaz, GPU boşta da güç çeker
- [ ] T069 Kıyas matrisini **üçüncü sütunla** yeniden üret (T055'in çıktısı güncellenir) ve yorumu yaz: hangi eksende kim önde, ve FPGA'nın savunmasının **dağıtım zarfı** olduğu — hız değil. `docs/olculen-degerler.md`'ye işle

⚠️ **GK-01 riski**: makine `nvlddmkm.sys` yüzünden günde ~1 çöküyor
([risk-register.md](../../docs/risk-register.md)). GPU'ya yük bindirmek bunu
tetikleyebilir; ölçüm serisi **koşum başına** diske yazılmalı. Aynı zamanda
teşhis fırsatı: GPU hesabı düzenli çökertiyorsa sürücü sorununun kapsamı
netleşir.

**Checkpoint**: Kıyas üç sütunlu ve her sütun ölçülmüş.

---

> 🔒 **MVP'den sonra** — kapsam 2026-09-21'de donduruldu; öbek 4 (T026–T038) bitmeden başlanmaz.

## Phase 6C: Sayısal genişlik Pareto eğrisi — **FPGA'ya özgü katkı**

**Neden**: Bu, projenin GPU'da **karşılığı olmayan** tek sonucudur. 18 bit,
iki bağımsız kısıtın tam kesişimidir — yukarıdan doğruluk (H eşiğini geçen en
dar format Q1.17), aşağıdan donanım (BRAM36'nın azami kelime genişliği 36 bit,
re+im = 2×18 tam oturuyor, sıfır israf). GPU'da ne 18 bitlik reel vardır ne de
"bellek kelimesine hizalama" diye bir kavram. Gerekçe:
[neden-fpga.md §2.2b](../../docs/neden-fpga.md).

**Elde olan**: fidelity × genişlik tablosu (Q1.13…Q1.23, `format_fidelity.py`).
**Eksik olan**: her genişlikte **donanım maliyeti**.

⚠️ **Kübit sayısına DOKUNULMAZ.** Süpürülen tek şey `real_t` genişliğidir;
`N_QUBITS` hep 16 kalır. ("18 bit" hassasiyettir, kübit sayısı değil.)

**Bağımlılık**: yok — kart **gerekmez**, GPU tabanıyla (Phase 6B) paralel koşar.

- [ ] T070 `hls/src/qir_types.hpp`'de genişliği derleme zamanı parametresi yap: `QIR_REAL_BITS` (varsayılan **18**). Türev tipler birlikte ölçeklenir: `acc_t` = `ap_fixed<2*W, 2>`, `sum_t` buna göre. ⚠️ `phase_t` **bağımsızdır** (TUR çözünürlüğü, ayrı karar) — dokunulmaz. ⛔ **Kapı**: varsayılan genişlikte üretilen ikili bugünküyle **bit bit aynı** sonuç vermeli; `ci_fidelity_gate.py` 4/4 geçmeli. Geçmezse refaktör bozuktur, süpürme başlamaz
- [ ] T071 Her genişlik için (14, 16, **18**, 20, 24) trig LUT'u yeniden üret (`gen_trig_lut.py` 18 bite göre yazılmış) ve **C-sim koş**. Ölçülen fidelity, `format_fidelity.py`'nin sayısal modeliyle uyuşmalı. ⛔ **Uyuşmayan genişliğin donanım rakamı çizilmez** — bozuk bir tasarımın maliyetini raporlamak, eğriyi tamamen değersizleştirir
- [ ] T072 Her genişlikte `csynth` koş ve topla: **BRAM_18K, DSP, LUT, FF, II, toplam çevrim, tahmini periyot**. Damgalı JSON: `docs/measurements/genislik-pareto_<tarih>_<git-hash>.json`. ⚠️ HLS'in LUT tahmini **2× şişik** (ölçülen oran 0,39–0,50× ve **sabit değil**) — eğride LUT sütunu *tahmin* olarak etiketlenir, gerçek sayı yalnız implementasyondan gelir
- [ ] T073 Pareto figürünü üret (`docs/figures/`) ve `docs/neden-fpga.md` §2.2b'yi **ölçülmüş** tabloyla güncelle. Anlatı: dirseğin 18 bitte olması ve o noktanın GPU'da **seçilemez** olması. ⛔ "18 bit fp16'dan daha doğru" **yazılmaz** — iddia doğruluk üstünlüğü değil, ifade edilebilirlik ve sığmadır

**Checkpoint**: Projenin FPGA'ya özgü katkısı ölçülmüş bir eğriyle ortada.

---

> 🔒 **MVP'den sonra** — kapsam 2026-09-21'de donduruldu; öbek 4 (T026–T038) bitmeden başlanmaz.

## Phase 6D: Sıcak başlangıç — optimize edici döngüsünü kısaltma

**Neden**: Süreyi domine eden şey tek çağrı değil, **klasik optimize edici
döngüsüdür**. Referansta `optimizer_iterations = 99` (COBYLA), yani bir alt
problem = 99 FPGA çağrısı = **3,69 s**. Gecelik toplu işte sorun değil, ama
**artımlı güncelleme yolunda** (adres değişikliği, kullanıcı bekliyor) doğrudan
gecikmedir ([sistem-mimarisi.md §3, §7](../../docs/sistem-mimarisi.md)).

**Bağımlılık**: yok — **kart ve FPGA gerekmez**. Tamamen Qiskit referans
yolunda ölçülür; sonuç iterasyon sayısıdır, donanım süresi değil.

⛔ **Tek başına iterasyon sayısı ölçüt DEĞİLDİR.** 5 adımda yakınsayıp daha
kötü bir tura oturan bir başlangıç, iyileştirme değil gerilemedir. Her
görevde **iterasyon ve çözüm kalitesi birlikte** raporlanır.

- [ ] T074 Taban dağılımı: ≥20 farklı problem örneğinde soğuk başlangıçla (rastgele γ/β) COBYLA koş; **iterasyon sayısı** ve `optimal_probability`/`best_energy` dağılımını çıkar. Tek örnekten (99) genelleme yapılmaz — dağılım gerekir
- [ ] T075 Sıcak başlangıç: bir önceki çözümün (γ, β) değerleriyle başla ve **az değişmiş** bir problem üzerinde koş (artımlı yolun benzetimi — bir durağın adresi değiştirilir). İterasyon sayısı **ve** çözüm kalitesi T074 tabanıyla karşılaştırılır
- [ ] T076 Sabit açı QAOA: literatürden/önceden belirlenmiş γ/β ile optimize ediciyi tamamen kaldır (**99 → 1 çağrı**). ⚠️ Beklenen bedel çözüm kalitesindedir; **ne kadar** kaybedildiği ölçülür. Kabul edilebilirse artımlı yol saniyenin altına iner
- [ ] T077 Sonucu `docs/measurements/sicak-baslangic_<tarih>_<git-hash>.json` olarak yaz ve [sistem-mimarisi.md §7](../../docs/sistem-mimarisi.md) tablosunu **ölçülmüş** değerlerle güncelle. Hiçbiri kazanmazsa bu da sonuçtur ve öyle yazılır

**Checkpoint**: Artımlı yolun gerçek gecikmesi biliniyor.

---

## Phase 7: Faz kapanışı ve çapraz kesen işler

- [ ] T056 [P] `docs/olculen-degerler.md`'ye Faz 5 ölçümlerini işle — tez/makale için **tek referans** orası
- [ ] T057 [P] `docs/olculen-degerler.md` — **kapsam sınırlarını açıkça yaz**: (a) faz ekseni bu fazda **hiç ölçülmedi**, Faz 2'nin n=8 cosim PASS'inden geliyor; (b) genlik fidelity'si **devralınan çıkarım**, ölçülmüş değil; (c) ölçümler sistem düzeyinde, bileşen düzeyinde değil
- [ ] T058 [P] `docs/decisions/` altına ADR yaz — K1 (çoklu izdüşüm), K2 (EMIO I2C erken), K3 (`fpga/` üst dizini). Şablon: `docs/decisions/ADR-TEMPLATE.md`
- [ ] T059 [P] `docs/risk-register.md` güncelle — PYNQ 2.5 / Vivado 2025.2 `.hwh` riskini T007'nin sonucuna göre **kapat veya yeniden derecelendir**
- [ ] T060 [P] `docs/decisions/dead-ends.md` — elenen yollar: PYNQ 3.x imajı, `.hwh` elle yamama, board files indirme, ayrı AXI Timer IP'si
- [ ] T061 [P] `CLAUDE.md` "Şu anki faz" paragrafını Faz 5 sonuçlarıyla güncelle
- [ ] T062 `specs/003-zynq-ps-kartta-kosum/SIRADAKI.md` güncelle ve `docs/faz-sonu-kontrol.md` listesini geç
- [ ] T063 `specs/003-zynq-ps-kartta-kosum/quickstart.md` faz kapanış kapısındaki **tüm kutuları** doğrula — G0'dan G6'ya hepsi geçildi mi

---

## Dependencies & Execution Order

### Faz bağımlılıkları

- **Phase 1 (G0, öbek 0)**: Bağımlılık yok — **ilk koşulur**, öbek 4'ü bloke eder
- **Phase 2 (öbek 1–3)**: Öbek 1 ve 3 bağımsız; öbek 2 öbek 1'e bağlı
- **Phase 3 (US1)**: Phase 1 **ve** Phase 2 tamamlanmalı
- **Phase 4 (US2)**: US1'e bağlı
- **Phase 5 (US3)**: US1 + INA219'a bağlı; **US2'yi beklemez**
- **Phase 6 (US4)**: US2 + US3'e bağlı
- **Phase 6B (GPU tabanı)**: US4'e bağlı; **kart gerekmez**, US1–US3 ile paralel koşabilir
- **Phase 6C (genişlik Pareto)**: bağımlılık **yok**; kart gerekmez, her an koşabilir
- **Phase 6D (sıcak başlangıç)**: bağımlılık **yok**; kart ve FPGA gerekmez, saf Qiskit
- **Phase 7**: Hepsine bağlı

### Kullanıcı hikâyesi bağımlılıkları

- **US1 (P1)**: Phase 1+2 sonrası başlar. Diğer hikâyelere bağımlı değil — **MVP**
- **US2 (P2)**: US1'e bağlı (doğrulanmamış çekirdekte ölçüm anlamsız)
- **US3 (P3)**: US1'e bağlı; US2'den **bağımsız** — paralel koşabilir
- **US4 (P3)**: Birleştirme adımı; US2 **ve** US3 gerekli

### Zorunlu sıralamalar (pazarlıksız)

| Kural | Neden |
|---|---|
| T001–T007 (G0) **her şeyden önce** | Sonradan öğrenilirse öbek 4'ün konak kodu çöpe gider |
| T025 (G2) **T032'den önce** | Kodlayıcı kartsız doğrulanmazsa uyuşmazlık "donanım mı kodlayıcı mı" belirsizliğinde kalır |
| T039 (protokol) **T044'ten önce** | Ön kayıt (FR-011, SC-009) — sonuca bakıp protokol ayarlanamaz |
| T048 (kalibrasyon) **T050'den önce** | Kalibre edilmemiş aletin ölçümü geçersiz (SC-005) |
| T014 (EMIO I2C) **T017'den önce** | Sonra eklemek bitstream'i yeniden üretir, US1/US2 ölçümleri tekrarlanır |

### Paralel fırsatlar

- **T001–T004** birlikte: IP açma, iki betik yazımı ve kart açılışı birbirinden bağımsız
- **T008–T012** birlikte: belge güncellemelerinin hepsi farklı dosyada
- **T019–T024** birlikte: kodlayıcı parçaları ve testleri — **donanım beklemez** (Prensip V)
- **Öbek 1+3 ile G0 aynı anda**: belge işleri ve kodlayıcı, probe sonucunu beklemez
- **US2 ile US3**: ikisi de yalnız US1'e bağlı, birbirine değil
- **T056–T060** birlikte: kapanış belgeleri farklı dosyalarda

---

## Parallel Example: Phase 2, donanım beklerken

```powershell
# Belge öbeği (öbek 1) — hiçbiri karta dokunmaz
# T008 fpga/README.md · T009 docs/repo-conventions.md · T010 CLAUDE.md
# T011 fpga/rtl/.gitkeep · T012 .gitignore

# Kodlayıcı öbeği (öbek 3) — Prensip V, kart gerekmez
# T019 paketleme · T020 ölçekleme · T021 istisna · T022 düzen
# T023 cost vektörleri · T024 testler
python -m pytest agent/tests/test_encoder.py -v
```

---

## Implementation Strategy

### Önce MVP (US1)

1. **Phase 1 (G0)** — A/B yolu kararı. Bir saat.
2. **Phase 2** — öbek 1 ve 3 donanım beklemeden, öbek 2 bitstream.
3. **Phase 3 (US1)** — kartta koşum + 20 izdüşümle doğrulama.
4. **DUR ve DOĞRULA**: US1 tek başına savunulabilir bir sonuçtur.

### Artımlı teslim

1. Phase 1 + 2 → temel hazır
2. US1 → bağımsız doğrulandı → **MVP**
3. US2 → gecikme ekseni → tek başına yayımlanabilir
4. US3 → enerji ekseni → **fazın asıl beklenen sonucu**
5. US4 → birleştirme

### Tek geliştirici sırası (Prensip VI)

Paralellik burada "aynı anda iki kişi" değil, **"donanım beklerken masa başı
iş"** demektir. G0'ın Vivado adımı koşarken öbek 1 ve 3 ilerletilir; kart
kapalıyken kodlayıcı tamamen bitirilebilir.

---

## Notes

- `[P]` = farklı dosya, tamamlanmamış göreve bağımlı değil
- **Kart kapalı**: her `ssh`/`scp` öncesi IP'yi seri konsoldan doğrula (`hostname -I`)
- ⛔ Besleme düzeni (adaptör + JP5=REG) **hiçbir aşamada değişmez**
- Ölçüm disiplini: **≥10 koşum, medyan ve yayılım birlikte, tek koşum rakamı yok**
- Ölçüm rakamı elle sabitlenmez — `docs/measurements/` altına **damgalı** (tarih + git hash + konfig) yazılır
- Her görev veya mantıklı grup sonrası commit
- Sentez ara çıktıları (`.log`, `.jou`, `vivado_prj/`) commit edilmez
