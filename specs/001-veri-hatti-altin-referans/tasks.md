---

description: "Faz 1 — Veri Hattı ve Altın Referans görev listesi"
---

# Tasks: Faz 1 — Veri Hattı ve Altın Referans

**Input**: `specs/001-veri-hatti-altin-referans/` tasarım belgeleri
**Prerequisites**: [plan.md](plan.md), [spec.md](spec.md), [research.md](research.md), [data-model.md](data-model.md), [contracts/](contracts/)

**Tests**: **DAHİL.** Faz 1 promptu pytest paketini açıkça istiyor ("QUBO enerjisi ile tur uzunluğu tutarlılığı, altın referansın optimali bulma oranı, matris servisi entegrasyon testi").

## SIRADAKİ

**Hedef (tek cümle)**: MVP (Phase 1-4, T001-T027) TAMAMLANDI — altın referans üretiliyor ve kaba kuvvetle doğrulanıyor; sırada Phase 5 (OSRM matris servisi, T028-T038).
**Dokunulacak dosyalar**: `services/matrix/app/main.py`, `services/matrix/app/osrm_client.py`, `services/matrix/app/cache.py`, `infra/docker/docker-compose.yml`
**Bilinen tuzak**: Git Bash'te `MSYS_NO_PATHCONV=1` şart (R-4). QAOA parametreleri şu an OPTİMİZE EDİLMİYOR (rastgele tohumlu) — optimali ölçme olasılığı p=1'de 4e-6, p=2'de 3e-5 çıktı; bkz. açık soru.
**Son güncelleme**: 2026-09-13, Faz 1

---

## Format: `[ID] [P?] [Story] Açıklama`

- **[P]**: Paralel koşabilir (farklı dosya, bekleyen bağımlılık yok)
- **[Story]**: US1…US4 — [spec.md](spec.md) kullanıcı hikâyeleri

## ⚠️ Faz sırası neden öncelik sırası değil

[spec.md](spec.md)'de US1 (altın referans) ve US2 (mesafe matrisi) **P1**, US3 (QUBO) **P2**. Ama US1 teknik olarak US3'ü **tüketiyor** — QUBO olmadan çözülecek bir problem yok. Öncelik *değeri*, bağımlılık ise *inşa sırasını* belirler.

**Bu yüzden sıra: US3 → US1 → US2 → US4.**

Kritik kazanç: US1, **gerçek OSRM matrisi beklemeden** elle yazılmış 5×5 fixture matrisiyle tamamlanabilir ve doğrulanabilir. Referansın doğruluğu kaba kuvvetle ölçülür ve bu **herhangi bir** matriste geçerlidir. Böylece Faz 2'nin beklediği çıktı, veri hattı hazır olmadan üretilir — [risk TK-01](../../docs/risk-register.md) ("H2 sonunda altın referans koşmuyorsa zincir kayar") bu şekilde erken kapatılır.

---

## Phase 1: Setup

**Amaç**: Bağımlılıklar ve dizin yapısı.

- [X] T001 `uv pip install --python .venv\Scripts\python.exe qiskit-aer pytest fastapi uvicorn httpx` ile bağımlılıkları kur (qiskit 2.5.2 ve numpy zaten kurulu; qiskit-aer 0.17.2 ölçümde doğrulandı)
- [X] T002 [P] `services/qubo/`, `services/reference/`, `services/matrix/app/` ve her birinin `tests/` alt dizinini `__init__.py` ile oluştur
- [X] T003 [P] `.gitignore`'a `data/osm/` ekle (OSM dökümü 44,6 MB — commit edilmez); `data/matrices/` **commit edilir**, hariç tutulmaz
- [X] T004 [P] Depo kökünde `pytest.ini` oluştur: `testpaths = services`, `pythonpath = .`

---

## Phase 2: Foundational (Bloklayıcı ön koşullar)

**Amaç**: Tüm hikâyelerin ihtiyaç duyduğu ortak zemin.

**⚠️ Bu faz bitmeden hiçbir kullanıcı hikâyesi başlayamaz.**

- [X] T005 `scripts/fetch_osm.ps1` yaz: BBBike İstanbul dökümünü `data/osm/Istanbul.osm.pbf` olarak indir, MD5'i `cb101d9243c3c605907e94f4266159c2` ile karşılaştır, **tutmazsa hata verip dur** (spec FR-005 — "en güncel veriyi indir" davranışı yasak)
- [X] T006 [P] `services/conftest.py` içinde `fixture_matrix_5x5` pytest fixture'ı oluştur: elle yazılmış, **asimetrik**, köşegeni 0 olan 5×5 `float64` matris. US1'in OSRM beklemeden ilerlemesini sağlar
- [X] T007 [P] `services/common/stamp.py` yaz: çıktı dosyalarına tarih + `git rev-parse --short HEAD` + konfigürasyon damgası basan yardımcı ([risk VR-03](../../docs/risk-register.md) gereği — damgasız ölçüm geçersiz)
- [X] T008 [P] `docs/measurements/.gitkeep` ve `data/matrices/.gitkeep` oluştur

**Checkpoint**: Zemin hazır — US3 başlayabilir.

---

## Phase 3: User Story 3 — QUBO formülasyonu (Priority: P2, teknik önkoşul)

**Goal**: Mesafe matrisini, hem kuantum hem klasik çözücünün kabul ettiği ortak probleme çeviren, doğruluğu kanıtlanmış bir dönüştürücü.

**Independent Test**: `fixture_matrix_5x5` üzerinde çalışır — OSRM gerekmez. Geçerli turların enerji sıralaması gerçek tur uzunluğu sıralamasıyla aynı olmalı ve kısıt ihlal eden **her** atama geçerli **her** turdan yüksek enerjili olmalı.

### Tests for User Story 3 ⚠️ (önce yaz, BAŞARISIZ olduklarını gör)

- [X] T009 [P] [US3] `services/qubo/tests/test_qubo_energy.py`: geçerli turların enerji sıralaması = gerçek tur uzunluğu sıralaması (spec FR-010)
- [X] T010 [P] [US3] `services/qubo/tests/test_penalty.py`: kısıt ihlal eden **her** atama, geçerli **her** turdan yüksek enerjili — ihlal sayısı **0** olmalı (spec SC-003)
- [X] T011 [P] [US3] `services/qubo/tests/test_penalty.py` içine ikinci test: `max(durations)` değişince `penalty_A` de değişir (sabit gömülü değer **yok**, spec FR-009)
- [X] T012 [P] [US3] `services/qubo/tests/test_brute_force.py`: N=5 için tur sayısı **tam 24** olmalı — `(N−1)!`, `5!=120` **değil** ([data-model.md §5](data-model.md))

### Implementation for User Story 3

- [X] T013 [US3] `services/qubo/qubo.py` içinde `QUBOProblem` veri sınıfı: alanlar `Q` (`ndarray (V,V) float64`, simetrik), `penalty_A` (float), `n_stops` (int), `var_map` (`dict[(city,time) → index]`). `V = (n_stops − 1)²`
- [X] T014 [US3] `services/qubo/qubo.py` içinde `matrix_to_qubo(durations, *, epsilon=0.1)`: one-hot TSP QUBO'su üretir, başlangıç şehrini sabitler, `penalty_A = (1+epsilon) * max(durations)` olarak **türetir** (R-6). `durations` kare değilse / köşegen ≠ 0 ise / `inf`/`nan` içeriyorsa `ValueError`
- [X] T015 [P] [US3] `services/qubo/qubo.py` içinde `energy(problem, assignment) -> float` ve `assignment_to_tour(problem, assignment) -> list[int] | None` — kısıt ihlalinde **`None`** döner, "en yakın geçerli tur" uydurmaz ([contracts/python-api.md](contracts/python-api.md))
- [X] T016 [US3] `services/qubo/brute_force.py` içinde `solve(durations) -> BruteForceResult`: başlangıç sabit, **`(N−1)!` tur** dolaşır (N=5 → 24). N > 8 ise `ValueError`

**Checkpoint**: QUBO doğrulanmış — US1 başlayabilir.

---

## Phase 4: User Story 1 — Altın referans (Priority: P1) 🎯 MVP · Faz 2'nin beklediği çıktı

**Goal**: Faz 2'nin donanım çekirdeğini doğrulayacak, kaba kuvvetle kanıtlanmış referans çözüm — **ham genlik vektörüyle birlikte**.

**Independent Test**: `fixture_matrix_5x5` ile koşar, OSRM gerekmez. QAOA'nın bulduğu en iyi tur kaba kuvvet optimaliyle **birebir** eşleşmeli; aynı tohum aynı sonucu vermeli; ham genlikler `complex128` ve normu 1 olmalı.

### Tests for User Story 1 ⚠️

- [X] T017 [P] [US1] `services/reference/tests/test_reference.py`: QAOA'nın en iyi turu, kaba kuvvet optimaliyle **birebir aynı** (spec SC-002, %100)
- [X] T018 [P] [US1] `services/reference/tests/test_determinism.py`: aynı `(problem, p, seed)` iki koşumda **bit-birebir aynı** `amplitudes` üretir (spec FR-018)
- [X] T019 [P] [US1] `services/reference/tests/test_amplitudes.py`: `amplitudes.dtype == complex128`, `len == 2**16`, `abs(norm − 1.0) < 1e-9` (spec SC-008)
- [X] T020 [P] [US1] `services/reference/tests/test_amplitudes.py` içine ikinci test: kaydet→yükle turu metadata'yı kayıpsız korur, `qubit_order` alanı `"little"` veya `"big"` olarak **dolu** ([risk DG-02](../../docs/risk-register.md))
- [X] T021 [P] [US1] `services/reference/tests/test_reference.py` içine tavan testi: `n_stops = 6` verildiğinde `ValueError` — 16 kübit sınırı (Anayasa Prensip III)

### Implementation for User Story 1

- [X] T022 [US1] `services/reference/qaoa_reference.py` içinde `ReferenceResult` veri sınıfı: `amplitudes` (`ndarray complex128 (2**V,)`), `probabilities`, `best_tour`, `best_energy`, `p`, `seed`, `qubit_order`, `backend`
- [X] T023 [US1] `services/reference/qaoa_reference.py` içinde `run(problem, *, p, seed, shots=None)`: Qiskit `QAOAAnsatz` + `AerSimulator(method="statevector")` ile koşar. **`problem.n_stops > 5` ise `ValueError`**. `shots=None` → tam statevector (varsayılan)
- [X] T024 [US1] `services/reference/qaoa_reference.py` içinde `qubit_order` alanını Qiskit'in konvansiyonunu **ölçerek** doldur (varsayma — tek kübitlik bilinen bir devreyle doğrula), [risk DG-02](../../docs/risk-register.md)
- [X] T025 [US1] `services/reference/amplitudes.py` içinde `save(result, path)` / `load(path)`: `<path>.npy` (complex128) + `<path>.json` (metadata). Dosya adı T007'nin damgalayıcısını kullanır
- [X] T026 [US1] `scripts/run_reference.ps1` yaz: `-Stops`, `-P`, `-Seed` parametreleriyle referansı üretir, çıktıyı `docs/measurements/reference_<tarih>_<githash>_p<N>` olarak yazar, **gerçek süre ve bellek** raporlar (tahmin yazmaz — Prensip II)
- [X] T027 [US1] p=1 ve p=2 için referansı üret, optimali bulma **oranını ölç ve raporla** (spec FR-016, SC-006 — hedef değer dayatılmaz, ölçüm dürüstlüğü esastır)

**Checkpoint**: 🎯 **Faz 2 artık başlayabilir.** Altın referans ve ham genlikler hazır.

---

## Phase 5: User Story 2 — Mesafe matrisi servisi (Priority: P1)

**Goal**: İstanbul'un gerçek yol ağından, tekrarlanabilir N×N sürüş-süresi matrisi.

**Independent Test**: Aynı durak listesi iki kez gönderildiğinde matrisler **bit-birebir aynı**; ağ kesikken önbellekten aynı sonuç dönüyor.

### Tests for User Story 2 ⚠️

- [X] T028 [P] [US2] `services/matrix/tests/test_cache.py`: aynı girdi → aynı önbellek anahtarı; **farklı sıradaki** aynı noktalar → **farklı** anahtar (spec edge case: yanlış önbellek isabeti)
- [X] T029 [P] [US2] `services/matrix/tests/test_matrix_api.py`: N < 2 ve N > 30 → `400 stop_count_out_of_range` ([contracts/matrix-api.md](contracts/matrix-api.md))
- [X] T030 [P] [US2] `services/matrix/tests/test_matrix_api.py` içine: ulaşılamayan çift → **`422 unreachable_pair`**; matris üretilmez, büyük sayıyla doldurulmaz (spec FR-007, Prensip II)
- [X] T031 [P] [US2] `services/matrix/tests/test_matrix_api.py` içine entegrasyon testi: OSRM ayaktayken 30 durak → 30×30, **900/900 hücre dolu**, asimetrik çift oranı yüksek (spec FR-002 kanıtı)

### Implementation for User Story 2

- [X] T032 [US2] `services/matrix/app/config.py`: `OSRM_URL`, `OSM_MD5`, `MATRIX_CACHE_DIR` ortam değişkenlerini okur ve **eksikse servis çalışmayı REDDEDER** (sessiz varsayılanla kalkmaz — [repo-conventions.md §7](../../docs/repo-conventions.md))
- [X] T033 [US2] `services/matrix/app/osrm_client.py`: OSRM `/table/v1/driving/{lon,lat;...}` çağrısı. Yanıtta `null` süre varsa `UnreachablePairError` fırlatır
- [X] T034 [US2] `services/matrix/app/cache.py`: anahtar `sha256(json(points) + osm_md5)`; `data/matrices/<anahtar>.npy` + `.json` yazar/okur
- [X] T035 [US2] `services/matrix/app/main.py`: FastAPI `POST /matrix` — girdi `points` (**2 ≤ N ≤ 30**), `use_cache` (varsayılan `true`); yanıt `durations`, `n`, `cache_hit`, `osm_md5`, `engine`, `cache_key`, `elapsed_ms`
- [X] T036 [US2] `services/matrix/app/main.py` içine `GET /health`: OSRM erişilemiyorsa `503` + `"osrm": "unreachable"`
- [X] T037 [P] [US2] `infra/docker/osrm/prepare.sh`: `osrm-extract -p /opt/car.lua` → `osrm-partition` → `osrm-customize`. Başına **`MSYS_NO_PATHCONV=1` uyarısı** yorum olarak yazılır (R-4)
- [X] T038 [US2] `infra/docker/docker-compose.yml`: `osrm-prepare` (bir kez koşar), `osrm-routed` (port 5000), `matrix` (port 8080) servisleri; OSM dökümü ve önbellek dizini bind-mount

**Checkpoint**: Gerçek veri hattı çalışıyor; US1 artık fixture yerine gerçek matrisle de koşabilir.

---

## Phase 6: User Story 4 — Tek komutla kurulabilirlik (Priority: P3)

**Goal**: Temiz bir makinede tek komutla ayağa kalkma.

**Independent Test**: Depo temiz bir dizine klonlanır, README'deki komut koşulur, altın referans üretilir. Süre **ölçülür ve yazılır**.

- [ ] T039 [US4] `README.md`'ye "Faz 1 — hızlı başlangıç" bölümü ekle: ön koşullar, tek komut, beklenen çıktı. Git Bash kullananlar için `MSYS_NO_PATHCONV=1` uyarısı
- [ ] T040 [US4] `scripts/setup_faz1.ps1`: `fetch_osm.ps1` → `docker compose up osrm-prepare` → `docker compose up -d` zincirini tek komutta koşar
- [ ] T041 [US4] Temiz bir dizinde uçtan uca kurulumu **gerçekten koş**, süreyi ölç ve README'ye yaz (spec SC-005 — tahmin değil, ölçüm)

---

## Phase 7: Polish & Cross-Cutting

- [ ] T042 [P] `docs/measurements/faz1-olcumler.md`: OSRM ön işleme, matris gecikmesi, referans süresi — hepsi **ölçülmüş** değerlerle (spec SC-007: raporda tahmini tek sayı bulunmaz)
- [ ] T043 [P] `docs/decisions/dead-ends.md`'i güncelle — Faz 1'de elenen bir yol varsa yaz (GraphHopper'ın matris API'sinin olmaması buraya düşer)
- [ ] T044 [quickstart.md](quickstart.md)'teki 6 senaryonun tamamını koş ve geçtiğini doğrula
- [ ] T045 [P] [faz-sonu-kontrol.md](../../docs/faz-sonu-kontrol.md) listesini uygula: ADR'ler yazıldı mı, CLAUDE.md'nin "şu anki faz" satırı güncel mi, SIRADAKİ bloğu güncel mi
- [ ] T046 `.\scripts\backup.ps1` çalıştır — Faz 1 çıktıları (özellikle `docs/measurements/`) yedeklensin ([backup.md §1](../../docs/backup.md): ölçüm verisi **yeniden üretilemez** kategoride)

---

## Dependencies & Execution Order

### Faz bağımlılıkları

```
Phase 1 (Setup)
    ↓
Phase 2 (Foundational) ──── T005 (OSM) yalnızca Phase 5'i besler
    ↓                        T006 (fixture) Phase 3 ve 4'ü besler
Phase 3 (US3: QUBO)
    ↓
Phase 4 (US1: Altın referans) 🎯 ──→ Faz 2 BURADAN SONRA başlayabilir
    ↓
Phase 5 (US2: Matris servisi)
    ↓
Phase 6 (US4: Kurulum)
    ↓
Phase 7 (Polish)
```

### Kritik gözlem

**Phase 5 (gerçek matris), Phase 4'ü (altın referans) bloklamıyor.** T006'nın fixture matrisi sayesinde referans, OSRM hiç kurulmadan tamamlanıp doğrulanabilir. Bu bilinçli bir tasarım: [risk TK-01](../../docs/risk-register.md) kritik yolun en kırılgan halkasının Faz 1 → Faz 2 geçişi olduğunu söylüyor; fixture bu halkayı erkene çeker.

### Paralellik fırsatları

- **Phase 1**: T002, T003, T004 paralel
- **Phase 2**: T006, T007, T008 paralel (T005 bağımsız, uzun sürebilir — arka planda başlatılabilir)
- **Phase 3**: T009–T012 (testler) paralel; T015 T013'ten sonra ama T014'e paralel
- **Phase 4**: T017–T021 (testler) paralel
- **Phase 5**: T028–T031 (testler) paralel; T037 diğerlerinden bağımsız
- **Phase 7**: T042, T043, T045 paralel

---

## Implementation Strategy

### MVP = Phase 1 + 2 + 3 + 4

**Neden bu kapsam**: Faz 2'nin (projenin M çekirdeği, [scope-triage.md](../000-kapsam-takvim/scope-triage.md)) beklediği tek şey **altın referans ve ham genlikler**. Phase 4 bittiğinde Faz 2 başlayabilir — gerçek OSRM matrisi hazır olmasa bile.

Bu, [takvimdeki](../000-kapsam-takvim/schedule.md) H2 hedefini ("altın referans koşuyor") en erken tarihte karşılar ve [TK-01 riskini](../../docs/risk-register.md) kapatır.

### Artımlı teslim

1. Phase 1 + 2 → zemin hazır
2. Phase 3 → QUBO doğrulanmış (fixture ile)
3. **Phase 4 → 🎯 Altın referans hazır → Faz 2 BAŞLAYABİLİR**
4. Phase 5 → gerçek veri hattı; referans artık gerçek matrisle de koşar
5. Phase 6 + 7 → kurulum kolaylığı ve cila

### Tek geliştirici notu

Paralellik işaretleri ([P]) tek geliştiricide "aynı anda kodla" demek değil; **bağlam değiştirmeden art arda yapılabilir** demektir. T005 (44,6 MB indirme) ve Docker imaj çekme işleri arka planda koşarken başka göreve geçilebilir.

---

## Notes

- `[P]` = farklı dosya, bekleyen bağımlılık yok
- Testler önce yazılır ve **başarısız olduğu görülür**, sonra implementasyon
- Her görev veya mantıklı grup sonrası commit (`<tip>(faz1): ...`)
- **Ölçülmemiş hiçbir sayı raporlanmaz** (Anayasa Prensip II) — bu kural görev açıklamalarında tekrar tekrar geçiyor çünkü en kolay ihlal edilen kural budur
- Her checkpoint'te durup hikâyeyi bağımsız doğrula
