r"""CPU tarafi is yukunu N saniye boyunca DONGUYE alir (Faz 5 / US3 enerji olcumu).

NEDEN DONGU: tek bir kosum ~90 ms suruyor. Hicbir batarya sayaci 90 ms'lik bir
tuketimi goremez -- Windows kapasiteyi mWh cinsinden ve dakikada bir
guncelliyor. Is yuku birkac dakika boyunca tekrarlanip toplam enerji kosum
sayisina bolunur.

AYNI DEVRE: cpu_reference_time.py ile birebir ayni QUBO, ayni p, ayni tohum.
Farkli devre kosmak, enerji ile gecikme olcumlerini kiyaslanamaz hale getirirdi.

⚠️ BATARYA KISMASI: Windows guc plani bataryada CPU'yu kisabilir. O yuzden bu
betik verimi (kosum/saniye) da raporlar. Bataryadaki verim, prizdekinden
belirgin dusukse enerji ve gecikme FARKLI calisma noktalarindan gelmis olur ve
bu rapora yazilmalidir.

Kullanim:
    .venv\Scripts\python.exe scripts\cpu_load_loop.py --saniye 300 --p 2
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

import numpy as np
from qiskit import transpile
from qiskit.circuit.library import QAOAAnsatz

KOK = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(KOK))
from services.common import stamp                      # noqa: E402
from services.qubo import qubo as qubo_mod             # noqa: E402
from services.reference import qaoa_reference          # noqa: E402


def devre_kur(p: int):
    """cpu_reference_time.py ile AYNI devreyi kurar."""
    from services.reference.cli import ornek_matris
    problem = qubo_mod.matrix_to_qubo(ornek_matris(5))
    cost_op, _ = qaoa_reference._qubo_to_ising(problem)
    a = QAOAAnsatz(cost_operator=cost_op, reps=p)
    qc = a.decompose(reps=3).assign_parameters(
        np.random.default_rng(42).uniform(0, np.pi, a.num_parameters))
    qc.save_statevector()
    return qc


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--saniye", type=int, default=300)
    ap.add_argument("--p", type=int, default=2)
    ap.add_argument("--etiket", default="yuk")
    a = ap.parse_args()

    from qiskit_aer import AerSimulator
    sim = AerSimulator(method="statevector")

    qc = devre_kur(a.p)
    tqc = transpile(qc, sim)
    print(f"devre hazir: p={a.p}, {len(qc.data)} kapi")

    # Isinma: ilk kosum JIT/tahsis maliyeti tasir, olcume dahil edilmez.
    sim.run(tqc).result()

    print(f"{a.saniye} saniye donguye giriliyor... (DOKUNMA)")
    kosum = 0
    sureler = []
    izler = []          # (baslangictan gecen sn, kosum suresi ms)
    bas = time.perf_counter()
    son_pencere = 0.0
    while time.perf_counter() - bas < a.saniye:
        t0 = time.perf_counter()
        sim.run(tqc).result()
        t1 = time.perf_counter()
        sureler.append(t1 - t0)
        izler.append((t0 - bas, (t1 - t0) * 1000))
        kosum += 1
        # 10 saniyelik pencerelerin medyani -- termal platoyu GORMEK icin.
        # Toplam medyan, turbo ile plato donemini birbirine karistirir.
        gecen = t1 - bas
        if gecen - son_pencere >= 10.0:
            pencere = [ms for (t, ms) in izler if t >= son_pencere]
            pencere.sort()
            print(f"  {gecen:5.0f} sn   {kosum:6d} kosum   "
                  f"pencere medyani {pencere[len(pencere)//2]:6.2f} ms")
            son_pencere = gecen
    toplam = time.perf_counter() - bas

    sureler_ms = sorted(s * 1000 for s in sureler)
    n = len(sureler_ms)

    def _med(xs):
        ys = sorted(xs)
        return round(ys[len(ys) // 2], 3) if ys else None

    # TURBO: ilk 2 saniye. Islemci bu pencerede tam hizda.
    turbo = _med([ms for (t, ms) in izler if t < 2.0])
    # PLATO: son 60 saniye (veya kosumun son ucte biri, hangisi kisaysa).
    plato_bas = max(toplam - 60.0, toplam * 2 / 3)
    plato = _med([ms for (t, ms) in izler if t >= plato_bas])
    # Plato gercekten oturdu mu: son iki 30 sn'lik dilim birbirine yakin mi
    d1 = _med([ms for (t, ms) in izler if toplam - 60 <= t < toplam - 30])
    d2 = _med([ms for (t, ms) in izler if t >= toplam - 30])
    oturdu = (d1 is not None and d2 is not None and abs(d2 - d1) / d1 < 0.03)

    ozet = {
        "etiket": a.etiket,
        "p": a.p,
        "kapi": len(qc.data),
        "toplam_saniye": round(toplam, 3),
        "kosum": kosum,
        "verim_kosum_sn": round(kosum / toplam, 4),
        "kosum_basina_ms": {
            "medyan": round(sureler_ms[n // 2], 3),
            "min": round(sureler_ms[0], 3),
            "max": round(sureler_ms[-1], 3),
        },
        "turbo_ms": turbo,
        "plato_ms": plato,
        "plato_oturdu": oturdu,
        "turbo_plato_orani": round(plato / turbo, 3) if (turbo and plato) else None,
    }
    ad = f"cpu-yuk-dongu_{stamp.stamped_name('x').split('_')[1]}_{a.etiket}_p{a.p}.json"
    yol = KOK / "docs" / "measurements" / ad
    yol.write_text(json.dumps(ozet, indent=2, ensure_ascii=False), encoding="utf-8")

    print()
    print(f"kosum          : {kosum}")
    print(f"verim          : {ozet['verim_kosum_sn']} kosum/sn")
    print(f"kosum basina   : medyan {ozet['kosum_basina_ms']['medyan']} ms "
          f"(min {ozet['kosum_basina_ms']['min']}, max {ozet['kosum_basina_ms']['max']})")
    print(f"TURBO (ilk 2sn): {turbo} ms")
    print(f"PLATO (son 60sn): {plato} ms   "
          f"({'oturdu' if oturdu else 'HENUZ OTURMADI - daha uzun kos'})")
    if turbo and plato:
        print(f"turbo/plato    : {plato/turbo:.2f}x yavaslama")
    print(f"yazildi        : {yol.name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
