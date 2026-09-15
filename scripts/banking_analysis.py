"""Bankalama şemalarını ÇAKIŞMA düzeyinde analiz eder. Faz 2 araştırma (a şıkkı) + S-4 sigortası.

Problem (SK-02, projenin 1 numaralı riski): kübit k'ye kapı uygulanırken genlik
çiftleri (i, i XOR 2^k) işlenir. Erişim adımı 2^k olduğu için TEK bir bankalama
şeması bütün k değerlerinde çakışmasız paralellik vermez.

Bu script bunu SİMÜLE ETMEZ, SAYAR: her k için, L şeritli bir boru hattının bir
çevrimde eriştiği adreslerin hangi bankalara düştüğünü hesaplar ve çakışmayı bulur.

Kabul: BRAM çift portludur -> banka başına 2 erişim/çevrim serbest.
       3 ve üstü erişim -> duraklama -> II > 1.

Kullanım:
    .venv/Scripts/python.exe scripts/banking_analysis.py
"""
from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from services.common import stamp

N_QUBITS = 16
N = 1 << N_QUBITS
PORT_PER_BANK = 2          # cift portlu BRAM
BRAM36_COUNT = 140         # XC7Z020, DS190
BRAM36_BITS = 36 * 1024


def pair_index(j: int, k: int) -> int:
    """j'inci çiftin düşük indeksi: j'ye k konumunda 0 biti sokulur."""
    dusuk = j & ((1 << k) - 1)
    yuksek = j >> k
    return (yuksek << (k + 1)) | dusuk


# ------------------------------------------------------------ bankalama şemaları
def bank_low(a: int, b: int) -> int:
    """(i) Naif: adresin en düşük b biti. En basit, HLS'in varsayılanına en yakın."""
    return a & ((1 << b) - 1)


def bank_xor2(a: int, b: int) -> int:
    """(ii) XOR: düşük b bit ile bir sonraki b bit XOR'lanır."""
    return (a & ((1 << b) - 1)) ^ ((a >> b) & ((1 << b) - 1))


def bank_xor_full(a: int, b: int) -> int:
    """(iii) Tam XOR: adresin TÜM b-bitlik parçaları XOR'lanır."""
    sonuc = 0
    x = a
    while x:
        sonuc ^= x & ((1 << b) - 1)
        x >>= b
    return sonuc


SEMALAR = {
    "naif (dusuk bitler)": bank_low,
    "XOR (2 parca)": bank_xor2,
    "XOR (tam katlama)": bank_xor_full,
}


def cakisma_analizi_pingpong(sema, b: int, lanes: int, k: int) -> tuple[int, int]:
    """Ping-pong (çift tampon): okumalar A dizisinden, yazmalar B dizisine.

    Okuma ve yazma AYRI fiziksel bellekte olduğu için banka başına yük yarıya iner.
    Hipotez: bu, yüksek k'deki çakışmayı ortadan kaldırır.
    """
    okuma: Counter[int] = Counter()
    yazma: Counter[int] = Counter()
    for j in range(lanes):
        i = pair_index(j, k)
        esi = i | (1 << k)
        okuma[sema(i, b)] += 1
        okuma[sema(esi, b)] += 1
        yazma[sema(i, b)] += 1
        yazma[sema(esi, b)] += 1
    tepe = max(max(okuma.values(), default=0), max(yazma.values(), default=0))
    cevrim = -(-tepe // PORT_PER_BANK)
    return tepe, cevrim


def cakisma_analizi(sema, b: int, lanes: int, k: int) -> tuple[int, int]:
    """Bir çevrimde `lanes` çift işlenirken bankalara düşen erişimleri sayar.

    ÖNEMLİ: Bir kapı uygulaması yerinde (in-place) yapıldığında her çift için
    DÖRT erişim gerekir: oku(i), oku(i'), yaz(i), yaz(i'). Yalnızca okumaları
    saymak çakışmayı OLDUĞUNDAN AZ gösterir — ilk denememdeki hata buydu.

    Döndürür: (en yüksek banka yükü, gereken çevrim sayısı)
    """
    erisimler: Counter[int] = Counter()
    for j in range(lanes):
        i = pair_index(j, k)
        esi = i | (1 << k)
        bi, be = sema(i, b), sema(esi, b)
        erisimler[bi] += 2      # oku + yaz
        erisimler[be] += 2      # oku + yaz
    tepe = max(erisimler.values()) if erisimler else 0
    cevrim = -(-tepe // PORT_PER_BANK)
    return tepe, cevrim


def azami_serit(sema, b: int, k: int, pingpong: bool) -> int:
    """II=1'i koruyan AZAMI serit sayisi = gercek verim.

    "II=1" tek basina aldaticidir: sayiyi az tutunca cakisma dogal olarak
    kaybolur. Onemli olan, cakismadan kac cift/cevrim islenebildigidir.
    Ust sinir = banka x port / (cift basina erisim).
    """
    banks = 1 << b
    tavan = banks * PORT_PER_BANK // (2 if pingpong else 4)
    en_iyi = 0
    for lanes in range(1, tavan + 1):
        fn = cakisma_analizi_pingpong if pingpong else cakisma_analizi
        if fn(sema, b, lanes, k)[1] == 1:
            en_iyi = lanes
        else:
            break
    return en_iyi


def parcalanma(bit_genlik: int = 36) -> dict:
    """ARRAY_PARTITION faktoru BRAM blok sayisini nasil degistirir?

    Faz 2 promptu "BRAM partition sayisi/parcalanmasi" istiyor. Bankalama
    bedava degildir: dizi F parcaya bolununce her parca AYRI BRAM olur ve
    parca 1024 kelimeden kucukse blogun geri kalani israf olur.
    """
    blok_kelime = BRAM36_BITS // 36          # 1024
    genis = -(-bit_genlik // 36)             # yan yana blok
    ideal = -(-N // blok_kelime) * genis     # parcalanmamis
    cikti = {}
    print(f"  {'faktor F':>8} {'kelime/parca':>13} {'blok/parca':>11} "
          f"{'toplam':>7} {'ping-pong':>10} {'%140':>7}  israf")
    for f in (1, 2, 4, 8, 16, 32, 64, 128, 256):
        kpp = N // f
        bpp = -(-kpp // blok_kelime) * genis
        toplam = f * bpp
        pp = toplam * 2
        kayip = toplam - ideal
        not_ = "yok" if kayip == 0 else f"+{kayip} blok ({toplam/ideal:.0f}x)"
        print(f"  {f:>8} {kpp:>13} {bpp:>11} {toplam:>7} {pp:>10} "
              f"{100*pp/BRAM36_COUNT:>6.1f}%  {not_}")
        cikti[f] = {"kelime_per_parca": kpp, "blok_toplam": toplam,
                    "pingpong_blok": pp, "israf_blok": kayip}
    return cikti


def devre_profili() -> dict:
    """Bankalama sorunu QAOA devresinde KAC kapiyi gercekten etkiliyor?

    Kritik ayrim: KOSEGEN kapilar (RZ, RZZ, faz) genligi yerinde bir sayiyla
    carpar -> (i, i XOR 2^k) ESLEMESI YOKTUR, dolayisiyla bankalama sorunu da
    yoktur. Yalnizca kosegen-olmayan kapilar (RX karistirici) esleme ister.

    Qiskit RZZ'yi CX-RZ-CX olarak ayristirir ve CX kosegen degildir; ama bu
    Qiskit'in kapi kumesinin kisitidir, bizim cekirdegimizin degil. Kendi
    donanimimizda RZZ dogrudan faz carpimi olarak uygulanir.
    """
    import numpy as np
    from qiskit.circuit.library import QAOAAnsatz
    from services.qubo import qubo as qubo_mod
    from services.reference import qaoa_reference
    from services.reference.cli import ornek_matris

    problem = qubo_mod.matrix_to_qubo(ornek_matris(5))
    cost_op, _ = qaoa_reference._qubo_to_ising(problem)
    n = problem.n_vars

    agirlik: Counter[int] = Counter(int(np.sum(pl.z)) for pl in cost_op.paulis)
    kosegen_rep = sum(v for w, v in agirlik.items() if w >= 1)

    cikti = {"n_kubit": n, "pauli_agirlik": dict(sorted(agirlik.items()))}
    print(f"  Maliyet operatoru: {len(cost_op.paulis)} Pauli terimi "
          f"(agirlik 1 = RZ: {agirlik[1]}, agirlik 2 = RZZ: {agirlik[2]}) — hepsi KOSEGEN")
    print()
    print(f"  {'p':>3} {'ayristirilmis':>14} {'  bundan eslemeli':>18} "
          f"{'yerlesik':>9} {'bundan eslemeli':>16}")
    for p in (1, 2, 3):
        a = QAOAAnsatz(cost_operator=cost_op, reps=p)
        qc = a.decompose(reps=3).assign_parameters(
            np.random.default_rng(42).uniform(0, np.pi, a.num_parameters))
        esl = sum(1 for inst in qc.data
                  if not np.allclose((m := np.asarray(inst.operation.to_matrix())),
                                     np.diag(np.diag(m))))
        yer_kos, yer_esl = kosegen_rep * p, n * p
        print(f"  {p:>3} {len(qc.data):>14} {esl:>18} {yer_kos + yer_esl:>9} "
              f"{yer_esl:>16}")
        cikti[f"p={p}"] = {"ayristirilmis_kapi": len(qc.data), "ayristirilmis_eslemeli": esl,
                           "yerlesik_kapi": yer_kos + yer_esl, "yerlesik_kosegen": yer_kos,
                           "yerlesik_eslemeli": yer_esl,
                           "eslemeli_azalma_kat": round(esl / yer_esl, 1)}
    print()
    print(f"  SONUC: yerlesik RZZ ile eslemeli kapi sayisi {cikti['p=2']['eslemeli_azalma_kat']}x")
    print(f"         azaliyor. Bankalama sorunu p=2'de 584 kapinin 384'unu degil,")
    print(f"         232 kapinin yalnizca {cikti['p=2']['yerlesik_eslemeli']}'sini (%13,8) etkiliyor.")
    return cikti


def verim_cift_cevrim(sema, b: int, k: int, pingpong: bool) -> tuple[float, int]:
    """GERCEK verim: cevrim basina islenebilen cift sayisi (lanes / cevrim).

    "II=1'i koruyan azami serit" metrigi yerinde sema icin 0 raporluyordu; bu
    "verim sifir" degil "II=1 hic olmuyor" demek. Baglayici olcut budur:
    serit sayisi uzerinde lanes/cevrim orani ENIYILENIR.
    """
    banks = 1 << b
    tavan = banks * PORT_PER_BANK // (2 if pingpong else 4)
    fn_ = cakisma_analizi_pingpong if pingpong else cakisma_analizi
    en_iyi, en_iyi_lane = 0.0, 0
    for lanes in range(1, tavan + 1):
        oran = lanes / fn_(sema, b, lanes, k)[1]
        if oran > en_iyi:
            en_iyi, en_iyi_lane = oran, lanes
    return en_iyi, en_iyi_lane


def main() -> None:
    b = 4              # 16 banka
    banks = 1 << b
    lanes = banks // 2  # 8 cift -> 16 erisim -> ideal durumda her bankaya 1

    print(f"Statevector: {N_QUBITS} kubit = {N} genlik")
    print(f"Banka sayisi: {banks} (b={b} bit), paralel cift: {lanes}, port/banka: {PORT_PER_BANK}")
    print(f"Ideal: her bankaya 1 erisim -> II=1\n")

    sonuclar = {}
    for ad, sema in SEMALAR.items():
        print(f"=== {ad} ===")
        print(f"  {'k':>3} {'tepe banka yuku':>16} {'gereken cevrim (~II)':>21}")
        kayit = {}
        for k in range(N_QUBITS):
            tepe, cevrim = cakisma_analizi(sema, b, lanes, k)
            isaret = "" if cevrim == 1 else ("  <-- CAKISMA" if cevrim <= 4 else "  <-- AGIR CAKISMA")
            # yalnizca uc durumlari ve ilk degisimi bas
            if k <= 5 or k >= 14 or cevrim > 1:
                print(f"  {k:>3} {tepe:>16} {cevrim:>21}{isaret}")
            kayit[k] = {"tepe_yuk": tepe, "cevrim": cevrim}
        en_kotu = max(v["cevrim"] for v in kayit.values())
        kotu_k = [k for k, v in kayit.items() if v["cevrim"] == en_kotu]
        print(f"  --> EN KOTU DURUM: {en_kotu} cevrim (k = {kotu_k})\n")
        sonuclar[ad] = {"per_k": kayit, "en_kotu_cevrim": en_kotu, "en_kotu_k": kotu_k}

    # --- Ping-pong karsilastirmasi + GERCEK VERIM taramasi ---
    print("=" * 74)
    print("VERIM: II=1'i koruyan azami serit sayisi (cift/cevrim)")
    print(f"Ust sinir: yerinde {banks*PORT_PER_BANK//4} cift, ping-pong {banks*PORT_PER_BANK//2} cift")
    print("=" * 74)
    print(f"  {'sema':<22} {'tamponlama':<12} {'en dusuk':>9} {'en yuksek':>10}  darbogaz k")
    verim = {}
    for ad, sema in SEMALAR.items():
        for etiket, pp in (("yerinde", False), ("ping-pong", True)):
            per_k = [azami_serit(sema, b, k, pp) for k in range(N_QUBITS)]
            dip = min(per_k)
            kotu_k = [k for k, v in enumerate(per_k) if v == dip]
            gosterim = str(kotu_k) if len(kotu_k) < 6 else f"{len(kotu_k)} k degeri"
            dip_str = "II=1 YOK" if dip == 0 else str(dip)
            print(f"  {ad:<22} {etiket:<12} {dip_str:>9} {max(per_k):>10}  {gosterim}")
            verim[f"{ad} | {etiket}"] = {"per_k": per_k, "en_dusuk": dip,
                                         "en_yuksek": max(per_k), "darbogaz_k": kotu_k}
    print()
    print("OKUMA: 'en dusuk', o semanin EN KOTU kubitindeki verimidir — boru hatti")
    print("       bir devrede butun k degerlerini gordugu icin baglayici olan budur.")
    print()
    print("!! UYARI — bu aritmetigin GORMEDIGI sey:")
    print("   k CALISMA ZAMANI parametresidir. HLS, ARRAY_PARTITION ile hangi")
    print("   parcaya erisildigini DERLEME ZAMANINDA cozemezse butun erisimleri")
    print("   seri hale getirir; II aritmetikten cok daha kotu cikar. Bu ancak")
    print("   SENTEZ RAPORUYLA gorulur (K-02/K-04 olcutu), hesapla degil.")
    print("   Ayrica ping-pong BRAM'i ikiye katlar: Q1.17'de %45,7 -> %91,4.")

    print()
    print("=" * 74)
    print("PARCALANMA: ARRAY_PARTITION faktorunun BRAM bedeli (Q1.17, 36-bit)")
    print("=" * 74)
    frag = parcalanma(36)
    print()
    print("ESIK: parca basina 1024 kelimenin altina dusuldugunde (F > 64) blogun")
    print("      geri kalani israf olur ve BRAM katlanir. F=16 bedava: 65536/16")
    print("      = 4096 = 4 x 1024, tam bolunuyor, tek blok bile israf yok.")

    print()
    print("=" * 74)
    print("DEVRE PROFILI: bankalama sorunu kac kapiyi gercekten etkiliyor?")
    print("=" * 74)
    profil = devre_profili()

    print()
    print("=" * 74)
    print("GERCEK VERIM: cift/cevrim (serit sayisi uzerinde eniyilenmis)")
    print("=" * 74)
    print(f"  {'sema':<22} {'tamponlama':<12} {'en kotu k':>10} {'en iyi k':>9} {'tavan':>6}")
    verim2 = {}
    for ad, sema in SEMALAR.items():
        for etiket, pp in (("yerinde", False), ("ping-pong", True)):
            oranlar = [verim_cift_cevrim(sema, b, k, pp)[0] for k in range(N_QUBITS)]
            tavan = banks * PORT_PER_BANK // (2 if pp else 4)
            print(f"  {ad:<22} {etiket:<12} {min(oranlar):>10.1f} {max(oranlar):>9.1f} {tavan:>6}")
            verim2[f"{ad} | {etiket}"] = {"en_kotu": min(oranlar), "en_iyi": max(oranlar),
                                          "tavan": tavan, "per_k": oranlar}
    print()
    print("  YORUM: yerinde semanin tavani 8 cift/cevrim (cift basina 4 erisim),")
    print("         ping-pong'unki 16 (cift basina 2 erisim, iki ayri bellek).")
    print("         Ping-pong'un ustunlugu bankalamadan degil, PORT SAYISINI")
    print("         ikiye katlamasindan geliyor — bedeli de tam olarak o: 2x BRAM.")

    # Kaydet
    meta = stamp.stamp(n_qubits=N_QUBITS, banks=banks, lanes=lanes, port_per_bank=PORT_PER_BANK)
    meta["verim"] = verim
    meta["parcalanma"] = frag
    meta["devre_profili"] = profil
    meta["verim_cift_cevrim"] = verim2
    meta["sonuclar"] = sonuclar
    kok = Path(__file__).resolve().parents[1]
    yol = stamp.measurements_dir(kok) / f"{stamp.stamped_name('banking-analysis')}.json"
    yol.write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Yazildi: {yol.name}")


if __name__ == "__main__":
    main()
