# Faz 5 — SIRADAKİ

## SIRADAKİ

**Hedef (tek cümle)**: Öbek 1 ve 3 **bitti**; sıradaki iş **öbek 2**
(T013–T018: gerçek blok tasarım, EMIO I2C, bitstream) — ama önce kartta
**parolasız sudo** çözülmeli, yoksa öbek 4 başlayamaz.

**Dokunulacak dosyalar**: `fpga/bd/qir_bd.tcl` (yok, T013 yazacak),
`fpga/bd/qir_constraints.xdc` (yok, T015), `fpga/bd/build.sh` (yok, T016)

**Bilinen tuzak**: T017'de **WNS ≥ 0 tutmazsa FCLK DÜŞÜRÜLMEZ** — 100 MHz,
Faz 2'nin bütün ölçümlerinin dayanağıdır; faz durur ve sebep araştırılır.
Ayrıca kartta `import pynq` root istiyor ve `sudo` parola soruyor.

**Son güncelleme**: 2026-09-20, Faz 5.2 (öbek 1 ve 3 bitti; G2 geçti)

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
| Kart | ✅ **AÇIK ve doğrulandı** (2026-09-20 10:22) |
| IP | **`192.168.1.2`** (RJ45) — ping 2 ms, SSH/9090/80 açık, MAC `00-05-6b-04-42-a1`.
Ayrıca **`192.168.2.99`** (USB ethernet gadget). Üç yoldan doğrulandı: seri `hostname -I`, mDNS `pynq.local`, ping |
| Seri konsol | **COM3**, 115200 8N1 — **parolasız açık** (`xilinx@pynq`). Yedek yol; ağ düşerse buradan girilir |
| SSH | ✅ **anahtarla parolasız** (2026-09-20). Anahtar: `%USERPROFILE%\.ssh\pynq` (şifresiz), parmak izi `SHA256:8rUb5U7k8QIVMYgYM3ZK5g0cX6rNNPogP0s4Gxxtiqw`.<br>`ssh -i $env:USERPROFILE\.ssh\pynq xilinx@192.168.1.2` · `scp` 157 KB = **1,6 sn** |
| sudo | ⚠️ **parola istiyor** — `import pynq` root gerektirdiği için öbek 4'ten önce çözülmeli |
| Besleme | **Adaptör**, **JP5 = REG** — ⚠️ DEĞİŞTİRİLMEYECEK (enerji ölçümü buna bağlı) |
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

**Karşılaştırma: gecikmede BAŞABAŞ.** 37,28 ms, CPU'nun turbo ve plato
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

## Faz 5 görev haritası (63 görev)

| Faz | Öbek | Görev | Durum |
|---|---|---|---|
| 1 | 0 — G0 uyumluluk | T001–T007 | ✅ **BİTTİ — A yolu** |
| 2 | 1 — `fpga/` + belgeler | T008–T012 | ✅ **BİTTİ** |
| 2 | 3 — konak kodlayıcı | T019–T025 | ✅ **BİTTİ — G2 geçti** |
| 2 | 2 — blok tasarım + bitstream | T013–T018 | ⬅️ **sıradaki** |
| 3 | 4 — US1 kartta koşum + 20 izdüşüm 🎯 | T026–T038 | bekliyor |
| 4 | 5 — US2 gecikme, üç kapsam | T039–T045 | bekliyor |
| 5 | 6 — US3 enerji (INA219) | T046–T050 | bekliyor |
| 6 | 7 — US4 kıyas matrisi | T051–T055 | bekliyor |
| 7 | — faz kapanışı | T056–T063 | bekliyor |

**MVP**: T001–T038 → *"16 kübitlik statevector emülatörü FPGA'da çalışıyor ve
doğrulandı"* — tek başına savunulabilir.

**Kartsız ilerleyebilen**: öbek 1 (belgeler) ve öbek 3 (kodlayıcı, T019–T025).
Öbek 3 **kesinlikle** öbek 4'ten önce bitmeli ki kartta çıkacak uyuşmazlık
donanıma izole olsun.

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
