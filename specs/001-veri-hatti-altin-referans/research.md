# Phase 0 — Araştırma ve Kararlar

**Faz**: 1 — Veri Hattı ve Altın Referans · **Tarih**: 2026-09-13
**Durum**: Tamamlandı — tüm NEEDS CLARIFICATION çözüldü, teknoloji seçimleri onaylandı

> **Anayasa Prensip II**: Aşağıdaki her sayı bu makinede gerçekten ölçüldü. Tahmini değer yok.
> **Ölçüm ortamı**: Docker 29.5.3, linux/x86_64, 6 CPU, 10,4 GB RAM · Python 3.13.12 · Intel64 Family 6 Model 186

---

## R-1 · Mesafe matrisi motoru

**Karar: OSRM** (`osrm/osrm-backend:latest`, BSD-2-Clause)

### Ölçülen veriler

Girdi: İstanbul OSM extract, 44,6 MB (BBBike, Last-Modified 2026-09-12, MD5 `cb101d9243c3c605907e94f4266159c2`)

| Kriter | OSRM | Valhalla | GraphHopper |
|---|---|---|---|
| Ön işleme süresi | **192 sn** (extract 126,5 + partition 38,4 + customize 27,1) | 1054 sn (17,6 dk) | **78 sn** |
| Tepe RAM (ön işleme) | **435 MiB** | 709 MiB | 1058 MiB |
| Docker imaj boyutu | **151 MB** | 972 MB | 516 MB |
| Üretilen veri | 282 MB | 66 MB (tiles) | **43 MB** |
| **N=30 matris gecikmesi** | **0,383 sn** medyan (min 0,080 / maks 1,273) | 12,87 sn medyan (min 5,37 / maks 15,80) | 🔴 **API YOK** |
| Matris tamlığı | **900/900** | 842/900 (58 ulaşılamaz) | — |
| Asimetrik çift | 434/435 | 404/435 | — |
| Kurulum | 3 komut | 4 komut, sıraya duyarlı | 1 komut |
| Resmî Docker imajı | ✅ | ✅ | ❌ topluluk (13★) |
| Lisans | BSD-2 | MIT | Apache-2.0, **matris ticari** |
| **Skor** | **46/50** | 33/50 | 25/50 |

### Rationale

- **GraphHopper elendi — ampirik**: Açık kaynak sürümünde `/matrix` ucu **yok**. Varsayım değil, test edildi: `/route` → 200, `/matrix` → **404**. N=30 için 900 ayrı rota çağrısı gerekirdi; spec FR-001'i makul maliyetle karşılayamıyor.
- **Valhalla elendi — performans**: Çalışıyor ama matris çağrısı OSRM'den **34 kat yavaş** (12,87 sn vs 0,383 sn) ve 58 çifti ulaşılamaz bırakıyor. Ön işleme de 5,5 kat uzun.
- **OSRM seçildi**: Her ölçülen eksende ya en iyi ya ikinci. Asıl kriter olan matris gecikmesinde açık ara önde.

### Alternatives considered

Yukarıdaki tablo. Valhalla'nın ilk denemede aldığı segfault **aracın kusuru değil**, eksik kurulum komutundandı (`admin.sqlite`/`tz.sqlite` önceden üretilmeli) — doğru sırayla koşunca çıkış kodu 0 verdi. Ancak yanlış sırada anlaşılır bir hata yerine segfault vermesi öğrenme maliyetine yazıldı.

### Doğrulama: gerçek yol ağı kullanılıyor mu?

OSRM matrisinde **435 durak çiftinin 434'ü asimetrik** (`t[i][j] ≠ t[j][i]`). Kuş uçuşu mesafe simetrik olurdu. Bu, tek yönlü yolların ve Boğaz köprü darboğazlarının modele girdiğinin doğrudan kanıtı — spec **FR-002** karşılanıyor. En uzun rota 3872 sn (65 dk), ortalama 1583 sn.

---

## R-2 · Kuantum doğrulama kütüphanesi

**Karar: Qiskit 2.5.2 + qiskit-aer 0.17.2** (Apache-2.0)

### Ölçülen veriler

16 kübit devre (H×16 + CNOT zinciri + RZ×16), 3 tekrarın en iyisi:

| Kriter | Qiskit (saf) | Qiskit + **Aer** | PennyLane 0.45.1 |
|---|---|---|---|
| 16 kübit statevector süresi | 67,3 ms | **8,9 ms** | 72,3 ms |
| Tepe bellek | 5,03 MB | **0,09 MB** | 4,14 MB |
| Ham genlik erişimi | ✅ complex128, norm 1,0 | ✅ | ✅ complex128, norm 1,0 |
| QAOA yardımcıları | ✅ `QAOAAnsatz` (reps=2 → 4 parametre) | ✅ | ✅ `qaoa.cost_layer`, `mixer_layer`, `x_mixer` |
| **Skor** | — | **40/40** | 33/40 |

### Rationale

Zorunlu kriteri — **ham genliklere doğrudan erişim** — ikisi de karşılıyor, dolayısıyla seçim oradan ayrışmadı. Belirleyici olan iki şey: Aer'in **8 kat** hız üstünlüğü, ve Anayasa Prensip IV'ün Qiskit'i **adıyla** bağlayıcı kılması. PennyLane'i seçmek anayasa değişikliği gerektirirdi; ölçümler bunu haklı çıkaracak bir üstünlük göstermiyor.

### Alternatives considered

- **PennyLane**: Yukarıda. Elendi.
- **Cirq/qsim**: Değerlendirilmedi. Gerekçe: Qiskit ve PennyLane zorunlu kriteri zaten karşıladı ve Qiskit anayasayla sabit; üçüncü bir kütüphaneyi ölçmek 14 hafta kısıtı altında (Prensip VI) getirisiz.

### Yan bulgu — Faz 2'yi ilgilendiriyor

16 kübit complex128 statevector = **1,0 MB**. [memory-budget.md](../../docs/memory-budget.md) PYNQ-Z2'nin toplam BRAM'inin 630 KB olduğunu gösteriyor. Yani **altın referansın kendi formatı donanıma sığmaz** — bu bir sorun değil, referans CPU'da koşuyor; ama Faz 2'nin dar formatlarıyla (float32 / Q1.15) kıyaslanabilmesi gerekiyor → **R-5**.

---

## R-3 · OSM veri kaynağı ve sürüm sabitleme

**Karar: BBBike İstanbul extract**, MD5 ile doğrulanarak pinlenir.

| Kaynak | Boyut | Tarih | Kapsam |
|---|---|---|---|
| **BBBike Istanbul** ✅ | 44,6 MB | 2026-09-12 | Yalnızca İstanbul — promptun istediği "İstanbul boyutu"na birebir |
| Geofabrik `turkey-260912.osm.pbf` | 615,9 MB | 2026-09-12 | Tüm Türkiye — 14x büyük, gereksiz |

**Rationale**: `turkey-latest.osm.pbf` bir **yönlendirme**dir → tarihli `turkey-260912.osm.pbf`. Yani "latest" URL'si sabitlenemez, tarihli olan sabitlenebilir. BBBike tarafında tarihli URL yok; bu yüzden **MD5 sağlaması** (`cb101d9243c3c605907e94f4266159c2`) sürüm kimliği olarak kullanılır ve `scripts/fetch_osm.ps1` indirdikten sonra doğrular, tutmazsa **hata verir**.

Bu, spec **FR-005**'i ("veri sürümü sabitlenmeli, 'en güncel veriyi indir' davranışı yasak") karşılar.

---

## R-4 · Windows/Git Bash tuzağı — MSYS yol dönüşümü

**Karar**: Docker'ı Git Bash'ten çağıran her betik `MSYS_NO_PATHCONV=1` ayarlamalı.

**Bulgu (yaşandı)**: `docker run ... osrm-extract -p /opt/car.lua` komutu şu hatayı verdi:

```
[error] the argument ('C:/Program Files/Git/opt/car.lua') for option '--profile' is invalid
```

Git Bash, konteyner **içindeki** `/opt/car.lua` yolunu Windows yoluna çevirmiş. `MSYS_NO_PATHCONV=1` ile çözüldü.

**Uygulama**: Bu tuzak `quickstart.md`'de ve ilgili betiklerin başında yorum olarak belgelenecek. Ayrıca PowerShell betikleri bu sorundan etkilenmez — `scripts/` altındakiler `.ps1` olarak yazılacak.

---

## R-5 · Altın referans çıktı formatı — Faz 2 kıyasını mümkün kılmak

**Karar**: Referans, ham genlik vektörünü **complex128 olarak `.npy`** biçiminde yazar; ayrıca metadata JSON'u tohum, p değeri, QUBO parametreleri ve kübit sıralama konvansiyonunu kaydeder.

**Rationale**: Faz 2'nin çekirdeği float32 veya Q1.15 üretecek ([memory-budget.md](../../docs/memory-budget.md)). Kıyas, referansı **donanımın formatına indirgeyerek** yapılmalı — tersi değil. complex128 referans, her dar formata kayıpsız indirgenebilir; float32 bir referans Q1.15 kıyasında belirsizlik yaratırdı.

**Kübit sıralaması kritik**: Risk kaydındaki [DG-02](../../docs/risk-register.md) "Qiskit kübit sıralama konvansiyonu ters (little/big endian)" riskini **yüksek olasılıklı** işaretliyor. Metadata bu konvansiyonu açıkça yazacak ve doğrulama paketi bir permütasyon testi içerecek — Faz 2'de "fidelity ≈ 0 ama genlik büyüklükleri doğru" imzasıyla saatler kaybetmemek için.

---

## R-6 · Ceza katsayısı türetimi

**Karar**: `A = (1 + ε) · max(matris)` — sabit gömülmez, matristen türetilir. Başlangıç `ε = 0,1`.

**Rationale**: Spec **FR-009** katsayının matristen türetilmesini şart koşuyor. Teorik alt sınır: bir kısıt ihlalinin cezası, en kötü geçerli turdan pahalı olmalı. `max(matris)` üzerinden türetmek bunu garantiler. `ε` payı, kayan nokta eşitlik durumlarına karşı güvenlik marjı.

**Doğrulama**: Testler (`test_penalty.py`) kısıt ihlal eden **her** aday çözümün enerjisinin **her** geçerli turdan yüksek olduğunu kontrol edecek (spec SC-003, ihlal sayısı 0 olmalı). Eğer ε=0,1 yetmezse test bunu yakalar ve değer yükseltilir.

---

## Çözülen NEEDS CLARIFICATION

| Soru | Çözüm |
|---|---|
| Hangi rotalama motoru? | OSRM (R-1, ölçümle, onaylandı) |
| Hangi kuantum kütüphanesi? | Qiskit + Aer (R-2, ölçümle, onaylandı) |
| Hangi OSM dökümü, nasıl pinlenir? | BBBike İstanbul + MD5 doğrulaması (R-3) |
| Referans çıktı formatı ne olmalı? | complex128 `.npy` + metadata JSON (R-5) |
| Ceza katsayısı nasıl belirlenir? | `(1+ε)·max(matris)`, testle doğrulanır (R-6) |
| Anayasa–prompt gerilimi (Qiskit vs PennyLane) | Çözüldü: ölçümler Qiskit'i destekliyor, anayasa değişikliği **gerekmedi** |

**Kalan NEEDS CLARIFICATION: yok.**
