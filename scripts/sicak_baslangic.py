"""6D (T074–T077): sıcak başlangıç ve sabit açı — optimize edici döngüsü kaç
çekirdek çağrısı ister, çözüm kalitesi ne olur.

Protokol: docs/measurements/sicak-baslangic-protokolu.md — önce DONAR, sonra
koşulur (FR-011). Bu betik protokolün yürütücüsüdür; tasarım sabitleri (örnek
tohumları, koşullar, beklentilerin ölçütleri) protokolle birlikte dondurulur.

Amaç fonksiyonu çekirdeğin Python ikizi (`native_formulation.py`; Qiskit'e
karşı ⟨E⟩ farkı ~1e-8). Yalnız RX vektörleştirildi. Kapı (protokol §5) başta
ikisini de denetler: hızlı RX yerleşikle bit bit aynı, ⟨E⟩ Qiskit'le < 1e-6.

Kullanım:
    .venv\\Scripts\\python.exe scripts\\sicak_baslangic.py            # ölçüm (temiz ağaç)
    .venv\\Scripts\\python.exe scripts\\sicak_baslangic.py --deneme   # yalnız akış, repo dışına
"""
from __future__ import annotations

import os

for _d in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS"):
    os.environ.setdefault(_d, "1")      # süreç başına tek iş parçacığı; paralellik süreçlerde

import argparse                                                # noqa: E402
import csv                                                     # noqa: E402
import json                                                    # noqa: E402
import platform                                                # noqa: E402
import subprocess                                              # noqa: E402
import sys                                                     # noqa: E402
import tempfile                                                # noqa: E402
import time                                                    # noqa: E402
from concurrent.futures import ProcessPoolExecutor             # noqa: E402
from pathlib import Path                                       # noqa: E402

import numpy as np                                             # noqa: E402
import scipy                                                   # noqa: E402
from scipy.optimize import minimize                            # noqa: E402
from scipy.stats import wilcoxon                               # noqa: E402

KOK = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(KOK))
from services.common import stamp                              # noqa: E402
from services.qubo import brute_force, qubo as qubo_mod        # noqa: E402
from services.reference import qaoa_reference as qr            # noqa: E402
from services.reference.cli import ornek_matris                # noqa: E402
from scripts import native_formulation as nf                   # noqa: E402

PROTOKOL = "sicak-baslangic-protokolu v1.0"
PROTOKOL_DOSYASI = KOK / "docs" / "measurements" / "sicak-baslangic-protokolu.md"
CSV_YOLU = KOK / "data" / "synthetic" / "deliveries.csv"

N_DURAK = 5
ORNEKLER = list(range(1, 21))        # I1–I20 (I0 = referans örneği, yalnız kapıda)
EGITIM = list(range(1, 11))          # sabit açı: açılar bunlardan çıkarılır
TEST = list(range(11, 21))           # sabit açı: bunlara uygulanır
TOHUMLAR = list(range(5))
P_LER = (2, 1)                       # p=2 manşet (kart p=2), p=1 ikincil
REJIMLER = ("R", "N")                # R: ham H (referans gibi), N: γ/s, s = max|h|,|J|
MAXITER = qr.MAX_QAOA_ITER           # referansla aynı (100)
TOL = 1e-6                           # referansla aynı (qaoa_reference.run)
RHOBEG = {"C1": 1.0, "C2": 0.1, "W1": 1.0, "W2": 0.1}
KART_P2_MS = 36.578                  # kart-gecikme_20260927_201475a_n16_p2, medyan
SANIYE_ALTI_NFEV = int(1000 // KART_P2_MS)      # 27 çağrı × 36,578 ms = 0,988 s
# Sonda seri olarak yeniden koşulup bit bit karşılaştırılan işler (faz, rejim, p, örnek, koşul, tohum)
TEKRAR = [("T074", "R", 2, 1, "C1", 0), ("T074", "N", 2, 7, "C1", 3),
          ("T075", "N", 2, 12, "W2", 1), ("T075", "R", 1, 20, "C2", 4)]


# ------------------------------------------------------------------ örnekler
def _csv() -> list[dict]:
    return list(csv.DictReader(CSV_YOLU.open(encoding="utf-8")))


def ornek_satirlari(k: int) -> list[int]:
    """I_k'nın CSV satırları (ilki depo). I0 = referans örneği (ilk 5 satır)."""
    if k == 0:
        return list(range(N_DURAK))
    rng = np.random.default_rng(1000 + k)
    return [int(i) for i in rng.choice(len(_csv()), N_DURAK, replace=False)]


def degistir(k: int, satirlar: list[int]) -> tuple[list[int], dict]:
    """I_k' = I_k'da bir durağın adresi değişir (artımlı yol). Depo değişmez;
    yeni adres aynı ilçeden, ilçede aday yoksa en yakın teslimattan."""
    rng = np.random.default_rng(2000 + k)
    tum = _csv()
    konum = int(rng.integers(1, N_DURAK))
    eski = satirlar[konum]
    ilce = tum[eski]["district"]
    adaylar = [i for i in range(len(tum)) if i not in satirlar and tum[i]["district"] == ilce]
    kural = "ayni_ilce"
    if not adaylar:
        diger = [i for i in range(len(tum)) if i not in satirlar]
        sure = [ornek_matris(2, [eski, i])[0, 1] for i in diger]
        adaylar = [diger[int(np.argmin(sure))]]
        kural = "en_yakin"
    yeni = int(rng.choice(adaylar))
    s2 = list(satirlar)
    s2[konum] = yeni
    return s2, {"konum": konum, "eski_satir": eski, "yeni_satir": yeni,
                "ilce": ilce, "kural": kural}


class Problem:
    def __init__(self, ad: str, satirlar: list[int]):
        self.ad = ad
        self.satirlar = [int(i) for i in satirlar]
        self.d = ornek_matris(N_DURAK, self.satirlar)
        self.q = qubo_mod.matrix_to_qubo(self.d)
        self.h, self.J, self.offset = qr.ising_katsayilari(self.q)
        self.n = self.q.n_vars
        self.E = nf.enerji_tablosu(self.h, self.J, self.n)
        self.s = float(max(np.abs(self.h).max(), np.abs(self.J).max()))
        self.turlar = list(brute_force.all_tours(N_DURAK))
        uzun = np.array([brute_force.tour_length(self.d, t) for t in self.turlar])
        self.gecerli_idx = np.array([self._indeks(t) for t in self.turlar])
        opt = np.flatnonzero(uzun <= uzun.min() + 1e-9)
        self.opt_idx = self.gecerli_idx[opt]
        self.opt_turlar = [self.turlar[i] for i in opt]
        self.E_opt = float(self.E[self.opt_idx[0]])
        # Kapı G4: geçerli turlarda QUBO enerjisi = tur uzunluğu + sabit, ve E_opt < 0
        fark = self.E[self.gecerli_idx] + self.offset - uzun
        if np.ptp(fark) > 1e-6 or not self.E_opt < 0:
            raise RuntimeError(f"{ad}: QUBO ile tur uzunlugu tutarsiz (ptp {np.ptp(fark):.3e})")
        self.taban_gecerli = bool(np.isin(int(np.argmin(self.E)), self.gecerli_idx))

    def _indeks(self, tur: list[int]) -> int:
        return sum(1 << self.q.var_map[(sehir, t)] for t, sehir in enumerate(tur[1:]))

    def ozet(self) -> dict:
        return {"ad": self.ad, "satirlar": self.satirlar, "s": self.s, "E_opt": self.E_opt,
                "offset": self.offset, "opt_turlar": self.opt_turlar,
                "taban_gecerli": self.taban_gecerli,
                "spektral_genislik": float(self.E.max() - self.E.min())}


# ------------------------------------------------------------------ devre
def rx_hizli(sv: np.ndarray, theta: float, k: int) -> np.ndarray:
    """nf.apply_rx'in vektörleştirilmiş hâli (aynı çiftler, aynı aritmetik)."""
    c, s = np.cos(theta / 2.0), np.sin(theta / 2.0)
    v = sv.reshape(-1, 2, 1 << k)
    a, b = v[:, 0, :], v[:, 1, :]
    out = np.empty_like(v)
    out[:, 0, :] = c * a - 1j * s * b
    out[:, 1, :] = -1j * s * a + c * b
    return out.reshape(-1)


def acilar(theta, p: int, rejim: str, s: float) -> tuple[np.ndarray, np.ndarray]:
    """θ, Qiskit parametre sırasıyla: [β_0..β_{p-1}, γ_0..γ_{p-1}]. N'de γ = γ̃/s."""
    theta = np.asarray(theta, dtype=float)
    beta, gamma = theta[:p], theta[p:]
    return beta, (gamma / s if rejim == "N" else gamma)


def durum(pr: Problem, beta, gamma) -> np.ndarray:
    sv = nf.init_uniform(pr.n)
    for b, g in zip(beta, gamma):
        sv = sv * np.exp(-1j * g * pr.E)
        for k in range(pr.n):
            sv = rx_hizli(sv, 2.0 * b, k)
    return sv


def amac(pr: Problem, theta, p: int, rejim: str) -> float:
    return nf.beklenen_deger(durum(pr, *acilar(theta, p, rejim, pr.s)), pr.E)


def olcutler(pr: Problem, sv: np.ndarray) -> dict:
    pb = np.abs(sv) ** 2
    pb = pb / pb.sum()
    pg = pb[pr.gecerli_idx]
    p_opt = float(pb[pr.opt_idx].sum())
    en_olasi = int(pr.gecerli_idx[int(np.argmax(pg))])
    return {"r": float(pb @ pr.E) / pr.E_opt, "P_opt": p_opt, "P_gecerli": float(pg.sum()),
            "opt_sira": int(1 + np.sum(pg > pb[pr.opt_idx].max())),
            "en_olasi_gecerli_optimal": en_olasi in set(pr.opt_idx.tolist())}


# ------------------------------------------------------------------ koşum
_ONBELLEK: dict[str, Problem] = {}


def _problem(ad: str, satirlar: list[int]) -> Problem:
    if ad not in _ONBELLEK:
        _ONBELLEK[ad] = Problem(ad, satirlar)
    return _ONBELLEK[ad]


def is_kos(is_: dict) -> dict:
    pr = _problem(is_["problem"], is_["satirlar"])
    p, rejim = is_["p"], is_["rejim"]
    t0 = time.perf_counter()
    r = minimize(lambda th: amac(pr, th, p, rejim), np.asarray(is_["x0"], dtype=float),
                 method="COBYLA",
                 options={"maxiter": is_["maxiter"], "tol": TOL, "rhobeg": is_["rhobeg"]})
    sure = time.perf_counter() - t0
    sv = durum(pr, *acilar(r.x, p, rejim, pr.s))
    sonuc = {k: is_[k] for k in ("faz", "rejim", "p", "ornek", "problem", "kosul", "tohum",
                                 "rhobeg")}
    sonuc.update({"x0": [float(v) for v in is_["x0"]], "x_son": [float(v) for v in r.x],
                  "nfev": int(r.nfev), "durum": int(r.status), "mesaj": str(r.message),
                  "tavan": bool(r.nfev >= is_["maxiter"]), "E_son": float(r.fun),
                  **olcutler(pr, sv), "sure_s": round(sure, 3)})
    return sonuc


def _anahtar(k: dict) -> tuple:
    return (k["faz"], k["rejim"], k["p"], k["ornek"], k["kosul"], k["tohum"])


def x0_soguk(k: int, tohum: int, p: int) -> list[float]:
    return [float(v) for v in np.random.default_rng([k, tohum]).uniform(0, np.pi, 2 * p)]


def isler_t074(ornekler, satir, maxiter) -> list[dict]:
    return [{"faz": "T074", "rejim": rj, "p": p, "ornek": k, "problem": f"I{k}",
             "satirlar": satir[k], "kosul": "C1", "tohum": t, "x0": x0_soguk(k, t, p),
             "rhobeg": RHOBEG["C1"], "maxiter": maxiter}
            for rj in REJIMLER for p in P_LER for k in ornekler for t in TOHUMLAR]


def isler_t075(ornekler, satir_d, t074: dict, maxiter) -> list[dict]:
    isler = []
    for rj in REJIMLER:
        for p in P_LER:
            for k in ornekler:
                for t in TOHUMLAR:
                    temel = {"faz": "T075", "rejim": rj, "p": p, "ornek": k,
                             "problem": f"I{k}'", "satirlar": satir_d[k], "tohum": t,
                             "maxiter": maxiter}
                    sicak = t074[("T074", rj, p, k, "C1", t)]["x_son"]
                    for kosul, x0 in (("C1", x0_soguk(k, t, p)), ("C2", x0_soguk(k, t, p)),
                                      ("W1", sicak), ("W2", sicak)):
                        isler.append({**temel, "kosul": kosul, "x0": list(x0),
                                      "rhobeg": RHOBEG[kosul]})
    return isler


# ------------------------------------------------------------------ kapı
def kapi(I0: Problem) -> dict:
    from qiskit.circuit.library import QAOAAnsatz
    from qiskit.quantum_info import Statevector

    sonuc = {}
    rng = np.random.default_rng(7)
    sv = rng.normal(size=1 << I0.n) + 1j * rng.normal(size=1 << I0.n)
    sonuc["G1_rx_azami_fark"] = max(
        float(np.abs(rx_hizli(sv, 0.7, k) - nf.apply_rx(sv, 0.7, k, I0.n)).max())
        for k in range(I0.n))
    op, _ = qr._qubo_to_ising(I0.q)
    g2 = []
    for p in (1, 2):
        a = QAOAAnsatz(cost_operator=op, reps=p).decompose(reps=3)
        for _ in range(4):
            th = rng.uniform(0, np.pi, 2 * p)
            q = float(np.real(Statevector.from_instruction(a.assign_parameters(th))
                              .expectation_value(op)))
            g2.append(abs(q - amac(I0, th, p, "R")))
    sonuc["G2_qiskit_azami_fark"] = max(g2)
    g3 = {}
    for p in (1, 2):
        ref = json.loads((KOK / "docs" / "measurements" /
                          f"reference_20260915_c6ad872_p{p}_n5.json").read_text(encoding="utf-8"))
        th = [ref["params"][f"β[{i}]"] for i in range(p)] + \
             [ref["params"][f"γ[{i}]"] for i in range(p)]
        m = olcutler(I0, durum(I0, *acilar(th, p, "R", I0.s)))
        g3[f"p{p}"] = {"P_opt": m["P_opt"], "referans": ref["optimal_probability"],
                       "goreli_fark": abs(m["P_opt"] / ref["optimal_probability"] - 1),
                       "E": amac(I0, th, p, "R"), "referans_E": ref["cost_after"]}
    sonuc["G3_referans"] = g3
    sonuc["G5_ayarlar"] = {"maxiter": MAXITER, "tol": TOL}
    sonuc["gecti"] = bool(
        sonuc["G1_rx_azami_fark"] <= 1e-14 and sonuc["G2_qiskit_azami_fark"] <= 1e-6
        and all(v["goreli_fark"] <= 1e-9 and abs(v["E"] - v["referans_E"]) <= 1e-6
                for v in g3.values())
        and MAXITER == 100 and TOL == 1e-6)
    return sonuc


# ------------------------------------------------------------------ özet ve beklentiler
def _med(x) -> float | None:
    return float(np.median(x)) if len(x) else None


def _ceyrekler(x) -> list[float] | None:
    return [float(v) for v in np.percentile(x, [25, 50, 75])] if len(x) else None


def _wilcoxon(a, b) -> float | None:
    a, b = np.asarray(a, float), np.asarray(b, float)
    if len(a) < 6:
        return None
    if np.all(a == b):
        return 1.0
    return float(wilcoxon(a, b).pvalue)


def _ornek_duzeyi(kosumlar, faz, rejim, p, kosul, olcut, ornekler) -> list[float]:
    """Her örnek için 5 tohumun medyanı -> örnek düzeyi değerler (örnek sırasıyla)."""
    return [_med([k[olcut] for k in kosumlar if (k["faz"], k["rejim"], k["p"], k["kosul"],
                                                 k["ornek"]) == (faz, rejim, p, kosul, o)])
            for o in ornekler]


def ozet_ve_beklentiler(kosumlar, s_sonuclari, ornekler) -> tuple[dict, dict]:
    ozet = {}
    for faz, kosullar in (("T074", ("C1",)), ("T075", ("C1", "C2", "W1", "W2"))):
        for rj in REJIMLER:
            for p in P_LER:
                for ks in kosullar:
                    sec = [k for k in kosumlar if (k["faz"], k["rejim"], k["p"], k["kosul"])
                           == (faz, rj, p, ks)]
                    if not sec:
                        continue
                    ozet[f"{faz}/{rj}/p{p}/{ks}"] = {
                        "kosum": len(sec),
                        "nfev_ceyrek": _ceyrekler([k["nfev"] for k in sec]),
                        "r_ceyrek": _ceyrekler([k["r"] for k in sec]),
                        "P_opt_ceyrek": _ceyrekler([k["P_opt"] for k in sec]),
                        "P_opt_duzgun_kati_medyan": _med([k["P_opt"] for k in sec]) * 65536,
                        "P_gecerli_medyan": _med([k["P_gecerli"] for k in sec]),
                        "tavan_orani": float(np.mean([k["tavan"] for k in sec])),
                        "en_olasi_optimal_orani": float(np.mean(
                            [k["en_olasi_gecerli_optimal"] for k in sec])),
                        "kart_gecikme_ms_turetilmis": _med([k["nfev"] for k in sec]) * KART_P2_MS,
                    }
    for rj in REJIMLER:
        for p in P_LER:
            sec = [s for s in s_sonuclari if (s["rejim"], s["p"]) == (rj, p)]
            if sec:
                ozet[f"T076/{rj}/p{p}/S"] = {
                    "problem": len(sec), "nfev": 1,
                    "r_ceyrek": _ceyrekler([s["r"] for s in sec]),
                    "P_opt_ceyrek": _ceyrekler([s["P_opt"] for s in sec]),
                    "P_opt_orani_ceyrek": _ceyrekler([s["P_opt_orani"] for s in sec]),
                    "kart_gecikme_ms_turetilmis": KART_P2_MS}

    bek = {}
    for p in P_LER:
        o = {}
        aralik = {rj: [] for rj in REJIMLER}
        for rj in REJIMLER:
            for k in ornekler:
                r = [x["r"] for x in kosumlar if (x["faz"], x["rejim"], x["p"], x["kosul"],
                                                  x["ornek"]) == ("T074", rj, p, "C1", k)]
                aralik[rj].append(max(r) - min(r))
        say = int(sum(a > b for a, b in zip(aralik["R"], aralik["N"])))
        o["H1"] = {"olcut": "r araligi (5 tohum) R > N olan ornek sayisi >= 15/20",
                   "deger": say, "ornek": len(ornekler), "tuttu": say >= 15}

        pr_ = {rj: _ornek_duzeyi(kosumlar, "T074", rj, p, "C1", "P_opt", ornekler)
               for rj in REJIMLER}
        oran = _med(pr_["N"]) / _med(pr_["R"])
        pw = _wilcoxon(pr_["N"], pr_["R"])
        o["H2"] = {"olcut": "P_opt ornek duzeyi medyani N/R >= 2 ve Wilcoxon p < 0,05",
                   "oran": oran, "p": pw,
                   "tuttu": bool(oran >= 2 and pw is not None and pw < 0.05)}

        for rj, h in (("N", "H3"), ("R", "H4")):
            rW2 = _ornek_duzeyi(kosumlar, "T075", rj, p, "W2", "r", ornekler)
            rC2 = _ornek_duzeyi(kosumlar, "T075", rj, p, "C2", "r", ornekler)
            pw = _wilcoxon(rW2, rC2)
            nW2 = _med(_ornek_duzeyi(kosumlar, "T075", rj, p, "W2", "nfev", ornekler))
            nC1 = _med(_ornek_duzeyi(kosumlar, "T075", rj, p, "C1", "nfev", ornekler))
            ust = _med(rW2) > _med(rC2)
            if h == "H3":
                o[h] = {"olcut": "N: r(W2) > r(C2), Wilcoxon p < 0,05; ve nfev(W2) <= 0,5*nfev(C1)",
                        "r_W2": _med(rW2), "r_C2": _med(rC2), "p": pw,
                        "nfev_W2": nW2, "nfev_C1": nC1,
                        "tuttu": bool(ust and pw is not None and pw < 0.05 and nW2 <= 0.5 * nC1)}
            else:
                o[h] = {"olcut": "R: r(W2) ile r(C2) farki anlamsiz (Wilcoxon p >= 0,05)",
                        "r_W2": _med(rW2), "r_C2": _med(rC2), "p": pw,
                        "tuttu": bool(pw is not None and pw >= 0.05)}

        oranlar = {rj: _med([s["P_opt_orani"] for s in s_sonuclari
                             if (s["rejim"], s["p"]) == (rj, p)]) for rj in REJIMLER}
        o["H5"] = {"olcut": "Sabit aci P_opt / C1 P_opt medyani: N >= 0,5 ve R < 0,5",
                   "N": oranlar["N"], "R": oranlar["R"],
                   "tuttu": bool(oranlar["N"] is not None and oranlar["N"] >= 0.5
                                 and oranlar["R"] < 0.5)}

        medyanlar = {anahtar: v["nfev_ceyrek"][1] for anahtar, v in ozet.items()
                     if anahtar.split("/")[2] == f"p{p}" and not anahtar.startswith("T076")}
        o["H6"] = {"olcut": f"COBYLA'li hicbir kosulun nfev medyani <= {SANIYE_ALTI_NFEV} degil",
                   "medyanlar": medyanlar,
                   "tuttu": bool(medyanlar and min(medyanlar.values()) > SANIYE_ALTI_NFEV)}
        bek[f"p{p}"] = o
    bek["manset"] = "p2"
    return ozet, bek


# ------------------------------------------------------------------ ana akış
def _git_blob(yol: Path) -> str | None:
    try:
        out = subprocess.run(["git", "hash-object", str(yol)], capture_output=True, text=True,
                             timeout=10, cwd=KOK)
        return out.stdout.strip() or None
    except (OSError, subprocess.SubprocessError):
        return None


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--deneme", action="store_true",
                    help="akış sınaması: yalnız I0, 1 tohum, maxiter 5, çıktı repo dışına")
    ap.add_argument("--surec", type=int, default=min(8, os.cpu_count() or 1))
    args = ap.parse_args()

    global ORNEKLER, EGITIM, TEST, TOHUMLAR
    if args.deneme:
        ORNEKLER, EGITIM, TEST, TOHUMLAR = [0], [0], [0], [0]
        maxiter = 5
        cikti = Path(tempfile.gettempdir()) / "qir-6d-deneme"
        cikti.mkdir(exist_ok=True)
    else:
        from scripts.cpu_load_loop import _kod_kirli
        if _kod_kirli():
            raise SystemExit("agac kirli — once commit (protokol §8)")
        maxiter = MAXITER
        cikti = stamp.measurements_dir(KOK)

    t_bas = time.perf_counter()
    I0 = Problem("I0", ornek_satirlari(0))
    k = kapi(I0)
    print(f"kapi: {'GECTI' if k['gecti'] else 'KALDI'}  (G1 {k['G1_rx_azami_fark']:.1e}, "
          f"G2 {k['G2_qiskit_azami_fark']:.1e})")
    if not k["gecti"]:
        raise SystemExit("kapi kaldi — olcum yapilmadi (protokol §5)")

    satir, satir_d, degisim, problemler = {}, {}, {}, {}
    for o in ORNEKLER:
        satir[o] = ornek_satirlari(o)
        satir_d[o], degisim[o] = degistir(o, satir[o])
        a, b = Problem(f"I{o}", satir[o]), Problem(f"I{o}'", satir_d[o])
        degisim[o]["opt_tur_degisti"] = a.opt_turlar != b.opt_turlar
        degisim[o]["matris_goreli_degisim"] = float(np.linalg.norm(b.d - a.d) /
                                                    np.linalg.norm(a.d))
        problemler[a.ad], problemler[b.ad] = a.ozet(), b.ozet()

    with ProcessPoolExecutor(max_workers=args.surec) as ex:
        is1 = isler_t074(ORNEKLER, satir, maxiter)
        print(f"T074: {len(is1)} kosum ...", flush=True)
        k1 = list(ex.map(is_kos, is1, chunksize=4))
        t074 = {_anahtar(x): x for x in k1}
        is2 = isler_t075(ORNEKLER, satir_d, t074, maxiter)
        print(f"T075: {len(is2)} kosum ...", flush=True)
        k2 = list(ex.map(is_kos, is2, chunksize=4))
    kosumlar = sorted(k1 + k2, key=_anahtar)

    # T076: eğitim örneklerinde en iyi (en düşük ⟨E⟩) C1 sonucu, bileşen bileşen medyan
    sabit, s_sonuclari = {}, []
    for rj in REJIMLER:
        for p in P_LER:
            en_iyi = []
            for o in EGITIM:
                sec = [t074[("T074", rj, p, o, "C1", t)] for t in TOHUMLAR]
                en_iyi.append(min(sec, key=lambda x: x["E_son"])["x_son"])
            th = [float(v) for v in np.median(np.array(en_iyi), axis=0)]
            sabit[f"{rj}/p{p}"] = th
            for o in TEST:
                for ad, srt, faz in ((f"I{o}", satir[o], "T074"), (f"I{o}'", satir_d[o], "T075")):
                    pr = _problem(ad, srt)
                    m = olcutler(pr, durum(pr, *acilar(th, p, rj, pr.s)))
                    c1 = _med([x["P_opt"] for x in kosumlar if (x["faz"], x["rejim"], x["p"],
                               x["kosul"], x["problem"]) == (faz, rj, p, "C1", ad)])
                    s_sonuclari.append({"rejim": rj, "p": p, "problem": ad, "theta": th,
                                        **m, "C1_P_opt_medyan": c1, "P_opt_orani": m["P_opt"] / c1})

    # Sonda belirlenimcilik: seçili işler seri yeniden koşulur, bit bit
    tum = {_anahtar(x): x for x in kosumlar}
    belirlenim = []
    for anahtar in (TEKRAR if not args.deneme else [_anahtar(kosumlar[0])]):
        eski = tum[anahtar]
        isler = (isler_t074(ORNEKLER, satir, maxiter) if anahtar[0] == "T074"
                 else isler_t075(ORNEKLER, satir_d, t074, maxiter))
        is_ = next(i for i in isler if _anahtar(i) == anahtar)
        yeni = is_kos(is_)
        belirlenim.append({"is": list(anahtar), "ayni": yeni["x_son"] == eski["x_son"]
                           and yeni["nfev"] == eski["nfev"] and yeni["E_son"] == eski["E_son"]})
    ayni = all(b["ayni"] for b in belirlenim)

    ozet, bek = ozet_ve_beklentiler(kosumlar, s_sonuclari, ORNEKLER)
    import qiskit
    kayit = {
        "protokol": PROTOKOL, "protokol_blob": _git_blob(PROTOKOL_DOSYASI),
        "deneme": bool(args.deneme),
        **stamp.stamp(n=16, durak=N_DURAK, p=list(P_LER), rejimler=list(REJIMLER),
                      ornekler=ORNEKLER, tohumlar=TOHUMLAR, maxiter=maxiter, tol=TOL,
                      rhobeg=RHOBEG),
        "ortam": {"python": platform.python_version(), "numpy": np.__version__,
                  "scipy": scipy.__version__, "qiskit": qiskit.__version__,
                  "makine": platform.platform(), "surec": args.surec},
        "kapi": k, "problemler": problemler, "degisimler": degisim,
        "sabit_acilar": sabit, "S_sonuclari": s_sonuclari,
        "belirlenimcilik": {"ayni": ayni, "isler": belirlenim},
        "gecerli": bool(k["gecti"] and ayni),
        "ozet": ozet, "beklentiler": bek, "kosumlar": kosumlar,
        "sure_s": round(time.perf_counter() - t_bas, 1),
    }
    yol = cikti / f"{stamp.stamped_name('sicak-baslangic')}.json"
    yol.write_text(json.dumps(kayit, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"belirlenimcilik: {'AYNI' if ayni else 'FARKLI'}; {len(kosumlar)} kosum, "
          f"{kayit['sure_s']} s")
    print(f"yazildi: {yol}")


if __name__ == "__main__":
    main()
