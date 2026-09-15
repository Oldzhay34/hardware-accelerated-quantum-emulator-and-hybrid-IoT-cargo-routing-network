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

### Henüz doğrulanmayanlar

- [ ] Jupyter arayüzü ağ üzerinden açılıyor mu
- [ ] Örnek overlay yükleniyor mu
- [ ] Kartın IP adresi / ağ erişimi
