# Kart Enerji Ölçüm Protokolü (US3, T046–T050)

| | |
|---|---|
| **Durum** | 🔒 v1.0 **DONDURULDU — 2026-10-04**, kullanıcı onayıyla, ilk kalibrasyondan önce. 📝 **v1.1 taslağı** (§11: kalibrasyonun gerilim kaynağı) onay bekliyor |
| **Sürüm** | **v1.1 (taslak, 7 Eki)** — değişiklik **§11**'de, **hiçbir kalibrasyon ya da ölçüm yapılmadan önce**. Kayıtlar `kart-enerji-protokolu v1.1` taşır |
| **Onaylanan metin** | commit `be2abfc`, git içerik özeti `c84a4d73756030bb0e5cddade68b8d0dd1636fce` (`git rev-parse be2abfc:docs/measurements/kart-enerji-protokolu.md`). Dondurmadan sonra yalnız bu üç durum satırı değişti: `git diff be2abfc -- <bu dosya>`. Yürütücü kod `be2abfc`'deki hâliyle donar |
| **Görev** | T046 (düzenek), T048 (kalibrasyon), T049–T050 (ölçüm), T069'un FPGA enerji hücresi |
| **Dayanak** | FR-009, FR-009c/d, FR-010, FR-011, SC-005, SC-006, SC-009 · [data-model §3, §3b](../../specs/003-zynq-ps-kartta-kosum/data-model.md) · dizüstü tarafı: [gpu-enerji-protokolu v1.1](gpu-enerji-protokolu.md) (**aynı yöntem**) · F2 iş yükü: [kart-olcum-protokolu v1.0](kart-olcum-protokolu.md) (**aynı kod**) |
| **Yürütücü** | `agent/ina219.py` (sürücü, örnekleyici, hesap), `agent/calibrate_ina219.py` (T048), `agent/measure_energy.py` (T049). Sabitler kodda; `agent/tests/test_ina219.py` kodu bu belgeye bağlar |

**Kural (FR-011, SC-009)**: ilk kalibrasyondan **önce** onaylanıp dondurulur;
sonuca bakıp değiştirilemez, değişiklik yeni sürümdür.

---

## 1. Soru

Kartın **tamamı** (12 V girişi), aynı hesabı PL'de (**F2**, FPGA çekirdeği)
ve PS'te (**P2**, aynı algoritma ARM'da) koştururken **koşum başına ne kadar
enerji** harcıyor; boşta **toplam ne kadar güç** çekiyor?

Neden: tez cümlesinin "5 W zarfında ölçülmüş enerji bedeli" kısmı; kıyas
matrisinin (T069) FPGA enerji hücresi; PS↔PL için gecikmedeki 2,30×'in
enerji karşılığı.

---

## 2. Önceden bilinenler — ön kayıt beyanı

| Bilinen | Değer | Kaynak |
|---|---|---|
| Kartta gecikme (JP5 = **USB**) | F2 `T_cekirdek` 36,578 ms; ARM float 84,13 ms | kart-gecikme p2 (27 Eyl), ps-pl-hizlanma (21 Eyl) |
| Dizüstü enerjisi (pilde, tüm makine) | CPU tek iş parçacığı **0,0217 J/koşum**; Aer CPU 0,243; GPU 0,0127 (⚠️ güvenilmez) | olculen-degerler §6.2 (3 Eki) |
| INA219 | 4 Eki: `0x40` cevap veriyor, yapılandırma `0x399F`; VIN uçları boştayken bara 888 mV, şönt −40 µV | bu oturum |
| Kartın gücü | **ölçülmedi.** Belgelerdeki "~3 W" kaynağı belirsiz bir tahmin | data-model §3 notu |
| ARM float `beklenen_deger` | −3950,990722656 | ps-pl-hizlanma (21 Eyl) |
| Kart saati | NTP yok, gerçek saatten ~20 saat geride (21 Eyl) → kart damgaları yalnız **sıralama** için; tarih damgası konakta | ps-pl-hizlanma notu |

---

## 3. Düzenek

- **12 V hattı (T046)**: adaptör → dişi DC jak klemensi → INA219 **VIN+** →
  şönt → **VIN−** → erkek DC jak klemensi → kartın güç jakı. **JP5 = REG.**
  Adaptörün kablosu **kesilmez**. Jak ölçüsü ve kutup (merkez +) adaptörle
  kart arasında multimetreyle doğrulanır.
- **I2C**: INA219 → kartın Arduino başlığı: VCC → 3,3 V, GND → GND, SCL → SCL,
  SDA → SDA (**etiketlere göre düz**, 4 Eki doğrulandı). Okuyan kartın kendi
  PS'i (EMIO I2C0, `/dev/i2c-0`) — bitstream yüklüyken.
- ⚠️ **Kablolar yalnız kart kapalıyken** değiştirilir (Linux kapatılır →
  anahtar OFF → adaptör çekilir). 4 Eki'de açıkken kablo değişince kart
  yeniden başladı.
- **INA219 yapılandırması `0x17FF`**: bara aralığı 16 V, PGA /4 (±160 mV →
  ±1,6 A), bara ve şönt ADC'si 12 bit **128 örnek ortalama**, sürekli kip.
  Yazılır ve **geri okunur**; ölçüm başında ve sonunda aynı olmalı.
- **Hesap ham yazmaçlardan**: I = V_şönt / **0,1 Ω** (nominal), P = V_bara × I.
  V_bara VIN−'dedir, yani **kartın girişi**; şöntte harcanan güç dahil değil.
  Çözünürlük 10 µV / 0,1 Ω = 0,1 mA → 12 V'ta ~1,2 mW.
- **Örnekleme**: ayrı bir süreçte **5 Hz** (0,2 sn), her örnek anında diske.
- ⚠️ **Öz-ölçüm**: örnekleyici ölçülen kartın ARM'ında koşar. Boş ve yük
  pencerelerinde aynı şekilde çalıştığı için kendi tüketimi farkta sadeleşir;
  yük penceresinde ARM'ı iş yüküyle paylaşır (en fazla koşum sayısında
  görülebilir). Beyan edilir, düzeltilmez.
- Ağ: Ethernet bağlı kalır (iki pencerede de aynı). Ölçüm `nohup` ile koşar;
  sırasında SSH'tan komut koşulmaz.

---

## 4. Kalibrasyon (T048) — enerji ölçümünden ÖNCE

**K1 (zorunlu) — bilinen direnç, kartın 5 V pininden** (⚠️ v1.1: **3,3 V** pininden ve direnç ağıyla — §11):
`5 V → VIN+ → VIN− → R → GND`. Bu sırada 12 V hattında INA219 **yoktur**
(kart adaptörden doğrudan beslenir).

1. R'yi kart **kapalıyken**, direncin kendi uçlarından multimetreyle ölç.
2. Devreyi kur, kartı aç; R'nin uçlarındaki gerilimi (**V**) multimetreyle
   oku (yük altında, paralel).
3. `calibrate_ina219` **30 sn** örnekler (ölçümle aynı örnekleyici ve
   yapılandırma). Bilinen yük = **V² / R**.

- Direnç **anma gücünün ≤ %25'inde** çalışmalı (ısınmayla direnç değişimi
  < %0,5): ör. 220 Ω / ≥ 0,5 W (5 V'ta 23 mA, 0,11 W) ya da 100 Ω / ≥ 1 W
  (50 mA, 0,25 W). Akım **≥ 20 mA** olmalı (INA219 ofseti ±10 µV = 0,1 mA →
  ≤ %0,5).
- Kalibrasyon noktası (5 V, 20–50 mA) ile ölçüm noktası (12 V, ~0,2–0,4 A)
  farklıdır — beyan edilir. INA219'un kazanç hatası aralık boyunca aynıdır;
  ofset yukarıdaki sınırla sınırlıdır.

**K2 (isteğe bağlı)**: multimetre seri akım kademesindeyse (≤ 200 mA)
bilinen = V × I.

**Kabul (SC-005)**: her kalibrasyonda **|sapma| < %5**. Gerilim ve akım
sapmaları ayrıca kaydedilir. Sapma ≥ %5 → **hiçbir enerji ölçümü yapılmaz**;
alet kararı kullanıcıya döner.

**Geçerlik**: kalibrasyon ile ölçüm arasında modül yeniden lehimlenmez,
yapılandırma değişmez; kalibrasyon kart saatine göre ölçümden **önce**dir
(FR-010; `measure_energy` bunu denetler).

---

## 5. Seriler — sıra SABİT

```
F2, P2, F2, P2      her biri: [ boş 170 sn ] -> [ yük 170 sn ]
```

| Seri | Taraf | İş yükü | Doğrulama |
|---|---|---|---|
| **F2** | PL (`fpga`) | `qir_kernel`, p=2, **TAM çağrı** (kodla + 1.095 yazma + koş + oku) — gecikme protokolünün `seri_kos`'u, ısınma 3 | her koşum C-sim bit deseniyle (`3204875187` — gecikme serisi A p=2 ile aynı) bit bit; zaman aşımı yok |
| **P2** | PS (`ps`) | aynı algoritma ARM'da: `bench_float_arm --saniye 170 --isinma 3` | `beklenen_deger` = −3950,990722656 |

- **Boş**: bitstream yüklü, çekirdek boşta, ARM'da yalnız Linux ve örnekleyici.
- **N** = yük penceresinde tamamlanan koşum, **ısınma dahil** (dizüstüyle
  aynı kural).
- ARM ikilisi **kartta** derlenir:
  `g++ -std=c++17 -O3 -DQIR_NO_VITIS -DQIR_N_QUBITS=16 -DQIR_REAL_FLOAT`
  (21 Eyl ARM tabanıyla aynı), sha256 kaydedilir.
- Her seri iki kez (ABAB): tekrarlanabilirlik ve sıra etkisi görünür.
- Toplam ~23 dk.

---

## 6. Hesap ve raporlama

- P̄ = pencere **içindeki** örneklerin ortalaması (pencere sınırları iş
  yükünün gerçek başlangıç/bitişi; başlangıç yükü yanlılığı yok).
- **E/koşum = (P̄_yük − P̄_boş) × t_yük / N** (data-model §3).
- Ortalamanın standart hatası **gösterge**dir (ardışık örnekler ilintili).
- Raporlanır: her seri ve iki tekrarın ortalaması; **P̄_boş mutlak** (kartın
  zarfı); ΔP; N; E/koşum; **E(P2) / E(F2)** (PS↔PL enerji oranı — aynı kart,
  aynı alet, aynı yöntem); F2 sırasındaki `T_cekirdek` medyanı (REG
  beslemesinde gecikme, USB'deki 36,578 ms ile).
- Dizüstüyle kıyas: **aynı yöntem** (delta), farklı alet (FR-009c izin
  verir), farklı kapsam (tüm kart ↔ tüm dizüstü) — kapsam farkı yazılır.
  Dizüstü GPU serileri güvenilmez işaretli olduğundan FPGA↔GPU enerji kıyası
  **bilgi** olarak kalır.
- Kalibrasyon sapması her enerji değerinin yanında yazılır.

---

## 7. Geçerlilik

| Durum | Karar |
|---|---|
| Kalibrasyon yok, geçmedi ya da ölçümden sonra | ölçüm **başlamaz** |
| F2'de bit sapması ya da zaman aşımı; P2'de `beklenen_deger` farklı | seri geçersiz, ölçüm **durur** |
| Pencerede örnek < beklenenin %90'ı | seri **geçersiz** |
| Doymuş şönt örneği ya da OVF | seri **geçersiz** |
| P̄_yük ≤ P̄_boş | seri **geçersiz** |
| INA219 yapılandırması başta ≠ sonda | ölçüm **geçersiz** |
| FCLK0 sonda %1'den fazla sapmış | ölçüm **geçersiz** |
| Zamana ya da güce bakarak örnek ayıklama | ⛔ **yapılmaz** |

---

## 8. Ön kayıtlı beklentiler (ölçümden ÖNCE)

| # | Beklenti | Gerekçe |
|---|---|---|
| B1 | Kartın boştaki toplam gücü (bitstream yüklü) **1,5–4,0 W** | PYNQ-Z2 sınıfı kart; "5 W zarfı" |
| B2 | F2'de ΔP **≤ 1,0 W** | PL çekirdeği küçük; ARM'ın tek çekirdeği yoklamada |
| B3 | F2 E/koşum **≤ 0,0217 J** (dizüstü CPU tek iş parçacığından az) | düşük güç, yavaşlığı telafi eder — **belirsiz** |
| B4 | E(P2) / E(F2) **≥ 1,5** | PL 2,30× hızlı; ek güç farkı bunu yiyemez |
| B5 | Kalibrasyon sapması **< %2** | modül ve multimetre ~%1 sınıfı |
| B6 | F2'de `T_cekirdek` medyanı **36,578 ms ± %0,5** | çevrim sayısı sabit; besleme düzeni değiştirmez |
| B7 | İki F2 tekrarının E/koşum'u birbirinin **%10**'u içinde; P2 için de | |

⛔ Tutmayan beklenti için ölçüt sonradan değiştirilmez; sonuç yazılır.

---

## 9. Çıktı

- `kalibrasyon_<tarih>_<git>_K<n>.json` (+ `.ornekler.csv`)
- `kart-enerji_<tarih>_<git>.json` (+ `.ornekler.csv`, `.log`) — seriler,
  pencere özetleri, `EnerjiOlcumu` alanları (`taraf`: `fpga` | `ps`, `alet`:
  `INA219-0.1ohm`, `kapsam`: `tum-kart`), kalibrasyon kayıtları, koşullar
- Kart dosyaları `scp` ile `docs/measurements/`'a alınır; tarih ve git
  damgası **konakta** verilir.

---

## 10. Kapsam dışı

p=1; FP64; PL rayının tek başına gücü (PYNQ-Z2'de raylar ayrı ölçülemiyor —
yalnız tüm kart); farklı FCLK; USB beslemede enerji.

---

## 11. v1.1 — kalibrasyondan önce (7 Eki) — 📝 onay bekliyor

**Neden**: elde yalnız 1/4 W dirençler var (200 Ω, 220 Ω, 1 kΩ — birer adet).
5 V'ta §4'ün iki kuralı (**≥ 20 mA** ve **her direnç anma gücünün ≤ %25'i**)
bu dirençlerin hiçbir birleşimiyle **birlikte** sağlanamıyor: 20 mA en az
0,1 W demek, tek bir 1/4 W direnç en fazla 62,5 mW alabilir; seri bağlamak
akımı 20 mA'nın altına düşürüyor, paralel bağlamak her direnci 5 V'a
bırakıyor.

| # | Değişiklik |
|---|---|
| Δ1 | K1'in gerilim kaynağı kartın **3,3 V** pini (5 V yerine) |
| Δ2 | Bilinen yük **birden fazla dirençten** kurulabilir; §4'ün kuralları **her dirence ayrı ayrı** uygulanır. Kurulan ağ: **200 Ω ∥ 220 Ω** (≈ 104,8 Ω) → 3,3 V'ta **31,5 mA**; 200 Ω 54 mW (%22), 220 Ω 50 mW (%20) |
| Δ3 | **R**, ağın iki ucundan, ağ kart tarafından **yalıtılmışken** ölçülür (kart kapalı, dönüş kablosu kartın GND'sinden çıkarılmış — aksi hâlde kartın kapalı 3,3 V devresi ağa paralel girer), multimetrenin **200 Ω** kademesinde; R = okuma − uçların kısa devre okuması |
| Δ4 | Kalibrasyon düzeninde VIN+, 3,3 V'u modülün **VCC sütunundan** bir köprü kabloyla alır (kartta tek 3,3 V soketi var); INA219'un kendi besleme akımı şöntten **geçmez** |

**Değişmeyen**: 30 sn ortalama, aynı örnekleyici ve yapılandırma, kabul
**|sapma| < %5**, B5 (< %2), ölçüm serileri (§5–§9).

**Ön kayıt beyanı**: v1.1 yazılırken INA219 yük altında **hiç okunmadı**.
Görülen tek değer, ağ devredeyken ölçülen "094" (kartın devresi paralel
girdiği için **geçersiz**, kullanılmaz). Kalibrasyon noktası artık 3,3 V /
31,5 mA (ölçüm noktası 12 V, ~0,2–0,4 A) — §4'teki aralık beyanı aynen
geçerli.
