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

PROTOKOL (🔒 gpu-taban-protokolu v1.1, docs/measurements/gpu-taban-olcum-protokolu.md):
dogrulama kosumu zamanlanmaz, ilk 3 zamanlanmis kosum istatistige girmez,
istatistik kart protokolu §8'in AYNI kodu (agent/measure_latency.py), her
pencerede nvidia-smi, sonda son kosum ilk kosumla bit bit, kirli agactan
docs/measurements'a yazilmaz. Protokolden sapan her sey HATADIR.

Kullanim:
    .venv\Scripts\python.exe scripts\cpu_load_loop.py --saniye 300 --p 2
    # deneme (kirli agac, olcum degil):  --cikti-dizini /tmp/deneme
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
from agent import measure_latency as ml                # noqa: E402  (kart §8, AYNI kod)

PROTOKOL = "gpu-taban-protokolu v1.1"   # docs/measurements/gpu-taban-olcum-protokolu.md (§12)
KAPSAMLAR = ("kosum",)                  # protokol §5, katman 1: T_kosum


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


def _komut(argv: list[str], zaman_asimi: float = 15) -> str | None:
    """Yan komut (nvidia-smi, powercfg ...) -- basarisizsa None; olcumu durdurmaz."""
    try:
        out = subprocess.run(argv, capture_output=True, timeout=zaman_asimi)
    except (OSError, subprocess.SubprocessError):
        return None
    try:
        metin = out.stdout.decode("utf-8").strip()
    except UnicodeDecodeError:      # Windows konsol cikisi OEM kod sayfasinda (Turkce: cp857)
        metin = out.stdout.decode("cp857", errors="replace").strip()
    return metin if out.returncode == 0 and metin else None


def _nvidia_smi(alanlar: str) -> list[str] | None:
    for exe in ("nvidia-smi", "/usr/lib/wsl/lib/nvidia-smi"):
        m = _komut([exe, f"--query-gpu={alanlar}", "--format=csv,noheader,nounits"], 10)
        if m:
            return [s.strip() for s in m.splitlines()[0].split(",")]
    return None


def _gpu_bilgisi() -> dict | None:
    """GPU adi, surucu ve guc siniri (WSL'de nvidia-smi PATH disinda)."""
    d = _nvidia_smi("name,driver_version,power.limit")
    return {"ad": d[0], "surucu": d[1], "guc_siniri_W": d[2]} if d else None


def _gpu_durumu() -> dict:
    """Protokol §4 'GPU durumu': sicaklik, SM saati, guc cekisi (okunamazsa N/A)."""
    d = _nvidia_smi("temperature.gpu,clocks.sm,power.draw")
    return ({"sicaklik_C": d[0], "sm_saat_MHz": d[1], "guc_cekisi_W": d[2]} if d
            else {"sicaklik_C": "N/A", "sm_saat_MHz": "N/A", "guc_cekisi_W": "N/A"})


def _windows_guc() -> dict:
    """Protokol §4 'Guc': plan, guc modu (overlay) ve sebeke durumu -- WSL'den
    Windows komutlariyla, salt okunur. Okunamayan alan None."""
    ps = _komut(["powershell.exe", "-NoProfile", "-Command",
                 "(Get-CimInstance Win32_Battery).BatteryStatus"], 30)
    return {
        "plan": _komut(["powercfg.exe", "/getactivescheme"]),
        "mod_overlay_ac": _komut(["reg.exe", "query",
                                  r"HKLM\SYSTEM\CurrentControlSet\Control\Power\User\PowerSchemes",
                                  "/v", "ActiveOverlayAcPowerScheme"]),
        "batarya_durumu": ps,          # 2 = sebekede (AC)
        "sebekede": (ps == "2") if ps else None,
    }


def _kod_kirli() -> bool:
    """Protokol §4 'temiz agac' = IZLENEN dosyalarda degisiklik yok. Izlenmeyen
    dosyalar (bu serinin kismi izi, onceki serilerin ciktilari) KOD degildir.
    stamp.is_dirty() onlari da sayar; 28 Eyl'de A-CPU'nun ciktisi A-GPU'yu
    reddettirdi. Kiyas icin ikisi de kaydedilir."""
    try:
        out = subprocess.run(["git", "status", "--porcelain", "--untracked-files=no"],
                             capture_output=True, text=True, timeout=10, cwd=KOK)
    except (OSError, subprocess.SubprocessError):
        return True
    return out.returncode != 0 or bool(out.stdout.strip())


def _loadavg() -> str | None:
    try:
        return Path("/proc/loadavg").read_text().strip()
    except OSError:
        return None


def _ortam(sim, meta: dict, device: str) -> dict:
    import qiskit
    import qiskit_aer
    return {
        "qiskit": qiskit.__version__,
        "qiskit_aer": qiskit_aer.__version__,
        "python": platform.python_version(),
        "platform": platform.platform(),
        "nproc": os.cpu_count(),
        "max_parallel_threads": sim.options.max_parallel_threads,
        "aer_is_parcacigi": meta.get("parallel_state_update"),
        "device_istenen": device,
        "device_metadata": meta.get("device"),
        "precision": sim.options.precision,
        "cuStateVec_enable": meta.get("cuStateVec_enable"),
        "fusion": meta.get("fusion"),
        "gpu": _gpu_bilgisi(),
    }


def _sv_baytlari(sonuc) -> bytes:
    return np.ascontiguousarray(np.asarray(sonuc.get_statevector(), dtype=np.complex128)).tobytes()


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--saniye", type=int, default=int(ml.SERI_SURE_S))
    ap.add_argument("--p", type=int, default=2)
    ap.add_argument("--etiket", default="yuk")
    ap.add_argument("--device", choices=("CPU", "GPU"), default="CPU")
    ap.add_argument("--referans", default=None,
                    help="altin referans (.json/.npy); verilmezse en yeni tarihli")
    ap.add_argument("--yalniz-dogrula", action="store_true",
                    help="zamanlama yok; yalniz referansa karsi dogrulama kaydi (T066)")
    ap.add_argument("--is-parcacigi", type=int, default=None,
                    help="Aer max_parallel_threads (protokol v1.1 §12 Δ2); verilmezse Aer varsayilani")
    ap.add_argument("--cikti-dizini", default=None,
                    help="varsayilan docs/measurements; deneme kosulari icin baska dizin")
    a = ap.parse_args()

    cikti_dizini = Path(a.cikti_dizini) if a.cikti_dizini else KOK / "docs" / "measurements"
    resmi = cikti_dizini.resolve() == (KOK / "docs" / "measurements").resolve()
    # Protokol §4/§7: seri temiz agacta; kirli agactan olcum docs/measurements'a girmez
    kod_kirli_bas = _kod_kirli()
    if resmi and not a.yalniz_dogrula and kod_kirli_bas:
        raise SystemExit("⛔ izlenen dosyalarda degisiklik var -- protokol §4: seri temiz agacta kosulur "
                         "(deneme icin --cikti-dizini <baska dizin>)")

    from qiskit_aer import AerSimulator
    if a.device not in AerSimulator().available_devices():
        raise SystemExit(f"{a.device} yok: {AerSimulator().available_devices()} "
                         "(GPU yalniz WSL venv'inde, docs/runbooks/gpu-aer-wsl.md)")
    secenek = {} if a.is_parcacigi is None else {"max_parallel_threads": a.is_parcacigi}
    sim = AerSimulator(method="statevector", device=a.device, **secenek)

    ref_json = referans_bul(a.p, a.referans)
    ref_meta = json.loads(ref_json.read_text(encoding="utf-8"))
    if int(ref_meta["p"]) != a.p:
        raise SystemExit(f"referans p={ref_meta['p']}, istenen p={a.p}")
    qc, problem = devre_kur(a.p, ref_meta["params"])
    tqc = transpile(qc, sim)
    print(f"devre hazir: p={a.p}, {len(qc.data)} kapi, cihaz {a.device}, referans {ref_json.name}")

    # Protokol §6: dogrulama kosumu -- zamanlanmaz
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
        yol = cikti_dizini / f"{stamp.stamped_name('aer-dogrulama')}_{a.device}_p{a.p}.json"
        yol.write_text(json.dumps(kayit, indent=2, ensure_ascii=False), encoding="utf-8")
        print(f"yazildi        : {yol.name}")
        if not dogrulama["gecti"]:
            raise SystemExit("⛔ fidelity H esiginin altinda -- ZAMANLAMA YAPILMADI")
        return 0
    ilk_sv = _sv_baytlari(ilk)

    onek = "cpu" if a.device == "CPU" else "gpu"
    yol = cikti_dizini / f"{stamp.stamped_name(f'{onek}-yuk-dongu')}_{a.etiket}_p{a.p}.json"
    kismi = yol.with_suffix(".kismi.jsonl")
    kosullar_bas = {"zaman": time.strftime("%Y-%m-%dT%H:%M:%S%z"), "loadavg": _loadavg(),
                    "gpu": _gpu_durumu(), "guc": _windows_guc()}
    kismi_f = kismi.open("w", encoding="utf-8")
    kismi_f.write(json.dumps({"ortam": ortam, "p": a.p, "kosullar_bas": kosullar_bas},
                             ensure_ascii=False) + "\n")
    yazilan = 0

    print(f"{PROTOKOL} -- {a.saniye} sn donguye giriliyor... (DOKUNMA)")
    sureler = []            # saniye, zamanlanan her kosum
    zamanlar = []           # kosum baslangici, seri basindan saniye
    gpu_okumalari = []      # §4: pencere sinirinda GPU durumu
    gecersiz = None
    son = ilk
    bas = time.perf_counter()
    son_pencere = 0.0
    while time.perf_counter() - bas < a.saniye:
        t0 = time.perf_counter()
        r = sim.run(tqc).result()
        t1 = time.perf_counter()
        sureler.append(t1 - t0)
        zamanlar.append(t0 - bas)
        son = r
        # §7: her kosumda yalniz cihaz denetlenir -- zamanlanan araligin DISINDA
        if r.results[0].metadata.get("device") != a.device:
            gecersiz = f"kosum {len(sureler)}: cihaz {r.results[0].metadata.get('device')}"
            break
        gecen = t1 - bas
        if gecen - son_pencere >= ml.PENCERE_S:
            pencere = sorted(s for s, t in zip(sureler, zamanlar) if t >= son_pencere)
            durum = _gpu_durumu()
            gpu_okumalari.append({"t_s": round(gecen, 3), **durum})
            print(f"  {gecen:5.0f} sn   {len(sureler):6d} kosum   "
                  f"pencere medyani {pencere[len(pencere) // 2] * 1000:7.3f} ms   "
                  f"GPU {durum['sicaklik_C']} C")
            son_pencere = gecen
            # GK-01: pencerenin izi diske, fsync
            for t, s in zip(zamanlar[yazilan:], sureler[yazilan:]):
                kismi_f.write(f"[{t:.6f}, {s * 1000:.4f}]\n")
            yazilan = len(sureler)
            kismi_f.flush()
            os.fsync(kismi_f.fileno())
    toplam = time.perf_counter() - bas
    kismi_f.close()

    # §6 sonda: son kosumun statevector'u dogrulama kosumununkiyle BIT BIT ayni mi
    son_kosum_ayni = _sv_baytlari(son) == ilk_sv
    if gecersiz is None and not son_kosum_ayni:
        gecersiz = "son kosumun statevector'u dogrulama kosumununkinden farkli (§6)"
    kosullar_son = {"zaman": time.strftime("%Y-%m-%dT%H:%M:%S%z"), "loadavg": _loadavg(),
                    "gpu": _gpu_durumu(), "guc": _windows_guc()}

    # §6 isinma: ilk ISINMA zamanlanmis kosum istatistige girmez (ham izde kalir)
    s_ist, z_ist = sureler[ml.ISINMA:], zamanlar[ml.ISINMA:]
    konfig = f"aer_{a.device}_n16_p{a.p}"
    kw = {"kapsamlar": KAPSAMLAR, "protokol_surumu": PROTOKOL}
    pen = ml.pencereler(z_ist, s_ist)
    for p_ in pen:          # pencereye, BITISINE en yakin GPU okumasini ekle
        bitis = p_["bas_s"] + ml.PENCERE_S
        yakin = min(gpu_okumalari, key=lambda g: abs(g["t_s"] - bitis), default=None)
        p_["gpu"] = yakin if yakin and abs(yakin["t_s"] - bitis) <= ml.PENCERE_S / 2 else None

    def _med_ms(xs):
        return round(float(np.median(xs)) * 1000, 3) if xs else None

    ozet = {
        "ne": "Aer gecikme serisi (6B, katman 1)",
        "protokol_surumu": PROTOKOL,
        "gecerli": gecersiz is None,
        "gecersizlik_nedeni": gecersiz,
        "etiket": a.etiket,
        "damga": stamp.stamp(device=a.device, saniye=a.saniye, p=a.p),
        # damga.git_dirty izlenmeyen dosyalari da sayar (bu serinin kismi izi dahil);
        # protokol §4'un olctugu sey kod_kirli_*: izlenen dosyalar
        "kod_kirli_bas": kod_kirli_bas,
        "kod_kirli_son": _kod_kirli(),
        "ortam": ortam,
        "kosullar_bas": kosullar_bas,
        "kosullar_son": kosullar_son,
        "dogrulama": dogrulama,
        "son_kosum_ayni": son_kosum_ayni,
        "p": a.p,
        "kapi": len(qc.data),
        "transpile_sonrasi": dict(tqc.count_ops()),
        "toplam_saniye": round(toplam, 3),
        "zamanlanan_kosum": len(sureler),
        "isinma_atilan": min(ml.ISINMA, len(sureler)),
        "verim_kosum_sn": round(len(sureler) / toplam, 4),
        "seri": ml.olcum_serisi(konfig, "kosum", s_ist, **kw),
        "ilk_ve_son": ml.ilk_ve_son(konfig, "kosum", z_ist, s_ist, **kw),
        "pencereler": pen,
        "plato": ml.plato(pen),
        # 19 Eyl Windows serisiyle ayni TANIM (kiyas icin degil, sureklilik icin)
        "eski_tanim": {
            "turbo_ms": _med_ms([s for s, t in zip(sureler, zamanlar) if t < 2.0]),
            "plato_ms": _med_ms([s for s, t in zip(sureler, zamanlar)
                                 if t >= max(toplam - 60.0, toplam * 2 / 3)]),
        },
        "ham_iz_ms": [[round(t, 6), round(s * 1000, 4)] for t, s in zip(zamanlar, sureler)],
    }
    yol.write_text(json.dumps(ozet, indent=1, ensure_ascii=False), encoding="utf-8")
    kismi.unlink()      # tam ozet yazildi; kismi iz yalniz cokme kaniti icindi

    sr, pl = ozet["seri"], ozet["plato"]
    print()
    print(f"gecerli        : {ozet['gecerli']}" + (f"  ({gecersiz})" if gecersiz else ""))
    print(f"kosum          : {len(sureler)} (isinma {ozet['isinma_atilan']} atildi), "
          f"verim {ozet['verim_kosum_sn']} kosum/sn")
    print(f"medyan / IQR   : {sr['medyan_s'] * 1000:.3f} ms / {sr['yayilim_s'] * 1000:.3f} ms  "
          f"(p99 {sr['p99_s'] * 1000:.3f}, maks {sr['max_s'] * 1000:.3f})")
    print(f"plato (±%0,5)  : {pl.get('oturdu')}  "
          f"(en buyuk sapma {pl.get('en_buyuk_sapma_orani', float('nan')):.4f})")
    print(f"son kosum ayni : {son_kosum_ayni}")
    print(f"yazildi        : {yol}")
    return 0 if ozet["gecerli"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
