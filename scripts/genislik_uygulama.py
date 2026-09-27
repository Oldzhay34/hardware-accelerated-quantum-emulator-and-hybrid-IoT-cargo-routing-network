"""6C eki — genişlik, UYGULAMA düzeyindeki çıktıyı değiştiriyor mu?

Fidelity tek bir sayıdır ve "fazla bit bir işe yarar mı" sorusunu tek başına
cevaplamaz: 1 − F küçük olsa da tek bir çıktının olasılığı (ör. optimum rota,
2,4·10⁻⁵) göreli olarak büyük sapabilir — sınır yalnızca TVD ≤ √(1 − F)'dir.
Bu betik her genişliğin ham statevector'ünden, altın referansın kendi
tanımlarıyla (services/reference/qaoa_reference.py) şunları hesaplar:

  - optimum rotanın olasılığı ve referansa göre bağıl hatası
  - 24 geçerli turun toplam olasılığı
  - QUBO enerjisinin beklenen değeri ⟨E⟩ ve bağıl hatası
  - en olası geçerli tur ve 24 turun olasılık sıralaması referansla aynı mı
  - dağılımlar arası toplam varyasyon uzaklığı (TVD)

Olasılıklar normlanmış |a|²'dir (sabit noktalı durum tam birim normda değil;
norm ayrıca raporlanır).

Girdi : <dizin>/W<n>/sv_n16_p{1,2}.npy + csim-fidelity_*_p{1,2}.json
        (hls/genislik_tarama.sh üretir; kullandığı referans JSON'dan okunur)
Çıktı : docs/measurements/genislik-uygulama_<tarih>_<git-hash>.json

Kullanım:
    .venv\\Scripts\\python.exe scripts\\genislik_uygulama.py hls\\build\\genislik
"""
from __future__ import annotations

import glob
import json
import sys
from pathlib import Path

import numpy as np

KOK = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(KOK))
from services.common import stamp                          # noqa: E402
from services.qubo import qubo as qubo_mod                 # noqa: E402
from services.reference.cli import ornek_matris            # noqa: E402
from services.reference.qaoa_reference import _tum_enerjiler  # noqa: E402

GENISLIKLER = (14, 16, 18, 20, 24)


def problem_ve_turlar():
    """Referansla AYNI problem (cli.py: matrix_to_qubo(ornek_matris(5)))."""
    problem = qubo_mod.matrix_to_qubo(ornek_matris(5))
    n = problem.n_vars
    enerjiler = _tum_enerjiler(problem)
    gecerli = {}
    for idx in range(2 ** n):
        bits = np.array([(idx >> k) & 1 for k in range(n)], dtype=np.int8)
        tur = qubo_mod.assignment_to_tour(problem, bits)
        if tur is not None:
            gecerli[idx] = tur
    # referansin tanimi: gecerli turlar icinde en dusuk enerjili
    en_iyi = min(gecerli, key=lambda i: enerjiler[i])
    return enerjiler, gecerli, en_iyi


def olcutler(sv: np.ndarray, enerjiler, gecerli, en_iyi) -> dict:
    norm2 = float(np.vdot(sv, sv).real)
    pr = np.abs(sv) ** 2 / norm2
    idx = np.fromiter(gecerli, dtype=np.int64)
    sira = idx[np.argsort(-pr[idx], kind="stable")]
    return {
        "norm2": norm2,
        "p_optimum": float(pr[en_iyi]),
        "p_gecerli_toplam": float(pr[idx].sum()),
        "beklenen_enerji": float(pr @ enerjiler),
        "en_olasi_gecerli_tur_idx": int(sira[0]),
        "_pr": pr,
        "_sira": sira,
    }


def main(argv: list[str]) -> int:
    kaynak = Path(argv[1])
    enerjiler, gecerli, en_iyi = problem_ve_turlar()
    sonuc = {"p1": [], "p2": []}
    referanslar = {}
    for p in (1, 2):
        for w in GENISLIKLER:
            d = kaynak / f"W{w}"
            fj = sorted(glob.glob(str(d / f"csim-fidelity_*_n16_p{p}.json")))[-1]
            fmeta = json.loads(Path(fj).read_text(encoding="utf-8"))
            assert int(fmeta["real_bits"]) == w
            ref_yol = KOK / fmeta["referans_dosya"]      # testbench goreli yazar
            if p not in referanslar:
                ref_sv = np.load(ref_yol)
                ref_meta = json.loads(ref_yol.with_suffix(".json").read_text(encoding="utf-8"))
                r = olcutler(ref_sv, enerjiler, gecerli, en_iyi)
                # KAPI: problem ve indeksleme referansla ayni mi -- referansin
                # kendi optimal_probability'si yeniden uretilmeli
                assert np.isclose(r["p_optimum"], ref_meta["optimal_probability"],
                                  rtol=1e-9, atol=0), (r["p_optimum"], ref_meta["optimal_probability"])
                assert list(gecerli[en_iyi]) == list(ref_meta["best_tour"])
                referanslar[p] = {"dosya": ref_yol.name, "sv": ref_sv, **r}
            ref = referanslar[p]
            assert ref_yol.name == ref["dosya"], "genislikler farkli referans kullanmis"
            sv = np.load(d / f"sv_n16_p{p}.npy")
            m = olcutler(sv, enerjiler, gecerli, en_iyi)
            f = abs(np.vdot(ref["sv"], sv)) ** 2 / (np.vdot(ref["sv"], ref["sv"]).real * m["norm2"])
            assert abs(f - float(fmeta["fidelity"])) < 1e-8, (w, p, f, fmeta["fidelity"])
            sonuc[f"p{p}"].append({
                "genislik_bit": w,
                "fidelity": f,
                "sqrt_1_eksi_F_TVD_siniri": float(np.sqrt(max(0.0, 1 - f))),
                "TVD": float(0.5 * np.abs(m["_pr"] - ref["_pr"]).sum()),
                "norm2": m["norm2"],
                "p_optimum": m["p_optimum"],
                "p_optimum_bagil_hata": m["p_optimum"] / ref["p_optimum"] - 1,
                "p_gecerli_toplam": m["p_gecerli_toplam"],
                "p_gecerli_bagil_hata": m["p_gecerli_toplam"] / ref["p_gecerli_toplam"] - 1,
                "beklenen_enerji": m["beklenen_enerji"],
                "beklenen_enerji_bagil_hata": m["beklenen_enerji"] / ref["beklenen_enerji"] - 1,
                "en_olasi_tur_ayni": m["en_olasi_gecerli_tur_idx"] == ref["en_olasi_gecerli_tur_idx"],
                "tur_siralamasi_ayni": bool(np.array_equal(m["_sira"], ref["_sira"])),
            })

    print(f"{'p':>2} {'W':>3} {'1-F':>9} {'TVD':>9} {'P_opt bagil':>12} "
          f"{'P_gecerli bag.':>14} {'<E> bagil':>10} {'en olasi':>8} {'sira':>5}")
    for p in (1, 2):
        for s in sonuc[f"p{p}"]:
            print(f"{p:>2} {s['genislik_bit']:>3} {1 - s['fidelity']:>9.2e} {s['TVD']:>9.2e} "
                  f"{s['p_optimum_bagil_hata']:>+12.2e} {s['p_gecerli_bagil_hata']:>+14.2e} "
                  f"{s['beklenen_enerji_bagil_hata']:>+10.2e} "
                  f"{'ayni' if s['en_olasi_tur_ayni'] else 'FARKLI':>8} "
                  f"{'ayni' if s['tur_siralamasi_ayni'] else 'FARKLI':>5}")

    veri = {
        "ne": "Genislik taramasi, uygulama duzeyi olcutler (6C eki)",
        "damga": stamp.stamp(kaynak_dizin=str(kaynak)),
        "tanimlar": ("Olasiliklar normlanmis |a|^2. Optimum ve gecerli tur tanimi "
                     "services/reference/qaoa_reference.py ile ayni; referansin kendi "
                     "optimal_probability degeri yeniden uretilerek dogrulandi."),
        "referans": {f"p{p}": {k: v for k, v in r.items() if not k.startswith("_") and k != "sv"}
                     for p, r in referanslar.items()},
        "optimum_tur": list(gecerli[en_iyi]),
        "gecerli_tur_sayisi": len(gecerli),
        "sonuclar": sonuc,
    }
    yol = KOK / "docs" / "measurements" / (stamp.stamped_name("genislik-uygulama") + ".json")
    yol.write_text(json.dumps(veri, ensure_ascii=False, indent=1), encoding="utf-8")
    print("yazildi:", yol)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
