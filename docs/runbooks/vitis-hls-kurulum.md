# Runbook — Vitis HLS Kurulumu

**Amaç**: Faz 2'nin sentez ölçütlerini ([002 spec](../../specs/002-fpga-statevector-cekirdegi/spec.md) SC-002, SC-003, SC-005) doğrulanabilir hale getirmek.
**İlgili risk**: [SK-04](../risk-register.md) — *"Vitis HLS kurulum/lisans sorunu"*, karar tarihi **H1 sonu (20 Eylül)**, etki **Yüksek**.
**Durum**: 🔴 Kurulu değil. Bu runbook, kurulumu **kullanıcının** yapması için hazırlandı — indirme AMD hesabı gerektirdiğinden otomatikleştirilemez.

---

## Neden bu acil

Faz 2, [scope-triage.md](../../specs/000-kapsam-takvim/scope-triage.md)'de **M** etiketli — projenin çekirdeği. Vitis HLS olmadan:

| Yapılabilir | Yapılamaz |
|---|---|
| Çekirdek C++ kodunu yazmak | Sentez raporu üretmek |
| Bankalama şemasını tasarlamak | II ölçmek (SK-02'nin tek gerçek testi) |
| Standart derleyiciyle mantık doğrulaması | Cosim, IP export |

Yani **duracak iş yok** (Anayasa Prensip V), ama [K-02](../../specs/000-kapsam-takvim/cut-plan.md) ve [K-04](../../specs/000-kapsam-takvim/cut-plan.md) kesme tetiklerinin ölçütleri (H4, H6) bu araç olmadan **ölçülemez**. Kurulum geciktikçe o karar tarihleri anlamsızlaşır.

---

## Disk durumu (yeniden ölçüldü, 2026-09-15)

| Sürücü | Toplam | Boş | Not |
|---|---:|---:|---|
| C: | 248,9 GB | **52,5 GB** | İşletim sistemi — dar, kurulum hedefi **yapma** |
| D: | 226,9 GB | **52,7 GB** ⬇️ | ✅ Kurulum hedefi — ama **payı daraldı** |
| G: | 72,2 GB | 51,0 GB | Harici SSD (yedekler) — kurulum için kullanma |

> ⚠️ **D: 119,7 GB'dan 52,7 GB'a düştü** (13 → 15 Eylül). En büyük tüketiciler:
> `D:\steam` 68,3 GB ve `D:\docker` 58,4 GB (Docker Desktop veri dizini bu projede
> D:'ye taşınmıştı). Zynq-7000-only kurulum 25–40 GB istediği için **hâlâ yeter**,
> ama sonrasında ~13–28 GB kalır.
>
> **Sıkışırsa**: `docker system prune -a` ile önemli miktarda yer açılabilir —
> OSRM imajları yeniden çekilebilir, `data/osrm/` zaten repoda değil.
> Steam'e dokunma, o kullanıcının kendi alanı.

---

## ⚠️ Kritik: cihaz ailesi seçimi

AMD'nin birleşik yükleyicisi (Vitis Unified Installer) varsayılan olarak **tüm cihaz ailelerini** işaretli getirir ve kurulum **100–130 GB** tutar. PYNQ-Z2 = **Zynq-7000** (XC7Z020); başka hiçbir aile gerekmiyor.

**Sihirbazda yalnızca `Zynq-7000` işaretli kalsın.** Şunları kaldır:
- Versal (tüm varyantlar)
- UltraScale / UltraScale+
- Alveo / Data Center kartları
- Kintex, Virtex (7-serisi olanlar dahil — Zynq-7000 yeterli)

> ⚠️ **2026-09-15 DÜZELTMESİ — "25–40 GB" YANLIŞTI.** O rakam eski Vivado
> sürümlerinden hatırlanmıştı. 2025.2'de yükleyicinin kendi gösterdiği gerçek
> değerler (Vivado ML Standard + Vitis HLS + **yalnızca Zynq-7000**, Model
> Composer kaldırılmış):
>
> | | |
> |---|---:|
> | Download Size | **16,61 GB** |
> | **Disk Space Required** | **60,66 GB** |
>
> Yani kurulum **D:'nin 52,7 GB'ına da sığmıyor**. Yer açmadan devam edilemez.
> Not: "Disk Space Required" tepe değerdir (indirme + açma); "Final Disk Usage"
> kurulum sonrası daha düşük olabilir — ama yükleyici **tepe değere göre** engel
> koyar.

Cihaz ailesi kısıtlaması yine de kritik: hepsi seçili bırakılırsa 100–130 GB'a çıkar.

---

## İndirilecek dosya ve sağlamaları (2026-09-15'te doğrulandı)

AMD'nin kendi imzalı `.digests` dosyasından alındı (PGP imzalı, `SHA512` hash'li):

| | |
|---|---|
| Dosya | `FPGAs_AdaptiveSoCs_Unified_SDI_2025.2_1114_2157_Win64.exe` |
| Sürüm | Unified Installer **2025.2**, Windows 64-bit |
| MD5 | `1ecf89bb9f8f7d124637178c3e3ca396` |
| SHA-1 | `6cf218748e0b7540442d35a8a7af3fc46211f983` |
| SHA-256 | `ddcea24a734b2727d152703c784bd822195a5898333cfc8c5041a92eadd6ea36` |

⚠️ **Dikkat**: İndirme sayfasındaki "Download File Verification" penceresinde **Digest** butonu
installer'ı değil, yalnızca bu sağlama dosyasını indirir (~1,4 KB). Asıl installer için pencereyi
kapatıp **Windows Self Extracting Web Installer** satırındaki indirme bağlantısını kullan —
Linux satırıyla karıştırma.

### İndirme sonrası doğrulama

```powershell
(Get-FileHash "$env:USERPROFILE\Downloads\FPGAs_AdaptiveSoCs_Unified_SDI_2025.2_1114_2157_Win64.exe" -Algorithm SHA256).Hash.ToLower()
# beklenen: ddcea24a734b2727d152703c784bd822195a5898333cfc8c5041a92eadd6ea36
```

Tutmazsa **kuruluma başlama** — bozuk installer'la 25-40 GB'lık kurulumun ortasında kalmak,
10 saniyelik kontrolden çok daha pahalıdır. (Aynı disiplin `scripts/fetch_osm.ps1`'de OSM
dökümü için zaten uygulanıyor — spec FR-005.)

## 🔴 Smart App Control uyarısı — kuruluma başlamadan oku

2026-09-15'te [SK-05](../risk-register.md) keşfedildi: Windows **Smart App Control
açık** ve `g++` ile üretilen her yeni imzasız `.exe`'yi engelliyor. Bu, Vitis'in
akışlarını **eşit etkilemez** — hangi adımın etkilendiği önemli:

| Vitis adımı | Kullanıcı kodundan ikili ÇALIŞTIRIR mı | SAC riski | Hangi ölçüt |
|---|:---:|:---:|---|
| `csynth` (sentez) | ❌ hayır — C++'ı RTL'e **derler** | ✅ **güvenli** | **SC-002, SC-003** |
| `csim` | ✅ evet — testbench'i derleyip koşar | ⚠️ riskli | SC-001 |
| `cosim` | ✅ evet | ⚠️ riskli | SC-005 |

> **Sonuç: kritik yol güvende.** BRAM ve II sayıları `csynth`'ten gelir ve o
> kullanıcı ikilisi çalıştırmaz. `csim` engellenirse kayıp yok — C-sim
> doğrulaması zaten WSL'de koşuyor ve geçti
> ([faz2-csim.md](../measurements/faz2-csim.md)). Yalnızca `cosim`/SC-005 (US5,
> P3 öncelikli) etkilenir.
>
> Bu yüzden **kurulum Windows'ta yapılır**; Linux'a taşıma gereksiz bir
> karmaşıklık olurdu. SAC kapatılmaz — geri alınamaz bir güvenlik değişikliğidir.

---

## Adımlar

### 0. İndirme sayfası (2026-09-15'te sayfa açılarak doğrulandı)

**Doğrudan adres — sürüm seçiciyle uğraşma:**

```
https://www.amd.com/en/support/downloads/adaptive-socs-and-fpgas/development-tools/2025-2.html
```

*(Eski `xilinx.com/support/download.html` → **301** → `.../adaptive-socs-and-fpgas.html`,
oradan da sürüm seçilir. Yukarıdaki bağlantı doğrudan 2025.2'ye gider.)*

#### ⚠️ Neden 2025.2, neden 2026.1 DEĞİL

Sayfanın kendi duyurusu: *"Starting with the **2026.1** release, AMD Vivado Design
Suite is evolving to a new **tiered licensing model**... pay only for the device
families and features that you need."*

PYNQ-Z2 = Zynq-7000 (XC7Z020) ve bu aile tarihsel olarak **ücretsiz** Vivado ML
Standard kapsamındaydı. Kademeli lisanslamada hangi ailelerin ücretsiz katmanda
kaldığı **doğrulanmadı**. 2025.2, değişiklikten önceki son sürüm — 40 GB'lık bir
kurulumun sonunda "bu cihaz ailesi lisansınızda yok" duvarına çarpmamak için
**2025.2 seçilir**. 2026.1'e geçiş, ücretsiz katmanın Zynq-7000'i kapsadığı
doğrulandıktan sonra ayrı bir karar olur.

#### Sayfadaki üç seçenekten hangisi

| Satır | Tip | Boyut | Bu mu? |
|---|---|---:|:---:|
| **Windows Self Extracting Web Installer** | EXE | **233,33 MB** | ✅ **BU** |
| Linux Self Extracting Web Installer | BIN | 346,7 MB | ❌ |
| 2025.2 **SFD** (Single File Download) | TAR/GZIP | **95,68 GB** | ❌ sakın |

1. **AMD hesabıyla giriş yap** (indirme oturum açmadan başlamaz) ve
   **"Windows Self Extracting Web Installer"** satırına tıkla. Dosya yalnızca
   **233 MB**'dır; asıl içerik kurulum sırasında iner.

   > ⚠️ **2026-09-15'te burada takılındı**: satırın yanındaki **"Verify Download"**
   > butonuna basıldı ve yalnızca 1,4 KB'lık `.digests` dosyası indi; asıl `.exe`
   > hiç başlamadı. O buton sağlama dosyasını verir, yükleyiciyi değil —
   > tıklanacak yer **başlığın kendisidir**.
2. Yükleyiciyi çalıştır, **kurulum hedefini `D:\Xilinx\`** olarak ayarla.
3. Cihaz ailesi adımında **yalnızca Zynq-7000** bırak (yukarıdaki uyarı).
4. Kurulum bitince `vitis_hls` komutunun PATH'te olduğunu doğrula.
5. **SK-04'ün ölçütü**: örnek bir HLS projesi uçtan uca sentezlensin. Bu koşmadan risk kapanmış sayılmaz.

### Kurulum sonrası doğrulama (SK-04 kapanış ölçütü)

Sırayı bozma — **en riskli adım en başta**, çünkü başarısız olursa kalan işi
yeniden planlamak gerekir:

```bash
vitis_hls -version
```

Sonra **hemen `csim` denemesi** — SK-05'in Vitis'i etkileyip etkilemediğini
öğrenmenin tek yolu bu ve cevabı erken bilmek gerekiyor:

```bash
cd C:\Users\olcay\IdeaProjects\qir-engine; vitis_hls -f hls\tcl\csim.tcl
```

| Sonuç | Anlamı | Ne yapılır |
|---|---|---|
| Koştu | SAC Vitis'i etkilemiyor | Normal akış |
| *"Uygulama Denetimi ilkesi..."* | SK-05 Vitis'i de vuruyor | **Panik yok.** `csynth` yine çalışır (kullanıcı ikilisi koşmaz); C-sim WSL'de kalır, yalnızca `cosim`/SC-005 düşer. SK-05'e yaz. |

Son olarak sentez — SC-002/SC-003'ün geldiği yer:

```bash
cd C:\Users\olcay\IdeaProjects\qir-engine; vitis_hls -f hls\tcl\csynth.tcl
```

**SK-04 KAPALI** için gereken: `vitis_hls -version` çalışıyor **ve** bir proje
uçtan uca sentezleniyor (`csynth` raporu üretiliyor). `csim` çalışması kapanış
koşulu **değildir** — o SK-05'in konusu.

---

## İndirme sırasında ne yapılabilir

İndirme saatler sürebilir. O sırada Faz 2'nin araçtan bağımsız kısımları ilerletilebilir:

- Bankalama şemalarının **kağıt üstünde** çıkarılması — `k=0` ve `k=15` için hangi adreslerin aynı bankaya düştüğü ([S-4 sigortası](../risk-register.md), zaten planlıydı).
- Çekirdek C++ iskeletinin yazılması (standart derleyiciyle derlenebilir halde).
- Faz 1 altın referansını okuyup genlik kıyası yapan doğrulama kodunun yazılması.

---

## Temizlik

İndirme bitince yükleyicinin geçici önbelleği (genelde `%TEMP%` veya `Downloads` altında, birkaç GB) silinebilir.
