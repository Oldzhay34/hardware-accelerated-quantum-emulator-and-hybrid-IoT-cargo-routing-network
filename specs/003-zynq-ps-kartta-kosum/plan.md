# Implementation Plan: Faz 5 — Zynq PS + Kartta Koşum

**Branch**: `003-zynq-ps-kartta-kosum` | **Date**: 2026-09-19 |
**Spec**: [spec.md](spec.md)

**Input**: Feature specification from `specs/003-zynq-ps-kartta-kosum/spec.md`

---

## Summary

Faz 2'nin sentezlenmiş çekirdeğini PYNQ-Z2'de gerçekten koşturmak ve Faz 2'den
kalan **her tahmini sayıyı ölçüme çevirmek**. Teknik yol: IP paketinden Vivado
2025.2 blok tasarımıyla bitstream üretmek, çekirdeği AXI-Lite üzerinden
sürmek, çıktısını altın referansa karşı doğrulamak, gecikmeyi üç ayrı kapsamda
ve enerjiyi INA219 ile ölçmek.

Plan yazılırken depo incelendi ve spec'in iki varsayımının **tutmadığı**
görüldü. İkisi de planın şeklini belirliyor:

| # | Bulgu | Sonuç |
|---|---|---|
| 1 | `artifacts/ip/*.zip` **bitstream değil**, IP kataloğu paketi | US1'den önce bir **Vivado blok tasarım** adımı gerekiyor — spec'te adı geçmiyor |
| 2 | Çekirdek genlik vektörünü **dışarı vermiyor** (madde K-1, yalnız skaler `beklenen_deger`) | SC-001'in *"fidelity ≥ 0,99"* ölçütü kartta **doğrudan ölçülemez** |

İkincisi yeniden sentez gerektirmeden çözüldü: `cost` bir AXI girişidir ve
`run_circuit`'e girmez. Devre sabit tutulup yalnız `cost` değiştirilerek
koşulunca kart, **aynı statevector'ün bağımsız bir izdüşümünü** verir —
≥20 izdüşüm, tasarıma hiç dokunmadan (karar K1).

Ayrıntı ve gerekçeler: [research.md](research.md).

**Kritik risk (spec'te işaretli, planın ilk görevi)**: Kartta PYNQ 2.5 (2019),
IP ise Vitis 2025.2 — altı yıl fark. PYNQ'nun `.hwh` ayrıştırıcısı **tek bir
alt sürüm farkında bile** kırılmış olarak belgelenmiş. Plan buna bel bağlamıyor:
çekirdek yalnızca `s_axilite` kullandığı için `Bitstream` + `MMIO` yedek yolu
**tam işlevsellik** veriyor ve DMA/sürücü keşfi hiç gerekmiyor.

---

## Technical Context

**Language/Version**: Python 3.6 (kart tarafı — PYNQ 2.5'in taşıdığı sürüm),
Python 3.11 (konak: kodlayıcı, analiz, Qiskit), Tcl 8.6 (Vivado blok tasarım),
C++ (mevcut HLS çekirdeği — **değiştirilmiyor**)

**Primary Dependencies**: `pynq` 2.5 (kart), `numpy`, `qiskit-aer` (konak
altın referans), Vivado 2025.2 (WSL/Ubuntu, `/opt/Xilinx/2025.2/Vivado` —
kurulu ve `xc7z020` destekli olduğu doğrulandı)

**Storage**: Yeni veri deposu **yok**. Ölçümler `docs/measurements/` altına
damgalı JSON (`<ad>_<tarih>_<git-hash>_<konfig>.json`); ikili yapıtlar
`artifacts/bitstream/` (git'e girmez, SHA-256 depoda)

**Testing**: `pytest` (konak kodlayıcı, **kartsız**), C-sim eşdeğerlik kapısı,
kart üzerinde doğrulama/ölçüm betikleri

**Target Platform**: PYNQ-Z2 (`xc7z020clg400-1`), PynqLinux 2.5 Glasgow,
192.168.1.2 üzerinden SSH. Besleme: adaptör, **JP5 = REG (sabit)**

**Project Type**: Donanım/gömülü + ölçüm koşum takımı. Tek bir servis değil;
iki yapıt üretiliyor — bir **bitstream** ve bir **ölçüm kaydı**.

**Performance Goals**: Hedef yok, **ölçüm var**. Beklenti: gecikmede başabaş
(FPGA tahmini 37,28 ms; CPU turbo 32,75 / plato 41,93 ms), fark **enerji
ekseninde** çıkacak (CPU 0,644 J/koşum ölçüldü; FPGA ölçülmedi).

**Constraints**:
- Statevector çip-içi BRAM'de kalır; `m_axi` **yok** (madde K-1, Prensip III)
- Zamanlama 100 MHz'de tutmalı — tutmazsa FCLK **düşürülmez**, faz durur
  (Faz 2 ölçümleri 100 MHz'e dayanıyor)
- Besleme düzeni değiştirilemez (enerji karşılaştırılabilirliği)
- `p ≤ P_MAX = 3`, `n = 16` derleme zamanı sabiti

**Scale/Scope**: n=16 (65.536 genlik), p=1 ve p=2 birincil. Konfigürasyon
başına ≥10 koşum. Dört kullanıcı hikâyesi, biri (US3) tedarike bağlı.

---

## Constitution Check

*GATE: Phase 0 öncesi geçmeli, Phase 1 sonrası yeniden denetlenir.*

| İlke | Durum | Gerekçe |
|---|---|---|
| **I. Onay Kapısı** | ✅ | [research.md](research.md) yedi karar noktasının her birinde karşılaştırma tablosu üretti. Üçü kullanıcıya sunuldu ve **2026-09-19'da onaylandı** (aşağıda). |
| **II. Ölçüm Dürüstlüğü** | ✅ | Plan tahmini rakam üretmiyor. Genlik fidelity'sinin **devralınan çıkarım**, faz ekseninin ise bu fazda **hiç ölçülmediği** raporda açıkça yazılacak (SC-008). `hizlanma < 1` çıkarsa bulgu olarak raporlanır, gizlenmez. |
| **III. Donanım Bütçesi** | ✅ | Çekirdek **değiştirilmiyor**. `m_axi` eklenmiyor, statevector DDR'a taşmıyor, n=16 sınırı korunuyor. Çoklu izdüşüm de tasarıma dokunmuyor — yalnız AXI girişini değiştiriyor. |
| **IV. Altın Referans** | ✅ | Kartın çıktısı ≥20 bağımsız izdüşümle Qiskit'e karşı doğrulanmadan hiçbir hız/enerji rakamı raporlanmıyor. |
| **V. Donanımsız Süreklilik** | ✅ | Konak kodlayıcı **kart olmadan** C-sim'e karşı doğrulanıyor (G2, madde H-5). C-sim/cosim yolu bozulmuyor. |
| **VI. 14 Hafta** | ✅ | Her iş öbeği M/H/İ etiketli. Genlik penceresi varyantının bedeli **peşinen ödenmiyor**, yalnız gerekirse. |

### Onaylanan kararlar (Prensip I, 2026-09-19)

| # | Karar | Sonuç |
|---|---|---|
| **K1** | Genlik fidelity'si kartta ölçülemiyor (madde K-1) | **Çoklu izdüşüm.** `cost` bir AXI girişi olduğu ve yalnız `expectation_scaled`'i beslediği için, aynı devre **≥20 rastgele `cost` vektörüyle** koşulur → aynı statevector'ün 20 bağımsız izdüşümü. Tasarım değişmez, yeniden sentez yok. Hepsi kart↔C-sim birebir tutmalı. Yöntem **fazı görmez** — faz n=8 cosim'den gelir ve rapor bunu ayrıca yazar. Ayrışma teşhis edilemezse genlik penceresi o zaman. (§R3) |
| **K2** | EMIO I2C ne zaman? | **İlk bitstream'e dahil.** Şimdi ~10 dk; sonra bir sentez turu **artı** US1/US2 ölçümlerinin tekrarı. (§R5) |
| **K3** | Donanım kaynağı nereye? | **Yeni `fpga/` üst dizini** (`bd/` + şimdiden ayrılan `rtl/`). `hls/` §2'de "Vitis HLS kaynakları" diye tanımlı; zincir zaten `artifacts/ip/`'te bölünüyor. `repo-conventions.md` §2, `CLAUDE.md` depo haritası ve `fpga/README.md` **aynı değişiklikte** güncellenir. (§R7) |

---

## Project Structure

### Documentation (this feature)

```text
specs/003-zynq-ps-kartta-kosum/
├── plan.md                        # Bu dosya
├── research.md                    # Faz 0 — altı karar, iki sert gerçek
├── data-model.md                  # Faz 1 — beş varlık, kalıcılık kalıbı
├── quickstart.md                  # Faz 1 — G0..G6 doğrulama kapıları
├── contracts/
│   ├── axi-register-map.md        # Kart yüzeyi (MMIO yedek yolunun tek kaynağı)
│   └── host-encoder.md            # Ölçekleme + paketleme (devralınan borç)
├── checklists/requirements.md     # 16/16 geçti
├── SIRADAKI.md
└── tasks.md                       # /speckit-tasks üretecek — bu komut ÜRETMEZ
```

### Source Code (repository root)

```text
hls/                        # DOKUNULMUYOR — çekirdek Faz 2'de donduruldu

fpga/                       # YENİ ÜST DİZİN (karar K3)
├── README.md               # kapsamı ve hls/ ile sınırı
├── bd/                     # Vivado blok tasarım
│   ├── probe_hwh.sh        # G0: PS + gercek qir_kernel IP -> .hwh (uyumluluk denemesi)
│   ├── qir_bd.tcl          # PS preset (elle, board files YOK) + qir_kernel + EMIO I2C
│   └── build.sh            # G1: BD -> sentez -> implementasyon -> .bit/.hwh
└── rtl/                    # ŞİMDİDEN AYRILDI — elle yazılacak Verilog için

agent/                      # PYNQ fpga-agent (Faz 5'in servis tarafı)
├── encoder.py              # Ölçekleme + sabit-nokta paketleme (host-encoder.md)
├── board.py                # AXI sürücü: Overlay (A) / Bitstream+MMIO (B) yolları
├── run_board.py            # G3: çoklu izdüşümlü doğrulama koşumu
├── measure_latency.py      # G4: üç kapsamlı gecikme serisi
└── tests/
    └── test_encoder.py     # G2: KARTSIZ doğrulama kapısı (Prensip V)

artifacts/bitstream/        # .bit/.hwh — git'e girmez (yapıt dizini)
└── README.md               # SHA-256 + üretim komutu + araç sürümü + AXI taban adresi

scripts/
└── build_comparison_matrix.py   # G6: kıyas matrisi

docs/measurements/          # damgalı JSON çıktıları
```

**Structure Decision**: Donanım **kaynağı** yeni `fpga/` üst dizinine gidiyor.
`hls/` [repo-conventions §2](../../docs/repo-conventions.md)'de *"Vitis HLS
kaynakları (Faz 2)"* diye tanımlı; Vivado blok tasarımını oraya koymak o
tanımla çelişirdi. Araç zinciri zaten `artifacts/ip/`'te bölünüyor — HLS orada
bitiyor, Vivado orada başlıyor. `fpga/rtl/` elle yazılacak Verilog için
şimdiden ayrılıyor (RTL `hls/` altına konamaz).

Yeni üst dizin açmanın bedeli **aynı değişikliğe dahildir**: `repo-conventions.md`
§2 dizin listesi, `CLAUDE.md` depo haritası ve `fpga/README.md`. Yapıtlar
`artifacts/bitstream/`'de kalmaya devam ediyor — `fpga/` kaynak dizinidir.

---

## İş öbekleri ve sıra

Sıra keyfî değil — her öbek bir öncekinin açtığı belirsizliği kapatır.

| # | Öbek | Kapsam | Bağımlılık | Kapı |
|---|---|---|---|---|
| ~~**0**~~ | ~~**`.hwh` uyumluluk denemesi**~~ ✅ **BİTTİ 2026-09-20 — A YOLU** | **M** | yok | G0 ✅ |
| 1 | `fpga/` dizini + belge güncellemeleri (K3) | M | yok | — |
| 2 | Blok tasarım + bitstream (EMIO I2C dahil) | M | 1 | G1 |
| 3 | Konak kodlayıcı (**kartsız** doğrulanır) | M | yok | G2 |
| 4 | US1 — kartta koşum + **≥20 izdüşümle** doğrulama | M | 0,2,3 | G3 |
| 5 | US2 — gecikme, üç kapsam | M | 4 | G4 |
| 6 | US3 — enerji (INA219) | H | 4 + INA219 | G5 |
| 7 | US4 — kıyas matrisi | H | 5 + 6 | G6 |
| — | Genlik penceresi varyantı | İ | **yalnız G3 başarısız ve teşhis edilemezse** | — |

Öbek 0, 1 ve 3 birbirinden bağımsızdır — donanım beklerken 1 ve 3 ilerleyebilir
(Prensip V).

**Öbek 0 neden ilk**: Cevap "PYNQ ayrıştıramıyor" ise öbek 4'ün tüm konak kodu
B yoluna göre yazılır. Sonradan öğrenilirse yazılan kod çöpe gider. Tam
sentezi beklemeye gerek yok — `.hwh`, BD çıktı ürünleri üretilirken yazılır
(sentez gerekmez). **Bir saatte cevaplanır, altıncı haftaya bırakılamaz.**

⛔ **Kukla BD PS + gerçek `qir_kernel` IP içermeli.** İlk taslakta "PS-only"
yazıyordu; bu **testi anlamsız kılar** — PS-only bir `.hwh`'de özel IP yoktur,
`ip_dict` boş döner ve bilinen ayrıştırma hatalarının hiçbiri (hepsi IP
tarafındadır) tetiklenmez. Probe boş `ip_dict`'i **başarı saymamalı**.
Ek maliyet ~5 dk. Bkz. [research.md](research.md) §R1, [quickstart.md](quickstart.md) G0.

✅ **SONUÇ (2026-09-20)**: Deneme koşuldu, **A yolu açık**. PYNQ 2.5 ayrıştırıcısı
`ip_dict`'i, taban adresi (`0x40000000`) ve **11 register'ın hepsini** okudu.
Öbek 4'ün konak kodu `Overlay("qir.bit")` üzerine yazılacak; B yolu yedekte kalır.

⚠️ Deney iki yeni kısıt çıkardı, **öbek 4 başlamadan çözülmeli**:
`import pynq` **root istiyor** (konak kodu `sudo` ile koşacak, karttaki sudo
parola soruyor) ve belgelerdeki `HWH` sınıfı bu sürümde **yok** (Zynq için
`_HWHZynq`). Ayrıntı: [research.md](research.md) §R1.

**Öbek 3 neden 4'ten önce**: Kodlayıcı kartsız doğrulanmazsa, kartta çıkan her
uyuşmazlık *"donanım mı, kodlayıcı mı"* belirsizliğinde kalır. Önce
doğrulanırsa uyuşmazlık **donanıma izole olur**. Planın en önemli sıralama
kararı budur.

**Öbek 4'ün izdüşüm maliyeti**: ≥20 `cost` vektörü × ~37 ms ≈ 1 sn koşum.
İzdüşüm başına yalnız `cost` yeniden yazılır (272 word); `phases` bir kez
yazılır. Yani doğrulama gücü neredeyse bedavaya geliyor.

**Öbek 6 bağımsızlığı**: INA219 elde ama bağlanmadı. US1/US2 onu **beklemiyor**;
tek bağı, blok tasarımda EMIO I2C yolunun açık olması (karar K2) — o da
öbek 2'de bir kez ödenir.

---

## Complexity Tracking

> Anayasa ihlali **yok**. Aşağıdakiler spec ile üretilebilir yapıt arasındaki
> sapmalardır ve Prensip II gereği gizlenmeden kaydedilir.

| Sapma | Neden gerekli | Reddedilen basit alternatif |
|---|---|---|
| SC-001 "fidelity ≥ 0,99" kartta **ölçülmüyor**, C-sim zincirinden **devralınıyor** | Çekirdek genlik vektörünü AXI'den vermiyor (madde K-1, Prensip III). 65.536 genlik = 288 KB; çekmek hızlandırmayı anlamsız kılar | `m_axi` ile yeniden sentez: madde K-1 ve Prensip III ihlali; ölçülen tasarım ≠ raporlanan tasarım olur; Faz 2'nin kaynak/zamanlama sayıları geçersizleşir |
| **Faz ekseni bu fazda hiç ölçülmüyor** | Çoklu izdüşüm olasılık ağırlıklı bir toplamdır (`Σ p_i·E_i / Σ p_i`) ve fazları görmez. Faz, Faz 2'nin n=8 cosim PASS'inden gelir | Faz görebilen bir yüzey eklemek: yine yeniden sentez demek. Rapor bu iş bölümünü **açıkça yazar** (Prensip II) |
| EMIO I2C, ihtiyaç duyulmadan **önce** blok tasarıma ekleniyor | US3'te eklemek bitstream'i yeniden üretir; SHA değişir, US1/US2 ölçümleri **tekrarlanır** (FR-016 izlenebilirliği bozulur) | "Sonra ekleriz": bir sentez turu + ölçüm tekrarı; ~10 dk'lık iş saatlere çıkar |
| `T_yazma` ayrı bir ölçüm kapsamı olarak taşınıyor | 1.095 AXI-Lite yazımı küçük bir kalem değil ve CPU tarafında **karşılığı yok**; tek rakam raporlamak kıyası çarpıtır | Tek "uçtan uca" rakamı: FR-007'nin açıkça reddettiği şey |
| Yeni `fpga/` üst dizini açılıyor ([repo-conventions §2](../../docs/repo-conventions.md) değişiyor) | `hls/` §2'de "Vitis HLS kaynakları" diye tanımlı; Vivado BD'sini oraya koymak tanımla çelişir. Elle yazılacak RTL de `hls/` altına konamaz | `hls/bd/`: tek araç zincirini birleştirir görünür ama zincir **zaten** `artifacts/ip/`'te bölünmüş durumda; devir noktası orasıdır |

---

## Sonraki adım

`/speckit-tasks`. Prensip I kapısı **kapandı** — K1, K2, K3 sunuldu ve
2026-09-19'da onaylandı.
