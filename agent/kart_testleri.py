"""Kartta US1 ek testleri — T034 (belirlenimcilik) ve T036 (p sınırı).

# PYTHON 3.6 UYUMU ZORUNLU — KARTTA koşar (PYNQ 2.5 / Python 3.6.5).
# ⛔ `sudo` ile koşulmalı: `import pynq` root ister.

Kullanım (kartta):
    sudo python3 -m agent.kart_testleri \\
        --bit       qir_20260920_d350605.bit \\
        --reference reference_20260915_c6ad872_p2_n5 \\
        --vektorler izdusum_vektorleri.json \\
        --beklenen  izdusum_beklenen.json \\
        --cikti     kart-testleri.json

--------------------------------------------------------------------------
T034 — belirlenimcilik (SC-002, madde A-5)
--------------------------------------------------------------------------
Aynı girdiyle ardışık TAM çağrılar (1.095 yazma) **bit düzeyinde aynı**
çıktı vermeli. Kısa yol (yalnız `cost`) kullanılmaz: belirlenimcilik tam
çağrı sırası için iddia ediliyor.

--------------------------------------------------------------------------
T036 — sınır davranışı (madde A-3 / K-2)
--------------------------------------------------------------------------
`p=0` ve `p=4` → çekirdek erken döner, `0x0050` **değişmez**, `ap_vld`
**kalkmaz**. Bu bir hata değil, test edilecek bir davranıştır.

⚠️ `ap_vld` (0x0054) okununca SIFIRLANIR (COR). Geçerli koşumun `ap_vld`'si
okunup temizlenmeden p=0 koşulursa önceki `1` görülür ve test yanlışlıkla
"çekirdek yazdı" der. Bu yüzden her geçersiz koşumdan önce temizlenir.
"""
# PYTHON 3.6 UYUMU ZORUNLU (yukarı bakın)
import argparse
import json
import sys

from agent import board as bd
from agent import encoder as enc
from agent.run_board import devreyi_kodla, _bits

TEKRAR_T034 = 5


def _ap_vld_oku_ve_temizle(kart):
    """0x0054 bit0. Okuma temizler (COR)."""
    return bool(kart._oku(bd.ADDR_BEKLENEN_DEGER_CTRL) & 0x1)


def t034(kart, kk, beklenen_bits):
    bitler = []
    for _ in range(TEKRAR_T034):
        r = kart.kosum(kk)
        if not r.gecerli:
            return {"gecti": False, "hata": r.hata}
        bitler.append(_bits(r.beklenen_deger_ham))
    ayni = len(set(bitler)) == 1
    return {
        "tekrar": TEKRAR_T034,
        "bitler": ["0x{:08X}".format(b) for b in bitler],
        "hepsi_ayni": ayni,
        "csim_ile_ayni": ayni and bitler[0] == beklenen_bits,
        "gecti": ayni and bitler[0] == beklenen_bits,
    }


def t036(kart, kk):
    # Önce geçerli bir koşum: 0x0050'de bilinen bir değer olsun.
    r = kart.kosum(kk)
    if not r.gecerli:
        return {"gecti": False, "hata": "hazirlik kosumu gecersiz: " + str(r.hata)}
    onceki = kart._oku(bd.ADDR_BEKLENEN_DEGER) & 0xFFFFFFFF
    vld_gecerli = _ap_vld_oku_ve_temizle(kart)       # 1 olmalı; okuma temizler

    sonuclar = {"hazirlik_bits": "0x{:08X}".format(onceki),
                "hazirlik_ap_vld": vld_gecerli}
    gecti = vld_gecerli
    for p in (0, 4):
        _ap_vld_oku_ve_temizle(kart)                 # kalıntı olmasın
        kart._yaz(bd.ADDR_P, p)
        bitti, sure, _ = kart.basla_ve_bekle()
        sonra = kart._oku(bd.ADDR_BEKLENEN_DEGER) & 0xFFFFFFFF
        vld = _ap_vld_oku_ve_temizle(kart)
        tamam = bitti and (sonra == onceki) and (not vld)
        gecti = gecti and tamam
        sonuclar["p{}".format(p)] = {
            "ap_done_geldi": bitti,
            "sure_s": sure,
            "deger_bits": "0x{:08X}".format(sonra),
            "degismedi": sonra == onceki,
            "ap_vld": vld,
            "gecti": tamam,
        }

    # Geçersiz p çekirdeği bozmamalı: geçerli koşum aynı sonucu vermeli.
    r2 = kart.kosum(kk)
    sonra_gecerli = r2.gecerli and _bits(r2.beklenen_deger_ham) == onceki
    sonuclar["sonra_gecerli_kosum_ayni"] = sonra_gecerli
    sonuclar["gecti"] = gecti and sonra_gecerli
    return sonuclar


def main(argv=None):
    ap = argparse.ArgumentParser(description="Kartta T034 + T036")
    ap.add_argument("--bit", required=True)
    ap.add_argument("--reference", required=True)
    ap.add_argument("--vektorler", required=True)
    ap.add_argument("--beklenen", required=True)
    ap.add_argument("--cikti", required=True)
    a = ap.parse_args(argv)

    with open(a.vektorler) as f:
        vek = json.load(f)
    with open(a.beklenen) as f:
        bek = json.load(f)
    with open(a.reference if a.reference.endswith(".json")
              else a.reference + ".json") as f:
        ref = json.load(f)

    phases, cb, sb, p, _ = devreyi_kodla(ref)
    k0 = vek["kodlu"][0]
    kk = enc.KodlanmisKosum(cost=k0["words"], phases=phases, cos_beta=cb,
                            sin_beta=sb, p=p, olcek=k0["olcek"])
    beklenen_bits = int(bek["beklenen"][0]["bits"])

    kart = bd.Kart(a.bit).yukle()
    print("FCLK0 {:.3f} MHz (yuklemeden sonra {:.3f}, ayar {})".format(
        kart.olculen_fclk, kart.fclk_yukleme_sonrasi,
        "YAPILDI" if kart.fclk_ayarlandi else "gerekmedi"))

    s34 = t034(kart, kk, beklenen_bits)
    print("T034 belirlenimcilik:", "GECTI" if s34["gecti"] else "KALDI", s34)
    s36 = t036(kart, kk)
    print("T036 p sinirlari   :", "GECTI" if s36["gecti"] else "KALDI", s36)

    cikti = {"ne": "Kartta T034 (belirlenimcilik) + T036 (p siniri)",
             "bitstream": a.bit, "p": p, "izdusum_indeksi": 0,
             "fclk_mhz": kart.olculen_fclk,
             "fclk_yukleme_sonrasi_mhz": kart.fclk_yukleme_sonrasi,
             "fclk_ayarlandi": kart.fclk_ayarlandi,
             "t034": s34, "t036": s36}
    with open(a.cikti, "w") as f:
        json.dump(cikti, f, indent=1)
    return 0 if (s34["gecti"] and s36["gecti"]) else 1


if __name__ == "__main__":
    sys.exit(main())
