"""C-sim çıktısını altın referansla VE Python ikiziyle kıyaslar. T022.

Neden iki kıyas:
  1. **C-sim vs altın referans** — SC-001'in ölçütü. Testbench bunu zaten
     hesaplıyor; burada bağımsız olarak tekrar hesaplanır (ikinci göz).
  2. **C-sim vs Python ikizi** — asıl değerli olan bu. `native_formulation.py`
     aynı algoritmayı Q1.17 kuantalamasıyla koşar. İki bağımsız uygulama
     BİT DÜZEYİNDE aynı çıkmalıdır. Fidelity tek başına ince hataları gizler;
     bir kübitin kapısı atlanmış olsa bile fidelity yüksek kalabilir.

Kullanım:
    .venv/Scripts/python.exe scripts/compare_amplitudes.py \
        --reference docs/measurements/reference_..._p2_n5 \
        --csim      docs/measurements/csim-dump_p2_n16.npy
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from scripts.native_formulation import (
    _params_ayikla, apply_cost_layer, apply_rx, enerji_tablosu, fidelity, init_uniform,
)
from services.common import stamp
from services.reference import amplitudes

FRAC_BITS = 17
OLCEK = 1 << FRAC_BITS
UST = 1.0 - 1.0 / OLCEK
PHASE_BITS = 18


def q1_17(v: np.ndarray) -> np.ndarray:
    """ap_fixed<18,1,AP_RND_CONV,AP_SAT> ile AYNI davranış.

    np.round = yakına yuvarlama, yarım ise çifte = AP_RND_CONV.
    np.clip  = doyurma = AP_SAT.
    """
    re = np.clip(np.round(v.real * OLCEK) / OLCEK, -1.0, UST)
    im = np.clip(np.round(v.imag * OLCEK) / OLCEK, -1.0, UST)
    return re + 1j * im


def tura_cevir(aci: float) -> int:
    """Terim başına fazı tur cinsinden PHASE_BITS-bit sabit noktaya indirger."""
    M = 1 << PHASE_BITS
    t = np.mod(aci / (2 * np.pi), 1.0)
    return int(np.round(t * M)) % M


def q_real(x):
    """Tek bir reel sayıyı real_t'ye (Q1.17) indirger — kapı KATSAYILARI için.

    ⚠️ Bu satır ilk sürümde YOKTU ve iki uygulama %75 genlikte ayrıştı (azami
    6,1 LSB). Sebep: C++ `cos`/`sin` çıktısını `real_t`'ye atadığı için
    kuantalıyor, Python ise tam duyarlıkta tutuyordu. Donanımda katsayı bir
    LUT'tan gelir ve SONLU duyarlıktadır — gerçekçi olan C++'ın davranışıdır.
    Fidelity bu farkı gizlemişti; bit düzeyi kıyas yakaladı.
    """
    return np.clip(np.round(np.asarray(x) * OLCEK) / OLCEK, -1.0, UST)


def _rx_q1_17(sv, cos_half, sin_half, k, n):
    """gates_pairing.hpp `apply_rx<K>` ile BİREBİR aynı aritmetik sıra."""
    out = sv.copy()
    j = np.arange(1 << (n - 1), dtype=np.int64)
    i0 = ((j >> k) << (k + 1)) | (j & ((1 << k) - 1))
    i1 = i0 | (1 << k)
    ar, ai = sv[i0].real, sv[i0].imag
    br, bi = sv[i1].real, sv[i1].imag
    out[i0] = q1_17((cos_half * ar + sin_half * bi)
                    + 1j * (cos_half * ai - sin_half * br))
    out[i1] = q1_17((cos_half * br + sin_half * ai)
                    + 1j * (cos_half * bi - sin_half * ar))
    return out


def python_ikizi(h, J, gamma, beta, n) -> np.ndarray:
    """C++ çekirdeğinin Python karşılığı — AYNI faz ve kuantalama yolu.

    Faz akümülatörü tam sayıdır ve mod 2^PHASE_BITS taşar; C++'taki
    `ap_uint<18>` davranışının birebir karşılığı. Kapı katsayıları (cos/sin)
    da `real_t`'ye indirgenir — C++ öyle yapıyor.
    """
    M = 1 << PHASE_BITS
    idx = np.arange(1 << n, dtype=np.int64)
    bit = ((idx[:, None] >> np.arange(n)) & 1).astype(np.int64)

    sv = q1_17(init_uniform(n))
    for r in range(len(gamma)):
        acc = np.zeros(1 << n, dtype=np.int64)
        for k in range(n):
            t = tura_cevir(-gamma[r] * h[k])
            acc += np.where(bit[:, k] == 1, -t, t)
        for a in range(n):
            for b in range(a + 1, n):
                if J[a, b] == 0.0:
                    continue
                t = tura_cevir(-gamma[r] * J[a, b])
                acc += np.where((bit[:, a] ^ bit[:, b]) == 1, -t, t)
        acc %= M
        # C++ `turn_to_cos_sin` cos/sin'i real_t'ye ATAR -> kuantalanır
        c = q_real(np.cos(2 * np.pi * acc / M))
        s = q_real(np.sin(2 * np.pi * acc / M))
        sv = q1_17((sv.real * c - sv.imag * s) + 1j * (sv.real * s + sv.imag * c))
        # exp(-i*beta*X) = RX(2*beta) -> cos(2*beta/2) = cos(beta)
        cb, sb = float(q_real(np.cos(beta[r]))), float(q_real(np.sin(beta[r])))
        for k in range(n):
            sv = _rx_q1_17(sv, cb, sb, k, n)
    return sv


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--reference", required=True, help="uzantisiz referans yolu")
    ap.add_argument("--csim", help="tb_kernel --dump ciktisi (.npy)")
    a = ap.parse_args()

    kok = Path(__file__).resolve().parents[1]
    ref = amplitudes.load(Path(a.reference))
    if not ref.params:
        raise SystemExit("HATA: referansta 'params' yok — yeniden uretilmeli")

    h = np.array(ref.ising_h)
    J = np.array(ref.ising_J)
    gamma, beta = _params_ayikla(ref.params, ref.p)
    n = ref.n_qubits
    hedef = np.asarray(ref.amplitudes)

    ikiz = python_ikizi(h, J, gamma, beta, n)
    f_ikiz = fidelity(hedef, ikiz)
    print(f"Referans            : {Path(a.reference).name}  (n={n}, p={ref.p})")
    print(f"Python ikizi vs ref : {f_ikiz:.9f}")

    sonuc = {"n_qubits": n, "p": ref.p, "python_ikizi_fidelity": f_ikiz,
             "referans": Path(a.reference).name}

    if a.csim:
        csim = np.load(a.csim)
        f_csim = fidelity(hedef, csim)
        # ASIL ÖLÇÜT: iki bağımsız uygulama bit düzeyinde aynı mı?
        ayni = np.array_equal(csim, ikiz)
        azami = float(np.max(np.abs(csim - ikiz)))
        farkli = int(np.count_nonzero(csim != ikiz))
        print(f"C-sim vs ref        : {f_csim:.9f}")
        print(f"C-sim vs Python ikizi")
        print(f"   bit-birebir      : {ayni}")
        print(f"   azami fark       : {azami:.3e}")
        print(f"   farkli genlik    : {farkli} / {csim.size}"
              f"  (%{100*farkli/csim.size:.4f})")
        if not ayni:
            lsb = 1.0 / OLCEK
            print(f"   NOT: 1 LSB = {lsb:.3e}. Azami fark bunun "
                  f"{azami/lsb:.1f} katı.")
        sonuc.update({"csim_fidelity": f_csim, "bit_birebir": ayni,
                      "azami_fark": azami, "farkli_genlik": farkli,
                      "lsb": 1.0 / OLCEK})

    meta = stamp.stamp(not_="C-sim, Python ikizi ve altin referans uclu kiyas")
    meta["sonuclar"] = sonuc
    yol = stamp.measurements_dir(kok) / f"{stamp.stamped_name('compare-amplitudes')}_n{n}_p{ref.p}.json"
    yol.write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\nYazildi: {yol.name}")


if __name__ == "__main__":
    main()
