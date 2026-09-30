"""6B — GPU tabanı protokolü v1.1 §12 Δ2: iş parçacığı taramasından T seçimi.

Seçim kuralı (protokolde taramadan ÖNCE yazıldı):
  60 sn'lik noktaların medyanı en düşük T; medyanı en düşüğün %1'i içinde
  olanlar arasında EN KÜÇÜK T. Bir nokta eksik ya da geçersizse seçim YAPILMAZ.

Girdi : docs/measurements/cpu-yuk-dongu_<tarih>_<hash>_taramaT<T>_p2.json
Çıktı : docs/measurements/aer-is-parcacigi-secimi_<tarih>_<hash>.json
        stdout'un son satırı yalnız seçilen T (çalıştırıcı okur)

Kullanım:  python scripts/aer_is_parcacigi_sec.py <tarih> <git-hash> [dizin]
           (dizin yalnız sınama için; varsayılan docs/measurements)
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

KOK = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(KOK))
from services.common import stamp  # noqa: E402

TARAMA = (1, 2, 4, 6, 8, 10, 16)
PROTOKOL = "gpu-taban-protokolu v1.1"
ESIT_ORAN = 0.01


def main(argv: list[str]) -> int:
    tarih, git = argv[1], argv[2]
    olcum = Path(argv[3]) if len(argv) > 3 else KOK / "docs" / "measurements"
    satirlar = []
    for t in TARAMA:
        yol = olcum / f"cpu-yuk-dongu_{tarih}_{git}_taramaT{t}_p2.json"
        if not yol.exists():
            raise SystemExit(f"⛔ tarama noktasi eksik: {yol.name} -- secim yapilmadi")
        d = json.loads(yol.read_text(encoding="utf-8"))
        if not d["gecerli"] or d["protokol_surumu"] != PROTOKOL or d["p"] != 2:
            raise SystemExit(f"⛔ gecersiz tarama noktasi: {yol.name} -- secim yapilmadi")
        if d["ortam"]["max_parallel_threads"] != t:
            raise SystemExit(f"⛔ {yol.name}: istenen T={t}, kayitli "
                             f"{d['ortam']['max_parallel_threads']}")
        s = d["seri"]
        satirlar.append({"T": t, "dosya": yol.name, "aer_is_parcacigi": d["ortam"]["aer_is_parcacigi"],
                         "medyan_ms": s["medyan_s"] * 1000, "iqr_ms": s["yayilim_s"] * 1000,
                         "p99_ms": s["p99_s"] * 1000, "maks_ms": s["max_s"] * 1000,
                         "kosum": s["kosum_sayisi"]})
    en_dusuk = min(r["medyan_ms"] for r in satirlar)
    adaylar = [r for r in satirlar if r["medyan_ms"] <= en_dusuk * (1 + ESIT_ORAN)]
    secilen = min(adaylar, key=lambda r: r["T"])["T"]

    for r in satirlar:
        isaret = "  <-- secilen" if r["T"] == secilen else ""
        print(f"T={r['T']:>2}  medyan {r['medyan_ms']:8.3f} ms  IQR {r['iqr_ms']:7.3f}  "
              f"p99 {r['p99_ms']:8.3f}  maks {r['maks_ms']:8.3f}  n {r['kosum']}{isaret}")
    veri = {
        "ne": "Aer CPU is parcacigi taramasi ve T secimi (protokol v1.1 §12 Δ2)",
        "protokol_surumu": PROTOKOL,
        "damga": stamp.stamp(tarih=tarih, tarama_git=git),
        "kural": ("medyani en dusuk T; en dusugun %1'i icindekiler arasinda en kucuk T"),
        "tablo": satirlar,
        "en_dusuk_medyan_ms": en_dusuk,
        "adaylar_T": [r["T"] for r in adaylar],
        "secilen_T": secilen,
    }
    (olcum / f"aer-is-parcacigi-secimi_{tarih}_{git}.json").write_text(
        json.dumps(veri, indent=1, ensure_ascii=False), encoding="utf-8")
    print(secilen)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
