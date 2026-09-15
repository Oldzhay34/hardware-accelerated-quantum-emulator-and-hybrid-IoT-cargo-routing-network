"""CPU referans zamani — tasarim kararini belirleyen olcum.

Soru: ping-pong'un ~3,4x hizi, SC-002'yi (BRAM <= %85) kirma pahasina degiyor mu?
Cevap CPU'nun ne kadar yavas olduguna bagli.

DURUSTLUK NOTU: iki CPU tabani var ve arasinda 20x fark var. Qiskit'in
Statevector.evolve'u Python seviyesindedir ve ADIL TABAN DEGILDIR; Aer'in C++
statevector simulatoru adil tabandir. Tez kiyasi (Faz 10) Aer'e karsi yapilir.

Ayrica: CPU ayristirilmis devreyi (585 kapi) kosar, FPGA yerlesik formulasyonu
(232 kapi) kosar. Hizlanmanin bir kismi DONANIMDAN degil FORMULASYONDAN gelir;
ayni formulasyonu CPU da benimseyebilir. Faz 10 bunu ayirmalidir.

Kullanim:
    .venv/Scripts/python.exe scripts/cpu_reference_time.py
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

import numpy as np
from qiskit import transpile
from qiskit.circuit.library import QAOAAnsatz
from qiskit.quantum_info import Statevector

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from services.common import stamp
from services.qubo import qubo as qubo_mod
from services.reference import qaoa_reference

TEKRAR = 15
F_MHZ = 100
# HESAPLANAN cevrim sayilari - scripts/banking_analysis.py verimlerinden turetildi.
# yerinde: k<4'te 8 cift/cevrim, k>=4'te 4; ping-pong: her k'de 16.
FPGA_CEVRIM = {"yerinde (Q1.17)": 237_568, "ping-pong (Q1.17)": 69_632}


def olc(calistir) -> dict:
    calistir()                                   # isinma
    t = [(lambda: (time.perf_counter(), calistir(), time.perf_counter()))() for _ in range(TEKRAR)]
    sureler = [b - a for a, _, b in t]
    return {"medyan_ms": round(float(np.median(sureler)) * 1000, 2),
            "min_ms": round(min(sureler) * 1000, 2),
            "max_ms": round(max(sureler) * 1000, 2), "tekrar": TEKRAR}


def main() -> None:
    kok = Path(__file__).resolve().parents[1]
    sys.path.insert(0, str(kok))
    from services.reference.cli import ornek_matris

    problem = qubo_mod.matrix_to_qubo(ornek_matris(5))
    cost_op, _ = qaoa_reference._qubo_to_ising(problem)
    sonuc: dict = {}

    try:
        from qiskit_aer import AerSimulator
        sim = AerSimulator(method="statevector")
    except ImportError:
        sim = None
        print("UYARI: qiskit-aer yok, yalnizca Python tabani olculecek.")

    for p in (1, 2):
        a = QAOAAnsatz(cost_operator=cost_op, reps=p)
        qc = a.decompose(reps=3).assign_parameters(
            np.random.default_rng(42).uniform(0, np.pi, a.num_parameters))
        kayit = {"kapi": len(qc.data)}

        kayit["qiskit_python"] = olc(lambda: Statevector.from_int(0, 2**16).evolve(qc))
        print(f"p={p}: {len(qc.data)} kapi")
        print(f"   Qiskit Statevector (Python, ADIL DEGIL): "
              f"{kayit['qiskit_python']['medyan_ms']:>8.1f} ms")

        if sim is not None:
            qc2 = qc.copy(); qc2.save_statevector()
            tqc = transpile(qc2, sim)
            kayit["aer_cpp"] = olc(lambda: sim.run(tqc).result())
            print(f"   Aer statevector (C++, ADIL TABAN):    "
                  f"{kayit['aer_cpp']['medyan_ms']:>8.1f} ms")
        sonuc[f"p={p}"] = kayit

    # MUHAFAZAKAR SECIM: CPU'nun EN IYI zamani kullanilir. Bu makine olcum
    # sirasinda gurultulu (p=2'de min 66 ms / max 981 ms gorildi); medyan
    # kararsiz. En iyi zaman FPGA'yi en az kayiran taban, yani en durust olani.
    taban = sonuc["p=2"].get("aer_cpp", sonuc["p=2"]["qiskit_python"])["min_ms"]
    taban_ad = ("Aer C++" if "aer_cpp" in sonuc["p=2"] else "Qiskit Python") + " EN IYI"
    print(f"\nFPGA TAHMINI (HESAPLANAN, p=2, {F_MHZ} MHz) — adil tabana ({taban_ad}) karsi:")
    for ad, c in FPGA_CEVRIM.items():
        ms = c / (F_MHZ * 1e6) * 1000
        print(f"   {ad:<20} {c:>8} cevrim = {ms:>5.2f} ms  -> {taban/ms:>6.1f}x")
        sonuc[f"fpga_{ad}"] = {"cevrim": c, "ms": round(ms, 3),
                               "hizlanma_vs_adil_taban": round(taban / ms, 1)}
    print("\n!! Bu hizlanma sayilari TAHMINDIR (Prensip II). Teze ancak sentez")
    print("   raporu ve kartta olcum geldikten sonra girebilir (Faz 10).")

    meta = stamp.stamp(problem="5-durak-16-kubit", frekans_mhz=F_MHZ,
                       not_="CPU OLCULEN; FPGA cevrimleri HESAPLANAN")
    meta["sonuclar"] = sonuc
    yol = stamp.measurements_dir(kok) / f"{stamp.stamped_name('cpu-referans-zaman')}.json"
    yol.write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\nYazildi: {yol.name}")


if __name__ == "__main__":
    main()

