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

**Hedef (tek cümle)**: **T039** — [protokol taslağı](../../docs/measurements/kart-olcum-protokolu.md)
yazıldı (2026-09-27), **kullanıcı onayı bekliyor**; onaylanınca v1.0 olarak
dondurulur, ardından T040–T044. ⛔ Onaysız ölçüm alınmaz.

**Dokunulacak dosyalar**: `docs/measurements/kart-olcum-protokolu.md` (yeni),
`agent/measure_latency.py` (yeni), `agent/board.py` (`kosum()` zamanlaması)

**Bilinen tuzak**: ⚠️ **Protokol öncesi görülen değer**: G3 koşumunda
`t_cekirdek` alanı ~36,5 ms gösterdi (p=2, yoklamayla, tek çağrı başına) —
sentez tahmini 37,28 ms. Bu bir ölçüm serisi **değil** ve raporlanmaz; ama
SC-009 *"sonuca bakıp protokol ayarlanamaz"* diyor: protokol bunu **bildiğini
yazarak** dondurulmalı. Ayrıca T045b **yarım**: ARM tarafı ölçüldü (84,13 ms),
FPGA tarafı hâlâ tahmin — T044'ün kart ölçümü gelince yeniden hesaplanır.

**Son güncelleme**: 2026-09-27, Faz 5.6 (öbek 4 kartta bitti; sıradaki T039)

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
| INA219 | elde, **bağlanmadı** — yalnız öbek 6 (US3) için |
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
gecikme p=2 **37,28 ms** (tahmin, kartta ölçülmedi) ·
fidelity ≥0,99997 · cosim PASS (**n=8 ve n=16**)

**CPU** (2026-09-19 temiz ölçüm, prizde, 7474 koşum, plato oturdu):
turbo **32,75 ms** · plato **41,93 ms** · enerji **0,644 J/koşum**

⛔ **"BAŞABAŞ" SONUCU GEÇERSİZ** (21 Eyl) — o taban Qiskit Aer'di ve ~10× adil değildi.
Aynı kod konak CPU'da **3,273 ms** (CPU 11,4× hızlı); kart üstü ARM'da **84,13 ms**
(**FPGA 2,26× hızlı** ← geçerli olan bu). Bkz. [§22](../../docs/measurements/faz2-sentez.md),
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
| 4 | 5 — US2 gecikme, üç kapsam | T039–T045 | 🔵 **sıradaki: T039** (T045b yarım: FPGA tarafı T044'ü bekliyor) |
| 5 | 6 — US3 enerji (INA219) | T046–T050 | bekliyor |
| 6 | 7 — US4 kıyas matrisi | T051–T055 | bekliyor |
| 6B | **GPU tabanı** (2026-09-21 eklendi) | T064–T069 | bekliyor — kart gerekmez |
| 6C | **Genişlik Pareto eğrisi** — FPGA'ya özgü katkı (2026-09-21 eklendi) | T070–T073 | bekliyor — kart gerekmez, bağımlılık yok |
| 6D | **Sıcak başlangıç** (2026-09-21 eklendi) | T074–T077 | bekliyor — kart ve FPGA gerekmez |
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
