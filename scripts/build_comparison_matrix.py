"""Kıyas matrisi — görevler T051–T055 ve T069 (Faz 5, US4 + 6B).

Tasarım **v1** (kullanıcı onayı 2026-10-16):

- **SC-007**: hiçbir hücre elle yazılmaz. Her hücre bir ölçüm kaydından okunur
  ve kaynağını (dosya + alan) taşır.
- **FR-012**: her kayıttan n, p ve problem kimliği **okunur**; n=16, p=2 ve aynı
  referans problem değilse hücre üretilmez.
- **SC-008**: oran yalnız iki taraf da ölçülmüş, geçerli ve güvenilirse
  hesaplanır; aksi hâlde `null` kalır ve `not` yazılır.
- Enerji oranı yalnız **aynı kapsamda** (kart ↔ kart). Kapsamlar arası
  (kartın 5 V girişi ↔ tüm dizüstü) oran hesaplanmaz; değerler yan yana durur.
- Ana tablo **"aynı algoritma"** katmanıdır (FPGA'yla kıyaslanabilen tek
  katman). Aer katmanı ayrı tablodur ve FPGA'yla kıyaslanmaz.
- Faz 2'nin Aer tabanı **girmez** (geçersiz taban).
- Priz/pil kontrol ölçümü gecikme hücrelerinin **yerine geçmez**
  (priz-pil-kontrol-protokolu §5); verilirse kararı not olarak eklenir.

Kullanım:
    .venv\\Scripts\\python.exe scripts\\build_comparison_matrix.py          # özet, dosya yazmaz
    .venv\\Scripts\\python.exe scripts\\build_comparison_matrix.py --yaz    # temiz ağaçta JSON yazar
    ... --kontrol docs\\measurements\\priz-pil-kontrol_<tarih>_<git>.json
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

KOK = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(KOK))
from services.common import stamp                              # noqa: E402

TASARIM = "kiyas-matrisi v1 (kullanici onayi 2026-10-16)"
N, P = 16, 2
REFERANS = "reference_20260915_c6ad872_p2_n5"
OLCUM_DIZINI = KOK / "docs" / "measurements"

# Kayıtta referans adı yoksa problemi çıktının kendisi tanıtır. Bağlantı, hem
# referans adını hem parmak izini taşıyan bir kayıtla ÇALIŞMA ANINDA doğrulanır;
# öyle bir kayıt yoksa (None) bağlantı "beyan" olarak işaretlenir.
PARMAK_IZLERI = {
    "arm_float": ("-3950.990722656", "ps-pl-hizlanma_20260921_c504294.json"),
    "float": ("-3950.989990234", "gpu-ayni-algoritma_20261003_f15dd47_enerjiE3_fp32_p2.json"),
    "fpga_bits": ("3204875187", None),   # referansın C-sim bit deseni (kart-olcum-protokolu v1.0)
}

PLATFORMLAR = {
    "arm": "ARM Cortex-A9 (PS, kart)",
    "fpga": "FPGA (PL, kart)",
    "cpu": "Dizustu CPU, tek is parcacigi (ayni algoritma)",
    "gpu": "GPU RTX 4060 Laptop, FP32 (ayni algoritma)",
}
KISA_AD = {"arm": "ARM", "fpga": "FPGA", "cpu": "CPU", "gpu": "GPU"}
AER_PLATFORMLAR = {"aer_cpu": "Qiskit Aer, dizustu CPU (T=4)", "aer_gpu": "Qiskit Aer, GPU"}

DISARIDA = [
    {"ne": "Faz 2 Aer tabani (19 Eyl, cpu-yuk-dongu_20260919_prizde-temiz_p2 ve 19 Eyl enerji olcumu)",
     "neden": "gecersiz taban: Aer ayni isi ~12x fazla kapiyla yapiyor; 'basabas' sonucu buna dayaniyordu "
              "(olculen-degerler §6, CLAUDE.md 'Isim')"},
]


class KonfigUyumsuz(ValueError):
    """FR-012: kayıt n=16, p=2, aynı problem değil."""


# =========================================================================
# Yardımcılar
# =========================================================================
def _json(dizin: Path, ad: str) -> dict:
    return json.loads((dizin / ad).read_text(encoding="utf-8"))


def _np(metin: str) -> tuple[int, int]:
    """'n=16 p=2' ya da 'n16_p2' biçiminden (n, p)."""
    m = re.search(r"n=?(\d+)[\s_]+p=?(\d+)", metin)
    if not m:
        raise KonfigUyumsuz(f"n/p okunamadi: {metin[:60]!r}")
    return int(m.group(1)), int(m.group(2))


def problem_kaniti(dizin: Path, tur: str, deger: str) -> dict:
    """`tur`: 'ad' (kayıtta referans adı) ya da PARMAK_IZLERI anahtarı."""
    if tur == "ad":
        if REFERANS not in deger:
            raise KonfigUyumsuz(f"farkli problem: {deger}")
        return {"tur": "ad", "deger": REFERANS, "baglanti": "kayitta"}
    beklenen, bag_dosya = PARMAK_IZLERI[tur]
    if deger != beklenen:
        raise KonfigUyumsuz(f"{tur} parmak izi {deger} != {beklenen}")
    if bag_dosya is None:
        return {"tur": tur, "deger": deger, "baglanti": "beyan",
                "not": "referans adiyla birlikte gecen bir kayit yok; kart-olcum-protokolu v1.0"}
    metin = (dizin / bag_dosya).read_text(encoding="utf-8")
    if REFERANS not in metin or beklenen not in metin:
        raise KonfigUyumsuz(f"{bag_dosya} parmak izini referansa baglamiyor")
    return {"tur": tur, "deger": deger, "baglanti": f"dogrulandi: {bag_dosya}"}


def konfig_denetle(n: int, p: int, kanit: dict) -> dict:
    if (n, p) != (N, P):
        raise KonfigUyumsuz(f"n={n} p={p}, beklenen n={N} p={P}")
    return {"n": n, "p": p, "problem": kanit}


def _ms(s: float | None) -> float | None:
    return None if s is None else s * 1000.0


def _gecikme(dosya: str, alan: str, medyan_ms, p25_ms, p75_ms, p99_ms, kosum, gecerli,
             konfig, notlar=()) -> dict:
    return {"medyan_ms": medyan_ms, "p25_ms": p25_ms, "p75_ms": p75_ms, "p99_ms": p99_ms,
            "p99_medyan": (p99_ms / medyan_ms) if (p99_ms and medyan_ms) else None,
            "kosum": kosum, "gecerli": bool(gecerli), "konfig": konfig,
            "kaynak": {"dosya": dosya, "alan": alan}, "notlar": list(notlar)}


def kapsam_anahtari(metin: str) -> str:
    """Enerji kapsamı — oranın kurulup kurulamayacağını belirler."""
    if metin.startswith("kart-5v-girisi"):
        return "kart-5v-girisi"
    if "tum dizustu" in metin:
        return "tum-dizustu"
    raise ValueError(f"bilinmeyen kapsam: {metin!r}")


# =========================================================================
# Gecikme kaynakları
# =========================================================================
def gecikme_arm(dizin: Path) -> dict:
    ad = "ps-pl-hizlanma_20260921_c504294.json"
    d = _json(dizin, ad)
    o = d["olcumler"]["arm_float"]
    kanit = problem_kaniti(dizin, "ad", d["kosum"])
    return _gecikme(ad, "olcumler.arm_float", o["medyan_ms"], o["p25_ms"], o["p75_ms"], None,
                    o["tekrar"], True, konfig_denetle(*_np(d["kosum"]), kanit),
                    [f"p99 kayitta yok ({o['tekrar']} tekrar)"])


def gecikme_fpga(dizin: Path) -> dict:
    ad = "kart-gecikme_20260927_201475a_n16_p2.json"
    s = _json(dizin, ad)["seri"]
    c = s["ozet"]["cekirdek"]["seri"]
    kanit = problem_kaniti(dizin, "fpga_bits", str(s["beklenen_bits"]))
    return _gecikme(ad, "seri.ozet.cekirdek.seri", _ms(c["medyan_s"]), _ms(c["p25_s"]),
                    _ms(c["p75_s"]), _ms(c["p99_s"]), c["kosum_sayisi"], s["gecerli"],
                    konfig_denetle(s["n_qubits"], s["p"], kanit),
                    ["kapsam: T_cekirdek (yalniz hesap; kodlama ve yazma haric)"])


def gecikme_cpu(dizin: Path) -> dict:
    ad = "adil-cpu-tabani_20260921_c504294.json"
    d = _json(dizin, ad)
    v = d["varyantlar"]["float_yerel"]
    kanit = problem_kaniti(dizin, "ad", d["kosum"])
    return _gecikme(ad, "varyantlar.float_yerel", v["medyan_ms"], None, None, None, v["tekrar"],
                    True, konfig_denetle(*_np(d["kosum"]), kanit),
                    [f"yalniz {v['tekrar']} tekrar; p25/p75/p99 kayitta yok"])


def _gecikme_seri_kaydi(dizin: Path, ad: str, notlar=()) -> dict:
    """gpu-taban-protokolu v1.1 biçimindeki kayıtlar (aynı algoritma GPU, Aer)."""
    d = _json(dizin, ad)
    s = d["seri"]
    kanit = problem_kaniti(dizin, "ad", d["dogrulama"]["referans"])
    n, _ = _np(s["konfig"])
    return _gecikme(ad, "seri", _ms(s["medyan_s"]), _ms(s["p25_s"]), _ms(s["p75_s"]),
                    _ms(s["p99_s"]), s["kosum_sayisi"], d["gecerli"] and d["dogrulama"]["gecti"],
                    konfig_denetle(n, d["p"], kanit), notlar)


def gecikme_gpu(dizin: Path) -> dict:
    return _gecikme_seri_kaydi(dizin, "gpu-ayni-algoritma_20260930_14a59ee_seriG32-2_fp32_p2.json",
                               ["prizde (T067, 30 Eyl); pilde daha hizli olculdu (olculen-degerler §6.2)"])


# =========================================================================
# Enerji kaynakları
# =========================================================================
def enerji_kart(dizin: Path, taraf: str) -> dict:
    """`taraf`: 'F2' (PL) ya da 'P2' (ARM). İki tekrarın ortalaması."""
    ad = "kart-enerji_20261008_47b15b1.json"
    d = _json(dizin, ad)
    seriler = [s for s in d["seriler"] if s["ad"] == taraf]
    p2 = [s for s in d["seriler"] if s["ad"] == "P2"]
    if not seriler or not p2:
        raise KonfigUyumsuz(f"{ad}: {taraf} ya da P2 serisi yok")
    # Problem: P2'nin bench çıktısı referansı tanıtır; F2 AYNI koşumda aynı
    # --reference dosyasından beslenir (agent/measure_energy.main).
    kanitlar = {problem_kaniti(dizin, "arm_float", s["is_yuku"]["bench"]["beklenen_deger"])["deger"]
                for s in p2}
    kanit = problem_kaniti(dizin, "arm_float", kanitlar.pop()) if len(kanitlar) == 1 else None
    if kanit is None:
        raise KonfigUyumsuz("P2 serileri farkli problem")
    if taraf == "F2":
        kanit = dict(kanit, **{"not": "F2 ayni kosumda ayni --reference dosyasindan (measure_energy.main)"})
        konf = [_np(s["is_yuku"]["t_cekirdek"]["konfig"]) for s in seriler]
    else:
        konf = [_np(s["is_yuku"]["ham_cikti"]) for s in seriler]
    if len(set(konf)) != 1:
        raise KonfigUyumsuz("tekrarlar farkli n/p")
    e = [s["enerji"]["enerji_j_kosum"] for s in seriler]
    ort = sum(e) / len(e)
    return {
        "j_kosum": ort, "tekrarlar_j": e, "tekrar_farki_yuzde": (max(e) - min(e)) / ort * 100.0,
        "bos_w": sum(s["enerji"]["bos_guc_w"] for s in seriler) / len(seriler),
        "yuk_w": sum(s["enerji"]["yuk_guc_w"] for s in seriler) / len(seriler),
        "kapsam": d["kapsam"], "kapsam_anahtari": kapsam_anahtari(d["kapsam"]),
        "gecerli": bool(d["gecerli"]) and all(s["gecerli"] for s in seriler), "guvenilir": True,
        "konfig": konfig_denetle(*konf[0], kanit),
        "kaynak": {"dosya": ad, "alan": "seriler[ad=%s].enerji.enerji_j_kosum (ortalama)" % taraf},
        "notlar": ["delta yontemi; R_etkin ile (olculen-degerler §6.3)"] + (
            ["F2 tam cagri (kodlama + 1.095 yazma + kosum + okuma); P2 yalniz cekirdek -- "
             "asimetri F2 aleyhine (protokol §5)"] if taraf == "F2" else
            ["iki tekrar farkli seviyede; neden bilinmiyor (olculen-degerler §6.4)"]),
    }


def enerji_dizustu(dizin: Path, seri: str) -> dict:
    """`seri`: E1 (Aer CPU), E2 (Aer GPU), E3 (GPU aynı algoritma), E4 (CPU aynı algoritma)."""
    ad = f"enerji-batarya_20261003_f15dd47_{seri}.json"
    d = _json(dizin, ad)
    yk = d["is_yuku_kaydi"]
    if yk.endswith(".txt"):
        metin = (dizin / yk).read_text(encoding="utf-8-sig")
        m = re.search(r"beklenen_deger\s*:\s*(\S+)", metin)
        kanit = problem_kaniti(dizin, "float", m.group(1) if m else "")
        konfig = konfig_denetle(*_np(metin), kanit)
    else:
        w = _json(dizin, yk)
        kanit = problem_kaniti(dizin, "ad", w["dogrulama"]["referans"])
        konfig = konfig_denetle(_np(w["seri"]["konfig"])[0], w["p"], kanit)
    return {
        "j_kosum": d["kosum_basina_j"], "bos_w": d["bos"]["ortalama_guc_mw"] / 1000.0,
        "yuk_w": d["yuk"]["ortalama_guc_mw"] / 1000.0,
        "kapsam": d["yontem"], "kapsam_anahtari": kapsam_anahtari(d["yontem"]),
        "gecerli": True, "guvenilir": not d["uyarilar"], "konfig": konfig,
        "kaynak": {"dosya": ad, "alan": "kosum_basina_j", "is_yuku_kaydi": yk},
        "notlar": ["pilde (gpu-enerji-protokolu v1.1)"] + (
            [f"GUVENILMEZ: {u}" for u in d["uyarilar"]] + ["kiyasa girmez (protokol §6)"]
            if d["uyarilar"] else []),
    }


# =========================================================================
# Oranlar
# =========================================================================
def gecikme_orani(x: dict | None, fpga: dict | None, ad: str) -> dict:
    """t_x / t_FPGA: > 1 ise FPGA hızlı."""
    if not x or not fpga or not (x["gecerli"] and fpga["gecerli"]):
        return {"oran": None, "not": "bir taraf olculmedi ya da gecersiz (SC-008)"}
    r = x["medyan_ms"] / fpga["medyan_ms"]
    aralik, n = None, None
    if None not in (x["p25_ms"], x["p75_ms"], fpga["p25_ms"], fpga["p75_ms"]):
        aralik = [x["p25_ms"] / fpga["p75_ms"], x["p75_ms"] / fpga["p25_ms"]]
    else:
        n = "yayilim: bir tarafta ceyrekler kayitta yok"
    ifade = f"FPGA {r:.2f}x hizli" if r >= 1 else f"{ad} {1 / r:.1f}x hizli"
    return {"oran": r, "aralik_ceyrek": aralik, "ifade": ifade, "not": n}


def enerji_orani(x: dict | None, fpga: dict | None) -> dict:
    """E_x / E_FPGA (koşum başına ek enerji): > 1 ise FPGA az harcıyor."""
    if not x or not fpga:
        return {"oran": None, "not": "bir taraf olculmedi (SC-008)"}
    nedenler = []
    if x["kapsam_anahtari"] != fpga["kapsam_anahtari"]:
        nedenler.append(f"kapsamlar farkli ({x['kapsam_anahtari']} <-> {fpga['kapsam_anahtari']}): "
                        "oran hesaplanmaz (tasarim v1)")
    if not (x["gecerli"] and fpga["gecerli"] and x["guvenilir"] and fpga["guvenilir"]):
        nedenler.append("bir taraf gecersiz ya da guvenilmez (SC-008)")
    if nedenler:
        return {"oran": None, "not": "; ".join(nedenler)}
    r = x["j_kosum"] / fpga["j_kosum"]
    aralik = None
    if "tekrarlar_j" in x and "tekrarlar_j" in fpga:
        aralik = [min(x["tekrarlar_j"]) / max(fpga["tekrarlar_j"]),
                  max(x["tekrarlar_j"]) / min(fpga["tekrarlar_j"])]
    return {"oran": r, "aralik_tekrar": aralik,
            "ifade": f"FPGA {r:.2f}x az" if r >= 1 else f"FPGA %{(1 / r - 1) * 100:.0f} fazla"}


# =========================================================================
# Matris
# =========================================================================
def _guvenli(f, *a):
    """Hücre üretilemezse (FR-012) matris yine kurulur; hücre `null` + neden."""
    try:
        return f(*a), None
    except KonfigUyumsuz as e:
        return None, str(e)


def kontrol_notu(yol: Path | None) -> dict | None:
    if yol is None:
        return None
    k = json.loads(yol.read_text(encoding="utf-8"))
    return {"dosya": yol.name, "gecerli": k["gecerli"], "protokol": k["protokol"],
            "G": {a: k["karar_G"][a] for a in ("guc_kaynagi_etkisi", "taban")},
            "K": {a: k["karar_K"][a] for a in ("guc_kaynagi_etkisi", "taban")},
            "kural": "kontrol olcumu gecikme hucrelerinin yerine GECMEZ (priz-pil-kontrol-protokolu §5)"}


def matris_kur(dizin: Path = OLCUM_DIZINI, kontrol: Path | None = None) -> dict:
    gec = {"arm": _guvenli(gecikme_arm, dizin), "fpga": _guvenli(gecikme_fpga, dizin),
           "cpu": _guvenli(gecikme_cpu, dizin), "gpu": _guvenli(gecikme_gpu, dizin)}
    enr = {"arm": _guvenli(enerji_kart, dizin, "P2"), "fpga": _guvenli(enerji_kart, dizin, "F2"),
           "cpu": _guvenli(enerji_dizustu, dizin, "E4"), "gpu": _guvenli(enerji_dizustu, dizin, "E3")}
    kn = kontrol_notu(kontrol)

    hucreler, oranlar = {}, {}
    for pf, ad in PLATFORMLAR.items():
        g, g_hata = gec[pf]
        e, e_hata = enr[pf]
        if kn and pf in ("cpu", "gpu") and g:
            g = dict(g, kontrol=kn["K" if pf == "cpu" else "G"] | {"dosya": kn["dosya"],
                                                                    "kural": kn["kural"]})
        elif pf in ("cpu", "gpu") and g:
            g = dict(g, notlar=g["notlar"] + ["priz/pil kontrol olcumu henuz yapilmadi"])
        hucreler[pf] = {"ad": ad, "gecikme": g, "gecikme_hatasi": g_hata,
                        "enerji": e, "enerji_hatasi": e_hata}
        if pf != "fpga":
            oranlar[pf] = {"gecikme": gecikme_orani(g, gec["fpga"][0], KISA_AD[pf]),
                           "enerji": enerji_orani(e, enr["fpga"][0])}

    aer_g = {"aer_cpu": _guvenli(_gecikme_seri_kaydi, dizin,
                                 "cpu-yuk-dongu_20260930_14a59ee_seriA-CPU-v11_p2.json"),
             "aer_gpu": _guvenli(_gecikme_seri_kaydi, dizin,
                                 "gpu-yuk-dongu_20260930_14a59ee_seriA-GPU-v11_p2.json")}
    aer_e = {"aer_cpu": _guvenli(enerji_dizustu, dizin, "E1"),
             "aer_gpu": _guvenli(enerji_dizustu, dizin, "E2")}
    aer = {pf: {"ad": ad, "gecikme": aer_g[pf][0], "gecikme_hatasi": aer_g[pf][1],
                "enerji": aer_e[pf][0], "enerji_hatasi": aer_e[pf][1]}
           for pf, ad in AER_PLATFORMLAR.items()}
    ag, ac = aer_g["aer_gpu"][0], aer_g["aer_cpu"][0]
    aer_oran = {"gpu_cpu_gecikme": (ac["medyan_ms"] / ag["medyan_ms"]) if ag and ac and
                ag["gecerli"] and ac["gecerli"] else None,
                "gpu_cpu_enerji": enerji_orani(aer_e["aer_gpu"][0], aer_e["aer_cpu"][0]),
                "not": "Aer katmani FPGA'yla KIYASLANMAZ (Aer ayni isi farkli kapi dizisiyle yapiyor)"}

    return {"ne": "Kiyas matrisi (US4 T051-T055 + 6B T069)", "tasarim": TASARIM,
            "konfig": {"n": N, "p": P, "problem": REFERANS},
            "ana_tablo": {"katman": "ayni algoritma (FPGA'yla kiyaslanabilen tek katman)",
                          "hucreler": hucreler, "fpgaya_gore_oranlar": oranlar},
            "aer_katmani": {"hucreler": aer, "oranlar": aer_oran},
            "disarida_birakilan": DISARIDA, "kontrol_olcumu": kn}


def _f(x, bicim):
    return "-" if x is None else format(x, bicim)


def ozet_yaz(m: dict) -> str:
    h, o = m["ana_tablo"]["hucreler"], m["ana_tablo"]["fpgaya_gore_oranlar"]
    sat = ["| Eksen | " + " | ".join(h[p]["ad"] for p in PLATFORMLAR) + " |",
           "|---|" + "---:|" * len(PLATFORMLAR)]

    def satir(baslik, fn):
        sat.append(f"| {baslik} | " + " | ".join(fn(p) for p in PLATFORMLAR) + " |")

    satir("Gecikme medyani (ms)", lambda p: _f((h[p]["gecikme"] or {}).get("medyan_ms"), ".3f"))
    satir("p99 / medyan", lambda p: _f((h[p]["gecikme"] or {}).get("p99_medyan"), ".4f"))
    satir("Kosum basina ek enerji (J)", lambda p: _f((h[p]["enerji"] or {}).get("j_kosum"), ".5f")
          + ("" if (h[p]["enerji"] or {}).get("guvenilir", True) else " (guvenilmez)"))
    satir("Kapsam", lambda p: (h[p]["enerji"] or {}).get("kapsam_anahtari", "-"))
    satir("Bosta / yukte (W)", lambda p: "-" if not h[p]["enerji"] else
          f"{h[p]['enerji']['bos_w']:.3f} / {h[p]['enerji']['yuk_w']:.3f}")
    satir("Gecikme, FPGA'ya gore", lambda p: "1" if p == "fpga" else
          (o[p]["gecikme"].get("ifade") or o[p]["gecikme"]["not"]))
    satir("Enerji, FPGA'ya gore", lambda p: "1" if p == "fpga" else
          (o[p]["enerji"].get("ifade") or o[p]["enerji"]["not"]))
    return "\n".join(sat)


def main() -> int:
    ap = argparse.ArgumentParser(description=TASARIM)
    ap.add_argument("--dizin", type=Path, default=OLCUM_DIZINI)
    ap.add_argument("--kontrol", type=Path, help="priz-pil-kontrol_<tarih>_<git>.json")
    ap.add_argument("--yaz", action="store_true", help="kiyas-matrisi_<tarih>_<git>.json yaz")
    a = ap.parse_args()

    m = matris_kur(a.dizin, a.kontrol)
    print(ozet_yaz(m))
    if a.yaz:
        if stamp.is_dirty():
            print("HATA: calisma agaci kirli -- damga icerikle eslesmez, yazilmadi", file=sys.stderr)
            return 1
        m["damga"] = stamp.stamp(tasarim=TASARIM)
        yol = a.dizin / (stamp.stamped_name("kiyas-matrisi") + ".json")
        yol.write_text(json.dumps(m, ensure_ascii=False, indent=1), encoding="utf-8")
        print(f"yazildi: {yol}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
