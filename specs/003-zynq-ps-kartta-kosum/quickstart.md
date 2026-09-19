# Faz 1 — Doğrulama Kılavuzu: Zynq PS + Kartta Koşum

**Tarih**: 2026-09-19 · **Plan**: [plan.md](plan.md)

Bu dosya, fazın **koşulabilir doğrulama senaryolarıdır** — uygulama ayrıntısı
`tasks.md`'ye aittir. Senaryolar sırayla kapıdır: biri geçmeden sonraki
anlamlı değildir.

Tüm konak komutları **PowerShell** sözdizimindedir; çalışma dizini
`C:\Users\olcay\IdeaProjects\qir-engine`.

---

## Ön koşullar

| | Durum |
|---|---|
| Kart | 192.168.1.2, SSH/Jupyter doğrulandı (2026-09-19) |
| Besleme | **Adaptör, JP5 = REG** — ⚠️ **değiştirilmeyecek** (enerji ölçümü buna bağlı) |
| Boot kaynağı | JP4 = SD |
| Vivado | `/opt/Xilinx/2025.2/Vivado` (WSL/Ubuntu) — kurulu, `xc7z020` destekli |
| IP paketi | `artifacts/ip/qir_kernel_ip_20260917_15931cc.zip` |
| INA219 | Elde, **bağlanmadı** — yalnız G5 için |

Kart erişimi:

```bash
ssh xilinx@192.168.1.2 "python3 -c 'import pynq; print(pynq.__version__)'"
```

---

## G0 — Uyumluluk denemesi ⚠️ **İLK İŞ, HER ŞEYDEN ÖNCE**

**Ne kanıtlar**: PYNQ 2.5'in Vivado 2025.2 `.hwh`'sini ayrıştırıp
ayrıştıramadığını — yani `Overlay` (A yolu) mu yoksa `MMIO` (B yolu) mu
kullanılacağını.

**Neden önce**: Cevap "hayır" ise US1'in tüm konak kodu B yoluna göre yazılır.
Sonradan öğrenilirse yazılan kod çöpe gider. Bir saatte cevaplanır.

**Tam sentez beklenmez** — `.hwh`, BD çıktı ürünleri üretilirken yazılır
(`validate_bd_design` + `generate_target all`), sentez/implementasyon gerekmez.

⛔ **Kukla BD PS + gerçek `qir_kernel` IP içermeli, PS-only OLMAMALI.**
PS-only bir `.hwh`'de özel IP yoktur; ayrıştırıcı için en kolay durumdur ve
`ip_dict` boş döner — test "geçer" ama hiçbir şey kanıtlamaz. Bilinen
ayrıştırma hatalarının tamamı IP tarafındadır. Ek maliyet ~5 dk.

```powershell
wsl -d Ubuntu -e bash fpga/bd/probe_hwh.sh
scp artifacts/bitstream/probe.hwh xilinx@192.168.1.2:/home/xilinx/
```

```bash
ssh xilinx@192.168.1.2 "python3 /home/xilinx/probe_test.py"
```

`probe_test.py` — boş `ip_dict`'i **başarı saymaz**:

```python
from pynq.pl_server.hwh_parser import HWH
h = HWH('/home/xilinx/probe.hwh')
assert len(h.ip_dict) > 0, 'ip_dict BOS -- test anlamsiz, kukla BD IP icermiyor'
assert any('qir' in k.lower() for k in h.ip_dict), 'qir_kernel bulunamadi'
print('AYRISTIRDI:', list(h.ip_dict))
for ad, bilgi in h.ip_dict.items():
    print(' ', ad, 'taban:', hex(bilgi.get('phys_addr', 0)),
          'register:', len(bilgi.get('registers', {})))
```

Register haritası da okunabiliyorsa **A yolu gerçekten açıktır**; yalnız
`ip_dict` dolup register'lar boş geliyorsa bu **kısmi başarıdır** ve taban
adresi `.hwh`'den alınıp erişim yine `MMIO` ile yapılır.

> ⚠️ `pynq.pl_server.hwh_parser` içe aktarma yolu PYNQ 2.5'te **doğrulanmalı**;
> farklıysa `python3 -c "import pynq, os; print(os.path.dirname(pynq.__file__))"`
> ile modül aranır. Yolun kendisi bir varsayımdır, sonuç değildir.

**Beklenen sonuçlar — ikisi de plan için geçerli çıktıdır:**

| Sonuç | Anlamı | Plan |
|---|---|---|
| `AYRISTIRDI n` | A yolu açık | `Overlay` kullanılır, B yolu yine de yazılır (yedek) |
| `AttributeError` / `KeyError` | A yolu kapalı (beklenen) | **B yolu**: `Bitstream` + `MMIO`, taban adres elle |

**Kapı**: Sonuç ne olursa olsun `research.md` §R1'e tarih damgasıyla işlenir.
Faz bu bilgi olmadan ilerlemez.

---

## G1 — Bitstream üretilir ve saklanır

**Ne kanıtlar**: FR-016 / SC-010 — karta yüklenecek ikili var, izlenebilir.

```powershell
wsl -d Ubuntu -e bash fpga/bd/build.sh
```

**Beklenen**:

- `artifacts/bitstream/qir_<tarih>_<hash>.bit` ve `.hwh` oluşur
- **EMIO I2C blok tasarımda** (karar K2) — US3 için yeniden sentez gerekmeyecek
- Zamanlama **tutar** (WNS ≥ 0) — tutmazsa faz durur, FCLK düşürülmez
  (100 MHz Faz 2 ölçümlerinin dayanağıdır)
- `artifacts/bitstream/README.md` SHA-256, üretim komutu, araç sürümü,
  **AXI taban adresi** ile güncellenir

**Kapı**: `axi_taban_adres` kaydedilmeden G3'e geçilmez — B yolunun tek
doğruluk kaynağı odur.

---

## G2 — Konak kodlayıcı, **kart olmadan** doğrulanır

**Ne kanıtlar**: [host-encoder.md](contracts/host-encoder.md) madde H-5.
Ölçekleme borcu kapandı, paketleme doğru.

```powershell
python -m pytest agent/tests/test_encoder.py -v
wsl -d Ubuntu -e bash hls/build_and_run.sh
```

**Beklenen**:

- Kodlayıcı, aralık dışı katsayıda **istisna fırlatır** (madde H-3) — sessizce
  doyurmaz
- Ölçek geri uygulandığında beklenen değer, altın referansla Faz 2 fidelity
  bütçesi içinde uyuşur
- Kart **hiç gerekmez** (Prensip V)

**Kapı**: Bu geçmeden karta bağlanılmaz. Geçmeden gidilirse kartta çıkacak her
uyuşmazlık *"donanım mı, kodlayıcı mı"* belirsizliğinde kalır.

---

## G3 — Çekirdek kartta koşuyor ve çıktısı doğru (US1)

**Ne kanıtlar**: SC-001, SC-002, SC-003 · FR-001–FR-006

```powershell
python agent/run_board.py --n 16 --p 2 --izdusum 20 --tohum 42
```

**Çoklu izdüşüm (karar K1)**: `cost` yalnızca `expectation_scaled`'i besler,
`run_circuit`'e hiç girmez. Devre sabit tutulup **yalnız `cost` değiştirilerek**
yeniden koşulunca kart, aynı statevector'ün **bağımsız bir izdüşümünü** verir.
Çekirdek durumsuz ve belirlenimci olduğu için her koşum aynı vektörü üretir.

| | |
|---|---|
| İzdüşüm sayısı | **≥ 20** rastgele `cost` vektörü |
| Tohum | Sabit, JSON'a kaydedilir |
| Maliyet | 20 × ~37 ms ≈ 1 sn; izdüşüm başına yalnız `cost` (272 word) yeniden yazılır |

**Beklenen**:

| Ölçüt | Beklenti |
|---|---|
| `ap_idle` başlangıçta | 1 (madde A-1) |
| `ap_done` süresi | ~37 ms, 5 sn zaman aşımından çok önce |
| **20 izdüşümün hepsi ↔ C-sim** | **birebir** (SC-003) — biri bile sapsa kapı kapalı |
| Beklenen değer ↔ altın referans | Faz 2 fidelity bütçesi içinde uyuşur |
| İki ardışık koşum | **bit düzeyinde aynı** (SC-002, madde A-5) |
| `p=0` ve `p=4` | Çekirdek koşmaz, `0x0050` değişmez (madde A-3) |
| Kart yeniden başlatıldıktan sonra | Aynı sonuç (durumsuzluk, FR-005) |

**Kapı — uyuşmazlık hâlinde**: Bu bir tasarım krizi değil **doğrulama
kriziydir**. Hangisinin doğru olduğu altın referansla belirlenir ve fark
kapanmadan **hiçbir hız/enerji rakamı raporlanmaz** (spec §Edge Cases).
Çoklu izdüşümün teşhis değeri tek skalerden yüksektir: hangi `cost`
vektörlerinde saptığı, hatayı `h` yoluna mı `J` yoluna mı daralttığını
gösterir. Desen yine de neden vermezse — ve yalnız o zaman — genlik penceresi
varyantı devreye alınır ([research.md](research.md) §R3).

> ⚠️ **Bu yöntem fazı görmez.** `expectation_scaled` olasılık ağırlıklı bir
> toplamdır (`Σ p_i·E_i / Σ p_i`), yani yalnız `|ψ_i|²`'yi kısıtlar. Faz ekseni
> bu fazda **hiç ölçülmez**; Faz 2'nin **n=8 cosim PASS**'inden gelir. Rapor bu
> iş bölümünü açıkça yazar.
>
> Genlik fidelity'si de burada **ölçülmez, devralınır** (SC-008): 20 izdüşümün
> kart↔C-sim eşleşmesi + C-sim↔altın referans ölçülmüş fidelity'si.

---

## G4 — Gecikme kartta ölçülüyor (US2)

**Ne kanıtlar**: SC-004 · FR-007, FR-008

```powershell
python agent/measure_latency.py --n 16 --p 2 --tekrar 30
python agent/measure_latency.py --n 16 --p 1 --tekrar 30
```

**Beklenen**:

- **Üç kapsam ayrı ayrı** raporlanır: `T_cekirdek`, `T_yazma`, `T_uctan_uca`
- Her konfigürasyon için **≥ 10** koşum; medyan **ve yayılım** birlikte
  (tek koşum rakamı hiçbir yere yazılmaz)
- `docs/measurements/kart-gecikme_<tarih>_<hash>_n16_p2.json` damgalı yazılır

**HLS tahminiyle karşılaştırma**: Tahmin p=2 için 37,28 ms. Sapma **gizlenmez**;
nedeni araştırılır, bulunamazsa **bulunamadığı yazılır** (FR-014).

> ⚠️ `T_yazma` küçük bir kalem değildir: 1.095 register yazımı. CPU tarafında
> bu maliyet **yoktur**, dolayısıyla `T_cekirdek` ile `T_uctan_uca` kıyasta
> farklı sonuç verir ve **ikisi de** raporlanır.

> ⚠️ Isınma/kısılma ardışık koşumları yavaşlatabilir — bu yüzden yayılım
> raporlanır ve koşum sırası kaydedilir.

---

## G5 — Enerji kartta ölçülüyor (US3)

**Ne kanıtlar**: SC-005, SC-006 · FR-009, FR-009c, FR-009d, FR-010

**Ön koşul**: INA219, 12 V hattında seri (0,1 Ω şönt). EMIO I2C blok tasarımda
hazır (§R5).

⚠️ **Besleme düzeni değiştirilmez** — adaptör + JP5=REG sabit kalır. USB'ye
dönülürse CPU tarafıyla karşılaştırma geçersizleşir.

```powershell
ssh xilinx@192.168.1.2 "python3 /home/xilinx/calibrate_ina219.py"
ssh xilinx@192.168.1.2 "python3 /home/xilinx/measure_energy.py --sure 120"
```

**Beklenen**:

| Ölçüt | Beklenti |
|---|---|
| Kalibrasyon sapması | **< %5** (SC-005) — aşarsa ölçüm geçersiz |
| Boş güç / yük gücü | **Ayrı ayrı** kaydedilir |
| Döngü süresi | ≥ 60 sn (tek koşum ~37 ms, ölçülemez) |
| Enerji | `(P_yuk - P_bos) * sure / kosum_sayisi` J/koşum |
| Kapsam | **"tüm kart"** olarak yazılır (yalnız PL değil) |

**Karşı taraf** (ölçüldü, yeniden ölçülmeyecek): CPU **0,644 J/koşum**,
batarya delta yöntemi, kapsam "tüm dizüstü".

**Modül gelmezse / yanarsa**: Enerji ekseni düşer. Gecikme ekseni tek başına
raporlanır ve enerjinin **neden** ölçülemediği yazılır (FR-014, SC-008).

---

## G6 — Kıyas matrisi (US4)

**Ne kanıtlar**: SC-007, SC-008 · FR-012, FR-013

```powershell
python scripts/build_comparison_matrix.py
```

**Beklenen**:

- Her hücre bir ölçüm serisine **işaret eder** — elle yazılmış sayı yok
- İki taraf da **aynı n, aynı p, aynı problem**
- Hızlanma oranı **ölçülmüş** değerlerden hesaplanır, yayılımla birlikte
- Ölçülemeyen eksen varsa `null` + **neden**

> **Beklenen bulgu**: Gecikmede başabaş. FPGA tahmini 37,28 ms, CPU turbo
> 32,75 / plato 41,93 ms — FPGA tam aralarına düşüyor. `hizlanma < 1` çıkması
> **hata değil bulgudur** ve öyle raporlanır (Prensip II). Tezin sonucu
> **enerji ekseninde** belirlenecek.

---

## Faz kapanış kapısı

| | Ölçüt |
|---|---|
| ☐ | G0 sonucu `research.md` §R1'e damgalı işlendi |
| ☐ | `fpga/README.md` yazıldı; `repo-conventions.md` §2 ve `CLAUDE.md` depo haritası güncellendi (karar K3) |
| ☐ | Bitstream SHA-256 + AXI taban adresi depoda kayıtlı (SC-010) |
| ☐ | Ölçüm protokolü ilk ölçümden **önce** yazıldı ve donduruldu (SC-009) |
| ☐ | ≥20 izdüşümün **hepsi** kart↔C-sim birebir tuttu; tohum kayıtlı |
| ☐ | Raporda faz ekseninin **bu fazda ölçülmediği** ve n=8 cosim'den geldiği yazılı |
| ☐ | Genlik fidelity'sinin **devralınan çıkarım** olduğu yazılı, ölçülmüş gibi değil (SC-008) |
| ☐ | Hiçbir gecikme serisi < 10 koşum (SC-004) |
| ☐ | Raporda **tahmini tek bir sayı yok**; ölçülemeyen eksen varsa nedeni yazılı (SC-008) |
| ☐ | Kararlar ADR'ye, SIRADAKİ güncel ([faz-sonu-kontrol.md](../../docs/faz-sonu-kontrol.md)) |
| ☐ | Sonuçlar [docs/olculen-degerler.md](../../docs/olculen-degerler.md)'e işlendi |
