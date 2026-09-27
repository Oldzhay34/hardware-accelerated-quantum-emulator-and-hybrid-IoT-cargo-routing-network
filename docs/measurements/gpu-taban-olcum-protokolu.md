# GPU Tabanı Gecikme Ölçüm Protokolü (6B, T067)

| | |
|---|---|
| **Durum** | 📝 **TASLAK — onay bekliyor.** Onaylanmadan ve dondurulmadan hiçbir GPU/Aer gecikme serisi koşulmaz |
| **Sürüm** | v1.0 (taslak) — ölçüm kodu her çıktıya `gpu-taban-protokolu v1.0` yazar |
| **Onaylanan metin** | — (dondurulunca commit ve git içerik özeti buraya) |
| **Görev** | T067 (bu belge + ölçüm), T065b'nin ölçüm kısmı, T069'un gecikme sütunu |
| **Dayanak** | FR-011, FR-012, FR-013, FR-014, SC-004, SC-009 · [ADR 0010](../decisions/0010-gpu-tabani-iki-katman.md) · [kart-olcum-protokolu v1.0](kart-olcum-protokolu.md) (istatistik ölçütleri buradan **aynen** alınır) |

**Kural (FR-011, SC-009)**: Bu protokol ilk GPU/Aer gecikme serisinden
**önce** onaylanıp dondurulur. Sonuca bakıp değiştirilemez; değişiklik yeni
sürümdür (§10).

---

## 1. Ne ölçülüyor — iki katman (ADR 0010)

| Katman | Soru | Kıyaslanır | ⛔ Kıyaslanmaz |
|---|---|---|---|
| **1 — Aer** | Hazır bir simülatörde (Qiskit Aer) GPU, CPU'dan ne kadar hızlı? | Aer-CPU ↔ Aer-GPU, **aynı ortam**, yalnız cihaz değişir | FPGA (Aer QAOA'yı ayrıştırıyor, 12× algoritmik fark — [hatalar #5](../hatalar-ve-duzeltmeler.md)); Windows'taki eski Aer rakamları |
| **2 — Aynı algoritma** (T065b) | Çekirdeğin **kendi algoritması** GPU'da ne kadar sürer? | FPGA `T_cekirdek` (36,578 / 20,385 ms), dizüstü CPU `bench_kernel` float (3,273 ms), ARM (84,13 ms) | Aer rakamları |

Ölçülmeyen: enerji (T068, ayrı ek), GPU'nun başka problem boyutları.

---

## 2. Önceden bilinenler — ön kayıt beyanı

Protokol aşağıdakiler **bilinerek** yazıldı. Hiçbiri protokollü seri değildir
ve hiçbiri sonuç olarak yazılmaz; önyargı kaynağı olabilecekleri için beyan
edilir.

| Bilinen | Değer | Kaynak |
|---|---:|---|
| ⚠️ Duman testi, Aer **CPU**, p=2, 12 sn, **rastgele** parametreler, 6 iş parçacığı | medyan **36,48 ms** (min 27,05, maks 51,34) | T065 duman testi, 27 Eyl (dosyası silindi, ölçüm değil) |
| ⚠️ Duman testi, Aer **GPU**, aynı koşullar | medyan **26,63 ms**; ilk 2 sn 24,71 → son dilim 32,83 ms | aynı |
| Aer CPU, **Windows** (Qiskit 2.5.2 / Aer 0.17.2, rastgele parametreler; iş parçacığı sayısı **kaydedilmedi** — Aer varsayılanı tüm mantıksal çekirdekler) | turbo 32,75 ms, plato 41,93 ms | [cpu-yuk-dongu prizde-temiz](cpu-yuk-dongu_20260919_prizde-temiz_p2.json) |
| Aer doğruluğu, bu ortam, iki cihaz, p=1/2 | fidelity 1 (1−F < 10⁻¹⁵) | T066, [aer-dogrulama](aer-dogrulama_20260927_f9a8ace_GPU_p2.json) |
| Dizüstü CPU, aynı algoritma (`bench_kernel`), float, p=2, tek iş parçacığı | **3,273 ms** medyan (n=10, IQR 0,19); fidelity 0,999999897 | [adil-cpu-tabani](adil-cpu-tabani_20260921_c504294.json) |
| FPGA `T_cekirdek` (kart, protokol v1.0) | p=2 **36,578 ms**, p=1 **20,385 ms** | [kart-gecikme p2](kart-gecikme_20260927_201475a_n16_p2.json) |
| GPU | RTX 4060 Laptop, 8 GB, sürücü 616.92, güç sınırı 45 W; boşta **72–74 °C** (P8), ekranı da bu GPU sürüyor | `nvidia-smi`, 27 Eyl |

⚠️ İlk iki satır protokolden **önce** görüldü (T065 duman testi). §3'teki A1
ve A2 bu değerler **bilinerek** yazıldı ve bağımsız tahmin sayılmaz. Katman 2
hiç koşulmadı — G beklentilerinin hepsi **bağımsızdır**.

---

## 3. Ön kayıtlı beklentiler (ölçümden ÖNCE)

Tutmayan beklenti **bulgudur**, gizlenmez.

**Katman 1 — Aer**

| # | Beklenti | Gerekçe |
|---|---|---|
| A1 ⚠️ | p=2 medyan oranı CPU/GPU **1× ile 3× arası** | ⚠️ **Bilinerek** (duman 1,37×). n=16 küçük (1 MB); Aer'de kapı başına ek yük ve statevector'ün konağa kopyası baskın |
| A2 ⚠️ | GPU serisinde yavaşlama (ilk 50 koşum → son 60 sn) CPU'dakinden **büyük**; GPU platosu ±%0,5 ölçütüyle **oturmayabilir** | ⚠️ **Bilinerek** (duman: 12 sn'de 24,7 → 32,8 ms). Dizüstü GPU, boşta 72 °C |
| A3 | p=1/p=2 süre oranı GPU'da CPU'dakinden **büyük** | Bağımsız. GPU'nun sabit ek yükü (iş gönderme, kopya) kapı sayısıyla ölçeklenmez |
| A4 | Kuyruk (p99 / medyan) GPU'da CPU'dakinden **uzun** | Bağımsız. WSL/WDDM zamanlaması; GPU aynı anda ekranı sürüyor |
| A5 | Serinin son koşumunun statevector'ü ilk koşumunkiyle **bit bit aynı**, iki cihazda da | Bağımsız. Belirlenimcilik; ısınan GPU'da bozulma olmadığının kanıtı |

**Katman 2 — aynı algoritma (hiç koşulmadı, hepsi bağımsız)**

| # | Beklenti | Gerekçe |
|---|---|---|
| G1 | FP32, p=2 medyan **≤ 1 ms** → FPGA'dan **≥ 36×** hızlı | 65.536 genlik L2 önbelleğe sığar; iş, ~40 çekirdek başlatmasının gecikmesi |
| G2 | FP32, p=2, dizüstü CPU `bench_kernel` float'tan (3,273 ms) **hızlı** | aynı |
| G3 | FP64 / FP32 süre oranı **< 2** | Tüketici GPU'da FP64 verimi FP32'nin 1/64'ü; oran küçük çıkarsa süre hesap değil **başlatma** bağlıdır |
| G4 | FP32 fidelity ≥ 0,999 (H); FP64 fidelity FP32'den **belirgin iyi değil** | Faz sözcükleri (18 bit) ve trig tablosu (13 bit) çekirdekle aynı; taban oradan gelir (CPU float: 1 − 1,0·10⁻⁷) |

---

## 4. Deney koşulları — her seride kaydedilir

| Koşul | Değer / kural |
|---|---|
| Ortam | WSL2 Ubuntu 24.04, `/root/qir-gpu-venv`: Qiskit 1.4.6, Aer-GPU 0.15.1 (katman 2: + CuPy, sürümü kaydedilir). **İki cihaz aynı venv'de** |
| CPU iş parçacığı | ⚠️ **AÇIK KARAR K1** (§11). Hangisi olursa olsun `nproc` ve Aer'in kullandığı iş parçacığı sayısı kaydedilir |
| Aer ayarları | `method=statevector`, `precision=double`, füzyon **varsayılan (açık)**, `cuStateVec_enable` **varsayılan (kapalı)** — iki cihazda aynı; metadata'dan okunup kaydedilir |
| Devre | Altın referansın devresi (`reference_20260915_c6ad872_p{1,2}_n5`), optimize parametreler adıyla |
| Güç | **Prizde**, şarj adaptörü takılı. Windows güç modu seri başında okunup kaydedilir; seriler arasında **değiştirilmez** |
| Makine yükü | Vivado/Vitis/noVNC **kapalı**. Seri sırasında klavye/fare kullanılmaz. WSL `/proc/loadavg` seri öncesi ve sonrası |
| GPU durumu | Her 10 sn'lik pencere sınırında `nvidia-smi` ile sıcaklık, SM saati, güç çekişi (okunamazsa `N/A` yazılır) — zamanlanan bölgenin **dışında** |
| Git | Seri **temiz ağaçta** koşulur. `git_dirty: true` olan seri raporlanmaz |
| Sıra ve soğuma | §6'daki sıra sabittir; seriler arasında **≥ 5 dk boşta** bekleme; her serinin başında GPU sıcaklığı kaydedilir |

---

## 5. Kapsamlar

Zamanlayıcı: `time.perf_counter()` (WSL/Linux, ns çözünürlük).

| Katman | Kapsam | Başlar | Biter | İçerir |
|---|---|---|---|---|
| 1 | `T_kosum` | `sim.run(tqc)` çağrısından hemen önce | `.result()` döndüğünde | iş gönderme + simülasyon + (GPU'da) 1 MB statevector'ün konağa kopyası + Python ek yükü — **bir Aer kullanıcısının gördüğü süre**. `transpile` bir kez, seriden önce |
| 2 | `T_hesap` | ilk çekirdek başlatmasından hemen önce | tek float sonuç konakta (senkronizasyon sonrası) | statevector başlatma + p katman (fazların girdiden hesaplanması dahil) + beklenen değer indirgemesi. **`bench_kernel.cpp`'nin zamanladığı tek `qir_kernel(...)` çağrısının GPU karşılığı** ve FPGA `T_cekirdek`'inin karşılığı. Girdiler (`phases`, `cos_beta`, `sin_beta`, `cost`, `p`) önceden GPU belleğinde |

⛔ Katman 2'de **senkronizasyonsuz zamanlama yasak** — yalnız çekirdek
başlatmayı ölçer, hesabı değil.

---

## 6. Seriler

| Seri | Katman | Cihaz / varyant | p | Süre |
|---|---|---|---|---|
| A-CPU | 1 | Aer CPU | 2 | **300 sn** |
| A-GPU | 1 | Aer GPU | 2 | 300 sn |
| B-CPU | 1 | Aer CPU | 1 | 300 sn |
| B-GPU | 1 | Aer GPU | 1 | 300 sn |
| G32-2 | 2 | GPU FP32 | 2 | 300 sn |
| G64-2 | 2 | GPU FP64 | 2 | 300 sn |
| G32-1 | 2 | GPU FP32 | 1 | 300 sn |
| G64-1 | 2 | GPU FP64 | 1 | 300 sn |

Sıra tablodaki gibidir (katman 2, T065b doğrulandıktan sonra). **Süreye
göre** — kart protokolüyle aynı gerekçe (turbo penceresi tuzağı, [hatalar
#4](../hatalar-ve-duzeltmeler.md)); her seri ≥ 30 koşumu kendiliğinden aşar.

**Isınma**: seriden önceki **doğrulama koşumu** zamanlanmaz; ardından ilk
**3** zamanlanmış koşum istatistikten atılır (kart protokolü §6 ile aynı),
ham izde kalır.

**Doğruluk koşulu (Prensip IV)**:
- **Başta**: doğrulama koşumunun statevector'ü altın referansa karşı —
  fidelity < 0,999 ise seri **başlamaz** (T066 kapısı, `cpu_load_loop.py`).
- **Sonda**: son koşumun statevector'ü doğrulama koşumununkiyle **bit bit**
  karşılaştırılır; fark varsa seri **geçersiz**.
- Her koşumu doğrulamak yapılmaz: aynı döngü T068'de enerji ölçer ve koşum
  başına ek iş, koşum başına enerjiyi şişirirdi. Her koşumda yalnız
  metadata'daki `device` alanı denetlenir (zamanlanan bölgenin dışında).

---

## 7. Dışlama kuralları

| Durum | Karar |
|---|---|
| Doğrulama koşumu (başta) | zamanlanmaz — önceden sabit |
| İlk 3 zamanlanmış koşum | istatistikten atılır — önceden sabit |
| Başta fidelity < 0,999 | seri **başlamaz** |
| Sonda statevector ilk koşumdan farklı | **seri geçersiz** |
| Bir koşumda `device` istenen cihaz değil | **seri geçersiz** |
| `git_dirty: true` | seri raporlanmaz |
| Makine çöktü (GK-01) | seri **geçersiz**, yeniden başlatmadan sonra baştan koşulur; kısmi iz (`*.kismi.jsonl`) saklanır ve çökme [risk-register GK-01](../risk-register.md)'e zamanı ve seriyle yazılır — **kendisi bir veri noktasıdır** |
| Süresi uzun ya da kısa görünen koşum | ⛔ **ATILMAZ.** Zamana bakarak aykırı değer ayıklanmaz |

---

## 8. İstatistik — kart protokolü v1.0 §8 ile **aynı**

Ölçütler kopyalanmaz, **aynı kod çağrılır** (`agent/measure_latency.py`:
`pencereler`, `plato`; `OlcumSerisi` alanları):

- **medyan** ve **IQR** manşet; min, maks, p95, p99, jitter (maks − min)
- `kosum_sayisi < 10` → seri üretilmez (SC-004); tek koşum hiçbir yere yazılmaz
- 10 sn'lik pencereler (medyan + GPU sıcaklığı); **ilk 50 koşum** ve **son 60
  sn** ayrı raporlanır
- **Plato oturdu** ⇔ son 6 pencere medyanının hepsi, ortalamalarının
  **±%0,5**'i içinde. Oturmadıysa oturmadığı yazılır; **seri uzatılmaz**
- Süreklilik için eski alanlar da yazılır: `turbo_ms` (ilk 2 sn), `plato_ms`
  (son 60 sn) — 19 Eyl Windows serisiyle aynı tanım, ama o seriyle
  **kıyaslanmaz** (§9)

---

## 9. Karşılaştırma kuralları (T069)

- **Katman 1**: oran = medyan(CPU) / medyan(GPU), aynı p, IQR'larla birlikte;
  ayrıca son-60-sn medyanlarıyla. Yalnız şu nitelemeyle yazılır: *"Qiskit Aer
  içinde, n=16, bu dizüstünde"*. ⛔ FPGA'yla, ⛔ Windows Aer rakamlarıyla
  kıyaslanmaz.
- **Katman 2**: G32-2 medyanı ↔ FPGA `T_cekirdek` (36,578 ms) ve
  `bench_kernel` float (3,273 ms). Kapsam farkı yazılır: FPGA tarafı Python
  yoklamasıyla (`δ` ≈ 21,5 µs kötümser), `bench_kernel` C++ içinden, GPU
  tarafı senkronizasyonlu `perf_counter`. FP64 yalnız G3 ve G4 için.
- ⛔ *"GPU FPGA'dan X× hızlı"* cümlesi yalnız katman 2'den ve **tabanıyla**
  kurulur. FPGA'nın savunması hız değil **dağıtım zarfıdır**
  ([neden-fpga.md](../neden-fpga.md)).
- Sonuç ne çıkarsa çıksın raporlanır (6B ilkesi).

---

## 10. Çıktı ve sürüm

- Katman 1: `docs/measurements/{cpu,gpu}-yuk-dongu_<tarih>_<git-hash>_<etiket>_p{1,2}.json`
  (`scripts/cpu_load_loop.py`) — §8'in hepsi, ham iz, §4 koşulları,
  `dogrulama` (başta) ve `son_kosum_ayni` (sonda), `protokol_surumu`
- Katman 2: `docs/measurements/gpu-ayni-algoritma_<tarih>_<git-hash>_fp{32,64}_p{1,2}.json`
  (T065b betiği), aynı alanlar
- **Dondurma**: onaydan sonra üst tablo `Durum: 🔒 DONDURULDU`, tarih ve
  dondurma commit'iyle güncellenir; ölçüm kodu sürüm dizesini her çıktıya yazar
- **Değişiklik**: yeni sürüm (v1.1 …), gerekçesi ve *"sonuç görüldükten sonra
  mı"* sorusunun cevabı yazılır

---

## 11. Dondurmadan önce kapanacak açık kararlar

| # | Karar | Seçenekler | Öneri |
|---|---|---|---|
| **K1** | WSL'in gördüğü işlemci sayısı | (a) `.wslconfig`'te `processors=16` — ölçüm süresince, `wsl --shutdown` gerekir; bellek 8 GB kalır. (b) 6'da bırak, raporda yaz | **(a)**: ana makinede 16 mantıksal işlemci var, WSL 6 görüyor (16 Eyl'de Vitis bellek sorunu yüzünden sınırlandı). Aer CPU 6 iş parçacığıyla koşarsa CPU/GPU oranı **GPU lehine şişer** — ölçülen şey cihaz değil yapılandırma farkı olur. Katman 2'yi etkilemez |
