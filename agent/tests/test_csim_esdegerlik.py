"""G2 kapısı — konak kodlayıcı ↔ C-sim **bit bit** eşdeğerliği (görev T025).

**Kart gerekmez** (Anayasa Prensip V, madde H-5).

Neden beklenen değer değil de word karşılaştırması: beklenen değerleri
karşılaştırmak, iki farklı hatanın birbirini götürmesine izin verir. Word'ler
bit bit tutuyorsa kodlayıcı, Faz 2'de Qiskit'e karşı doğrulanmış (fidelity
≥0,99997) ve RTL'e karşı doğrulanmış (cosim, n=16) C yolunun **tam olarak
aynısını** üretiyor demektir.

C tarafının word dökümünü üretmek için:

    wsl -d Ubuntu -e bash -c "cd /mnt/c/Users/olcay/IdeaProjects/qir-engine && \\
      g++ -std=c++17 -O2 -DQIR_NO_VITIS -DQIR_N_QUBITS=16 -Ihls/src -Ihls/tb \\
      hls/tb/tb_kernel.cpp hls/tb/qir_kernel_debug.cpp hls/src/qir_kernel.cpp \\
      -o hls/build/tb_words && ./hls/build/tb_words \\
      --reference docs/measurements/reference_20260915_c6ad872_p2_n5 --n 16 \\
      --git-hash g2gate --out-dir hls/build --dump-words hls/build/c_words.json"

--------------------------------------------------------------------------
KAPSAM — neyin C'ye karşı doğrulandığı, neyin doğrulanmadığı
--------------------------------------------------------------------------
C'YE KARŞI (bit bit)   : `phases`, `cos_beta`, `sin_beta`
                         → yuvarlama kipi, işaret, TUR dönüşümü, dizi düzeni
KENDİ SÖZLEŞMESİNE KARŞI: ölçekleme protokolü (S, geri dönüş, H-2 payı)
                         → C testbench'inde karşılığı YOK, orada ölçekleme
                           hiç yapılmıyor (bkz. aşağıdaki doyma testi)
"""
import glob
import json
import os

import pytest

from agent.encoder import (
    AralikDisi, N_QUBITS, PHASES_WORD, REAL_Q_MAX, beta_dizileri,
    cost_dizisi, kosum_kodla, phases_dizisi,
)

KOK = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
C_WORDS = os.path.join(KOK, "hls", "build", "c_words.json")
REFERANS = os.path.join(KOK, "docs", "measurements",
                        "reference_20260915_c6ad872_p2_n5.json")


def _param(params, onek, r):
    """C'deki `param_bul` ile aynı: sıraya değil ADA bakar."""
    koseli = "[{}]".format(r)
    for ad, deger in params.items():
        if ad.startswith(onek) and koseli in ad:
            return deger
    raise KeyError("parametre yok: {}{}".format(onek, koseli))


@pytest.fixture(scope="module")
def veri():
    if not os.path.isfile(C_WORDS):
        pytest.skip("C word dökümü yok ({}). Modül başındaki komutu koşun."
                    .format(C_WORDS))
    if not os.path.isfile(REFERANS):
        pytest.skip("referans JSON yok: {}".format(REFERANS))
    with open(C_WORDS, encoding="utf-8") as f:
        c = json.load(f)
    with open(REFERANS, encoding="utf-8") as f:
        ref = json.load(f)
    p = ref["p"]
    gammalar = [_param(ref["params"], "γ", r) for r in range(p)]
    betalar = [_param(ref["params"], "β", r) for r in range(p)]
    return c, ref, p, gammalar, betalar


# =========================================================================
# Bit bit eşdeğerlik
# =========================================================================
def test_phases_bit_bit_ayni(veri):
    """En kritik karşılaştırma: TUR dönüşümü, işaret ve dizi düzeni birlikte."""
    c, ref, p, gammalar, _ = veri
    bizim = phases_dizisi(ref["ising_h"], ref["ising_J"], gammalar)
    assert len(bizim) == len(c["phases"]) == PHASES_WORD
    farkli = [(i, bizim[i], c["phases"][i])
              for i in range(PHASES_WORD) if bizim[i] != c["phases"][i]]
    assert not farkli, "ilk 5 fark (indeks, bizim, C): {}".format(farkli[:5])


def test_beta_bit_bit_ayni(veri):
    c, _, p, _, betalar = veri
    cb, sb, _ = beta_dizileri(betalar)
    assert cb == c["cos_beta"]
    assert sb == c["sin_beta"]


def test_kullanilmayan_katman_iki_tarafta_da_sifir(veri):
    """p=2 için 3. katman yazılmaz; iki taraf da sıfır bırakmalı."""
    c, ref, p, gammalar, _ = veri
    bizim = phases_dizisi(ref["ising_h"], ref["ising_J"], gammalar)
    for i in range(p * 272, PHASES_WORD):
        assert bizim[i] == 0 and c["phases"][i] == 0


def test_p_ve_n_tutuyor(veri):
    c, ref, p, _, _ = veri
    assert c["p"] == p
    assert c["n_qubits"] == ref["n_qubits"] == N_QUBITS


# =========================================================================
# Ölçekleme — kodlayıcının C'den KASITLI olarak ayrıldığı yer
# =========================================================================
def test_referans_katsayilari_gercekten_aralik_disi(veri):
    """Sözleşmenin uyardığı ~1e4 durumu bu referansta GERÇEKTEN var."""
    _, ref, _, _, _ = veri
    n = ref["n_qubits"]
    enb_h = max(abs(x) for x in ref["ising_h"])
    enb_j = max(abs(ref["ising_J"][a][b])
                for a in range(n) for b in range(a + 1, n))
    assert enb_h > 1000.0
    assert enb_j > 1000.0


def test_c_tarafi_cost_u_sessizce_doyuruyor(veri):
    """C testbench'i `cost.h[k] = real_t(h_j[k].num)` diyor — AP_SAT kırpıyor.

    Bu bir **bulgudur**, kodlayıcı hatası değil: ham katsayılar ±1'i kat kat
    aştığı için C tarafındaki `cost` dizisi neredeyse tamamen doymuş durumda.
    Sonuç olarak C'nin `beklenen_deger`'i doymuş bir Hamiltonyen'in beklenen
    değeridir — fidelity'yi etkilemez (`sv` yalnız `phases`'tan gelir).
    """
    c, ref, _, _, _ = veri
    n = ref["n_qubits"]
    doymus = sum(1 for k in range(n)
                 if c["cost"][k] in (REAL_Q_MAX, 0x20000))
    assert doymus == n, "beklenen: 16/16 h girdisi doymuş, bulunan {}".format(doymus)


def test_kodlayici_doyurmak_yerine_atar(veri):
    """Madde H-3: kodlayıcı aynı girdide **sessiz kalmaz**."""
    _, ref, _, _, _ = veri
    with pytest.raises(AralikDisi):
        cost_dizisi(ref["ising_h"], ref["ising_J"])


def test_olceklenince_gecer_ve_phases_degismez(veri):
    """`kosum_kodla` ölçekleyip `cost`'u kurtarır; `phases` HAM kalır.

    Bu, modül başlığındaki ayrımın uçtan uca kanıtıdır: ölçekleme `cost`'u
    kurtarırken devrenin hazırladığı durumu (yani `phases`'ı) değiştirmez.
    """
    c, ref, p, gammalar, betalar = veri
    k = kosum_kodla(ref["ising_h"], ref["ising_J"], gammalar, betalar, p)
    assert k.olcek > 1000.0
    assert k.phases == c["phases"], "ölçekleme phases'ı bozmamalı"
    assert k.cost != c["cost"], "cost ölçekli olduğu için C'den farklı olmalı"
