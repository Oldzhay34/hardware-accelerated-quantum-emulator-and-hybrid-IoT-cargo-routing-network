# Faz 5 — SIRADAKİ

## SIRADAKİ

**Hedef (tek cümle)**: Görev listesi (63 görev) üretildi; sıradaki iş **G0
uyumluluk denemesi** — ve elde hazır bir `.hwh` olduğu için bu **5 dakikada**
cevaplanabiliyor, T001–T005'i beklemeden.

**Dokunulacak dosyalar**: `specs/003-zynq-ps-kartta-kosum/tasks.md` (T001–T007),
`artifacts/ip/bd_0_20260917_15931cc.hwh` (hazır probe dosyası),
`fpga/bd/probe_test.py` (henüz yazılmadı — T003)

**Bilinen tuzak**: Kukla BD **PS-only olmamalı**; PS-only bir `.hwh`'de özel IP
yoktur, `ip_dict` boş döner ve test hiçbir şey kanıtlamaz. Elimizdeki
`bd_0_*.hwh` gerçek `qir_kernel` IP'sini içeriyor, o yüzden geçerli.

**Son güncelleme**: 2026-09-19, Faz 5.0 (tasks bitti, implement başlamadı)

---

## ŞU AN KOŞAN İŞ ⏳

**n=16 cosim**, 2026-09-19 ~19:50'de başlatıldı. `/root/cosim-n16.sh`,
log `/var/log/cosim-n16.log`, durum `bash /root/cosim-durum.sh`.

- Hedef **37,28 ms** simüle zaman (p=2). ⚠️ Daha önce 53,75 ms sanılıyordu —
  o **p=3'ün max gecikmesi** ve YANLIŞTI; bütün "11 saat sürer" tahminleri
  bu hatadan geliyordu.
- Hız devrenin bölümüne göre değişiyor: mikser (toplamın %64'ü) ~0,1 ms/dk,
  geri kalanı ~1,6 ms/dk. Tahmini toplam **~4-5 saat**.
- Yavaşlığın sebebi: `DEPENDENCE` pragması yüzünden autotb her bellek
  erişiminde uyarı üretiyor (~127 bin adet). Kapatma anahtarı **aranıp
  bulunamadı**.
- Beklenen sonuç: `PASS`, fidelity **0,999978179**.
- Geçerse [olculen-degerler.md](../../docs/olculen-degerler.md) §2 ve §7'deki
  *"n=16 RTL eşdeğerliği ölçülmedi"* uyarıları kalkar.

⚠️ **Cosim koşarken ağır iş başlatma** — özellikle CPU ölçümü (sonuç kirlenir)
ve Vivado/Vitis (yarışır). Üç kez tam bu yüzden yarıda kesildi.

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
| Kart | **KAPALI** (2026-09-19'da prizden çekildi) |
| IP | `192.168.1.2` idi — **tekrar açılınca değişebilir**, seri konsoldan `hostname -I` |
| Seri konsol | **COM3**, 115200 8N1 |
| Besleme | **Adaptör**, **JP5 = REG** — ⚠️ DEĞİŞTİRİLMEYECEK (enerji ölçümü buna bağlı) |
| PYNQ | **2.5 (Glasgow)** ⚠️ Vitis 2025.2 ile 6 yıl fark → G0'ın sebebi |
| INA219 | elde, **bağlanmadı** — yalnız öbek 6 (US3) için |

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
fidelity ≥0,99997 · cosim PASS (n=8)

**CPU** (2026-09-19 temiz ölçüm, prizde, 7474 koşum, plato oturdu):
turbo **32,75 ms** · plato **41,93 ms** · enerji **0,644 J/koşum**

**Karşılaştırma: gecikmede BAŞABAŞ.** 37,28 ms, CPU'nun turbo ve plato
değerlerinin arasına düşüyor. Tezin sonucu **enerji ekseninde** belirlenecek —
kaba hesap FPGA lehine 3,5–5,8× ama **ölçülmedi**.

⚠️ Eski CPU rakamları (77,6 / 92,7 ms) **geçersiz** — arka planda cosim
koşarken alınmışlardı ve `TEKRAR=15` yalnız turbo penceresini görüyordu.
Bkz. [faz2-sentez.md](../../docs/measurements/faz2-sentez.md) §18.

Tez/makale için tek referans: [docs/olculen-degerler.md](../../docs/olculen-degerler.md)

---

## Faz 5 görev haritası (63 görev)

| Faz | Öbek | Görev | Durum |
|---|---|---|---|
| 1 | 0 — G0 uyumluluk | T001–T007 | ⬅️ **sıradaki** |
| 2 | 1,2,3 — belge, bitstream, kodlayıcı | T008–T025 | bekliyor |
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
