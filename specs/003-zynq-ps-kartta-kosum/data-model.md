# Faz 1 — Veri Modeli: Zynq PS + Kartta Koşum

**Tarih**: 2026-09-19 · **Girdi**: [spec.md](spec.md) §Key Entities,
[research.md](research.md)

Bu fazın ürettiği şey bir servis değil, **kayıt**tır. Modelin tamamı, bir
sayının nereden geldiğinin sonradan gösterilebilmesi (FR-013, SC-007) üzerine
kuruludur.

---

## Varlıklar

### 1. `Kosum` — tek bir kart çalıştırması

En küçük ölçüm birimi. Tek başına **rapora giremez** (FR-008: en az 10 tekrar).

| Alan | Tip | Not |
|---|---|---|
| `n_qubit` | int | 16 (derleme zamanı sabiti, K-3) |
| `p` | int | 1..3; kıyas için 1 ve 2 |
| `girdi_ozeti` | str | Girdi parametrelerinin SHA-256'sı — belirlenimcilik kanıtı |
| `izdusum_no` | int | Bu koşumun kaçıncı `cost` izdüşümü olduğu (§`IzdusumSerisi`) |
| `beklenen_deger_ham` | float | Karttan okunan `0x0050` — **ölçeklenmiş birimde** |
| `beklenen_deger` | float | Ölçek geri uygulanmış hâli (§R3b) |
| `t_cekirdek_s` | float | `ap_start` → `ap_done` |
| `t_yazma_s` | float | 1.095 register yazımı |
| `t_uctan_uca_s` | float | Kodlama + yazma + koşum + okuma |
| `zaman_damgasi` | ISO-8601 | |
| `git_hash` | str | Konak kodunun sürümü |
| `bitstream_sha256` | str | **Hangi ikilinin koştuğu** (SC-010) |

> ⚠️ `beklenen_deger_ham` ve `beklenen_deger` **ayrı** tutulur. Ölçek hatası
> bu fazın en olası sessiz hatasıdır (Faz 2'den devralınan borç); ham değer
> saklanmazsa hata sonradan teşhis edilemez.

**Geçerlilik kuralları**

- `ap_done` zaman aşımına uğrarsa koşum **kaydedilir ama `gecerli=false`**
  işaretlenir ve hiçbir seride sayılmaz (spec §Edge Cases).
- `p < 1 || p > 3` → çekirdek çalışmaz, çıkış değişmez (madde K-2). Bu bir
  hata değil, **test edilecek bir davranıştır**.

---

### 1b. `IzdusumSerisi` — aynı statevector'ün ≥20 izdüşümü

US1'in doğrulama birimi (karar K1). Devre sabit, `cost` değişken: her koşum
**aynı** statevector'ün farklı bir doğrusal izdüşümünü verir.

| Alan | Tip | Not |
|---|---|---|
| `devre` | str | `phases`, `cos_beta`, `sin_beta`, `p` özeti — **tüm izdüşümlerde aynı** |
| `tohum` | int | `cost` vektörlerini üreten RNG tohumu — yeniden üretilebilirlik |
| `izdusum_sayisi` | int | **≥ 20** |
| `kosumlar` | `Kosum[]` | Her biri bir `cost` vektörüne karşılık |
| `csim_degerleri` | float[] | Aynı girdilerle C-sim çıktısı |
| `sapan_izdusumler` | int[] | Kart ≠ C-sim olan izdüşümlerin indeksleri |

**Değişmezler**

- `izdusum_sayisi < 20` → seri **geçersiz**; US1 kapısı açılmaz.
- `sapan_izdusumler` boş **olmak zorundadır**. Bir tanesi bile doluysa faz
  kapanmaz (spec §Edge Cases).
- Tüm koşumların `devre` özeti aynı olmalı — farklıysa izdüşümler aynı
  statevector'e ait değildir ve seri anlamsızdır.

> ⚠️ **Bu seri fazı kısıtlamaz.** `expectation_scaled` olasılık ağırlıklı bir
> toplamdır (`Σ p_i·E_i / Σ p_i`), yalnız `|ψ_i|²`'yi görür. Faz ekseninin
> kanıtı Faz 2'nin **n=8 cosim PASS**'idir ve raporda **ayrı bir satır**
> olarak yazılır — bu serinin içine karıştırılmaz.

---

### 2. `OlcumSerisi` — aynı konfigürasyonun ≥10 koşumu

Rapora girebilen en küçük birim.

| Alan | Tip | Not |
|---|---|---|
| `konfig` | str | ör. `n16_p2_fpga` |
| `kosum_sayisi` | int | **≥ 10** (FR-008) |
| `medyan_s` | float | |
| `min_s` / `max_s` | float | |
| `yayilim_s` | float | Çeyrekler arası açıklık (IQR) |
| `kapsam` | enum | `cekirdek` \| `yazma` \| `uctan_uca` (FR-007) |
| `protokol_surumu` | str | Ön kayıtlı protokolün sürümü (FR-011) |
| `kosumlar` | `Kosum[]` | Ham koşumlar — özet ham veriden ayrılmaz |

**Değişmez**: `kosum_sayisi < 10` olan bir seri **serileştirilmez**; üretim
anında hata verir. SC-004'ün kod düzeyindeki karşılığı budur.

---

### 3. `EnerjiOlcumu` — bir tarafın enerji kaydı

İki tarafta da **aynı şekle** sahiptir; alet farklı olabilir, yöntem farklı
olamaz (FR-009c).

| Alan | Tip | Not |
|---|---|---|
| `taraf` | enum | `fpga` \| `cpu` |
| `alet` | str | `INA219-0.1ohm` \| `batarya-sayaci` |
| `kapsam` | str | ör. `tum-kart` \| `tum-dizustu` (FR-009, SC-006) |
| `bos_guc_w` | float | Yüksüz güç — **ayrı kaydedilir** |
| `yuk_guc_w` | float | Yük altındaki güç |
| `sure_s` | float | Döngü süresi (≥ 60 sn, FR-009d) |
| `kosum_sayisi` | int | Döngüde tamamlanan koşum |
| `enerji_j_kosum` | float | `(yuk_guc_w - bos_guc_w) * sure_s / kosum_sayisi` |
| `kalibrasyon` | `Kalibrasyon` | FR-010 |

> Mutlak güç değil **delta** raporlanır. Dizüstü ekranı ~10 W, tüm PYNQ kartı
> ~3 W — mutlak kıyas sonucu ekranın belirlemesi demek olurdu.

### 3b. `Kalibrasyon`

| Alan | Tip | Not |
|---|---|---|
| `bilinen_yuk_w` | float | Referans yük |
| `okunan_w` | float | Aletin okuduğu |
| `sapma_yuzde` | float | **< %5 olmalı** (SC-005) |
| `zaman_damgasi` | ISO-8601 | Ölçümlerden **önce** (FR-010) |

**Değişmez**: `sapma_yuzde ≥ 5` ise o aletle alınan hiçbir `EnerjiOlcumu`
geçerli sayılmaz.

---

### 4. `KiyasSatiri` — FPGA ve CPU yan yana

| Alan | Tip | Not |
|---|---|---|
| `konfig` | str | **İki tarafta da aynı** n, p, problem (FR-012) |
| `fpga_gecikme` | `OlcumSerisi` ref | |
| `cpu_gecikme` | `OlcumSerisi` ref | |
| `fpga_enerji` | `EnerjiOlcumu` ref | |
| `cpu_enerji` | `EnerjiOlcumu` ref | |
| `hizlanma` | float \| `null` | Ölçülmüş değerlerden **hesaplanır** |
| `not` | str | Ölçülemeyen eksen varsa **nedeni** (SC-008) |

**Değişmez**: Hiçbir hücre elle doldurulamaz; her hücre bir `OlcumSerisi` veya
`EnerjiOlcumu` kimliğine **işaret eder**. `hizlanma` iki taraf da doluysa
hesaplanır, aksi hâlde `null` kalır ve `not` zorunlu olur.

> ⚠️ Gecikme ekseninde başabaş beklendiği **şimdiden biliniyor** (FPGA 37,28 ms
> tahmini, CPU turbo 32,75 / plato 41,93 ms). `hizlanma < 1` çıkması bir hata
> değil, **bulgudur** ve öyle raporlanır (Prensip II).

---

### 5. `DonanimYapiti` — karta yüklenen ikili

| Alan | Tip | Not |
|---|---|---|
| `dosya` | path | `artifacts/bitstream/qir_<tarih>_<hash>.bit` |
| `sha256` | str | **Depoda kayıtlı** (§R6) |
| `kaynak_git_hash` | str | Hangi koddan üretildi |
| `arac_surumu` | str | `Vivado 2025.2` |
| `ip_paketi` | str | `qir_kernel_ip_20260917_15931cc.zip` |
| `uretim_komutu` | str | Yeniden üretim reçetesi |
| `axi_taban_adres` | hex | MMIO yedek yolu için **zorunlu** (§R1) |

`axi_taban_adres` normalde `.hwh`'den okunur. PYNQ 2.5 onu ayrıştıramazsa tek
kaynak **bu kayıttır** — bu yüzden yapıtın parçasıdır, keşfedilen bir değer değil.

---

## Varlık ilişkileri

```
DonanimYapiti ──yüklenir──> (kart)
                              │
                              ├── Kosum ×≥20 ──> IzdusumSerisi   (US1: doğrulama)
                              │
                              ├── Kosum ×≥10 ──> OlcumSerisi     (US2: gecikme)
                              │                       │
                              └── EnerjiOlcumu(fpga) ─┤
                                                      ▼
CPU tarafı ── OlcumSerisi + EnerjiOlcumu(cpu) ──> KiyasSatiri
```

`IzdusumSerisi` kıyasa **girmez** — kapıdır. Geçmeden `OlcumSerisi` toplanmaz.

---

## Kalıcılık

Yeni bir veri deposu **yoktur**. Kayıtlar, depoda hâlihazırda işleyen kalıba
yazılır: `docs/measurements/` altında damgalı JSON
(`<ad>_<tarih>_<git-hash>[_<konfig>].json`).

| Dosya | İçerik |
|---|---|
| `kart-gecikme_<tarih>_<hash>_n16_p2.json` | `OlcumSerisi` |
| `kart-dogrulama_<tarih>_<hash>_n16_p1.json` | `IzdusumSerisi` + altın referans karşılaştırması |
| `kart-enerji_<tarih>_<hash>.json` | `EnerjiOlcumu` + `Kalibrasyon` |
| `kiyas-matrisi_<tarih>_<hash>.json` | `KiyasSatiri[]` |

Nihai özet [docs/olculen-degerler.md](../../docs/olculen-degerler.md)'e işlenir —
tez/makale için tek referans orasıdır.
