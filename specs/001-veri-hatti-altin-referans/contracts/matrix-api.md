# Sözleşme — Mesafe Matrisi HTTP API

**Servis**: `services/matrix` · **Taban**: `http://localhost:8080`

---

## `POST /matrix`

N duraklık koordinat listesinden N×N sürüş-süresi matrisi döndürür. Sonuç önbelleğe yazılır; aynı girdi ikinci kez geldiğinde önbellekten döner ve **bit-birebir aynıdır**.

### İstek

```json
{
  "points": [[41.0186, 28.9397], [40.9833, 29.0333], [41.0422, 29.0083]],
  "use_cache": true
}
```

| Alan | Tip | Zorunlu | Kural |
|---|---|---|---|
| `points` | `[[lat, lon], ...]` | ✅ | 2 ≤ N ≤ 30 |
| `use_cache` | bool | ✗ (varsayılan `true`) | `false` → OSRM'e taze sorgu, sonuç yine önbelleğe yazılır |

### Yanıt 200

```json
{
  "durations": [[0.0, 1834.2, 921.5], [1799.0, 0.0, 1102.3], [944.1, 1088.7, 0.0]],
  "n": 3,
  "cache_hit": false,
  "osm_md5": "cb101d9243c3c605907e94f4266159c2",
  "engine": "osrm/5.x",
  "cache_key": "a3f2...",
  "elapsed_ms": 383
}
```

- `durations` birimi **saniye**. Köşegen 0.
- Matris **asimetrik olabilir** — beklenen davranıştır (gerçek yol ağı).

### Hatalar

| Kod | Ne zaman | Gövde |
|---|---|---|
| `400` | N < 2 veya N > 30 | `{"error": "stop_count_out_of_range", "n": 42, "max": 30}` |
| `400` | Koordinat aralık dışı | `{"error": "invalid_coordinate", "index": 3}` |
| `422` | **Ulaşılamayan durak çifti** | `{"error": "unreachable_pair", "pairs": [[2,7]]}` |
| `503` | OSRM erişilemiyor | `{"error": "engine_unavailable"}` |

> **422 kritik**: Spec FR-007 gereği ulaşılamayan çift olduğunda matris **üretilmez**. Büyük bir sayıyla doldurmak (`9999999`) yasaktır — Prensip II, uydurma değer.

---

## `GET /health`

```json
{"status": "ok", "osrm": "reachable", "osm_md5": "cb101d92..."}
```

OSRM erişilemiyorsa `503` ve `"osrm": "unreachable"`.

---

## Açılışta doğrulama (zorunlu)

Servis, şu ortam değişkenleri eksikse **çalışmayı reddeder** (sessiz varsayılanla kalkmaz — [repo-conventions.md §7](../../../docs/repo-conventions.md) standardı):

| Değişken | Örnek |
|---|---|
| `OSRM_URL` | `http://osrm:5000` |
| `OSM_MD5` | `cb101d92...` — beklenen döküm sağlaması |
| `MATRIX_CACHE_DIR` | `/data/matrices` |
