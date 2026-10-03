# GPU Tabanı Enerji Ölçüm Protokolü (6B, T068)

| | |
|---|---|
| **Durum** | 🔒 v1.0 **DONDURULDU — 2026-10-03**, kullanıcı onayıyla, ilk enerji serisinden önce. ⛔ v1.0 ile yapılan tek koşu (3 Eki 13:59–14:22, git `d1e714b`) **GEÇERSİZ** — çalıştırıcı hatası, [hata #12](../hatalar-ve-duzeltmeler.md). 📝 **v1.1 taslağı onay bekliyor** (§9) |
| **Sürüm** | **v1.1 (taslak, 3 Eki)** — değişiklikler **§9**'da, ⚠️ **geçersiz koşudan, bazı gerçek değerler görüldükten sonra**. Enerji kayıtları `gpu-enerji-protokolu v1.1` taşır. v1.1 metni, §9'u ekleyen commit'te donar |
| **Onaylanan metin** | commit `38f85b3`, git içerik özeti `b04397ba79caf4c5d0c620f365bd8cc769189e30` (`git rev-parse 38f85b3:docs/measurements/gpu-enerji-protokolu.md`). Dondurmadan sonra yalnız bu üç durum satırı ve §4'e eklenen **"Ekran kapanması / uyku"** satırı değişti (3 Eki ön denetiminde bulundu, **ölçümden önce**): `git diff 38f85b3 -- <bu dosya>` |
| **Görev** | T068 (bu belge + ölçüm), T069'un enerji sütunu |
| **Dayanak** | FR-009b/c/d, FR-011, FR-013, FR-014, SC-009 · [gpu-taban-olcum-protokolu v1.1](gpu-taban-olcum-protokolu.md) (gecikme; aynı iş yükleri) · [ADR 0010](../decisions/0010-gpu-tabani-iki-katman.md) · CPU yöntemi: [faz2-sentez §19](faz2-sentez.md) |

**Kural (FR-011, SC-009)**: ilk enerji serisinden **önce** onaylanıp dondurulur;
sonuca bakıp değiştirilemez, değişiklik yeni sürümdür.

---

## 1. Ne ölçülüyor

**Koşum başına iş enerjisi**, dizüstünün tamamı kapsamında: aynı iş yükü
bataryadan beslenirken boştaki ve yük altındaki gücün **farkı**, koşum
sayısına bölünür. Alet ve yöntem 19 Eyl CPU ölçümüyle (0,644 J/koşum)
**birebir aynı** (T068 kuralı); yalnız iş yükü değişir.

| Seri | İş yükü | Katman (ADR 0010) | Kıyaslanır |
|---|---|---|---|
| **E1** | Aer CPU, p=2, T=4 (`cpu_load_loop.py`) | 1 | E2 |
| **E2** | Aer GPU, p=2, T=4 (`cpu_load_loop.py --device GPU`) | 1 | E1 |
| **E3** | Aynı algoritma GPU FP32, p=2 (`gpu_ayni_algoritma.py`) | 2 | E4; ileride FPGA (öbek 6) |
| **E4** | Aynı algoritma CPU float, **tek iş parçacığı**, p=2 (`bench_kernel`) | 2 | E3; ileride FPGA |

Ölçülmeyen: p=1, FP64, FPGA/ARM (kart enerjisi öbek 6'da, INA219 ile).
⛔ 19 Eyl'in 0,644 J'si bu kıyasa **girmez** (Windows, Aer 0.17, rastgele
parametre, iş parçacığı sayısı kayıtsız); E1 onun bu ortamdaki yeniden ölçümüdür.

---

## 2. Önceden bilinenler — ön kayıt beyanı

| Bilinen | Değer | Kaynak |
|---|---:|---|
| CPU enerjisi, eski ortam | boşta 21,58 W, yük 34,80 W, **0,644 J/koşum** | [cpu-enerji-batarya](cpu-enerji-batarya_15931cc.json) |
| Bataryada kısma, eski ortam, CPU | verim **−%18**, süre +%22 | [faz2-sentez §19](faz2-sentez.md) |
| Prizde gecikme (T067): E1–E4 iş yükleri | 36,23 / 29,94 / 0,997 / 3,273 ms | [olculen-degerler §6.1](../olculen-degerler.md) |
| ⚠️ `nvidia-smi` GPU güç çekişi, prizde, T067 serileri sırasında | boşta ~6–9 W, katman 2 yükünde 10–18 W | T067 pencere okumaları (yan ürün) |
| Batarya | tam dolu **37,7 Wh**, 1 Eki %97; pilde güç modu "En iyi performans" | WMI, 1 Eki |

`nvidia-smi` değerleri **yalnız GPU kartı**dır ve farklı bir kapsamdır; §3'teki
E3 beklentisi bunlar **bilinerek** yazıldı.

---

## 3. Ön kayıtlı beklentiler (ölçümden ÖNCE)

| # | Beklenti | Gerekçe |
|---|---|---|
| N1 ⚠️ | E3 (GPU, aynı algoritma) **< 0,1 J/koşum** | ~1 ms × onlarca W; ⚠️ GPU gücü `nvidia-smi`'den kabaca bilinerek |
| N2 | E3, E1'den ve E2'den **≥ 10×** az | 30–36× hızlı; ek güç bunu tümüyle yiyemez |
| N3 | E2 / E1 (Aer GPU / Aer CPU) **0,5–2** arası | GPU 1,2× hızlı ama ek güç çekiyor — yön belirsiz |
| N4 | E3 < E4 — aynı algoritmada GPU, tek iş parçacıklı CPU'dan koşum başına **daha az** enerji harcar | 3,3× hızlı; bağımsız tahmin |
| N5 | Bataryada GPU verimi prizdekinin **%80'inden az** (E3 verimi < 0,8 × 436,7 koşum/sn) | Dizüstü dGPU pilde güç sınırına iner; bağımsız |
| N6 | Tüm pencerelerde iki enerji hesabı (A: gücün integrali, B: kapasite farkı) **≤ %10** ayrışır | Eski ölçümde %3,6 / %0,9 |

---

## 4. Deney koşulları — her seride kaydedilir

| Koşul | Değer / kural |
|---|---|
| Güç | **Fişten çıkık** (kaydedici prizde örnek görürse kayıt **geçersiz**, `battery_energy.py` reddeder) |
| Batarya | Başta **≥ %80** (yalnız başlangıç koşulu — ölçüm sırasında %80'in altına inmesi beklenir ve serbesttir); herhangi bir seri başında < %30 ise ölçüm durur. Tahmini tüketim 15–17 Wh (37,7 Wh'nin %40–45'i) → %97'den başlanırsa ~%52–57'de biter. Pil tasarrufu otomatik eşiği pilde **%0** (`ESBATTTHRESHOLD`, 1 Eki) — ölçüm sırasında kendiliğinden devreye girmez. Batarya seviyesi seriden seriye düştüğü için sıra etkisi (§5) raporda yazılır |
| Ekran | Harici monitör yok; parlaklık ölçümden önce **kullanıcı tarafından sabitlenir** ve değeri beyan edilir, ölçüm boyunca **değiştirilmez**. (WMI bu dizüstünde parlaklığı `0` döndürüyor — okunamıyor; kayıtta `0` görünür, beyan edilen değer rapora yazılır.) |
| Güç modu | Pilde "En iyi performans" (`ActiveOverlayDcPowerScheme`), kaydedilir |
| Ekran kapanması / uyku | ⚠️ 3 Eki ön denetimi: bu güç planında pilde ekran **180 sn** sonra kapanır, makine **180 sn** sonra uyur — ölçüm 26 dk dokunulmadan sürdüğü için ilk serinin ortasında devreye girerdi. Çalıştırıcı ölçüm boyunca `SetThreadExecutionState` (ES_CONTINUOUS \| ES_SYSTEM_REQUIRED \| ES_DISPLAY_REQUIRED) ile ikisini de engeller; **kalıcı ayar değişmez**, istek onu tutan süreç bitince kalkar. Boş ve yük pencerelerinde aynı durum → farkta sadeleşir. Her serinin koşullarına `ekran_uyku_engeli` yazılır. (Aynı denetimde pil tasarrufu eşiği pilde yine **%0**, ekran koruyucu yok, tek monitör.) |
| Makine | Vivado/Vitis/noVNC kapalı; klavye/fare kullanılmaz; ağ ve Bluetooth durumu değiştirilmez |
| Ortam | WSL, `/root/qir-gpu-venv` (gecikme protokolüyle aynı), Aer T=4. **v1.1**: WSL sanal makinesi ölçüm boyunca (boş pencereler dahil) **açık tutulur** (§9 Δ2), koşullara `wsl_acik` yazılır |
| Git | Kod commit'lenmiş (`_kod_kirli` kuralı) |

---

## 5. Yöntem — her seri için bir çift

```
[ boş: 180 sn kayıt, iş yükü YOK ] -> [ yük: 180 sn kayıt, iş yükü kayıtla birlikte başlar ]
```

- Kaydedici: `scripts/battery_logger.ps1` — saniyede bir `DischargeRate` (mW)
  ve `RemainingCapacity` (mWh). **Değişmez.**
- **Boş pencere her serinin hemen önünde yeniden alınır** (T068 kuralı: GPU
  boşta da güç çeker; önceki serinin ısısı da sadeleşsin). Ayrıca soğuma işlevi
  görür; seriler arası ek bekleme yok.
- İş yükü döngüsü **170 sn** (Python başlangıcı, derleme ve doğrulama koşumuyla
  birlikte 180 sn'lik kayda sığsın diye); E4 **175 sn** (başlangıç yükü yok).
- **Hesap** (`scripts/battery_energy.py`, 19 Eyl ile aynı):
  `koşum başına J = (P̄_yük − P̄_boş) × t_yük_kaydı / N`,
  N = iş yükünün zamanlanmış koşum sayısı (ısınma dahil, doğrulama hariç).
- ⚠️ **Bilinen yanlılık**: kayıt penceresi başlangıç yükünü (içe aktarma,
  derleme, doğrulama) ve döngü bittikten sonraki birkaç saniyeyi de içerir →
  koşum başına enerji **hafifçe fazla** çıkar. Yöntem eski ölçümle aynı kalsın
  diye düzeltilmez; yazılır.
- Sıra **sabit**: E1, E2, E3, E4 (batarya boşaldıkça gerilim düşer; sıra
  etkisi tekdüze olsun diye değiştirilmez, yazılır).

---

## 6. Geçerlilik

| Durum | Karar |
|---|---|
| Kaydedici prizde örnek gördü | seri **geçersiz**, baştan |
| A/B sapması > %10 (bir pencere) | seri **güvenilmez**; raporlanır ama kıyasa girmez |
| P̄_yük ≤ P̄_boş | seri **geçersiz** |
| İş yükü doğrulaması kaldı (E1–E3: fidelity kapısı / sonda bit bit; E4: `beklenen_deger` = −3950,989990234) | seri **geçersiz** |
| Makine çöktü (GK-01) | seri geçersiz, kısmi kayıt saklanır, baştan |
| Zamana ya da güce bakarak örnek ayıklama | ⛔ **yapılmaz** |

---

## 7. Karşılaştırma ve raporlama

- Her seri: P̄_boş, P̄_yük, ΔP, N, **J/koşum**, A/B sapmaları, **bataryadaki
  verim** ve prizdeki (T067) verime oranı — **çalışma noktası farkı
  düzeltilmez**, yazılır (19 Eyl kuralı).
- Katman 1: E2/E1. Katman 2: E3/E4. ⛔ Katmanlar arası oran kurulmaz.
- ⛔ Kart (FPGA/ARM) ile kıyas bu protokolde **yok** — kart tarafı öbek 6'da
  farklı aletle (INA219) ölçülecek; T069'da iki taraf dolunca, kapsam farkı
  (dizüstünün tamamı ↔ kartın tamamı) yazılarak kurulur.
- `nvidia-smi` güç okumaları (her 10 sn) ikincil, **yalnız GPU** kapsamlı bilgi
  olarak eklenir; manşet değer değildir.

---

## 8. Çıktı

- `docs/measurements/batarya-{bos,yuk}_<tarih>_<git-hash>_E<n>.csv` — ham kayıt
- `docs/measurements/enerji-batarya_<tarih>_<git-hash>_E<n>.json` — hesap
- iş yükü kayıtları gecikme protokolünün adlandırmasıyla (`...enerjiE<n>...`)
- Seri başına koşullar: `docs/measurements/enerji-kosullar_<tarih>_<git-hash>.json`
  (batarya mWh/%, şebeke durumu, pildeki güç modu, zaman)
- Çalıştırıcı: `scripts/enerji_serileri.ps1` (Windows; kaydedici Windows'ta,
  iş yükü WSL'de). `-Deneme` kipi yalnız akışı sınar: kaydedici yerine sahte
  veri, kısa süreler, çıktı repo dışına — **ölçüm değildir**.

---

## 9. v1.1 — geçersiz ilk koşudan sonra (3 Eki) — 📝 onay bekliyor

### 9.1 Ne oldu

v1.0 ile 3 Eki 13:59–14:22'de (git `d1e714b`, fişten çıkık, parlaklık %0
beyan edildi) koşuldu. **Koşunun tamamı geçersiz**:

- **E1–E3'ün yük pencereleri sahte kaydediciden geldi.** `-ArgumentList …,
  [bool]$Deneme` PowerShell'in argüman kipinde bool değil **`'[bool]False'`
  metni** olarak geçti; boş olmayan metin "doğru" sayıldı ve yük penceresinde
  `-Deneme`'nin sabit 30.000 mW'lık sahte verisi yazıldı. Fark edilme biçimi:
  üç serinin yük gücü **birebir** 30.000,0 mW. `-Deneme` sınaması bunu
  yakalayamazdı (orada sahte veri zaten beklenen davranış). [Hata #12](../hatalar-ve-duzeltmeler.md).
- **E4 başlamadı**: başta `/tmp`'ye derlenen `bench_kernel` kayboldu. WSL
  sanal makinesi ~1 dk boşta kalınca kapanıyor, açılışta `/tmp` temizleniyor.
- Aynı nedenle **boş pencerelerde WSL kapalıydı**, her yük penceresinin
  başında yeniden açılıyordu → açılış enerjisi yük tarafına yazılıyordu
  (sahte veri olmasaydı da bir yanlılık olurdu).

Koşunun dosyaları repoya **girmedi** (kanıt olarak repo dışında saklandı).

### 9.2 Değişiklikler

| # | Değişiklik | Tür |
|---|---|---|
| Δ1 | Kip bayrağı gerçek bool (`$Deneme.IsPresent`); iş tipini denetler ve kipini bildirir (`KIP:GERCEK`/`KIP:SAHTE`); ana betik her yük penceresinden sonra beklenen kiple karşılaştırır, uyuşmazsa seri **geçersiz** | çalıştırıcı hatası |
| Δ2 | WSL sanal makinesi ölçüm boyunca **açık** tutulur (boş pencereler dahil) → boş ve yük pencerelerinde aynı durum; koşullara `wsl_acik` | **ölçüm koşulu** (§4 Ortam satırı) |
| Δ3 | `bench_kernel` ikilisi `/root`'a derlenir (`/tmp` değil) | çalıştırıcı hatası |

Yöntem (§5), seriler (§1), geçerlilik (§6) ve **beklentiler (§3) değişmedi**.

### 9.3 Ön kayıt beyanı — geçersiz koşuda görülen GERÇEK değerler

| Görülen | Değer | Etkisi |
|---|---|---|
| Boş pencere ortalama gücü (gerçek kaydedici, **WSL kapalı**) | E1 21,73 · E2 22,46 · E3 18,15 · E4 17,92 W | v1.1'de WSL açık olacağı için boş güç bundan farklı çıkabilir |
| İş yükü verimi, **pilde** (iş yükü kayıtları gerçek) | E1 31,84 koşum/sn (medyan 27,04 ms) · E2 34,81 (25,81 ms) · E3 **1519,2** (0,5325 ms) | T067'de prizde: 25,55 · 29,28 · **436,7** koşum/sn. Pilde **daha yüksek**; nedeni bilinmiyor, yorumlanmadı |
| Yük gücü, enerji/koşum | **görülmedi** (sahte veriydi) | N1–N4 ve N6 **kör** kalır |

⚠️ **N5 artık kör değil**: E3'ün pildeki verimi görüldü (1519 koşum/sn, N5
eşiği 0,8 × 436,7 = 349). N5 olduğu gibi kalır ve değerlendirilir, ama raporda
**"sonuç görüldükten sonra"** işaretiyle yazılır; doğrulayıcı kanıt sayılmaz.
