r"""CPU tarafi is yukunu N saniye boyunca DONGUYE alir (Faz 5 / US3 enerji olcumu).

NEDEN DONGU: tek bir kosum ~90 ms suruyor. Hicbir batarya sayaci 90 ms'lik bir
tuketimi goremez -- Windows kapasiteyi mWh cinsinden ve dakikada bir
guncelliyor. Is yuku birkac dakika boyunca tekrarlanip toplam enerji kosum
sayisina bolunur.

AYNI DEVRE: altin referansin (reference_*_p<p>_n5.json) QUBO'su ve OPTIMIZE
edilmis parametreleri (adiyla) -- C-sim'in, cosim'in ve kartin kostugu devrenin
aynisi. (27 Eyl'e kadar tohum-42 RASTGELE parametreler kullaniliyordu: kapilar
ayni, acilar farkli; o hali altin referansa karsi dogrulanamazdi.)

DOGRULAMA ONCE (T066, Prensip IV): isinma kosumunun statevector'u altin
referansa karsi olculur; fidelity H esiginin (0,999) altindaysa ZAMANLAMA
BASLAMAZ. Sonuc cikti JSON'unun `dogrulama` alaninda. --yalniz-dogrula ile
yalniz dogrulama kaydi yazilir (aer-dogrulama_*.json).

⚠️ BATARYA KISMASI: Windows guc plani bataryada CPU'yu kisabilir. O yuzden bu
betik verimi (kosum/saniye) da raporlar. Bataryadaki verim, prizdekinden
belirgin dusukse enerji ve gecikme FARKLI calisma noktalarindan gelmis olur ve
bu rapora yazilmalidir.

GPU (Faz 5 / 6B, T065, ADR 0010): ayni dongu --device GPU ile. ⛔ AYRI BETIK
YOK -- farkli kosum hatti rakamlari kiyaslanamaz kilar. GPU yolu yalniz WSL'deki
qiskit-aer-gpu venv'inde var (docs/runbooks/gpu-aer-wsl.md); CPU/GPU kiyasi
icin CPU da AYNI venv'de kosulur, yalniz cihaz degisir. Bu Aer tabani FPGA ile
KIYASLANMAZ (QAOA ayristirmasi, hata #5) -- yalniz Aer ici GPU/CPU orani.

⚠️ GK-01 (makine gunde ~1 cokuyor): iz her 10 sn'lik pencerede diske yazilir
ve fsync edilir (<olcum>.kismi.jsonl). Cokmede en fazla bir pencere kaybolur;
basarili bitiste kismi dosya silinir. Kosum basina yazmak zamanlama dongusunu
bozardi.

Kullanim:
    .venv\Scripts\python.exe scripts\cpu_load_loop.py --saniye 300 --p 2
    # WSL, GPU venv:
    /root/qir-gpu-venv/bin/python scripts/cpu_load_loop.py --device GPU --etiket prizde
    /root/qir-gpu-venv/bin/python scripts/cpu_load_loop.py --device GPU --yalniz-dogrula
"""
from __future__ import annotations

import argparse
import json
import os
import platform
import subprocess
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


H_ESIGI = 0.999    # Faz 2 butcesi (Prensip IV); altinda zamanlama baslamaz


def referans_bul(p: int, yol: str | None) -> Path:
    """Verilmezse en yeni TARIHLI referans; ayni tarihte iki referans varsa durur
    (git hash'i siralanabilir degil, yanlis dosya secilmesin)."""
    if yol:
        return Path(yol).with_suffix(".json")
    adaylar = sorted((KOK / "docs" / "measurements").glob(f"reference_*_p{p}_n5.json"))
    tarih = adaylar[-1].name.split("_")[1]
    ayni = [a for a in adaylar if a.name.split("_")[1] == tarih]
    if len(ayni) != 1:
        raise SystemExit(f"ayni tarihli birden fazla referans, --referans ver: {ayni}")
    return ayni[0]


def devre_kur(p: int, parametreler: dict[str, float]):
    """Altin referansin devresi: ayni QUBO, parametreler ADIYLA baglanir."""
    from services.reference.cli import ornek_matris
    problem = qubo_mod.matrix_to_qubo(ornek_matris(5))
    cost_op, _ = qaoa_reference._qubo_to_ising(problem)
    a = QAOAAnsatz(cost_operator=cost_op, reps=p).decompose(reps=3)
    adlar = {pr.name for pr in a.parameters}
    if adlar != set(parametreler):
        raise SystemExit(f"parametre adlari uyusmuyor: devre {sorted(adlar)}, "
                         f"referans {sorted(parametreler)}")
    qc = a.assign_parameters({pr: parametreler[pr.name] for pr in a.parameters})
    qc.save_statevector()
    return qc, problem


def _optimum_indeksi(problem) -> int:
    """qaoa_reference.run ile ayni tanim: gecerli turlar icinde en dusuk enerjili."""
    enerjiler = qaoa_reference._tum_enerjiler(problem)
    for idx in np.argsort(enerjiler):
        bits = np.array([(idx >> k) & 1 for k in range(problem.n_vars)], dtype=np.int8)
        if qubo_mod.assignment_to_tour(problem, bits) is not None:
            return int(idx)
    raise RuntimeError("gecerli tur yok")


def dogrula(sonuc, ref_json: Path, meta: dict, problem) -> dict:
    """Isinma kosumunun statevector'u altin referansa karsi (Prensip IV)."""
    ref = np.load(ref_json.with_suffix(".npy"))
    sv = np.asarray(sonuc.get_statevector(), dtype=np.complex128)
    f = abs(np.vdot(ref, sv)) ** 2 / (np.vdot(ref, ref).real * np.vdot(sv, sv).real)
    probs = np.abs(sv) ** 2
    en_iyi = _optimum_indeksi(problem)
    # oz-denetim: problem ve indeksleme referansinkiyle ayni mi
    if not np.isclose(abs(ref[en_iyi]) ** 2, meta["optimal_probability"], rtol=1e-9, atol=0):
        raise SystemExit("optimum indeksi referansin optimal_probability'sini uretmiyor")
    return {
        "referans": ref_json.name,
        "referans_backend": meta.get("backend"),
        "fidelity": float(f),
        "bir_eksi_F": float(1 - f),
        "max_genlik_farki": float(np.max(np.abs(sv - ref))),
        "p_optimum_referans": meta["optimal_probability"],
        "p_optimum_bu_kosum": float(probs[en_iyi]),
        "esik": H_ESIGI,
        "gecti": bool(f >= H_ESIGI),
    }


def _gpu_bilgisi() -> dict | None:
    """nvidia-smi'den GPU adi, surucu ve guc siniri (WSL'de PATH disinda)."""
    for exe in ("nvidia-smi", "/usr/lib/wsl/lib/nvidia-smi"):
        try:
            out = subprocess.run(
                [exe, "--query-gpu=name,driver_version,power.limit,temperature.gpu",
                 "--format=csv,noheader"], capture_output=True, text=True, timeout=10)
        except (OSError, subprocess.SubprocessError):
            continue
        if out.returncode == 0 and out.stdout.strip():
            ad, surucu, guc, sicaklik = [s.strip() for s in out.stdout.splitlines()[0].split(",")]
            return {"ad": ad, "surucu": surucu, "guc_siniri": guc, "baslangic_sicaklik_C": sicaklik}
    return None


def _ortam(sim, meta: dict, device: str) -> dict:
    import qiskit
    import qiskit_aer
    return {
        "qiskit": qiskit.__version__,
        "qiskit_aer": qiskit_aer.__version__,
        "python": platform.python_version(),
        "platform": platform.platform(),
        "device_istenen": device,
        "device_metadata": meta.get("device"),
        "precision": sim.options.precision,
        "cuStateVec_enable": meta.get("cuStateVec_enable"),
        "fusion": meta.get("fusion"),
        "gpu": _gpu_bilgisi() if device == "GPU" else None,
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--saniye", type=int, default=300)
    ap.add_argument("--p", type=int, default=2)
    ap.add_argument("--etiket", default="yuk")
    ap.add_argument("--device", choices=("CPU", "GPU"), default="CPU")
    ap.add_argument("--referans", default=None,
                    help="altin referans (.json/.npy); verilmezse en yeni tarihli")
    ap.add_argument("--yalniz-dogrula", action="store_true",
                    help="zamanlama yok; yalniz referansa karsi dogrulama kaydi (T066)")
    a = ap.parse_args()

    from qiskit_aer import AerSimulator
    if a.device not in AerSimulator().available_devices():
        raise SystemExit(f"{a.device} yok: {AerSimulator().available_devices()} "
                         "(GPU yalniz WSL venv'inde, docs/runbooks/gpu-aer-wsl.md)")
    sim = AerSimulator(method="statevector", device=a.device)

    ref_json = referans_bul(a.p, a.referans)
    ref_meta = json.loads(ref_json.read_text(encoding="utf-8"))
    if int(ref_meta["p"]) != a.p:
        raise SystemExit(f"referans p={ref_meta['p']}, istenen p={a.p}")
    qc, problem = devre_kur(a.p, ref_meta["params"])
    tqc = transpile(qc, sim)
    print(f"devre hazir: p={a.p}, {len(qc.data)} kapi, cihaz {a.device}, referans {ref_json.name}")

    # Isinma: ilk kosum JIT/tahsis maliyeti tasir, olcume dahil edilmez.
    ilk = sim.run(tqc).result()
    meta = ilk.results[0].metadata
    # available_devices() tek basina yetmez: is GERCEKTEN istenen cihazda mi kostu
    if meta.get("device") != a.device:
        raise SystemExit(f"istenen {a.device}, kosulan {meta.get('device')}")
    ortam = _ortam(sim, meta, a.device)

    # Prensip IV: zamanlanacak devrenin ciktisi once altin referansa karsi
    dogrulama = dogrula(ilk, ref_json, ref_meta, problem)
    print(f"dogrulama      : fidelity {dogrulama['fidelity']:.15f} "
          f"(1-F {dogrulama['bir_eksi_F']:.2e}), P_opt {dogrulama['p_optimum_bu_kosum']:.6e} "
          f"(ref {dogrulama['p_optimum_referans']:.6e}) -> "
          f"{'GECTI' if dogrulama['gecti'] else 'KALDI'}")
    if a.yalniz_dogrula or not dogrulama["gecti"]:
        kayit = {"ne": "Aer statevector, altin referansa karsi (T066)",
                 "damga": stamp.stamp(device=a.device, p=a.p),
                 "ortam": ortam, "kapi": len(qc.data),
                 "transpile_sonrasi": dict(tqc.count_ops()), "dogrulama": dogrulama}
        yol = KOK / "docs" / "measurements" / (
            f"{stamp.stamped_name('aer-dogrulama')}_{a.device}_p{a.p}.json")
        yol.write_text(json.dumps(kayit, indent=2, ensure_ascii=False), encoding="utf-8")
        print(f"yazildi        : {yol.name}")
        if not dogrulama["gecti"]:
            raise SystemExit("⛔ fidelity H esiginin altinda -- ZAMANLAMA YAPILMADI")
        return 0

    onek = "cpu" if a.device == "CPU" else "gpu"
    ad = f"{onek}-yuk-dongu_{stamp.stamped_name('x').split('_')[1]}_{a.etiket}_p{a.p}.json"
    yol = KOK / "docs" / "measurements" / ad
    kismi = yol.with_suffix(".kismi.jsonl")
    kismi_f = kismi.open("w", encoding="utf-8")
    kismi_f.write(json.dumps({"ortam": ortam, "p": a.p}, ensure_ascii=False) + "\n")
    yazilan = 0

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
            # GK-01: pencerenin izini diske -- zamanlanan araligin DISINDA
            for t, ms in izler[yazilan:]:
                kismi_f.write(f"[{t:.6f}, {ms:.4f}]\n")
            yazilan = len(izler)
            kismi_f.flush()
            os.fsync(kismi_f.fileno())
    toplam = time.perf_counter() - bas
    kismi_f.close()

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
        "damga": stamp.stamp(device=a.device, saniye=a.saniye),
        "ortam": ortam,
        "dogrulama": dogrulama,
        "p": a.p,
        "kapi": len(qc.data),
        "transpile_sonrasi": dict(tqc.count_ops()),
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
    yol.write_text(json.dumps(ozet, indent=2, ensure_ascii=False), encoding="utf-8")
    kismi.unlink()      # tam ozet yazildi; kismi iz yalniz cokme kaniti icindi

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
