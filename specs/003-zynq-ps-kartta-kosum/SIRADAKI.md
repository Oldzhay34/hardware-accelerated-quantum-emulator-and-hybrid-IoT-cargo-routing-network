# Faz 5 — SIRADAKİ

## SIRADAKİ

> # 🔒 KAPSAM DONDURULDU — 2026-09-21
>
> **Öbek 4 (T026–T038, MVP) bitene kadar yeni görev AÇILMAZ.**
>
> Gerekçe: 21 Eylül'de 14 görev eklendi (T064–T077) ve öbek 4'ten **hiçbiri**
> bitmedi. Eklenenlerin hepsi iyi fikir — ama hepsi MVP'nin *süsü*, MVP'nin
> kendisi değil. Öbek 4 bittiğinde elde **tek başına savunulabilir** bir sonuç
> olur: *"16 kübitlik statevector emülatörü FPGA'da çalışıyor ve altın
> referansa karşı doğrulandı."* Bu cümle GPU'dan, enerjiden ve rota
> kalitesinden bağımsız ayakta durur — ve şu an **söylenemiyor**, çünkü
> bitstream kartta koşmadı.
>
> T064–T077 (GPU tabanı, Pareto, sıcak başlangıç) **MVP'den sonra**.
> İyi bir fikir çıkarsa tasks.md'ye yazılır ama **başlanmaz**.

**Hedef (tek cümle)**: **T032** — bitstream'i karta yükle ve `ap_idle`
okunabildiğini doğrula; ardından **T033/G3** (20 izdüşüm bit bit tutmalı).
⚠️ Önce **ağ** çözülmeli: bitstream 3,86 MB, seri porttan ~12 dk sürer.

**Dokunulacak dosyalar**: `artifacts/bitstream/qir_20260920_d350605.{bit,hwh}`,
`agent/` (karta kopyalanacak), `artifacts/izdusum_{vektorleri,beklenen}.json`

**Bilinen tuzak**: Konak kodu `sudo` ile koşar (`import pynq` root ister) ve
FCLK'yi **doğrular** (`board.Kart.yukle()` %1'den saparsa istisna atar).
Bir sapma görülürse **ilk şüpheli GÜÇ** olmalı, mantık değil — bkz. donanım
tablosundaki JP5 notu.

**Son güncelleme**: 2026-09-21, Faz 5.5 (T026–T031 bitti; T032 kart bekliyor)

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
| Kart | **KAPALI** (2026-09-20, düzgün kapatıldı). Açılışta IP'yi seri konsoldan yine doğrula |
| IP | **`192.168.1.2`** (RJ45) — ping 2 ms, SSH/9090/80 açık, MAC `00-05-6b-04-42-a1`.
Ayrıca **`192.168.2.99`** (USB ethernet gadget). Üç yoldan doğrulandı: seri `hostname -I`, mDNS `pynq.local`, ping |
| Seri konsol | **COM3**, 115200 8N1 — **parolasız açık** (`xilinx@pynq`). Yedek yol; ağ düşerse buradan girilir |
| SSH | ✅ **anahtarla parolasız** (2026-09-20). Anahtar: `%USERPROFILE%\.ssh\pynq` (şifresiz), parmak izi `SHA256:8rUb5U7k8QIVMYgYM3ZK5g0cX6rNNPogP0s4Gxxtiqw`.<br>`ssh -i $env:USERPROFILE\.ssh\pynq xilinx@192.168.1.2` · `scp` 157 KB = **1,6 sn** |
| sudo | ✅ **parolasız** (2026-09-20, `/etc/sudoers.d/010_xilinx-nopasswd`, `visudo -c` parsed OK) |
| `import pynq` | ✅ root altında çalışıyor — PYNQ **2.5**, `Overlay`/`Bitstream`/`MMIO` erişilebilir |
| FCLK0 | **100,0 MHz** ölçüldü (boot varsayılanı) — bitstream'in zamanlama hedefiyle aynı. Yine de konak kodu **doğrulamalı**, varsaymamalı |
| Kart parolası | ⚠️ **fabrika varsayılanı** (`/etc/shadow` 2019'dan beri değişmemiş). Kasadaki değer karta hiç uygulanmamış — bkz. [secrets-audit.md](../../docs/secrets-audit.md) |
| Besleme | ⚠️ **JP5 şu an `USB`** (21 Eyl: kart adaptörsüz açıldı → REG olamaz). Daha önce bu satır "REG" diyordu, **yanlıştı**.<br>⚠️ USB 2,5 W verir; PL %43 LUT + %67 BRAM @100 MHz bunu zorlayabilir. Gerilim düşerse **sessiz yanlış sonuç** verir ve mantık hatası sanılır.<br>**Öneri**: T032 öncesi kartı kapat → JP5 = **REG** → adaptör + USB + ethernet.<br>⛔ Enerji ölçümü (öbek 6) **hangi düzende** yapıldığını kaydetmek ZORUNDA; iki düzen karışırsa rakamlar kıyaslanamaz |
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
| 3 | 4 — US1 kartta koşum + 20 izdüşüm 🎯 | T026–T038 | 🔵 **T026–T031 BİTTİ**, T032 kart bekliyor |
| 4 | 5 — US2 gecikme, üç kapsam | T039–T045 | bekliyor |
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

## ⚠️ AĞ SORUNU — T032'den önce çözülmeli

Kart açıkken (21 Eyl) ölçülen durum:

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
