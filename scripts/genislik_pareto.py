"""6C / T072 — genişlik taramasının donanım maliyetini ve fidelity'sini toplar.

Girdi:
  qir_hls_prj_W<n>/solution1/syn/report/   (hls/genislik_sentez.sh üretir)
  <fidelity_dizini>/W<n>/csim-fidelity_*_n16_p{1,2}.json  (hls/genislik_tarama.sh)
  docs/measurements/format-fidelity_*.json  (sayısal model, karşılaştırma için)

Çıktı: docs/measurements/genislik-pareto_<tarih>_<git-hash>.json

⚠️ LUT ve FF sütunları HLS TAHMİNİDİR — bu projede HLS LUT'u 2× fazla sayıyor
(ölçülen oran 0,39–0,50×, sabit değil; olculen-degerler.md §3). Gerçek sayı
yalnız implementasyondan gelir ve o yalnız 18 bit için var. BRAM ve DSP
tahmini gerçeğe yakın (BRAM birebir, DSP 0,92×).

Kullanım:
    .venv\\Scripts\\python.exe scripts\\genislik_pareto.py <fidelity_dizini>
"""
from __future__ import annotations

import glob
import json
import re
import subprocess
import sys
import xml.etree.ElementTree as ET
from datetime import date
from pathlib import Path

KOK = Path(__file__).resolve().parents[1]
GENISLIKLER = (14, 16, 18, 20, 24)
H_ESIGI, M_ESIGI = 0.999, 0.99
# 18 bit için Vivado implementasyonu (olculen-degerler.md §3-4) — tek gerçek satır
IMPL_18 = {"LUT": 22535, "FF": 19466, "DSP": 33, "BRAM_18K": 187, "post_route_ns": 9.122}


def _xml(yol: Path) -> ET.Element:
    return ET.parse(yol).getroot()


def _bul(kok: ET.Element, ad: str) -> str | None:
    for e in kok.iter():
        if e.tag.split("}")[-1] == ad and e.text and e.text.strip():
            return e.text.strip()
    return None


def _ii(rapor: Path, modul: str) -> int | None:
    y = rapor / f"{modul}_csynth.xml"
    return int(_bul(_xml(y), "PipelineII")) if y.exists() else None


def _rpt_cevrimler(rpt: Path) -> dict:
    """Üst raporun tablosundan: init, beklenen değer ve katman (min/maks)."""
    metin = rpt.read_text(encoding="utf-8", errors="replace")

    def ornek(ad):
        m = re.search(r"\|grp_" + ad + r"\S*\s*\|\S+\s*\|\s*(\d+)\|\s*(\d+)\|", metin)
        return (int(m.group(1)), int(m.group(2))) if m else None

    katman = re.search(r"\|- layer_loop\s*\|\s*\d+\|\s*\d+\|\s*(\d+)\s*~\s*(\d+)\|", metin)
    return {"init": ornek("qir_kernel_Pipeline_init_loop"),
            "beklenen_deger": ornek("expectation_scaled"),
            "katman": (int(katman.group(1)), int(katman.group(2))) if katman else None}


def _statevector_bram(rpt: Path, w: int) -> int:
    """Üst modülün Memory tablosu = statevector. `sv` bir amp_t{re,im} dizisi,
    cyclic 2 bölünmüş; HLS yapıyı re/im'e ayırınca 4 bellek × 32768 kelime × W
    bit çıkar. Tablo bundan saparsa sessizce toplamak yerine dur."""
    metin = rpt.read_text(encoding="utf-8", errors="replace")
    blok = metin.split("* Memory:", 1)[1].split("\n\n", 1)[0]
    satirlar = [s.split("|") for s in blok.splitlines() if s.strip().startswith("|")]
    bellekler = [s for s in satirlar
                 if len(s) > 9 and s[1].strip() not in ("Memory", "Total")]
    assert len(bellekler) == 4, f"statevector 4 bellek bekleniyordu: {len(bellekler)}"
    for s in bellekler:
        assert (int(s[7]), int(s[8])) == (32768, w), f"beklenmeyen bellek: {s[1].strip()}"
    return sum(int(s[3]) for s in bellekler)


def sentez(rapor: Path, w: int = 18) -> dict:
    ust = _xml(rapor / "qir_kernel_csynth.xml")
    c = _rpt_cevrimler(rapor / "qir_kernel_csynth.rpt")
    init, bd, kat = c["init"][1], c["beklenen_deger"], c["katman"]
    return {
        "BRAM_18K": int(_bul(ust, "BRAM_18K")),
        "BRAM_statevector": _statevector_bram(rapor / "qir_kernel_csynth.rpt", w),
        "DSP": int(_bul(ust, "DSP")),
        "LUT_hls_tahmini": int(_bul(ust, "LUT")),
        "FF_hls_tahmini": int(_bul(ust, "FF")),
        "tahmini_periyot_ns": float(_bul(ust, "EstimatedClockPeriod")),
        "II_rx_dyn_pair_loop": _ii(rapor, "apply_rx_dyn_Pipeline_rx_dyn_pair_loop"),
        "II_cost_amp_loop": _ii(rapor, "apply_cost_layer_Pipeline_cost_amp_loop"),
        "II_exp_amp_loop": _ii(rapor, "expectation_scaled_Pipeline_exp_amp_loop"),
        "cevrim_p2_hls_max": init + 2 * kat[1] + bd[1],
        "cevrim_p2_hls_min": init + 2 * kat[0] + bd[0],
        "cevrim_p3_ust_max": int(_bul(ust, "Worst-caseLatency")),
    }


def fidelity(dizin: Path, w: int) -> dict:
    out = {}
    for p in (1, 2):
        ys = sorted(glob.glob(str(dizin / f"W{w}" / f"csim-fidelity_*_n16_p{p}.json")))
        if ys:
            d = json.loads(Path(ys[-1]).read_text(encoding="utf-8"))
            assert int(d.get("real_bits", 18)) == w, f"W{w} dosyasi baska genislikte"
            out[f"p{p}"] = float(d["fidelity"])
    return out


def model() -> dict:
    y = sorted(glob.glob(str(KOK / "docs" / "measurements" / "format-fidelity_*.json")))[-1]
    t = json.loads(Path(y).read_text(encoding="utf-8"))["sonuclar"]["bit_taramasi_p2"]
    return {v["toplam_bit"]: v["fidelity"] for v in t.values()}, Path(y).name


def main(argv: list[str]) -> int:
    fdir = Path(argv[1])
    mdl, mdl_dosya = model()
    satirlar = []
    for w in GENISLIKLER:
        rapor = KOK / f"qir_hls_prj_W{w}" / "solution1" / "syn" / "report"
        if not (rapor / "qir_kernel_csynth.xml").exists():
            print(f"W={w}: sentez raporu YOK ({rapor})")
            continue
        s = sentez(rapor, w)
        f = fidelity(fdir, w)
        s.update({"genislik_bit": w, "format": f"Q1.{w - 1}", "bit_per_genlik": 2 * w,
                  "BRAM36_kelimesine_sigar": 2 * w <= 36,
                  "fidelity_p2": f.get("p2"), "fidelity_p1": f.get("p1"),
                  "H_gecti_p2": (f.get("p2") or 0) >= H_ESIGI,
                  "model_fidelity_p2": mdl.get(w)})
        satirlar.append(s)

    # 18 bit tutarlılık: tarama koşusu asıl projenin raporuyla aynı mı?
    asil = sentez(KOK / "qir_hls_prj" / "solution1" / "syn" / "report")
    s18 = next((s for s in satirlar if s["genislik_bit"] == 18), None)
    alanlar = ("BRAM_18K", "BRAM_statevector", "DSP", "LUT_hls_tahmini", "FF_hls_tahmini",
               "cevrim_p3_ust_max", "II_rx_dyn_pair_loop", "II_cost_amp_loop")
    tutarlilik = ({a: (s18[a], asil[a]) for a in alanlar if s18[a] != asil[a]}
                  if s18 else {"hata": "W=18 yok"})

    print(f"{'W':>3} {'BRAM':>5} {'SV':>4} {'DSP':>4} {'LUT*':>7} {'FF*':>7} {'per ns':>7} "
          f"{'II rx/cost':>10} {'p2 cevrim':>10} {'F p2':>11} {'model':>11}")
    for s in satirlar:
        print(f"{s['genislik_bit']:>3} {s['BRAM_18K']:>5} {s['BRAM_statevector']:>4} "
              f"{s['DSP']:>4} {s['LUT_hls_tahmini']:>7} "
              f"{s['FF_hls_tahmini']:>7} {s['tahmini_periyot_ns']:>7.3f} "
              f"{s['II_rx_dyn_pair_loop']:>4}/{s['II_cost_amp_loop']:<5} {s['cevrim_p2_hls_max']:>10} "
              f"{s['fidelity_p2'] or 0:>11.9f} {s['model_fidelity_p2'] or 0:>11.9f}")
    print("* HLS tahmini. 18 bit tutarlilik (tarama vs asil proje):",
          "AYNI" if not tutarlilik else tutarlilik)

    git = subprocess.run(["git", "rev-parse", "--short", "HEAD"], capture_output=True,
                         text=True, cwd=KOK).stdout.strip() or "unknown"
    kirli = bool(subprocess.run(["git", "status", "--porcelain"], capture_output=True,
                                text=True, cwd=KOK).stdout.strip())
    veri = {
        "ne": "6C genislik Pareto taramasi (T071 fidelity + T072 csynth)",
        "tarih": date.today().isoformat(), "git_hash": git, "calisma_agaci_kirli": kirli,
        "sabit_tutulan": {"n_qubits": 16, "phase_bits": 18, "trig_lut_indeks_bit": 13,
                          "saat_hedefi_ns": 10.0, "part": "xc7z020clg400-1"},
        "uyari": ("LUT/FF HLS tahminidir (bu projede 2x sisik, oran sabit degil). "
                  "Cevrimler HLS en kotu durumu (max); kartta 18 bit %1,9 alti olculdu."),
        "BRAM_statevector_tanimi": ("ust modulun Memory tablosu: sv (amp_t{re,im}, cyclic 2) "
                                    "-> 4 bellek x 32768 kelime x W bit"),
        "fidelity_kaynagi": "C-sim (hls/genislik_tarama.sh), Qiskit altin referansina karsi",
        "model_kaynagi": mdl_dosya,
        "implementasyon_18_bit": IMPL_18,
        "tutarlilik_18_bit": "AYNI" if not tutarlilik else tutarlilik,
        "satirlar": satirlar,
    }
    yol = KOK / "docs" / "measurements" / f"genislik-pareto_{date.today():%Y%m%d}_{git}.json"
    yol.write_text(json.dumps(veri, ensure_ascii=False, indent=1), encoding="utf-8")
    print("yazildi:", yol)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
