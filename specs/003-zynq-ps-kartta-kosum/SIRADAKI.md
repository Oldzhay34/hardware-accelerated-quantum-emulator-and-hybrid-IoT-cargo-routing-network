# Faz 5 — SIRADAKİ

## SIRADAKİ

> # ✅ MVP KARTTA GEÇTİ — 2026-09-27
>
> **Öbek 4 (T026–T038) bitti.** *"16 kübitlik statevector emülatörü FPGA'da
> çalışıyor ve altın referansa karşı doğrulandı"* cümlesi artık **ölçülmüş**:
> p=2 ve p=1 için 20/20 izdüşüm C-sim ile **bit bit** aynı; belirlenimcilik,
> durumsuzluk (yeniden başlatma) ve p=0/p=4 sınırı geçti. Kayıt:
> [kart-dogrulama p2](../../docs/measurements/kart-dogrulama_20260927_67165a7_n16_p2.json),
> [p1](../../docs/measurements/kart-dogrulama_20260927_67165a7_n16_p1.json).
>
> 21 Eyl'deki kapsam dondurmasının koşulu (öbek 4 bitene kadar) **sağlandı**;
> 6B/6C/6D kilitleri resmen kalktı. Önerilen sıra yine de öbek 5 → 6 → 7:
> 2,26×'in FPGA tarafı hâlâ **tahmin** ve onu T044 kapatır.

**Kart işi (4 Eki, bu fazda)**: öbek 6 — kart enerjisi. ✅ INA219 konuşuyor (VCC lehimi açıktı, düzeltildi; SCL/SDA düz). 📝 [kart-enerji-protokolu](../../docs/measurements/kart-enerji-protokolu.md) taslağı + `agent/ina219.py`, `calibrate_ina219.py`, `measure_energy.py` hazır, **onay bekliyor**. Sıra: onay → **T048 kalibrasyon** (5 V pini + bilinen direnç; adaptör gerekmez — kullanıcıda uygun direnç var mı?) → **T046** (DC jak klemens adaptörleri **yok**, temin) → T049–T050. Kart JP5 = REG, adaptörle. ⚠️ Kablo değişikliği yalnız kart kapalıyken.

**Hedef (tek cümle)**: 6B **T069** — kıyas matrisi (T051–T055 betiği + GPU sütunu). Kartsız yazılabilir; FPGA enerji hücresi `null` + not (T053). ⚠️ **Önce karar**: iş yükleri **pilde prizdekinden hızlı** ölçüldü (GPU aynı algoritma 0,555 vs 0,997 ms) — §6.1'in 36,7×'i prizdeki T067'ye dayanıyor. Matrise girmeden önce prizde, soğuk GPU'yla kısa bir kontrol ölçümü önerilir (ön kayıtlı protokol gerekir).
⚠️ `.wslconfig` `processors=16` hâlâ açık — kontrol ölçümü yapılacaksa aynı ortamda kalmalı; sonra 6'ya geri alınabilir.

**3 Eki kapananlar**: ✅ **T068** enerji (v1.1; E1 0,243 / E4 0,0217 J geçerli, E2/E3 güvenilmez — [olculen-degerler §6.2](../../docs/olculen-degerler.md)); ✅ **6D** (T074–T077; ölçekleme P_opt'u 121× artırıyor, p=1 sabit açı tek çağrı — [§5.2](../../docs/olculen-degerler.md)). Hata kaydı **#12** (enerji çalıştırıcısında sahte kaydedici) ve **#13** (referans QAOA kalitesi ölçekleme ürünü).

**Dokunulacak dosyalar**: `scripts/cpu_load_loop.py` (doğrulama),
`services/reference/` (referansın nasıl üretildiği), T065b için yeni GPU
çekirdek betiği. Ortam: `/root/qir-gpu-venv` (repo dışı), runbook
[gpu-aer-wsl.md](../../docs/runbooks/gpu-aer-wsl.md).

**Bilinen tuzak**: `qiskit-aer-gpu` en fazla **0.15.1** → Qiskit **1.x**;
Windows `.venv` 2.5.2/0.17.2 → CPU tarafı da WSL venv'inde yeniden ölçülür.
Aer katmanı FPGA'yla **kıyaslanmaz** (585 kapı → transpile sonrası 336 CX +
168 RZ; hata #5). Ölçüm **temiz ağaçta**. GK-01: iz pencere başına diske.
⛔ GPU sonucu ne çıkarsa çıksın raporlanır.

**Tez cümlesi güncellendi** (27 Eyl, kullanıcı onayı): *"18-bit hassasiyet
noktası"* → *"ölçülmüş genişlik–doğruluk–alan eğrisi"* (CLAUDE.md).

## ✅ 6C KAPANDI (27 Eyl) — genişlik taraması

Figür: [genislik-pareto_20260927_dfe3eff.svg](../../docs/figures/genislik-pareto_20260927_dfe3eff.svg)
(`scripts/genislik_figur.py`, bağımlılıksız SVG, JSON'dan). Anlatı:
[neden-fpga.md §2.2b](../../docs/neden-fpga.md) yeniden yazıldı — **dirsek
yok**, genişlik bedeli ölçülmüş sürekli bir eksen (bit başına ~8–9 BRAM, sıfır
ek çevrim), 18 bir seçim; jüriye "neden 16 değil 18" cevabı orada.
Pareto'yu yeniden üretmek gerekirse C-sim dökümleri repoda değil: önce
`wsl -d Ubuntu -e bash hls/genislik_tarama.sh` (→ `hls/build/genislik`),
sonra `scripts\genislik_pareto.py hls\build\genislik`, sonra
`scripts\genislik_figur.py docs\measurements\genislik-pareto_<damga>.json`.

| Görev | Durum |
|---|---|
| **T070** `QIR_REAL_BITS` parametresi | ✅ varsayılan 18'de 4 döküm **bit bit aynı**, CI kapısı 4/4, trig tablosu 8192/8192 ham bit aynı |
| **T071** C-sim fidelity 14/16/18/20/24 | ✅ ön kayıtlı K1–K4 geçti; her 2 bit ~16× (kuramsal), 20→24'te ~1e-7 tabanı |
| **T072** csynth | ✅ beş genişlik. 18'in tarama koşusu asıl raporla **AYNI**. W=14 ilk koşuda sessizce boş döndü (aşağıda), tek başına yeniden koşunca normal |
| **T073** figür + §2.2b | ✅ figür (a: BRAM×(1−F), b: BRAM×W ile Faz 2 hesabı yan yana), §2.2b + §0 tablosu + mimari-gerekçe özeti yeniden yazıldı |
| **Ek** uygulama düzeyi | ✅ "fazla bit daha iyi olmaz mı" ölçüldü: 18 bitte optimum rota olasılığı −%0,96, 24 turun sırasında 1 takas (20 bitte yok); en olası tur 14–24 hepsinde aynı; p'nin etkisi ~180× büyük; 24 bit 20'ye göre bir şey katmıyor → 18'de kalındı. [genislik-uygulama](../../docs/measurements/genislik-uygulama_20260927_3df6a60.json), neden-fpga §2.2b jüri tablosu (kanıt düzeyleriyle) |

| W | BRAM_18K | DSP | LUT (HLS) | p=2 çevrim | Fidelity p=2 | Model |
|---|---:|---:|---:|---:|---:|---:|
| 14 | **152** | 36 | 44.472 | 3.728.217 | 0,994508 ❌H | 0,978861 |
| 16 | **169** | 36 | 44.800 | 3.728.217 | **0,999656** ✅H | 0,998674 |
| 18 | **187** | 36 | 45.131 | 3.728.217 | 0,999978 | 0,999917 |
| 20 | **204** | 30 | 45.917 | 3.728.218 | 0,9999985 | 0,999995 |
| 24 | **238** | 33 | 47.260 | 3.728.219 | 0,9999999 | 0,99999998 |

Kayıt: [genislik-pareto_20260927_dfe3eff](../../docs/measurements/genislik-pareto_20260927_dfe3eff.json)
(beş satır + `BRAM_statevector`; eski `_29b253c` W=14'süz, `_924216e`
statevector alanısız — tarihsel). Betikler:
`hls/genislik_tarama.sh` (C-sim), `hls/genislik_sentez.sh` (csynth, asıl
projeye dokunmaz → `qir_hls_prj_W<n>`), `scripts/genislik_pareto.py`
(toplama). Statevector BRAM'i tam **8W** (112/128/144/160/192), geri kalanı
40–46 blok.

⚠️ **W=14 ilk koşusu**: `vitis-run` hiçbir şey yazmadan 0 döndü, proje
dizini oluşmadı, döngü "TAMAM" dedi (tarama döngüsünün ilk koşusuydu).
27 Eyl 23:09'da tek başına yeniden koşunca 74 sn'de normal bitti; **neden
bulunamadı**. `genislik_sentez.sh` artık başarıyı **rapor varlığıyla**
ölçüyor, çıkış koduyla değil.

### ⛔ Çöken anlatı — tezde düzeltilmeli

Belgelerdeki *"18 bit iki bağımsız kısıtın tam kesişimi"* iddiasının **iki
yarısı da ölçümle düştü**:
1. **Doğruluk**: "H'yi geçen en dar format Q1.17, Q1.15 kalır" — bu
   `format_fidelity.py` **modelinden** geliyordu (her kapıdan sonra yuvarlar,
   hatayı ~3,8× fazla tahmin eder). Gerçek çekirdekte **Q1.15 = 0,999656,
   GEÇİYOR**.
2. **Donanım**: "19+ bit BRAM36 kelimesini aşar, BRAM ikiye katlanır" —
   **katlanmıyor**: BRAM bit başına ~9 blok **düzgün** artıyor (169 → 187 →
   204 → 238). 16 bit 18'den **18 blok az**. DSP'de de 18 üstünde sıçrama yok
   (DSP48 18-bit B portu argümanı da tutmadı). **Kök neden** (rapordaki
   Memory tablosu): HLS statevector'ü re/im **ayrı**, 4 bellek × 32.768
   kelime × W bit kuruyor → tam **8W** blok (128/144/160/192); 36-bit
   kelimeye paketleme hiç yok. Yan bulgu (doğrulanmadı): parite bitleri
   kullanılmıyor, 18 bitte 1K×18 düzeni 128 blok verebilirdi.

Eski iddia ⛔ ile işaretlendi: `neden-fpga.md` (§0 tablo + §2.2b),
`mimari-gerekce.md` (2 yer), `banking-research.md` §4, `memory-budget.md`,
`hizlandirici-kiyas-gunlugu.md`. Hata kaydı **#10**, olculen-degerler §2.2 +
§7 + §8 #5–6. ⚠️ Hâlâ eski iddiayı taşıyan (dokunulmadı, tarihsel):
`specs/002-…/quickstart.md:46`, `specs/003-…/tasks.md:288` bağlam paragrafı.

**Geriye kalan, savunulabilir FPGA'ya özgü katkı**: genişlik, ölçülmüş bir
maliyet/doğruluk eğrisi olan **serbest bir tasarım parametresi** — GPU'da
menü sabit (fp16/bf16/fp32). Eğride "dirsek" yok; 18 bir **seçim**,
zorunluluk değil. 16 bit, H'yi ~3× paya geçip BRAM'de %10 tasarruf ederdi.
CLAUDE.md tez cümlesi buna göre değiştirildi (27 Eyl, kullanıcı onayı).

## Bu oturumda (27 Eyl) yapılanlar — özet

- **Öbek 4 (MVP) kartta**: T032–T038 ✅ — 20/20 izdüşüm p=1/p=2 bit bit;
  FCLK 62,5 MHz hatası bulundu (kristal 33,333 vs 50 MHz), `board.py` düzeltildi
- **Öbek 5 (gecikme)**: protokol v1.0 dondu (onaylı metin `201475a`), p=2
  **36,578 ms**, p=1 **20,385 ms**, PS↔PL **2,30×**; T045 → HLS en kötü
  durum, RTL simülasyonu 36,5464 ms
- **INA219 (T047)**: I2C tarafı bağlandı (VCC→3.3V ölçüldü 3,32 V, SCL/SDA →
  Arduino başlığının sol ucu), `0x40` cevap verdi, yapılandırma `0x399F`.
  ⚠️ Başlık **lehimsiz** — temas aralıklı. VIN+/VIN− boş
- **Hata kaydı**: `docs/hatalar-ve-duzeltmeler.md` (rapor için, 10 kayıt)
- **Form 4203T**: dolduruldu, başlık "Hardware-Accelerated …" + özet
  "2.30× faster than the on-chip ARM core" (masaüstü `… - dolu.pdf`).
  ⚠️ Kullanıcının 17:34'teki sürümünün üzerine yazıldı — ne eklediği sorulacak
- **Vivado/Vitis GUI**: WSLg bozuk (WSL 2.7.3) → tarayıcıda noVNC
  (`xilinx-web vivado|vitis`, localhost:6080/6081); Vitis IDE için
  `libasound2t64` kuruldu. Ayrıntı: kullanıcı hafızası

## Kullanıcının yapacakları

1. **INA219'u lehimlet** (6'lı başlık + yeşil klemens) — bölüm lab / tamirci
2. **Vidalı klemensli DC jak adaptörü** (dişi + erkek) — almadan önce kart
   girişi ve adaptör fişi ölçüsü birlikte kontrol edilecek
3. **Form 4203T**: tarih/imza; 17:34 sürümünde bir şey eklediyse söylemek.
   Son teslim **02.10.2026**
4. ~~**Tez cümlesi kararı**~~ — ✅ verildi: "ölçülmüş genişlik–doğruluk–alan
   eğrisi"

## Öbek 6 için hatırlatma

Öbek 6 besleme düzenini **değiştirir** (JP5 → REG, adaptör INA219'un
içinden). Gecikme USB düzeninde ölçüldü; enerji serisinin düzeni ayrı
kaydedilmeli. İlk iş kalibrasyon (T048, sapma < %5) — geçmeden hiçbir enerji
rakamı sayılmaz.

**Öbek 5 sonucu (27 Eyl)**: ✅ protokol v1.0 donduruldu · ✅ p=2 **36,578 ms**,
p=1 **20,385 ms** (IQR ~15 µs, plato var, 16.159 koşum, hepsi C-sim ile bit
bit) · ✅ PS↔PL **2,30×** (iki taraf ölçüm) · ✅ T045: HLS modeli **en kötü
durum** (üçgen döngüler); **RTL simülasyonu 36,5464 ms**, kart 31 µs üstünde →
kart RTL'i koşuyor. ⬜ Döngü döngü dağılım kapanmadı (manşeti değiştirmez).
Ön kayıtlı **B7 tutmadı**. Kayıt: [olculen-degerler §5.1](../../docs/olculen-degerler.md).

**Son güncelleme**: 2026-10-03, Faz 5 (T068 ve 6D kapandı; sıradaki kartsız iş T069, önce prizde/pilde kontrol ölçümü kararı)

---

## KAPANAN İŞ ✅ n=16 cosim

**19 Eylül 21:13'te GEÇTİ.** Çekirdeğin tek çıkış portu `beklenen_deger`,
C modeliyle bit bit aynı: `0xbee28271` (= −0,442401439). `AESL_mErrNo` yok,
rc=0/rc=0.

⚠️ **Fidelity ile raporlanmaz.** JSON'daki 0,999978179 C modelinin Qiskit'e
karşı değeridir; `tb_kernel.cpp`'de karşılaştırılan dizi yazılım `sv[]`'sinden
dolar, cosim onu değiştirmez. Kanıt, yukarıdaki bit eşitliğidir.

⚠️ **65536 genliğin tek tek eşitliği gösterilmedi** — `sv[]` dahili BRAM,
çıkış portu değil. Tek uyaran (p=2, tek problem örneği).

**"11,5 saat" tahmini yanlıştı**: darboğaz tasarım değil, `run_sim.tcl`'in
xsim çıktısını Tcl kanal katmanından geçirmesiydi (`>&@ stdout`). Baypas
edilince **15 dk 48 sn**. Sonraki koşular:

```
wsl -d Ubuntu -e bash /root/cosim-hizli.sh        # 2.+3. asama, ~16 dk
wsl -d Ubuntu -e bash /root/cosim-hizli-durum.sh  # ilerleme
```

Ayrıntı: [faz2-sentez.md §20](../../docs/measurements/faz2-sentez.md)

---

## Yeni oturumda ilk komut

Çalışma dizini **`C:\Users\olcay\IdeaProjects\qir-engine`** olmalı — proje
skill'leri dizine bağlı kayıt oluyor.

```
/speckit-implement Faz 5, YALNIZCA T001-T007 (G0 uyumluluk denemesi) koşulsun.
Gerisine geçilmesin — cevap "PYNQ ayrıştıramıyor" ise T026 sonrasındaki konak
kodunun tamamı farklı yazılacak. Kısayol: artifacts/ip/bd_0_20260917_15931cc.hwh
zaten Vivado 2025.2 ile üretilmiş ve gerçek qir_kernel IP'sini içeriyor;
T001-T005 yerine bu dosya karta kopyalanıp probe_test.py koşulabilir.
```

---

## Donanım durumu

| | |
|---|---|
| Kart | **AÇIK** (2026-09-27; T035 için bir kez `sudo reboot` edildi, geri geldi) |
| IP | **`192.168.1.6`** (RJ45, **DHCP**, 2026-09-27) — MAC `00-05-6b-04-42-a1`. Önceki adresler: `.1.2` (20 Eyl). DHCP adresi değişebilir: **`pynq.local`** (mDNS) çalışıyor, ya da `arp -a \| Select-String 00-05-6b`.
Ayrıca **`192.168.2.99`** (eth0 statik yedeği) |
| Seri konsol | **COM3**, 115200 8N1 — **parolasız açık** (`xilinx@pynq`). Yedek yol; ağ düşerse buradan girilir |
| SSH | ✅ **anahtarla parolasız** (2026-09-20). Anahtar: `%USERPROFILE%\.ssh\pynq` (şifresiz), parmak izi `SHA256:8rUb5U7k8QIVMYgYM3ZK5g0cX6rNNPogP0s4Gxxtiqw`.<br>`ssh -i $env:USERPROFILE\.ssh\pynq xilinx@192.168.1.2` · `scp` 157 KB = **1,6 sn** |
| sudo | ✅ **parolasız** (2026-09-20, `/etc/sudoers.d/010_xilinx-nopasswd`, `visudo -c` parsed OK) |
| `import pynq` | ✅ root altında çalışıyor — PYNQ **2.5**, `Overlay`/`Bitstream`/`MMIO` erişilebilir |
| FCLK0 | Boot'ta **100,0 MHz** — ama ⚠️ **overlay yüklenince 62,5 MHz** oluyor (2026-09-27, T032). Sebep: `qir_bd.tcl` kristali **33,333** verdi, PYNQ-Z2'ninki **50 MHz**; Vivado IO PLL'i 1600 sanıp bölenleri 4×4 seçti, kartın IO PLL'i 1000 MHz. SLCR'den doğrulandı (IO/ARM/DDR FBDIV 20/26/21 ×50 MHz). `board.py` artık **ayarlayıp doğruluyor** (bölenler 1×10 → 100,000). PL ve zamanlama kapanışı **etkilenmez** |
| Kart parolası | ⚠️ **fabrika varsayılanı** (`/etc/shadow` 2019'dan beri değişmemiş). Kasadaki değer karta hiç uygulanmamış — bkz. [secrets-audit.md](../../docs/secrets-audit.md) |
| Besleme | **JP5 = `USB`** (kullanıcı teyidi 2026-09-27; adaptörsüz). USB kaynağı — dizüstü portu mu şarj aleti mi — **kaydedilmedi**; enerji ölçümünden (öbek 6) önce yazılmalı. US1 bu düzende koşuldu.<br>✅ **Gerilim düşüşü ölçülmedi** (27 Eyl, `agent/xadc_izle.py`): US1 koşumları boyunca 50 sn, 78.988 örnek — VCCINT **≥ 1,0151 V**, VCCBRAM ≥ 1,0159 V (aralık 0,95–1,05). Yani bu iş yükünde "sessiz yanlış sonuç" endişesi ölçümle kapandı.<br>⛔ Enerji ölçümü (öbek 6) **hangi düzende** yapıldığını kaydetmek ZORUNDA; iki düzen karışırsa rakamlar kıyaslanamaz |
| PYNQ | **2.5**, çekirdek `4.19.0-xilinx-v2019.1`, Python 3.6.5. ✅ G0 geçti — 6 yıllık fark sorun çıkarmadı |
| INA219 | **HW-831B modülü, I2C tarafı bağlı** (27 Eyl): VCC→3.3V (ölçüldü 3,32 V), GND, SCL/SDA → Arduino başlığının sol ucu (P15/P16). **T047 geçti** (`0x40`, yapılandırma `0x399F`). ⚠️ Pin başlığı ve klemens **LEHİMSİZ** — temas aralıklı (240 denemede 7). VIN+/VIN− boş. **T046 öncesi**: lehim + vidalı klemensli DC jak adaptörleri (dişi/erkek) + JP5=REG, adaptör 12 V 2,5 A |
| Dizüstü | ⚠️ **günde ~1 mavi ekran** — NVIDIA sürücüsü, risk [GK-01](../../docs/risk-register.md). Uzun ölçüm serileri **koşum başına** diske yazılmalı |

**Kart boot etmezse**: kırmızı LED yanıp **yeşil DONE sönükse ve konsol
sessizse**, sorun "kart bozuk" değil **"boot kaynağına ulaşılamıyor"**dur.
UART'ı FSBL yapılandırır, FSBL de SD'den okunur. Sırayla bak: DONE LED →
microSD tam oturmuş mu → JP4 `SD` konumunda mı. (2026-09-19'da SD kart
yuvasından çıkmıştı, iki saat kaybettirdi.)

---

## Ölçülmüş durum — yeniden ölçülmeyecek

**FPGA** (Vivado implementasyonu, gerçek):
LUT %42 · FF %18 · DSP %15 · BRAM %67 · post-route **9,122 ns** ·
gecikme p=2 **36,578 ms kartta ölçüldü** (27 Eyl; sentez modeli 37,28 ms) ·
fidelity ≥0,99997 · cosim PASS (**n=8 ve n=16**)

**CPU** (2026-09-19 temiz ölçüm, prizde, 7474 koşum, plato oturdu):
turbo **32,75 ms** · plato **41,93 ms** · enerji **0,644 J/koşum**

⛔ **"BAŞABAŞ" SONUCU GEÇERSİZ** (21 Eyl) — o taban Qiskit Aer'di ve ~10× adil değildi.
Aynı kod konak CPU'da **3,273 ms** (CPU 11,4× hızlı); kart üstü ARM'da **84,13 ms**
(**FPGA 2,26× hızlı**; 27 Eyl kart ölçümüyle **2,30×** ← geçerli olan bu). Bkz. [§22](../../docs/measurements/faz2-sentez.md),
[hizlandirici-kiyas-gunlugu.md](../../docs/hizlandirici-kiyas-gunlugu.md).

Eski metin: 37,28 ms, CPU'nun turbo ve plato
değerlerinin arasına düşüyor. Tezin sonucu **enerji ekseninde** belirlenecek —
kaba hesap FPGA lehine 3,5–5,8× ama **ölçülmedi**.

⚠️ Eski CPU rakamları (77,6 / 92,7 ms) **geçersiz** — arka planda cosim
koşarken alınmışlardı ve `TEKRAR=15` yalnız turbo penceresini görüyordu.
Bkz. [faz2-sentez.md](../../docs/measurements/faz2-sentez.md) §18.

**Konak kodlayıcı** (2026-09-20, G2): `phases` 816/816 word **bit bit** C-sim
ile aynı; `cos_beta`/`sin_beta` aynı. `cost` **kasıtlı farklı** — C sessizce
doyuruyor, kodlayıcı ölçekliyor. 59 test geçiyor, kart gerekmiyor.

⛔ **`beklenen_deger = -0,442401439` bir enerji DEĞİLDİR** — referansın ham
katsayıları (`max|h|=7512`) Q1.17'yi aşıyor ve C tarafında 16/16 h girdisi
doyuyor. fidelity ve RTL eşdeğerliği etkilenmez (ikisi de `cost`'tan
bağımsız). Bkz. [faz2-sentez.md §21](../../docs/measurements/faz2-sentez.md).

Tez/makale için tek referans: [docs/olculen-degerler.md](../../docs/olculen-degerler.md)

---

## Faz 5 görev haritası (77 görev — 63 + GPU + Pareto + sıcak başlangıç)

| Faz | Öbek | Görev | Durum |
|---|---|---|---|
| 1 | 0 — G0 uyumluluk | T001–T007 | ✅ **BİTTİ — A yolu** |
| 2 | 1 — `fpga/` + belgeler | T008–T012 | ✅ **BİTTİ** |
| 2 | 3 — konak kodlayıcı | T019–T025 | ✅ **BİTTİ — G2 geçti** |
| 2 | 2 — blok tasarım + bitstream | T013–T018 | ✅ **BİTTİ — WNS +0,776 ns** |
| 3 | 4 — US1 kartta koşum + 20 izdüşüm 🎯 | T026–T038 | ✅ **BİTTİ — MVP (27 Eyl)**: p=1/p=2 20/20 bit bit |
| 4 | 5 — US2 gecikme, üç kapsam | T039–T045 | ✅ **BİTTİ** (27 Eyl): p=2 36,578 ms, 2,30×; T045 nedeni HLS en kötü durumu, RTL simülasyonuyla doğrulandı |
| 5 | 6 — US3 enerji (INA219) | T046–T050 | bekliyor |
| 6 | 7 — US4 kıyas matrisi | T051–T055 | bekliyor |
| 6B | **GPU tabanı** (2026-09-21 eklendi) | T064–T069 | 🔵 T064–T068 + T065b ✅ (30 Eyl gecikme, 3 Eki enerji — GPU serileri güvenilmez işaretli); T069 kaldı |
| 6C | **Genişlik Pareto eğrisi** — FPGA'ya özgü katkı (2026-09-21 eklendi) | T070–T073 | ✅ **kapandı** (27 Eyl) — dirsek yok; "18 kesişim" anlatısı ölçümle **çöktü**, §2.2b yeniden yazıldı |
| 6D | **Sıcak başlangıç** (2026-09-21 eklendi) | T074–T077 | ✅ **kapandı** (3 Eki) — referans ayarı QAOA'yı rastgele düzeyine indiriyor; normalize p=1 sabit açı tek çağrıda saniye altı |
| 7 | — faz kapanışı | T056–T063 | bekliyor |

**MVP**: T001–T038 → *"16 kübitlik statevector emülatörü FPGA'da çalışıyor ve
doğrulandı"* — tek başına savunulabilir.

**Kartsız ilerleyebilen**: öbek 1 (belgeler) ve öbek 3 (kodlayıcı, T019–T025).
Öbek 3 **kesinlikle** öbek 4'ten önce bitmeli ki kartta çıkacak uyuşmazlık
donanıma izole olsun.

---

## AĞ SORUNU — 27 Eyl'de TEKRARLAMADI

✅ 2026-09-27: kart DHCP'den `192.168.1.6` aldı; bitstream + dosyalar (4,4 MB)
`scp` ile **3,5 sn**'de aktarıldı, kartta SHA-256 doğrulandı. 21 Eyl'deki
kira sorununun sebebi **bulunamadı** (değişen bir şey yapılmadı). Tekrarlarsa
aşağıdaki sıra geçerli.

21 Eyl'de ölçülen durum:

| | |
|---|---|
| `carrier` | **1** — kablo takılı, link var |
| DHCP | kira **vermedi**; kart statik yedeğe düştü (`192.168.2.99`) |
| Elle verilen `192.168.1.50` | Wi-Fi'daki laptop'tan **görünmüyor** |
| Seri port | ✅ çalışıyor — 73 KB'ı 19 sn'de aktardı (3,8 KB/s) |

**Neden önemli**: bitstream **3,86 MB**. Seri porttan sıkıştırılmış ~2 MB
→ base64 ~2,7 MB → **~12 dakika**, ve her denemede tekrarlanır.

**Deneme sırası**:
1. `sudo dhclient -v eth0` (bir kez daha, kart tam boot ettikten sonra)
2. Kabloyu router'ın **başka bir portuna** al
3. Kartı laptop'ın ethernet portuna **doğrudan** bağla, iki tarafa statik IP
4. Son çare: seri porttan aktar (çalışır, sadece yavaş)

⛔ microSD'yi çıkarıp kopyalamak **son çaredir** — 19 Eylül'de SD yuvası iki
saat kaybettirdi (risk DT-03).

---

## Onaylanmış kararlar

| # | Karar |
|---|---|
| **K1** | Genlik fidelity'si kartta ölçülemiyor → **≥20 `cost` izdüşümü** (tasarım değişmez). Faz bilgisini görmez; faz n=8 cosim'den gelir ve rapora böyle yazılır |
| **K2** | EMIO I2C **ilk bitstream'e** dahil — sonra eklemek US1/US2 ölçümlerini tekrarlatır |
| **K3** | Donanım kaynağı **yeni `fpga/` dizinine** (`bd/` + `rtl/`); `hls/` §2'de "Vitis HLS" diye tanımlı |
| — | Enerji: **kart INA219** (0,1 Ω), **dizüstü batarya sayacı** (adaptör 20V/6A, şönt yanardı). Yöntem iki tarafta da **delta** |

---

## Bilinen tuzaklar

- **FCLK kartta doğrulanmadan hiçbir gecikme raporlanmaz.** Overlay yüklemesi
  FCLK0'ı 62,5 MHz'e çekiyor (kristal hatası, donanım tablosu). `board.py`
  ayarlayıp doğruluyor ve yüklemeden hemen sonraki değeri kaydediyor
  (`fclk_yukleme_sonrasi_mhz`). `qir_bd.tcl`'deki kristal bir **sonraki
  derlemede** 50 MHz yapılmalı ve `.hwh` bölenleriyle doğrulanmalı
- **XADC bitstream yüklenirken 0 okur** (PL'de). `xadc_izle.py` bu örnekleri
  ayrı sayıyor; ham en-düşük "0,0 V" bir çökme değildir
- **PowerShell → `ssh`/`wsl` tırnakları bozuyor** (`( )`, `"`, `$`). Karta
  giden çok satırlı komutları betik dosyası olarak `scp` edip `bash dosya.sh`
  ile koş
- **Kartın saati ~3 saat geride** (NTP yok): ölçüm zaman damgası dizüstünden
  alınır
- **Slash komutu mesajın BAŞINDA** olmalı; çalışma dizini proje kökü olmalı
  (üst klasöre çıkınca skill'ler kayıttan düşüyor — 2026-09-19'da oldu)
- PowerShell 5.1'de **`&&` yok**, ayıraç `;`
- Vitis yalnız **WSL**'de; her çağrıda **`LC_ALL=en_US.UTF-8` şart**
- `open_solution -reset` **`impl/` dizinini siler** — `export.zip` ve
  `bd_0.hwh` bu yüzden `artifacts/ip/` altına kopyalandı
- `pgrep -f 'xsetup'` gibi kalıplar **kendini eşleştirir**; `[x]setup` yaz
- HLS'in kaynak tahmini **2 kata kadar yanılıyor** (LUT'ta 0,39–0,50×) ve oran
  sabit değil. **Kaynak gerekçesiyle varyant elenecekse gerekçe
  implementasyondan gelmeli**
- Yerleştirme-yönlendirme **monoton değil**: daha az talep eden varyant (#7)
  daha kötü yerleşti ve zamanlamayı tutturamadı
