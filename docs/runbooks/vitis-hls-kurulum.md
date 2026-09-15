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

## Disk durumu (ölçüldü, 2026-09-13)

| Sürücü | Toplam | Boş | Not |
|---|---:|---:|---|
| C: | 248,9 GB | **54,1 GB** | İşletim sistemi — dar, kurulum hedefi **yapma** |
| D: | 226,9 GB | **119,7 GB** | ✅ **Kurulum hedefi burası** |
| G: | 72,2 GB | 51,0 GB | Harici SSD (yedekler) — kurulum için kullanma |

---

## ⚠️ Kritik: cihaz ailesi seçimi

AMD'nin birleşik yükleyicisi (Vitis Unified Installer) varsayılan olarak **tüm cihaz ailelerini** işaretli getirir ve kurulum **100–130 GB** tutar. PYNQ-Z2 = **Zynq-7000** (XC7Z020); başka hiçbir aile gerekmiyor.

**Sihirbazda yalnızca `Zynq-7000` işaretli kalsın.** Şunları kaldır:
- Versal (tüm varyantlar)
- UltraScale / UltraScale+
- Alveo / Data Center kartları
- Kintex, Virtex (7-serisi olanlar dahil — Zynq-7000 yeterli)

Bu seçimle kurulum tipik olarak **25–40 GB**'a iner; D:'nin 119,7 GB'ı rahat karşılar.

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

## Adımlar

1. **AMD hesabıyla giriş yap** ve *Vitis Unified Software Platform* (veya *Vivado ML Standard* + Vitis HLS bileşeni) yükleyicisini indir. İndirici küçüktür (~1 GB); asıl indirme kurulum sırasında olur.
2. Yükleyiciyi çalıştır, **kurulum hedefini `D:\Xilinx\`** olarak ayarla.
3. Cihaz ailesi adımında **yalnızca Zynq-7000** bırak (yukarıdaki uyarı).
4. Kurulum bitince `vitis_hls` komutunun PATH'te olduğunu doğrula.
5. **SK-04'ün ölçütü**: örnek bir HLS projesi uçtan uca sentezlensin. Bu koşmadan risk kapanmış sayılmaz.

### Kurulum sonrası doğrulama (SK-04 kapanış ölçütü)

```powershell
# 1) Araç erişilebilir mi
vitis_hls -version

# 2) Ornek bir proje uctan uca sentezleniyor mu
#    (AMD'nin kendi ornekleri kurulum dizini altinda gelir)
```

Bu iki adım geçtiğinde [risk-register.md](../risk-register.md)'de **SK-04 KAPALI** işaretlenir.

---

## İndirme sırasında ne yapılabilir

İndirme saatler sürebilir. O sırada Faz 2'nin araçtan bağımsız kısımları ilerletilebilir:

- Bankalama şemalarının **kağıt üstünde** çıkarılması — `k=0` ve `k=15` için hangi adreslerin aynı bankaya düştüğü ([S-4 sigortası](../risk-register.md), zaten planlıydı).
- Çekirdek C++ iskeletinin yazılması (standart derleyiciyle derlenebilir halde).
- Faz 1 altın referansını okuyup genlik kıyası yapan doğrulama kodunun yazılması.

---

## Temizlik

İndirme bitince yükleyicinin geçici önbelleği (genelde `%TEMP%` veya `Downloads` altında, birkaç GB) silinebilir.
