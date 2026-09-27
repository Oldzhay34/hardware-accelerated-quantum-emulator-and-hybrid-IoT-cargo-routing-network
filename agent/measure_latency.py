"""Kart gecikme ölçümü — görevler T040–T044.

# PYTHON 3.6 UYUMU ZORUNLU — KARTTA koşar (PYNQ 2.5 / Python 3.6.5).
# ⛔ `sudo` ile koşulmalı: `import pynq` root ister.

Bu modül `docs/measurements/kart-olcum-protokolu.md`'nin (🔒 **v1.0**) kod
hâlidir. Aşağıdaki her sabit protokolün bir maddesine dayanır; protokolden
sapan her şey **hatadır**, "iyileştirme" değil. Protokol değişirse önce belge
yeni sürüm alır, sonra bu dosya.

Kullanım (kartta; uzun seriler `nohup` ile — bağlantı düşse de sürer):
    sudo nohup python3 -m agent.measure_latency --seri A --p 2 \\
        --bit qir_20260920_d350605.bit \\
        --reference reference_20260915_c6ad872_p2_n5 \\
        --beklenen-bits 3188759494 --besleme USB \\
        --cikti seri-A.json > seri-A.log 2>&1 &

--------------------------------------------------------------------------
SERİLER (protokol §6)
--------------------------------------------------------------------------
A / B : referans problem (`ising_h`, `ising_J`, γ, β) — her koşumda
        `kosum_kodla` ile YENİDEN kodlanır (`T_uctan_uca` bunu kapsar).
        Süreye göre: 300 sn.
K     : kontrol — izdüşüm vektörü 0 (tohum 42), önceden kodlanmış. Yalnız
        `T_cekirdek` ve `T_yazma` (girdi kodlanmadığı için `T_uctan_uca` yok).
        Sayıya göre: ≥ 30 koşum.

Her koşum TAM çağrıdır (1.095 yazma). İzdüşüm kısa yolu KULLANILMAZ (§5).
"""
# PYTHON 3.6 UYUMU ZORUNLU (yukarı bakın)
import argparse
import json
import struct
import sys
import time

import numpy as np

PROTOKOL_SURUMU = "kart-olcum-protokolu v1.0"

# --- protokol v1.0 sabitleri (madde numarasıyla) -------------------------
ISINMA = 3                  # §6 — her serinin ilk 3 koşumu atılır
MIN_KOSUM = 10              # §8, SC-004 — altında seri ÜRETİLMEZ
SERI_SURE_S = 300.0         # §6 — A ve B
KONTROL_ADET = 30           # §6 — K (≥ 30)
PENCERE_S = 10.0            # §8 — plato pencereleri
PLATO_PENCERE = 6           # §8 — son 6 pencere
PLATO_TOLERANS = 0.005      # §8 — ±%0,5
ILK_N = 50                  # §8 — "ilk 50 koşum"
SON_S = 60.0                # §8 — "son 60 sn"
YOKLAMA_OLCUM_N = 10000     # §5 — δ: AP_CTRL arka arkaya 10.000 okuma
FCLK_TOLERANS = 0.01        # §4 — seri sonunda da %1
YUZDELIK_YONTEMI = "numpy.percentile, dogrusal ara degerleme (varsayilan)"

KAPSAMLAR = ("cekirdek", "yazma", "uctan_uca")


class SeriGecersiz(RuntimeError):
    """§7: seriyi geçersiz kılan durum — ölçüm durur, sebep kaydedilir."""


# =========================================================================
# Saf istatistik — kart gerekmez, konakta test edilir
# =========================================================================
def olcum_serisi(konfig, kapsam, sureler_s):
    """`OlcumSerisi` (data-model §2) özeti. §8'deki alanların hepsi.

    ⛔ `kosum_sayisi < MIN_KOSUM` → **hata** (SC-004'ün kod karşılığı):
    tek koşum ya da kısa seri hiçbir yere yazılamaz.
    """
    if kapsam not in KAPSAMLAR:
        raise ValueError("bilinmeyen kapsam: {!r}".format(kapsam))
    n = len(sureler_s)
    if n < MIN_KOSUM:
        raise ValueError(
            "kosum_sayisi {} < {} — seri serilestirilmez (SC-004)".format(
                n, MIN_KOSUM))
    a = np.asarray(sureler_s, dtype=float)
    p25, med, p75, p95, p99 = np.percentile(a, [25, 50, 75, 95, 99])
    return {
        "konfig": konfig,
        "kapsam": kapsam,
        "kosum_sayisi": int(n),
        "medyan_s": float(med),
        "p25_s": float(p25),
        "p75_s": float(p75),
        "yayilim_s": float(p75 - p25),        # IQR
        "min_s": float(a.min()),
        "max_s": float(a.max()),
        "p95_s": float(p95),
        "p99_s": float(p99),
        "jitter_s": float(a.max() - a.min()),
        "protokol_surumu": PROTOKOL_SURUMU,
        "yuzdelik_yontemi": YUZDELIK_YONTEMI,
    }


def pencereler(zamanlar_s, degerler, pencere_s=PENCERE_S):
    """§8: koşumları başlangıç zamanına göre `pencere_s`'lik dilimlere böler.

    Döner: `[{"bas_s", "n", "medyan_s"}]`, zaman sırasıyla. Boş pencere yok.
    """
    kova = {}
    for t, v in zip(zamanlar_s, degerler):
        kova.setdefault(int(t // pencere_s), []).append(v)
    return [{"bas_s": k * pencere_s, "n": len(kova[k]),
             "medyan_s": float(np.median(kova[k]))} for k in sorted(kova)]


def plato(pencere_listesi, adet=PLATO_PENCERE, tolerans=PLATO_TOLERANS):
    """§8: plato oturdu ⇔ son `adet` pencere medyanının HEPSİ, bunların
    ortalamasının ±`tolerans` içinde. Pencere yetmezse `oturdu=None`."""
    if len(pencere_listesi) < adet:
        return {"oturdu": None, "neden": "yetersiz pencere ({} < {})".format(
            len(pencere_listesi), adet)}
    son = [p["medyan_s"] for p in pencere_listesi[-adet:]]
    ort = float(np.mean(son))
    sapma = max(abs(m - ort) / ort for m in son)
    return {"oturdu": bool(sapma <= tolerans), "son_medyanlar_s": son,
            "ortalama_s": ort, "en_buyuk_sapma_orani": float(sapma),
            "tolerans": tolerans}


def ilk_ve_son(konfig, kapsam, zamanlar_s, degerler):
    """§8: ilk `ILK_N` koşum ile son `SON_S` saniye AYRI raporlanır."""
    ilk = list(degerler[:ILK_N])
    t_son = zamanlar_s[-1] if zamanlar_s else 0.0
    son = [v for t, v in zip(zamanlar_s, degerler) if t >= t_son - SON_S]
    sonuc = {}
    for ad, dilim in (("ilk_{}_kosum".format(ILK_N), ilk),
                      ("son_{:g}_sn".format(SON_S), son)):
        try:
            sonuc[ad] = olcum_serisi(konfig, kapsam, dilim)
        except ValueError as e:
            sonuc[ad] = {"uretilemedi": str(e)}
    return sonuc


# =========================================================================
# Kart tarafı
# =========================================================================
_XADC = "/sys/bus/iio/devices/iio:device0/"


def xadc_sicaklik():
    """§4: çip sıcaklığı (°C). Zamanlanan yolun DIŞINDA okunur."""
    def r(ad):
        with open(_XADC + ad) as f:
            return float(f.read())
    return round((r("in_temp0_raw") + r("in_temp0_offset"))
                 * r("in_temp0_scale") / 1000.0, 2)


def yuk_ortalamasi():
    with open("/proc/loadavg") as f:
        return f.read().strip()


def yoklama_periyodu(kart, n=YOKLAMA_OLCUM_N):
    """T041 / §5: `δ` — AP_CTRL'ün arka arkaya `n` okunmasının ortalaması.

    `T_cekirdek`'e üst taraftan en fazla bir `δ` eklenir; rapor bunu verir.
    """
    from agent import board as bd
    t0 = time.perf_counter()
    for _ in range(n):
        kart._oku(bd.ADDR_AP_CTRL)
    return (time.perf_counter() - t0) / n


def _tek_kosum(kart, girdi, kodla):
    """Bir TAM çağrı. Döner: süreler + ham bit deseni, ya da None (zaman aşımı).

    `T_uctan_uca`: ham problem → `kosum_kodla` → 1.095 yazma → koşum → okuma.
    `kodla=False` (seri K): girdi önceden kodlanmış, `T_uctan_uca` yok.
    """
    from agent import board as bd
    from agent import encoder as enc
    t_bas = time.perf_counter()
    kk = enc.kosum_kodla(*girdi) if kodla else girdi
    t_kod = time.perf_counter()
    kart.yaz_tam(kk)
    t_yaz = time.perf_counter()
    bitti, t_cek, yoklama = kart.basla_ve_bekle()
    if not bitti:
        return None
    ham = kart._oku(bd.ADDR_BEKLENEN_DEGER) & 0xFFFFFFFF
    struct.unpack("<f", struct.pack("<I", ham))            # okuma = yorumlama
    t_son = time.perf_counter()
    return {
        "t_cekirdek_s": t_cek,
        "t_yazma_s": t_yaz - t_kod,
        "t_uctan_uca_s": (t_son - t_bas) if kodla else None,
        "t_kodlama_s": (t_kod - t_bas) if kodla else None,
        "yoklama": yoklama,
        "bits": ham,
    }


def seri_kos(kart, girdi, kodla, beklenen_bits, sure_s=None, adet=None):
    """§6–§7: ısınma + ölçüm döngüsü. Doğruluk HER koşumda denetlenir.

    ⛔ Bit sapması → `SeriGecersiz` (doğrulanmamış hesabın hızı ölçülmez).
    ⛔ Zaman değerine bakarak koşum ATILMAZ.
    """
    if (sure_s is None) == (adet is None):
        raise ValueError("ya sure_s ya adet verilmeli")
    zaman_asimi = 0
    for i in range(ISINMA):                    # §6: atılır, doğruluk yine denetlenir
        r = _tek_kosum(kart, girdi, kodla)
        if r is None:
            zaman_asimi += 1
        elif r["bits"] != beklenen_bits:
            raise SeriGecersiz("isinma kosumu {}: bit 0x{:08X} != C-sim 0x{:08X}".format(
                i, r["bits"], beklenen_bits))

    kosumlar, sicakliklar = [], []
    t0 = time.perf_counter()
    sonraki_pencere = 0.0
    while True:
        gecen = time.perf_counter() - t0
        if sure_s is not None and gecen >= sure_s:
            break
        if adet is not None and len(kosumlar) >= adet:
            break
        if gecen >= sonraki_pencere:           # §4: zamanlanan yolun DIŞINDA
            sicakliklar.append({"t_s": round(gecen, 3), "C": xadc_sicaklik()})
            sonraki_pencere += PENCERE_S
        if not kart.ap_idle():                 # madde A-1
            raise SeriGecersiz("ap_idle=0 (madde A-1), kosum {}".format(len(kosumlar)))
        t_rel = time.perf_counter() - t0
        r = _tek_kosum(kart, girdi, kodla)
        if r is None:                          # §7: seriye girmez, sayılır
            zaman_asimi += 1
            continue
        if r["bits"] != beklenen_bits:         # §6/§7: seri geçersiz
            raise SeriGecersiz("kosum {}: bit 0x{:08X} != C-sim 0x{:08X}".format(
                len(kosumlar), r["bits"], beklenen_bits))
        r["sira"] = len(kosumlar)
        r["t_rel_s"] = t_rel
        kosumlar.append(r)
    return kosumlar, sicakliklar, zaman_asimi


def ozetle(konfig, kosumlar):
    """Her kapsam için `OlcumSerisi` + pencereler + plato + ilk/son."""
    zaman = [k["t_rel_s"] for k in kosumlar]
    ozet = {}
    for kapsam, alan in (("cekirdek", "t_cekirdek_s"), ("yazma", "t_yazma_s"),
                         ("uctan_uca", "t_uctan_uca_s")):
        degerler = [k[alan] for k in kosumlar]
        if any(v is None for v in degerler):
            continue                           # seri K: uctan_uca yok
        pen = pencereler(zaman, degerler)
        ozet[kapsam] = {
            "seri": olcum_serisi(konfig, kapsam, degerler),
            "pencereler": pen,
            "plato": plato(pen),
            "ilk_ve_son": ilk_ve_son(konfig, kapsam, zaman, degerler),
        }
    return ozet


def _girdi_hazirla(a, ref):
    from agent import encoder as enc
    from agent.run_board import _param_bul, devreyi_kodla
    p = int(ref["p"])
    if p != a.p:
        raise SystemExit("referans p={}, istenen p={}".format(p, a.p))
    if a.seri in ("A", "B"):
        gammalar = [_param_bul(ref["params"], u"γ", r) for r in range(p)]
        betalar = [_param_bul(ref["params"], u"β", r) for r in range(p)]
        girdi = (ref["ising_h"], ref["ising_J"], gammalar, betalar, p)
        return girdi, True, "referans problem, her kosumda kosum_kodla ile kodlanir"
    with open(a.vektorler) as f:
        k0 = json.load(f)["kodlu"][0]
    phases, cb, sb, p, _ = devreyi_kodla(ref)
    kk = enc.KodlanmisKosum(cost=k0["words"], phases=phases, cos_beta=cb,
                            sin_beta=sb, p=p, olcek=k0["olcek"])
    return kk, False, "izdusum vektoru 0 (onceden kodlanmis)"


def main(argv=None):
    ap = argparse.ArgumentParser(description="Kart gecikme olcumu (protokol v1.0)")
    ap.add_argument("--seri", required=True, choices=("A", "B", "K"))
    ap.add_argument("--p", type=int, required=True)
    ap.add_argument("--bit", required=True)
    ap.add_argument("--reference", required=True)
    ap.add_argument("--vektorler", help="seri K icin izdusum_vektorleri.json")
    ap.add_argument("--beklenen-bits", type=int, required=True,
                    help="bu girdinin C-sim bit deseni (izdusum_ref ile uretilir)")
    ap.add_argument("--besleme", required=True, help="JP5 duzeni, orn. USB / REG")
    ap.add_argument("--cikti", required=True)
    a = ap.parse_args(argv)

    from pynq.ps import Clocks
    from agent import board as bd
    from agent.run_board import _sha256_dosya

    with open(a.reference if a.reference.endswith(".json")
              else a.reference + ".json") as f:
        ref = json.load(f)
    girdi, kodla, girdi_tanimi = _girdi_hazirla(a, ref)

    kosul = {"bitstream": a.bit, "bitstream_sha256": _sha256_dosya(a.bit),
             "besleme": a.besleme, "yuk_bas": yuk_ortalamasi(),
             "sicaklik_bas_C": xadc_sicaklik()}
    kart = bd.Kart(a.bit).yukle()               # FCLK ayarla + dogrula (§4)
    kosul.update({"fclk_bas_mhz": kart.olculen_fclk,
                  "fclk_yukleme_sonrasi_mhz": kart.fclk_yukleme_sonrasi,
                  "fclk_ayarlandi": kart.fclk_ayarlandi})
    delta = yoklama_periyodu(kart)
    print("seri {} p={} basliyor; FCLK {:.3f} MHz, delta {:.2f} us".format(
        a.seri, a.p, kart.olculen_fclk, delta * 1e6))
    sys.stdout.flush()

    cikti = {"ne": "Kart gecikme olcumu (US2)", "protokol_surumu": PROTOKOL_SURUMU,
             "seri": a.seri, "p": a.p, "n_qubits": 16, "girdi": girdi_tanimi,
             "beklenen_bits": a.beklenen_bits, "isinma": ISINMA,
             "yoklama_periyodu_delta_s": delta, "kosullar": kosul,
             "gecerli": False, "gecersizlik_nedeni": None}
    konfig = "n16_p{}_fpga_seri{}".format(a.p, a.seri)
    try:
        kosumlar, sicaklik, zaman_asimi = seri_kos(
            kart, girdi, kodla, a.beklenen_bits,
            sure_s=SERI_SURE_S if a.seri in ("A", "B") else None,
            adet=KONTROL_ADET if a.seri == "K" else None)
        fclk_son = float(Clocks.fclk0_mhz)
        kosul.update({"fclk_son_mhz": fclk_son, "yuk_son": yuk_ortalamasi(),
                      "sicaklik_son_C": xadc_sicaklik()})
        cikti.update({"zaman_asimi_sayisi": zaman_asimi, "sicakliklar": sicaklik,
                      "ozet": ozetle(konfig, kosumlar), "kosumlar": kosumlar})
        if abs(fclk_son - kart.fclk_mhz) / kart.fclk_mhz > FCLK_TOLERANS:
            raise SeriGecersiz("seri sonunda FCLK0 {:.3f} MHz (§4)".format(fclk_son))
        cikti["gecerli"] = True
    except SeriGecersiz as e:
        cikti["gecersizlik_nedeni"] = str(e)
    with open(a.cikti, "w") as f:
        json.dump(cikti, f)
    print("bitti: gecerli={} neden={} -> {}".format(
        cikti["gecerli"], cikti["gecersizlik_nedeni"], a.cikti))
    return 0 if cikti["gecerli"] else 1


if __name__ == "__main__":
    sys.exit(main())
