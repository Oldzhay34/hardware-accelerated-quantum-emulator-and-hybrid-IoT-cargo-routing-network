"""Sentetik kargo/teslimat verisi üretir. Faz 0.4 kararı — bkz. docs/data-governance.md.

Gerçek adres, şoför veya plaka KULLANILMAZ. İstanbul'un bilinen ilçe merkezleri etrafında
Gauss dağılımıyla nokta üretir; tamamen uniform rastgele üretimin aksine gerçekçi bir
kümeleme deseni verir (bkz. docs/data-governance.md §2 — kümeleme sonucunun gerçekçiliği).

Üretim deterministiktir: aynı --seed aynı veriyi verir (Anayasa Prensip II, ölçüm dürüstlüğü).
Faker sürümü çıktıyı etkileyebileceğinden manifest dosyasına kaydedilir.

Kullanım:
    .venv/Scripts/python.exe scripts/generate_synthetic_data.py --drivers 20 --deliveries 200
"""
from __future__ import annotations

import argparse
import csv
import json
import random
from pathlib import Path

import faker as faker_pkg
from faker import Faker

# (ilçe, lat, lon, ağırlık). Ağırlık kaba teslimat yoğunluğu göstergesidir; amaç gerçek
# nüfusu yansıtmak değil, tekdüze olmayan gerçekçi bir kümeleme deseni üretmektir.
ISTANBUL_DISTRICTS: list[tuple[str, float, float, int]] = [
    ("Kadıköy", 40.9833, 29.0333, 8),
    ("Üsküdar", 41.0224, 29.0157, 7),
    ("Maltepe", 40.9354, 29.1306, 6),
    ("Ataşehir", 40.9923, 29.1244, 7),
    ("Beşiktaş", 41.0422, 29.0083, 5),
    ("Şişli", 41.0602, 28.9877, 7),
    ("Kağıthane", 41.0808, 28.9647, 5),
    ("Bağcılar", 41.0342, 28.8567, 9),
    ("Bahçelievler", 41.0017, 28.8583, 7),
    ("Esenyurt", 41.0347, 28.6803, 9),
    ("Beylikdüzü", 41.0014, 28.6414, 6),
    ("Pendik", 40.8778, 29.2333, 7),
    ("Kartal", 40.9061, 29.1861, 6),
    ("Sultanbeyli", 40.9603, 29.2669, 4),
    ("Ümraniye", 41.0164, 29.1248, 8),
    ("Fatih", 41.0186, 28.9397, 6),
    ("Bakırköy", 40.9819, 28.8772, 5),
    ("Sarıyer", 41.1669, 29.0572, 3),
    ("Zeytinburnu", 40.9939, 28.9019, 5),
    ("Küçükçekmece", 41.0000, 28.7833, 8),
]

# İlçe merkezinden sapma (derece). ~0.012 derece ≈ 1.3 km — ilçe içi dağılım için makul.
JITTER_DEG = 0.012

# Faker'ın tr_TR locale'i sokak adlarında İngilizce sonek üretiyor ("Arslan Curve",
# "Erdoğan Roads"). Türkiye adres biçimi için kendi üreticimizi kullanıyoruz.
STREET_SUFFIXES = ("Caddesi", "Sokak", "Bulvarı", "Sokağı")


def synthetic_street(fake: Faker, rng: random.Random) -> str:
    """Türkçe adres biçiminde sentetik sokak adı."""
    if rng.random() < 0.3:
        return f"{rng.randint(1, 120)}. Sokak"
    return f"{fake.last_name()} {rng.choice(STREET_SUFFIXES)}"


def synthetic_person(fake: Faker) -> str:
    """Unvansız ad soyad — Faker'ın name() çıktısı 'Arş. Gör.' gibi unvanlar ekliyor."""
    return f"{fake.first_name()} {fake.last_name()}"


def build_drivers(fake: Faker, rng: random.Random, count: int) -> list[dict]:
    """Sentetik şoför kayıtları. İsim/telefon/plaka tamamen uydurmadır."""
    drivers = []
    for i in range(1, count + 1):
        drivers.append(
            {
                "driver_id": f"D{i:04d}",
                "full_name": synthetic_person(fake),
                # Telefon alanı bilinçli olarak YOK — bu projede sevkiyat/bildirim akışı
                # bulunmadığı için gereksiz. Bkz. docs/data-governance.md §1.1.
                "plate": f"34 {chr(rng.randint(65, 90))}{chr(rng.randint(65, 90))} {rng.randint(100, 999)}",
                "home_district": rng.choice(ISTANBUL_DISTRICTS)[0],
            }
        )
    return drivers


def build_deliveries(fake: Faker, rng: random.Random, count: int, drivers: list[dict]) -> list[dict]:
    """Sentetik teslimat noktaları. Koordinat = ilçe merkezi + Gauss sapma."""
    names = [d[0] for d in ISTANBUL_DISTRICTS]
    weights = [d[3] for d in ISTANBUL_DISTRICTS]
    centers = {d[0]: (d[1], d[2]) for d in ISTANBUL_DISTRICTS}

    deliveries = []
    for i in range(1, count + 1):
        district = rng.choices(names, weights=weights, k=1)[0]
        lat0, lon0 = centers[district]
        deliveries.append(
            {
                "delivery_id": f"T{i:05d}",
                "district": district,
                "lat": round(rng.gauss(lat0, JITTER_DEG), 6),
                "lon": round(rng.gauss(lon0, JITTER_DEG), 6),
                "address_line": f"{synthetic_street(fake, rng)} No:{rng.randint(1, 200)}",
                "recipient_name": synthetic_person(fake),
                "assigned_driver": rng.choice(drivers)["driver_id"],
                "weight_kg": round(rng.uniform(0.2, 25.0), 2),
            }
        )
    return deliveries


def write_csv(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--drivers", type=int, default=20)
    parser.add_argument("--deliveries", type=int, default=200)
    parser.add_argument("--seed", type=int, default=20260910)
    parser.add_argument("--out", type=Path, default=Path("data/synthetic"))
    args = parser.parse_args()

    rng = random.Random(args.seed)
    fake = Faker("tr_TR")
    Faker.seed(args.seed)

    drivers = build_drivers(fake, rng, args.drivers)
    deliveries = build_deliveries(fake, rng, args.deliveries, drivers)

    write_csv(args.out / "drivers.csv", drivers)
    write_csv(args.out / "deliveries.csv", deliveries)

    manifest = {
        "generator": "scripts/generate_synthetic_data.py",
        "seed": args.seed,
        "faker_version": faker_pkg.VERSION,
        "counts": {"drivers": len(drivers), "deliveries": len(deliveries)},
        "note": "Tamamen sentetik. Gerçek kişi, adres veya plaka içermez. Bkz. docs/data-governance.md",
    }
    (args.out / "MANIFEST.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    print(f"{len(drivers)} şoför, {len(deliveries)} teslimat -> {args.out}")
    print(f"seed={args.seed} faker={faker_pkg.VERSION}")


if __name__ == "__main__":
    main()
