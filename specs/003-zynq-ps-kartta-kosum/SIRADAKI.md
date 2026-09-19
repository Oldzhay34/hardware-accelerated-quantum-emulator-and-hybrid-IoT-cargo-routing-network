# Faz 5 — SIRADAKİ

## SIRADAKİ

**Hedef (tek cümle)**: Faz 5 planı ve 63 görev üretildi, üç mimari karar
onaylandı; sıradaki tek iş **T001–T007 (G0)** — PYNQ 2.5'in Vivado 2025.2
`.hwh`'sini ayrıştırıp ayrıştıramadığını öğrenmek.

**Dokunulacak dosyalar**: [tasks.md](tasks.md) (63 görev),
`fpga/bd/probe_hwh.tcl`, `fpga/bd/probe_hwh.sh`, `fpga/bd/probe_test.py`

⛔ **Kart şu an KAPALI.** Açılınca DHCP adresi değişmiş olabilir —
`192.168.1.2` bir varsayımdır. Seri konsoldan (COM3, 115200 8N1) `hostname -I`
ile doğrulanmadan hiçbir `ssh`/`scp` koşulmaz. JP4=SD, JP5=REG, adaptör.

**Planın bulduğu iki sert gerçek** (spec bunları varsaymıştı, tutmadı):

1. `artifacts/ip/*.zip` **bitstream değil**, IP kataloğu paketi. US1'den önce
   bir **Vivado blok tasarım** adımı gerekiyor — spec'te adı geçmiyor.
2. Çekirdek **genlik vektörünü dışarı vermiyor** (madde K-1, yalnız skaler
   `beklenen_deger`). SC-001'in fidelity ölçütü kartta doğrudan ölçülemez.

**Bilinen tuzak**: Kartta **PYNQ 2.5 (Glasgow, 2019)**, IP ise **Vitis 2025.2**
— altı yıl fark. PYNQ'nun `.hwh` ayrıştırıcısı **tek alt sürüm farkında bile**
kırılmış olarak belgelenmiş. Yedek yol sağlam: çekirdek yalnız `s_axilite`
kullandığı için `Bitstream` + `MMIO` tam işlevsellik veriyor, DMA gerekmiyor.
Yine de **G0 ilk görev** — bir saatte cevaplanır, altıncı haftaya bırakılamaz.

**Son güncelleme**: 2026-09-19, Faz 5.2 (görevler üretildi)

---

## Onaylanan üç karar (2026-09-19, Prensip I)

| # | Karar |
|---|---|
| **K1** | Genlik yerine **çoklu izdüşüm**: `cost` bir AXI girişi ve yalnız `expectation_scaled`'i besliyor → aynı devre ≥20 rastgele `cost` vektörüyle koşulup aynı statevector'ün 20 bağımsız izdüşümü alınır. **Tasarım değişmez, yeniden sentez yok.** Yöntem **fazı görmez** — faz n=8 cosim'den gelir, rapor bunu ayrıca yazar. |
| **K2** | **EMIO I2C ilk bitstream'e dahil** — sonra eklemek bir sentez turu artı US1/US2 ölçümlerinin tekrarı demek. |
| **K3** | Donanım kaynağı **yeni `fpga/` üst dizinine** (`bd/` + şimdiden ayrılan `rtl/`). `repo-conventions.md` §2, `CLAUDE.md` depo haritası ve `fpga/README.md` aynı değişiklikte güncellenir. |

---

## Yeni oturumda ilk yazılacak komut

Çalışma dizini **`C:\Users\olcay\IdeaProjects\qir-engine`** olmalı — proje
skill'leri (`.claude/skills/speckit-*`) dizine bağlı kayıt oluyor. Dizin üst
klasöre çıkarsa komut listesinden düşer (2026-09-19'da bu oldu).

Eğik çizgi **mesajın en başında** olacak:

```
/speckit-implement Faz 5 görevleri hazır (specs/003-zynq-ps-kartta-kosum/tasks.md,
63 görev). Önce SIRADAKI.md'yi oku. T001-T007 (G0) ile başla: PYNQ 2.5'in Vivado
2025.2 .hwh'sini ayrıştırıp ayrıştıramadığını öğren. Kukla BD PS + GERÇEK
qir_kernel IP içermeli, PS-only olursa test anlamsız olur; probe boş ip_dict'i
başarı saymamalı. Kart KAPALI — açıp seri konsoldan (COM3, 115200) hostname -I
ile IP'yi doğrula, besleme düzenine (adaptör, JP5=REG) dokunma. Öbek 1 (belgeler)
ve öbek 3 (konak kodlayıcı) donanım beklemeden paralel ilerleyebilir.
```

---

## Donanım durumu (2026-09-19'da doğrulandı)

| | |
|---|---|
| Kart IP | **192.168.1.2** (routerdan DHCP) |
| SSH / HTTP / Jupyter | ✅ 22, 80, **9090 → HTTP 200** |
| Seri konsol | **COM3**, 115200 8N1 — `xilinx@pynq:~$` |
| Besleme | **Adaptör**, **JP5 = REG** |
| PYNQ sürümü | **PynqLinux 2.5 (Glasgow)** ⚠️ |

⚠️ **Besleme kurulumu DEĞİŞTİRİLMEYECEK.** Enerji ölçümlerinin
karşılaştırılabilir olması buna bağlı. USB'ye geri dönülmez.

**Bugün yaşanan arıza ve teşhisi** (tekrarlarsa): kart boot etmedi, kırmızı LED
yanıyordu ama **yeşil DONE sönüktü** ve seri konsol **tamamen sessizdi**.
Sebep: jumper'larla uğraşırken **microSD kart yuvasından çıkmıştı**.
Ders: UART'ı FSBL yapılandırır, FSBL de SD'den okunur — **sessiz konsol
"kart bozuk" değil, "boot kaynağına ulaşılamıyor" demektir.** Önce DONE LED'ine
bak, sonra SD karta, sonra JP4'e (boot kaynağı, `SD` konumunda olmalı).

---

## Ölçülmüş durum — bunlar yeniden ölçülmeyecek

**FPGA** (implementasyon sonrası, gerçek — HLS tahmini değil):

| | |
|---|---:|
| LUT / FF / DSP / BRAM | %42 / %18 / %15 / %67 |
| Post-route | **9,122 ns**, zamanlama tuttu |
| Gecikme p=2 | 3.728.217 çevrim = **37,28 ms** (tahmin, kartta ölçülmedi) |
| Fidelity | ≥ 0,99997 (n=8/12/16), cosim PASS (n=8) |

**CPU** (2026-09-19, temiz ölçüm):

| | |
|---|---:|
| Turbo (ilk 2 sn) | **32,75 ms** |
| Plato (son 60 sn) | **41,93 ms** |
| Enerji | **0,644 J/koşum** (bataryada, 47,5 ms noktasında) |

**Karşılaştırma: gecikmede BAŞABAŞ.** FPGA'nın 37,28 ms'i CPU'nun turbo ve
plato değerlerinin arasına düşüyor. Tezin sonucu **enerji ekseninde**
belirlenecek — kaba hesap FPGA lehine 3,5–5,8× ama **ölçülmedi**.

⚠️ Eski CPU rakamları (77,6 / 92,7 ms) **geçersizdir** — arka planda cosim
koşarken alınmışlardı. Ayrıntı: [faz2-sentez.md](../../docs/measurements/faz2-sentez.md) §18.

Tez/makale için tek referans: [docs/olculen-degerler.md](../../docs/olculen-degerler.md).

---

## Faz 5'in dört işi (spec'teki öncelikler)

| | İş | Bağımlılık | Durum |
|---|---|---|---|
| — | **G0 uyumluluk denemesi** | yok | ⬅️ **sıradaki** |
| — | `fpga/` dizini + belge güncellemeleri | yok | bekliyor (G0'dan bağımsız) |
| — | Blok tasarım + bitstream (**spec'te yoktu**) | `fpga/` | bekliyor |
| — | Konak kodlayıcı, **kartsız** doğrulanır | yok | bekliyor (G0'dan bağımsız) |
| **US1** | Çekirdek kartta koşsun, ≥20 izdüşümle doğrulansın | G0 + bitstream + kodlayıcı | bekliyor |
| US2 | Kartta gerçek gecikme ölçümü (üç kapsam) | US1 | bekliyor |
| US3 | Kartta enerji ölçümü | US1 + INA219 ✅ elde | bekliyor |
| US4 | Kıyas matrisi | US2 + US3 | bekliyor |

⚠️ **Kodlayıcı kartsız doğrulanmadan karta gidilmez.** Gidilirse kartta çıkan
her uyuşmazlık *"donanım mı, kodlayıcı mı"* belirsizliğinde kalır. Planın en
önemli sıralama kararı budur.

**5.2 (tünel, kimlik, uzaktan erişim) kapsam DIŞI** — İ etiketli.

---

## Enerji ölçüm yöntemi (karar verildi, 2026-09-16/19)

- **Kart tarafı**: INA219, 12 V hattında seri. Elde, henüz bağlanmadı.
  Standart 0,1 Ω şönt doğru (PYNQ ~0,3 A çeker, ~1,2 mW çözünürlük).
- **CPU tarafı**: **batarya sayacı** — INA219 değil. Adaptör 20 V/6 A/120 W
  olduğu için 0,1 Ω şönt 5 A'de 2,5 W harcayıp yanardı. Batarya yöntemi aynı
  kapsamı (tüm dizüstü) sıfır riskle ölçüyor ve **ölçüm yapıldı**.
- **Yöntem iki tarafta da aynı: delta** (boş güç ile yük altındaki gücün farkı).
- Betikler: `scripts/battery_logger.ps1`, `scripts/cpu_load_loop.py`,
  `scripts/battery_energy.py`

---

## Diğer bilinen tuzaklar

- **Slash komutu mesajın BAŞINDA olmalı**, sonunda yazılırsa çalışmaz.
- Vitis yalnızca **WSL**'de çalışır (Windows'ta Device Guard engelliyor) ve her
  çağrıda **`LC_ALL=en_US.UTF-8` şart**. Bkz. `hls/run.sh`.
- `common.tcl`'deki `open_solution -reset`, `impl/` dizinini **siler** —
  `export.zip` bu yüzden bir kez kaybedildi. Kopyası `artifacts/ip/` altında.
- `pgrep -f 'xsetup'` gibi kalıplar **kendini eşleştirir**; `[x]setup` yaz.
- n=16 cosim ~11,5 saat sürüyor ve üç kez yarıda kesildi. **n=8 PASS verdi**,
  n=16 doğrulaması hâlâ açık ve önceliği düşük — Faz 5'in kart ölçümü onu
  fiilen geçersiz kılacak.
