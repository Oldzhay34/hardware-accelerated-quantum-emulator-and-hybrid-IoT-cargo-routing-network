"""Kartta izdüşüm doğrulaması — görev T031, kapı G3 (T033).

# PYTHON 3.6 UYUMU ZORUNLU — KARTTA koşar (PYNQ 2.5 / Python 3.6.5).
# ⛔ `sudo` ile koşulmalı: `import pynq` root ister.

Kullanım (kartta):
    sudo python3 -m agent.run_board \\
        --bit      qir_20260920_d350605.bit \\
        --reference reference_20260915_c6ad872_p2_n5 \\
        --vektorler izdusum_vektorleri.json \\
        --beklenen  izdusum_beklenen.json \\
        --cikti     kart-dogrulama.json

--------------------------------------------------------------------------
YÖNTEM
--------------------------------------------------------------------------
Çekirdeğin `m_axi` arayüzü yoktur (madde K-1): statevector çip-içi BRAM'de
kalır ve AXI'den görünmez, yani kartta genlik fidelity'si **ölçülemez**.
Onun yerine aynı statevector ≥20 farklı `cost` vektörüyle okunur; her biri
bir izdüşümdür ve hepsi birden bağımsız kısıtlar kurar (karar K1).

`cost` **devreye girmez** — yalnız `expectation_scaled`'i besler. Bu yüzden
ilk çağrı TAM (1.095 yazma), sonrakiler **kısa yol** (272 yazma): `phases`,
`cos_beta`, `sin_beta`, `p` yerinde kalır.

⛔ **Bu kısa yol gecikme ölçümünde KULLANILMAZ** (US2/G4 tam çağrı sırasını
ölçer). Burada yalnız doğrulama yapılıyor.

Karşılaştırma **bit düzeyinde**dir: float metni değil, IEEE-754 bit deseni.
Ondalık yazdırıp karşılaştırmak, son bitteki farkı gizler.
"""
# PYTHON 3.6 UYUMU ZORUNLU (yukarı bakın)
import argparse
import json
import math
import struct
import sys
import time

from agent import board as bd
from agent import encoder as enc

TAU = 2.0 * math.pi


def _param_bul(params, onek, r):
    """C tarafındaki `param_bul` ile aynı: sıraya değil ADA bakar."""
    koseli = "[{}]".format(r)
    for ad, deger in params.items():
        if ad.startswith(onek) and koseli in ad:
            return deger
    raise KeyError("parametre yok: {}{}".format(onek, koseli))


def _bits(f):
    """float -> IEEE-754 bit deseni (uint32)."""
    return struct.unpack("<I", struct.pack("<f", f))[0]


def devreyi_kodla(ref):
    """`phases`, `cos_beta`, `sin_beta`, `p` — izdüşümler arasında DEĞİŞMEZ."""
    p = int(ref["p"])
    gammalar = [_param_bul(ref["params"], u"γ", r) for r in range(p)]
    betalar = [_param_bul(ref["params"], u"β", r) for r in range(p)]
    phases = enc.phases_dizisi(ref["ising_h"], ref["ising_J"], gammalar)
    cb, sb, uyarilar = enc.beta_dizileri(betalar)
    return phases, cb, sb, p, uyarilar


def kos(a):
    with open(a.vektorler) as f:
        vek = json.load(f)
    with open(a.beklenen) as f:
        bek = json.load(f)
    with open(a.reference if a.reference.endswith(".json")
              else a.reference + ".json") as f:
        ref = json.load(f)

    kodlu = vek["kodlu"]
    beklenen = bek["beklenen"]
    if len(kodlu) != len(beklenen):
        raise SystemExit("vektor sayisi {} != beklenen {}".format(
            len(kodlu), len(beklenen)))
    if a.izdusum and a.izdusum < len(kodlu):
        kodlu, beklenen = kodlu[:a.izdusum], beklenen[:a.izdusum]
    if len(kodlu) < 20:
        raise SystemExit(
            "izdusum sayisi {} < 20 — karar K1 en az 20 bagimsiz izdusum "
            "istiyor; seri gecersiz".format(len(kodlu)))

    phases, cb, sb, p, uyarilar = devreyi_kodla(ref)
    if int(ref["n_qubits"]) != a.n or p != a.p:
        raise SystemExit("referans n={} p={}, istenen n={} p={}".format(
            ref["n_qubits"], p, a.n, a.p))

    print("=== kart hazirlaniyor ===")
    kart = bd.Kart(a.bit, yol=a.yol).yukle()
    print("  yol      : {}".format(a.yol))
    print("  FCLK0    : {:.3f} MHz  (dogrulandi)".format(kart.olculen_fclk))
    print("  ap_idle  : {}".format(kart.ap_idle()))
    if uyarilar:
        print("  doyma uyarilari: {}".format(uyarilar))

    kosumlar, sapanlar = [], []
    t0 = time.time()
    for i, (k, b) in enumerate(zip(kodlu, beklenen)):
        if i == 0:
            # TAM cagri: phases/beta/p bir kez yazilir
            kk = enc.KodlanmisKosum(cost=k["words"], phases=phases,
                                    cos_beta=cb, sin_beta=sb, p=p,
                                    olcek=k["olcek"])
            r = kart.kosum(kk)
        else:
            r = kart.izdusum(k["words"])   # KISA YOL: yalniz cost

        if not r.gecerli:
            sapanlar.append({"i": i, "sebep": r.hata})
            print("  [{:2d}] GECERSIZ: {}".format(i, r.hata))
            continue

        olculen_bits = _bits(r.beklenen_deger_ham)
        tutuyor = (olculen_bits == int(b["bits"]))
        kosumlar.append({
            "i": i, "olcek": k["olcek"],
            "beklenen_deger_ham": r.beklenen_deger_ham,
            "bits": olculen_bits,
            "csim_bits": int(b["bits"]),
            "csim_deger": b["beklenen_deger"],
            "bit_bit_ayni": tutuyor,
            "t_cekirdek_s": r.t_cekirdek,
            "t_yazma_s": r.t_yazma,
            "yazma_sayisi": r.yazma_sayisi,
        })
        if not tutuyor:
            sapanlar.append({
                "i": i, "sebep": "bit farki",
                "kart": "0x{:08X}".format(olculen_bits),
                "csim": "0x{:08X}".format(int(b["bits"])),
            })
        print("  [{:2d}] {:>14.9g}  0x{:08X}  {}".format(
            i, r.beklenen_deger_ham, olculen_bits, "OK" if tutuyor else "SAPMA"))

    sure = time.time() - t0
    gecerli = [k for k in kosumlar if k["bit_bit_ayni"]]

    print()
    print("=== SONUC ===")
    print("  izdusum      : {}".format(len(kodlu)))
    print("  bit bit ayni : {}".format(len(gecerli)))
    print("  sapan        : {}".format(len(sapanlar)))
    print("  sure         : {:.2f} s".format(sure))

    cikti = {
        "ne": "Kartta izdusum dogrulamasi (G3 / SC-003)",
        "bitstream": a.bit,
        "erisim_yolu": a.yol,
        "fclk_mhz": kart.olculen_fclk,
        "n_qubits": a.n, "p": p,
        "tohum": vek["tohum"],
        "izdusum_sayisi": len(kodlu),
        "bagimlilik_esigi": vek.get("bagimlilik_esigi"),
        "en_buyuk_benzerlik": vek.get("en_buyuk_benzerlik"),
        "kosumlar": kosumlar,
        "sapan_izdusumler": sapanlar,
        "gecti": (len(sapanlar) == 0 and len(gecerli) == len(kodlu)),
        "toplam_sure_s": sure,
        "not": ("Ilk cagri TAM (1095 yazma), sonrakiler kisa yol (272). "
                "Kisa yol GECIKME OLCUMUNDE kullanilmaz."),
    }
    with open(a.cikti, "w") as f:
        json.dump(cikti, f, indent=1)
    print("  yazildi      : {}".format(a.cikti))

    if not cikti["gecti"]:
        print()
        print("⛔ KAPI KAPALI (G3). Sapan izdusumler hangi katsayi yolunda")
        print("   hata oldugunu daraltir — h mi J mi. Fark kapanmadan")
        print("   HICBIR hiz/enerji rakami raporlanmaz.")
        return 1
    print()
    print("✅ G3 GECTI — {} izdusumun hepsi C-sim ile bit bit ayni.".format(len(kodlu)))
    return 0


def main(argv=None):
    ap = argparse.ArgumentParser(description="Kartta izdusum dogrulamasi (T031)")
    ap.add_argument("--bit", required=True)
    ap.add_argument("--reference", required=True)
    ap.add_argument("--vektorler", required=True)
    ap.add_argument("--beklenen", required=True)
    ap.add_argument("--cikti", required=True)
    ap.add_argument("--n", type=int, default=16)
    ap.add_argument("--p", type=int, default=2)
    ap.add_argument("--izdusum", type=int, default=20)
    ap.add_argument("--yol", choices=("A", "B"), default="A")
    return kos(ap.parse_args(argv))


if __name__ == "__main__":
    sys.exit(main())
