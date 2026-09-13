# Implementation Plan: Faz 1 — Veri Hattı ve Altın Referans

**Branch**: `001-veri-hatti-altin-referans` | **Date**: 2026-09-13 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `specs/001-veri-hatti-altin-referans/spec.md`

---

## Summary

İki çıktı üretilecek: (1) İstanbul OSM verisinden N×N gerçek sürüş-süresi matrisi döndüren konteynerli bir servis, (2) 5 duraklı TSP için, Faz 2'nin donanım çekirdeğini doğrulayacak **altın referans** QAOA çözücüsü.

**Teknik yaklaşım**: OSRM'in MLD boru hattı (extract → partition → customize) sabitlenmiş bir OSM dökümünden önceden derlenir; FastAPI sarmalayıcı `/table` ucunu çağırıp sonucu `.npy` + `.json` olarak önbelleğe yazar. QUBO dönüşümü saf NumPy ile yapılır. Altın referans Qiskit + Aer ile koşar ve **ham genlik vektörünü** diske yazar — Faz 2'nin genlik-genlik kıyası buna bağlıdır.

Teknoloji seçimleri ölçüme dayalı olarak yapıldı ve **kullanıcı tarafından 2026-09-13'te onaylandı** (Anayasa Prensip I). Ayrıntı: [research.md](research.md).

---

## Technical Context

**Language/Version**: Python 3.13.12 (proje venv'i mevcut)

**Primary Dependencies**:
- Mesafe matrisi: **OSRM** (`osrm/osrm-backend:latest`, 151 MB, BSD-2-Clause) — Docker ile
- Servis sarmalayıcı: FastAPI + uvicorn
- Sayısal: NumPy (kurulu)
- Kuantum: **Qiskit 2.5.2** (kurulu) + **qiskit-aer 0.17.2** (kurulacak) — Apache-2.0

**Storage**: Dosya sistemi. Matris önbelleği `data/matrices/<hash>.npy` + `.json`; altın referans çıktısı `docs/measurements/` altına damgalı yazılır.

**Testing**: pytest (kurulacak)

**Target Platform**: Windows 11 geliştirme makinesi + Docker Desktop (linux/x86_64 konteynerler). Donanım (PYNQ-Z2) **gerekmez** — Anayasa Prensip V.

**Project Type**: Konteynerli servis + Python kütüphanesi/CLI (monorepo içinde, [repo-conventions.md](../../docs/repo-conventions.md))

**Performance Goals** (ölçülmüş taban çizgileri, hedef değil):
- OSRM ön işleme: 192 sn / tepe 435 MiB (İstanbul 44,6 MB extract)
- N=30 matris gecikmesi: medyan 0,383 sn
- 16 kübit statevector (Aer): 8,9 ms / 0,09 MB

**Constraints**:
- **Determinizm zorunlu** (Prensip II): OSM sürümü MD5 ile pinlenir, tüm rastgelelik tohumlanır
- Altın referans 5 durak = **(5−1)² = 16 kübit** (Prensip III tavanı)
- Ham genliklere erişim **zorunlu** (Faz 2 ön koşulu)
- Ölçülmemiş sayı raporlanamaz (Prensip II)

**Scale/Scope**: Matris servisi N ≤ 30 durak; altın referans N = 5 durak.

---

## Constitution Check

*GATE: Phase 0 öncesi geçmeli, Phase 1 sonrası yeniden denetlenmeli.*

| # | İlke | Bu fazda nasıl karşılanıyor | Durum (ön) | Durum (tasarım sonrası) |
|---|---|---|---|---|
| I | **Onay kapısı** | OSRM ve Qiskit+Aer seçimleri iki karşılaştırma tablosu + ölçümle sunuldu, kullanıcı 2026-09-13'te yazılı onay verdi | ✅ | ✅ |
| II | **Ölçüm dürüstlüğü** | Plandaki her performans sayısı bu makinede ölçüldü; tahmini değer yok. Determinizm: OSM MD5 pinli, tohum sabit, matris önbelleği commit'lenir | ✅ | ✅ |
| III | **Donanım bütçesi önce** | 5 durak = 16 kübit, tavana birebir oturuyor. Altın referans complex128 (1,0 MB) kullanır — bu PYNQ BRAM'ine sığmaz, **ama referans CPU'da koşuyor**, kısıt Faz 2'nin çekirdeğine ait. Referansın formatı Faz 2'nin dar formatlarıyla (float32/Q1.15) kıyaslanabilir olmalı → `research.md` R-5 | ✅ | ✅ |
| IV | **Altın referans** | Bu fazın **ana çıktısı** budur. Qiskit, Prensip IV'te adıyla bağlayıcı; seçim bunu doğruluyor | ✅ | ✅ |
| V | **Donanımsız süreklilik** | Faz 1'in hiçbir adımı PYNQ-Z2 gerektirmez; kart elde olmasa da tamamı koşar | ✅ | ✅ |
| VI | **14 hafta kısıtı** | Faz 1 takvimde H1–H2, M etiketli. Kapsam 5 durak + 30 durakla sınırlı; genişletme yok | ✅ | ✅ |

**Sonuç: GEÇTİ.** Complexity Tracking tablosunda gerekçelendirilmesi gereken ihlal yok.

---

## Project Structure

### Documentation (this feature)

```text
specs/001-veri-hatti-altin-referans/
├── plan.md              # Bu dosya
├── research.md          # Phase 0 çıktısı — ölçümler ve kararlar
├── data-model.md        # Phase 1 çıktısı
├── quickstart.md        # Phase 1 çıktısı
├── contracts/           # Phase 1 çıktısı — HTTP ve Python arayüz sözleşmeleri
└── tasks.md             # /speckit-tasks çıktısı (bu komut ÜRETMEZ)
```

### Source Code (repository root)

Mevcut monorepo iskeletine ([repo-conventions.md](../../docs/repo-conventions.md)) oturuyor — yeni üst dizin açılmıyor.

```text
services/matrix/                 # Mesafe matrisi servisi (FastAPI + OSRM sarmalayıcı)
├── app/
│   ├── main.py                  # FastAPI uygulaması, /matrix ucu
│   ├── osrm_client.py           # OSRM /table çağrısı
│   ├── cache.py                 # .npy + .json önbellek, anahtar = koordinat+veri sürümü
│   └── config.py                # Ortam değişkenleri, açılışta doğrulama
└── tests/
    ├── test_cache.py
    └── test_matrix_api.py       # entegrasyon (OSRM ayakta)

services/qubo/                   # Problem formülasyonu — saf Python, servis değil
├── qubo.py                      # matrix_to_qubo(), ceza katsayısı türetimi
├── brute_force.py               # 5! = 120 tur, mutlak gerçek
└── tests/
    ├── test_qubo_energy.py      # enerji ↔ tur uzunluğu tutarlılığı
    └── test_penalty.py          # kısıt ihlali > her geçerli tur

services/reference/              # Altın referans
├── qaoa_reference.py            # p=1, p=2; genlik vektörü + histogram + en iyi tur
├── amplitudes.py                # ham genlikleri diske yazma (Faz 2 kıyası için)
└── tests/
    └── test_reference.py        # brute-force ile birebir doğrulama

infra/docker/
├── docker-compose.yml           # osrm-prepare (bir kez) + osrm-routed + matrix servisi
└── osrm/prepare.sh              # extract → partition → customize

scripts/
├── fetch_osm.ps1                # OSM dökümünü indir + MD5 doğrula
└── run_reference.ps1            # Altın referansı üret, çıktıyı damgala

data/
├── osm/                         # Pinlenmiş .pbf (git'e GİRMEZ, .gitignore)
└── matrices/                    # Önbelleklenen matrisler (commit EDİLİR — determinizm)
```

**Structure Decision**: Mevcut monorepo korunuyor. `services/` altında üç ayrı birim: `matrix` (konteynerli servis), `qubo` (saf kütüphane), `reference` (saf kütüphane + CLI). Ayrım, Faz 10'un klasik çözücüsünün `qubo`'yu **aynen** yeniden kullanabilmesi için (spec FR-011) — kıyasın adil olması buna bağlı. Hexagonal katmanlama bu fazda **uygulanmıyor**: üç birim de tek sorumluluklu ve dış bağımlılıkları (OSRM HTTP, dosya sistemi) zaten tek bir modülde izole; Faz 3'te gerçek mikroservisler doğduğunda [CLAUDE.md](../../CLAUDE.md)'deki hexagonal kural devreye girer.

---

## Complexity Tracking

> Constitution Check ihlal üretmedi — bu tablo boş.

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| — | — | — |
