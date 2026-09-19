# Faz 5 — SIRADAKİ

## SIRADAKİ

**Hedef (tek cümle)**: Faz 5 spec'i yazıldı ve onaylandı; sıradaki tek iş
`/speckit-plan` çalıştırıp planı üretmek — **ilk görevi PYNQ 2.5 ile Vitis
2025.2 arasındaki `.hwh` uyumluluk denemesi olmalı.**

**Dokunulacak dosyalar**: `specs/003-zynq-ps-kartta-kosum/spec.md` (hazır),
`specs/003-zynq-ps-kartta-kosum/checklists/requirements.md` (16/16 geçti),
`artifacts/ip/qir_kernel_ip_20260917_15931cc.zip` (Faz 5'in girdisi)

**Bilinen tuzak**: Kartta **PYNQ 2.5 (Glasgow, 2019)** var, IP paketi ise
**Vitis 2025.2** ile üretildi — altı yıl fark. PYNQ'nun `Overlay` sınıfı
`.hwh` dosyasını ayrıştıramayabilir ve bu **US1'i tamamen bloke eder**.
Bir saatte test edilir, altıncı haftaya bırakılmamalı.

**Son güncelleme**: 2026-09-19, Faz 5.0

---

## Yeni oturumda ilk yazılacak komut

Çalışma dizini **`C:\Users\olcay\IdeaProjects\qir-engine`** olmalı — proje
skill'leri (`.claude/skills/speckit-*`) dizine bağlı kayıt oluyor. Dizin üst
klasöre çıkarsa `/speckit-plan` komut listesinden düşer (2026-09-19'da bu oldu).

Eğik çizgi **mesajın en başında** olacak:

```
/speckit-plan Faz 5 spec'i (specs/003-zynq-ps-kartta-kosum/spec.md) onaylandı,
plana geç. Kart boot ediyor ve 192.168.1.2'de erişilebilir (SSH, Jupyter 9090
doğrulandı), adaptörle besleniyor (JP5=REG, enerji ölçümü için sabit kalacak).
IP paketi artifacts/ip/qir_kernel_ip_20260917_15931cc.zip hazır. CPU tabanı
temiz ölçüldü: turbo 32,75 ms, plato 41,93 ms, enerji 0,644 J/koşum.
KRİTİK RİSK — kartta PYNQ 2.5 (2019) var, IP ise Vitis 2025.2 ile üretildi;
PYNQ'nun Overlay sınıfı .hwh dosyasını ayrıştıramayabilir ve bu US1'i tamamen
bloke eder. Bu uyumluluk denemesi planın İLK görevi olmalı. INA219 elde ama
US3 için, US1/US2 onu beklemiyor.
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
| **US1** | Çekirdek kartta koşsun, çıktı Qiskit'e karşı doğrulansın | kart ✅, IP ✅ | ⬅️ **sıradaki** |
| US2 | Kartta gerçek gecikme ölçümü | US1 | bekliyor |
| US3 | Kartta enerji ölçümü | US1 + INA219 ✅ elde | bekliyor |
| US4 | Kıyas matrisi | US2 + US3 | bekliyor |

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
