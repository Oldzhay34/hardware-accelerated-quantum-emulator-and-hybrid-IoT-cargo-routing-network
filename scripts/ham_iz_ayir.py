"""Var olan ölçüm JSON'larındaki `ham_iz_ms`'i ayrı, sıkıştırılmış dosyaya taşır.

Tek seferlik, KAYIPSIZ bir dönüşüm (1 Eki 2026): 30 Eyl GPU tabanı serilerinin
ham izleri ana dosyaları 15 MB'a çıkarmıştı. Ölçülen hiçbir değer değişmez:
  - ham iz `<ad>.ham.json.gz`'ye yazılır ve geri açılıp BİREBİR karşılaştırılır
  - ana JSON'da `ham_iz_ms` yerine aynı konumda `ham_iz` işaretçisi durur
    (dosya adı, koşum sayısı, açık verinin sha256'sı, dönüşümün notu)
  - diğer bütün alanlar yeniden okunup orijinalle karşılaştırılır
Yeni seriler zaten böyle yazılır (cpu_load_loop.ham_iz_ayri_yaz).

Kullanım:  python scripts/ham_iz_ayir.py docs/measurements/<dosya>.json [...]
"""
from __future__ import annotations

import gzip
import json
import sys
from pathlib import Path

KOK = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(KOK))
from scripts.cpu_load_loop import ham_iz_ayri_yaz  # noqa: E402

NOT = "sonradan ayrildi (1 Eki 2026, scripts/ham_iz_ayir.py); kayipsiz, geri acilip dogrulandi"


def ayir(yol: Path) -> str:
    asil = json.loads(yol.read_text(encoding="utf-8"))
    if "ham_iz_ms" not in asil:
        return "atlandi (ham_iz_ms yok)"
    yan = yol.with_name(yol.stem + ".ham.json.gz")
    if yan.exists():
        raise SystemExit(f"⛔ yan dosya zaten var: {yan.name}")
    isaretci = {**ham_iz_ayri_yaz(yol, asil["ham_iz_ms"]), "not": NOT}
    yeni = {("ham_iz" if k == "ham_iz_ms" else k): (isaretci if k == "ham_iz_ms" else v)
            for k, v in asil.items()}
    yol.write_text(json.dumps(yeni, indent=1, ensure_ascii=False), encoding="utf-8")

    # denetim: ana dosya + yan dosya = orijinal
    geri = json.loads(yol.read_text(encoding="utf-8"))
    iz = json.loads(gzip.decompress(yan.read_bytes()))
    geri_birlesik = {("ham_iz_ms" if k == "ham_iz" else k): (iz if k == "ham_iz" else v)
                     for k, v in geri.items()}
    if geri_birlesik != asil:
        raise SystemExit(f"⛔ {yol.name}: geri birlestirme orijinalle AYNI DEGIL")
    return f"{len(iz)} kosum -> {yan.name}"


def main(argv: list[str]) -> int:
    for a in argv[1:]:
        print(f"{Path(a).name}: {ayir(Path(a))}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
