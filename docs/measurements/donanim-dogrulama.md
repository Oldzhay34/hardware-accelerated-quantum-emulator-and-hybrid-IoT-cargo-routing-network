# Donanım Doğrulama Ölçümleri — PYNQ-Z2

> Anayasa Prensip II: buradaki her satır gerçekten gözlemlendi. Tahmin yok.

---

## 2026-09-15 · İlk boot doğrulaması (S-1 sigortası, DT-01 riski)

**Bağlam**: Kart teslim alındı ve USB ile bağlandı. Takvimde H1'in ikinci günü.

### Cihaz tanıma

| | |
|---|---|
| Seri port | **COM3** |
| Denetleyici | FTDI **FT2232H** — `VID_0403 + PID_6010` |
| Cihaz kimliği | `FTDIBUS\VID_0403+PID_6010+1234-TULB\0000` |
| Durum | OK |

`TULB` seri numarası, PYNQ-Z2'nin üreticisi **TUL**'a işaret ediyor — kartın kendisi olduğunun teyidi.
FT2232H çift kanallıdır: bir kanal JTAG, diğeri UART.

### Seri port çıktısı (115200 8N1, gerçek okuma)

```
[  OK  ] Started ISC DHCP IPv4 server.
         Starting Samba NMB Daemon...
[  OK  ] Started ISC DHCP IPv6 server.
[  OK  ] Started Permit User Sessions.
[  OK  ] Started Getty on tty1.
[  OK  ] Started Serial Getty on ttyPS0.
[  OK  ] Reached target Login Prompts.

PYNQ Linux, based on Ubuntu 18.04    pynq ttyPS0

pynq login: xilinx (automatic login)

Last login: Mon Sep 30 09:03:48 UTC 2019 on ttyPS0
```

485 bayt okundu. Sistem boot etmiş, servisler ayakta, otomatik giriş yapılmış.

### Sonuç

| Risk / sigorta | Durum |
|---|---|
| [DT-00](../risk-register.md) — tedarik | ✅ **KAPALI** |
| [DT-01](../risk-register.md) — kart arızalı/boot etmiyor | 🟢 boot ölçütü **geçti**; Jupyter ve overlay ölçütleri **henüz doğrulanmadı** |
| [S-1](../risk-register.md) sigortası — boot testi | ✅ **yapıldı** |

**Not**: `Last login: Mon Sep 30 09:03:48 UTC 2019` satırı, kartın saatinin ayarlı olmadığını
gösteriyor (RTC pili yok, NTP'ye ulaşamamış). Ölçüm yapılırken **zaman damgası kartın kendi
saatinden alınmamalı** — aksi halde ölçüm kayıtları 2019 tarihli görünür. Faz 5'te ölçüm
damgalaması host tarafından yapılmalı ([VR-03](../risk-register.md) ile bağlantılı).

---

## 2026-09-15 · Ağ erişimi denemesi — ❌ başarısız, nedeni tespit edildi

### Kart tarafı (seri porttan okundu)

```
$ ip -br addr
lo       UNKNOWN   127.0.0.1/8 ::1/128
eth0     DOWN      192.168.2.99/24
sit0     DOWN

$ cat /sys/class/net/eth0/carrier
0
```

### Host tarafı (Windows)

| Kontrol | Sonuç |
|---|---|
| `ping 192.168.2.99` | ❌ başarısız |
| Port 9090 (Jupyter) / 80 / 22 | ❌ hepsi erişilemez |
| Host'ta `192.168.2.x` arayüzü | ❌ yok (mevcut: Wi-Fi `192.168.1.5`, VirtualBox `192.168.56.1`) |
| Host'ta RNDIS / USB Ethernet gadget cihazı | ❌ yok |

### Teşhis

**`carrier = 0` → PYNQ-Z2'nin RJ45 portuna Ethernet kablosu takılı değil.**

`192.168.2.99`, PYNQ'nun DHCP bulamadığında düştüğü **statik yedek adrestir** — arayüz DOWN
olduğu için bu adres kullanılamaz. USB bağlantısı yalnızca UART (ve JTAG) taşıyor; PYNQ-Z2'de
USB üzerinden ağ (RNDIS gadget) yok, host'ta da böyle bir cihaz görünmüyor.

### Çözüm

RJ45 portundan **Ethernet kablosuyla** yönlendiriciye bağlan. Kart o zaman DHCP ile
`192.168.1.x` alır (host'un Wi-Fi'ıyla aynı ağ) ve Jupyter `http://<kart-ip>:9090` üzerinden
erişilebilir olur. Yeni IP seri porttan `hostname -I` ile öğrenilir.

**Faz 2'yi engellemiyor** — Faz 2 (HLS çekirdek) karta hiç dokunmuyor (Anayasa Prensip V).
Bu yalnızca **Faz 5**'in (Zynq PS entegrasyonu, kartta koşum) ön koşulu.

### Henüz doğrulanmayanlar

- [ ] Jupyter arayüzü ağ üzerinden açılıyor mu — **Ethernet kablosu bekliyor**
- [ ] Örnek overlay yükleniyor mu — Jupyter erişimine bağlı
