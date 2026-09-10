# qir-engine — Kuantum-Esinli Rota Optimizasyon Motoru

Bir bitirme projesi: PYNQ-Z2 (Xilinx Zynq-7000) üzerinde çalışan bir statevector emülasyon çekirdeğini
Vitis HLS ile donanımda hızlandırmak; sonucu Qiskit altın referansına karşı doğrulamak; ve CPU referansına
karşı gecikme ile enerji eksenlerinde **gerçek ölçümle** karşılaştırmak. Bkz. [Anayasa](.specify/memory/constitution.md).

## Şu anki durum

**Faz 0 — Kapsam Triyajı** çalışıyor, onay bekliyor. Bkz. [specs/000-kapsam-takvim/](specs/000-kapsam-takvim/).

| Alt dal | Durum |
|---|---|
| 0.1 Risk kaydı ve karar tarihleri | ✅ [docs/risk-register.md](docs/risk-register.md) |
| 0.2 Depo iskeleti ve çalışma düzeni | ✅ bu commit |
| 0.3 – 0.7 | ⏳ sırada |

## Mimari (taslak — Faz 3.1'de kesinleşecek)

```
Saha (ESP32) ──MQTT──▶ L2 Backend ──▶ FPGA Agent (PYNQ) ──▶ HLS Çekirdek (statevector)
                            │                                        │
                            ▼                                        ▼
                     Karar Motoru                          Qiskit Altın Referans
                            │                                        │
                            └──────────▶ Karşılaştırma / Kıyas ◀─────┘
                                                │
                                                ▼
                                        Panel (React)
```

## Depo haritası

Bkz. [docs/repo-conventions.md](docs/repo-conventions.md) §2 — dizin düzeni ve her dizinin hangi fazda büyüyeceği.

## Yerel ayağa kaldırma

**Henüz yok.** `infra/docker/docker-compose.yml` hazır olduğunda (Faz 3+) buraya tek komut yazılacak. Şimdilik:

```bash
# Python tarafı (Qiskit altın referans, ölçüm analizi)
.venv\Scripts\activate   # Windows

# HLS tarafı — gcc (MinGW) ve Vitis HLS kurulu olmalı
gcc --version
```

## Anayasa

Bu proje altı bağlayıcı ilkeyle yönetilir (bkz. [.specify/memory/constitution.md](.specify/memory/constitution.md)):
onay kapısı · ölçüm dürüstlüğü · donanım bütçesi önce · altın referans · donanımsız süreklilik · 14 hafta kısıtı.
