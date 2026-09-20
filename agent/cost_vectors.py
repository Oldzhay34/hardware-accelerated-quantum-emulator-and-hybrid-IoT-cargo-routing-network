"""İzdüşüm `cost` vektörü üreticisi — madde H-7.

Sözleşme: `specs/003-zynq-ps-kartta-kosum/contracts/host-encoder.md`
Gerekçe: `specs/003-zynq-ps-kartta-kosum/research.md` §R3

--------------------------------------------------------------------------
NEDEN VAR
--------------------------------------------------------------------------
Çekirdeğin `m_axi` arayüzü yoktur (madde K-1): statevector çip-içi BRAM'de
kalır ve AXI'den **görünmez**. Yani kartta genlik fidelity'si ölçülemez.

Onun yerine aynı statevector, ≥20 farklı `cost` vektörüyle okunur. Her vektör
bir izdüşümdür; hepsi birden statevector'e dair bağımsız kısıtlar kurar
(karar K1).

⚠️ **Bağımsızlık kritiktir.** Birbirinin katı olan 20 vektör yazılırsa 20
ölçüm alınır ama doğrulama gücü **1 vektörünki kadar** kalır — ve bu, testler
yeşil yandığı için fark edilmez. Bağımsızlık üreticinin sorumluluğudur ve
`agent/tests/test_encoder.py` ile sabitlenir.
"""
from __future__ import annotations

import math
import random
from dataclasses import dataclass, field
from typing import List

from .encoder import N_QUBITS

# Vektör, [-1, 1) içinde doğrudan üretilir; ölçekleme yine de uygulanır
# (sözleşme: "yol aynı kalsın"). Bu yüzden burada kenar payı gerekmez.
ALT, UST = -1.0, 1.0

# İki vektör arasındaki |kosinüs benzerliği| bunun üstündeyse "bağımlı" sayılır.
# 0,30: rastgele 136 boyutlu vektörlerde beklenen |cos| ~ 1/sqrt(136) ≈ 0,086
# olduğundan bu eşik gerçek bağımlılığı yakalar, gürültüyü elemez.
BAGIMLILIK_ESIGI = 0.30


@dataclass
class IzdusumSerisi:
    """Üretilen vektör kümesi + yeniden üretilebilirlik defteri (madde H-7)."""
    tohum: int
    vektorler: List[dict] = field(default_factory=list)   # {"h": [...], "J": [[...]]}
    elenen: int = 0
    en_buyuk_benzerlik: float = 0.0

    def __len__(self) -> int:
        return len(self.vektorler)


def _duzlestir(h, J) -> List[float]:
    """Vektörü tek boyuta indirger: 16 h + 120 (a<b) J = 136 bileşen."""
    d = list(h)
    for a in range(N_QUBITS):
        for b in range(a + 1, N_QUBITS):
            d.append(J[a][b])
    return d


def _kosinus(u: List[float], v: List[float]) -> float:
    ic = sum(x * y for x, y in zip(u, v))
    nu = math.sqrt(sum(x * x for x in u))
    nv = math.sqrt(sum(y * y for y in v))
    if nu == 0.0 or nv == 0.0:
        return 1.0        # sıfır vektör: her şeye "bağımlı" say, elensin
    return ic / (nu * nv)


def uret(adet: int = 20, tohum: int = 20260920) -> IzdusumSerisi:
    """`adet` kadar bağımsız `cost` vektörü üretir.

    Sabit tohumlu — tohum `IzdusumSerisi.tohum`'a yazılır ve ölçüm kaydına
    girer (madde H-7). Aynı tohum aynı vektörleri verir.

    Eleme ölçütleri:
      * sıfır vektör (norm 0)
      * daha önce kabul edilmiş bir vektörle |cos| > `BAGIMLILIK_ESIGI`
        — birbirinin katı olanlar buraya düşer (|cos| = 1)
    """
    if adet < 1:
        raise ValueError("adet >= 1 olmalı")
    rng = random.Random(tohum)
    seri = IzdusumSerisi(tohum=tohum)
    kabul_duz: List[List[float]] = []

    deneme, ust_sinir = 0, adet * 200
    while len(seri.vektorler) < adet:
        deneme += 1
        if deneme > ust_sinir:
            raise RuntimeError(
                "{} denemede yalnız {} bağımsız vektör bulundu (hedef {}). "
                "Eşik {} fazla katı olabilir.".format(
                    ust_sinir, len(seri.vektorler), adet, BAGIMLILIK_ESIGI))

        h = [rng.uniform(ALT, UST) for _ in range(N_QUBITS)]
        J = [[0.0] * N_QUBITS for _ in range(N_QUBITS)]
        for a in range(N_QUBITS):
            for b in range(a + 1, N_QUBITS):
                J[a][b] = rng.uniform(ALT, UST)

        duz = _duzlestir(h, J)
        if all(x == 0.0 for x in duz):
            seri.elenen += 1
            continue

        enb = 0.0
        for onceki in kabul_duz:
            enb = max(enb, abs(_kosinus(duz, onceki)))
        if enb > BAGIMLILIK_ESIGI:
            seri.elenen += 1
            continue

        seri.en_buyuk_benzerlik = max(seri.en_buyuk_benzerlik, enb)
        kabul_duz.append(duz)
        seri.vektorler.append({"h": h, "J": J})

    return seri
