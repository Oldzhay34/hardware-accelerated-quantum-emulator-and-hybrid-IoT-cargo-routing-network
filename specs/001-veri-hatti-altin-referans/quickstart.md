# Quickstart — Faz 1 Doğrulama Kılavuzu

**Faz**: 1 — Veri Hattı ve Altın Referans · **Tarih**: 2026-09-13

> Bu belge **uygulama kodu içermez** — Faz 1 bittiğinde her şeyin gerçekten çalıştığını kanıtlayan koşulabilir senaryoları tarif eder.
> Arayüz ayrıntıları: [contracts/](contracts/) · Varlıklar: [data-model.md](data-model.md)

---

## Ön koşullar

| Gereksinim | Doğrulanan sürüm | Kontrol |
|---|---|---|
| Docker | 29.5.3, linux/x86_64 | `docker info` |
| Python | 3.13.12 (proje venv'i) | `.venv\Scripts\python.exe --version` |
| Disk | ≥ 1 GB boş (imaj 151 MB + veri 282 MB) | |
| İnternet | İlk kurulum için (OSM dökümü 44,6 MB) | |

**PYNQ-Z2 kartı GEREKMEZ** — Faz 1'in hiçbir adımı donanıma dokunmaz (Anayasa Prensip V).

### ⚠️ Git Bash kullanıyorsan

```bash
export MSYS_NO_PATHCONV=1
```

Bu olmadan Git Bash, konteyner **içindeki** yolları Windows yollarına çevirir ve `osrm-extract -p /opt/car.lua` şu hatayı verir: `the argument ('C:/Program Files/Git/opt/car.lua') ... is invalid`. PowerShell kullanıyorsan gerekmez (R-4).

---

## Senaryo 1 — Veri hattını sıfırdan kur

**Amaç**: Temiz bir makinede tek komutla ayağa kalkma (spec US4, SC-005).

```powershell
.\scripts\fetch_osm.ps1          # OSM dökümünü indirir, MD5 doğrular
docker compose -f infra/docker/docker-compose.yml up osrm-prepare
docker compose -f infra/docker/docker-compose.yml up -d osrm matrix
```

**Beklenen sonuç**:
- `fetch_osm.ps1` MD5'i `cb101d9243c3c605907e94f4266159c2` ile karşılaştırır; **tutmazsa hata verir ve durur** (spec FR-005).
- `osrm-prepare` üç adımı koşar ve çıkış kodu 0 verir.
- `curl http://localhost:8090/health` → `{"status":"ok","osrm":"reachable",...}`

**Ölçülen taban çizgisi** (bu makinede, tahmin değil): ön işleme **192 sn**, tepe **435 MiB**, üretilen veri **282 MB**.

---

## Senaryo 2 — Determinizm kanıtı

**Amaç**: Aynı girdi bit-birebir aynı çıktıyı verir (spec SC-001, Prensip II).

```powershell
# Aynı istek iki kez, iki ayrı dosyaya
curl -s -X POST localhost:8090/matrix -H "Content-Type: application/json" -d "@ornek_30_durak.json" -o m1.json
curl -s -X POST localhost:8090/matrix -H "Content-Type: application/json" -d "@ornek_30_durak.json" -o m2.json
```

**Beklenen**: `durations` alanları **birebir aynı**; ikinci yanıtta `cache_hit: true`.

**Çevrimdışı testi** (spec SC-004): Ağ kesildikten sonra aynı istek yine aynı matrisi döndürmeli — önbellekten.

---

## Senaryo 3 — Gerçek yol ağı kullanıldığının kanıtı

**Amaç**: Kuş uçuşu değil, gerçek sürüş süresi (spec FR-002).

Matristeki asimetrik çift sayısı sayılır: `durations[i][j] != durations[j][i]`.

**Beklenen**: Asimetrik çift oranı **yüksek** olmalı. Bu makinede ölçüldü: **434/435**. Kuş uçuşu mesafe kullanılsaydı 0/435 olurdu — bu sayı tek başına ayırt edici bir kanıttır.

Ayrıca 30×30 matriste **900/900** hücre dolu olmalı; `null` varsa servis zaten 422 döndürmeliydi.

---

## Senaryo 4 — QUBO doğruluğu

**Amaç**: Formülasyon hem kuantum hem klasik çözücü için doğru (spec US3).

```powershell
.venv\Scripts\python.exe -m pytest services/qubo/tests -v
```

**Beklenen testler geçer**:
- Geçerli turların enerji sıralaması = gerçek tur uzunluğu sıralaması.
- Kısıt ihlal eden **her** atama, geçerli **her** turdan yüksek enerjili (SC-003, ihlal sayısı **0**).
- `penalty_A`, `max(durations)` değişince birlikte değişir (sabit gömülü değil).

---

## Senaryo 5 — Altın referans, kaba kuvvetle doğrulanır

**Amaç**: Bu fazın ana çıktısı güvenilir (spec US1, SC-002).

```powershell
.\scripts\run_reference.ps1 -Stops 5 -P 1 -Seed 42
.\scripts\run_reference.ps1 -Stops 5 -P 2 -Seed 42
```

**Beklenen**:
- QAOA'nın bulduğu en iyi tur, kaba kuvvet optimaliyle **birebir aynı** (SC-002: %100).
- Kaba kuvvet **24 tur** dolaşır — `(5−1)!`, `5!` değil ([data-model.md §5](data-model.md)).
- Aynı tohumla iki koşum aynı sonucu verir.
- Çıktı `docs/measurements/reference_<tarih>_<githash>_p<N>.npy` + `.json` olarak **damgalı** yazılır (VR-03).

**Ölçülen taban çizgisi**: 16 kübit statevector, Aer ile **8,9 ms / 0,09 MB**.

---

## Senaryo 6 — Faz 2'nin ihtiyacı olan yüzey hazır mı

**Amaç**: Genlik-genlik kıyası mümkün (spec SC-008, FR-014, FR-017).

```python
from services.reference import amplitudes
ref = amplitudes.load("docs/measurements/reference_..._p2")

assert ref.amplitudes.dtype == np.complex128
assert len(ref.amplitudes) == 2**16          # 65536
assert abs(np.linalg.norm(ref.amplitudes) - 1.0) < 1e-9
assert ref.qubit_order in ("little", "big")  # DG-02 riskine karşı AÇIKÇA kayıtlı
```

**Neden kritik**: Faz 2 bu dosyayı doğrudan okuyacak. `qubit_order` yazılı değilse, "fidelity ≈ 0 ama genlik büyüklükleri doğru" imzasıyla saatler kaybedilir ([DG-02](../../docs/risk-register.md) bu riski **yüksek olasılıklı** işaretliyor).

---

## Tam doğrulama (hepsi)

```powershell
.venv\Scripts\python.exe -m pytest services -v
```

**Kapsam**: `qubo` birim testleri + `reference` doğrulama + `matrix` entegrasyon testi (OSRM ayakta olmalı).

---

## Sık karşılaşılan sorunlar

| Belirti | Sebep | Çözüm |
|---|---|---|
| `the argument ('C:/Program Files/Git/...')` | Git Bash yol dönüşümü | `export MSYS_NO_PATHCONV=1` (R-4) |
| `422 unreachable_pair` | Durak, yol ağına bağlı olmayan bir noktada | Durağı taşı — sessizce doldurmak **yasak** (Prensip II) |
| MD5 uyuşmazlığı | OSM dökümü değişmiş | Beklenen değer bilinçli güncellenmeli; **otomatik kabul edilmez** (FR-005) |
| `ValueError: n_stops > 5` | Altın referans tavanı | Beklenen davranış — 16 kübit sınırı (Prensip III) |
