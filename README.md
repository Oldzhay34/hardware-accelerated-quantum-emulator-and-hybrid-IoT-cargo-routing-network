# qir-engine — Kuantum-Esinli Rota Optimizasyon Motoru

Bir bitirme projesi: PYNQ-Z2 (Xilinx Zynq-7000) üzerinde çalışan bir statevector emülasyon çekirdeğini
Vitis HLS ile donanımda hızlandırmak; sonucu Qiskit altın referansına karşı doğrulamak; ve CPU referansına
karşı gecikme ile enerji eksenlerinde **gerçek ölçümle** karşılaştırmak. Bkz. [Anayasa](.specify/memory/constitution.md).

## Şu anki durum

**Faz 0** tamamlandı (0.1–0.7). **Faz 1 — Veri Hattı ve Altın Referans** MVP bitti, Phase 5–6 sürüyor. Bkz. [specs/001-veri-hatti-altin-referans/](specs/001-veri-hatti-altin-referans/).

| Bileşen | Durum |
|---|---|
| Altın referans QAOA (`services/reference/`) | ✅ 5 durak/16 kübit, kaba kuvvetle doğrulanmış |
| QUBO formülasyonu (`services/qubo/`) | ✅ |
| Mesafe matrisi servisi (`services/matrix/`) | ✅ gerçek OSRM'e karşı doğrulandı |
| Tek komutla kurulum | ⏳ bu bölüm |

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

## Faz 1 — hızlı başlangıç

**Ön koşullar**: Docker, Python 3.13 (proje `.venv`'i), ~1 GB boş disk.

> ⚠️ **Git Bash kullanıyorsan**: `export MSYS_NO_PATHCONV=1` şart. Aksi halde Docker konteyner
> içindeki yolları (`/opt/car.lua` gibi) Windows yoluna çevirip hata verir — bkz.
> [research.md R-4](specs/001-veri-hatti-altin-referans/research.md#r-4--windowsgit-bash-tuzağı--msys-yol-dönüşümü).

```powershell
# 1) Bağımlılıklar (bir kez)
uv pip install --python .venv\Scripts\python.exe qiskit-aer pytest fastapi uvicorn httpx

# 2) OSM verisini indir + MD5 doğrula
.\scripts\fetch_osm.ps1

# 3) OSRM'i hazırla (ön işleme ~192 sn) ve başlat
docker compose -f infra/docker/docker-compose.yml --profile prepare up osrm-prepare
docker compose -f infra/docker/docker-compose.yml up -d osrm matrix

# 4) Altın referansı üret (5 durak, p=1 ve p=2)
.\scripts\run_reference.ps1 -Stops 5 -P 1,2 -Seed 42

# 5) Testler
.venv\Scripts\python.exe -m pytest services -v
```

**Beklenen çıktı**: `docs/measurements/reference_<tarih>_<githash>_p<N>.{npy,json}` — Faz 2'nin
genlik-genlik kıyası için ham genlik vektörü. Ayrıntılı senaryolar:
[quickstart.md](specs/001-veri-hatti-altin-referans/quickstart.md).

**HLS tarafı** (Faz 2+) — gcc (MinGW) ve Vitis HLS kurulu olmalı: `gcc --version`

## Anayasa

Bu proje altı bağlayıcı ilkeyle yönetilir (bkz. [.specify/memory/constitution.md](.specify/memory/constitution.md)):
onay kapısı · ölçüm dürüstlüğü · donanım bütçesi önce · altın referans · donanımsız süreklilik · 14 hafta kısıtı.
