"""Konak kodlayıcı — ölçekleme + sabit-nokta paketleme.

Sözleşme: `specs/003-zynq-ps-kartta-kosum/contracts/host-encoder.md`
Register haritası: `.../contracts/axi-register-map.md`

Bu, fazın **en olası sessiz hata kaynağıdır**. Ham QUBO katsayıları ~1e4
mertebesinde; `ap_fixed`'in `AP_SAT`'ı onları uyarı vermeden kırpar ve hata
donanıma yıkılır. Bu yüzden madde H-3: kırpma **istisna fırlatır**.

Kartsız doğrulanır (Anayasa Prensip V, madde H-5) — `agent/tests/`.

--------------------------------------------------------------------------
ÖLÇEKLEME NEREYE UYGULANIR — dikkat
--------------------------------------------------------------------------
Ölçek **yalnız `cost`'a** uygulanır, `phases`'a UYGULANMAZ.

    cost   : real_t = ap_fixed<18,1> → [-1, 1) olmak ZORUNDA → ölçeklenir
    phases : mod 1'e indirgenmiş TUR → taşma zaten mod 2π → HAM kullanılır

Gerekçe `gates_diagonal.hpp`'de yazılı: fazlar konakta mod 1'e indirgendiği
için `|h| ~ 1e4` sorunu orada zaten çözülmüştür; ölçeklemek gereksiz olmanın
ötesinde **yanlıştır** — devrenin ürettiği durumu değiştirir. Sözleşme maddesi
H-4 de `h'_k` değil `h_k` yazar.

Sonuç: kart, GERÇEK QAOA durumunu hazırlar (ham h, ham gamma) ama beklenen
değeri ÖLÇEKLİ Hamiltonyen üzerinden ölçer; `* S` ile ham birime dönülür.

C tarafındaki karşılığı: `hls/tb/tb_kernel.cpp::tura_cevir`.
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Sequence

# --- Çekirdek sabitleri (hls/src/qir_types.hpp ile birebir) ---------------
N_QUBITS = 16
P_MAX = 3

REAL_BITS = 18          # ap_fixed<18, 1, AP_RND_CONV, AP_SAT>
REAL_FRAC = 17
REAL_SCALE = 1 << REAL_FRAC          # 131072
REAL_Q_MIN = -(1 << REAL_FRAC)       # -131072  ->  -1,0
REAL_Q_MAX = (1 << REAL_FRAC) - 1    # +131071  ->  +1 - 2^-17

PHASE_BITS = 18         # ap_uint<18>, TUR cinsinden
PHASE_SCALE = 1 << PHASE_BITS        # 262144

MASKE_18 = 0x3FFFF
TAU = 2.0 * math.pi

# --- Dizi boyutları (contracts/axi-register-map.md) -----------------------
COST_H = N_QUBITS                    # 16
COST_J = N_QUBITS * N_QUBITS         # 256  (yalnız a<b okunur, hepsi yazılır)
COST_WORD = COST_H + COST_J          # 272
PHASES_WORD = P_MAX * COST_WORD      # 816
BETA_WORD = P_MAX                    # 3
TOPLAM_YAZMA = PHASES_WORD + COST_WORD + 2 * BETA_WORD + 1   # 1095

# Kenar payı (madde H-2). Q1.17'nin üst sınırı 1 - 2^-17'dir ve AP_SAT tam
# 1,0'ı kırpar; S = max|·| seçilseydi en büyük katsayı tam 1,0'a oturup
# sessizce kırpılırdı.
OLCEK_PAYI = 1.001


class AralikDisi(ValueError):
    """Madde H-3: bir katsayı Q1.17'ye sığmıyor. Sessizce doyurmak yerine atılır."""


# =========================================================================
# Sabit-nokta dönüşümleri
# =========================================================================
def real_worda(x: float, *, ad: str = "deger") -> int:
    """Q1.17'ye paketle (`real_t`).

    `AP_RND_CONV` = yakınsak yuvarlama (yarıyı çifte). Python'un `round`'u da
    öyledir, bu yüzden birebir eşleşir — `floor(x+0.5)` KULLANILMAZ, tam .5
    sınırlarında ayrışırdı.

    Madde H-3: aralık dışıysa istisna. İşaret genişletmesi yok; ikiye tümleyen
    18-bit deseni maskelenir.
    """
    if not math.isfinite(x):
        raise AralikDisi("{}: sonlu değil ({})".format(ad, x))
    q = round(x * REAL_SCALE)
    if q < REAL_Q_MIN or q > REAL_Q_MAX:
        raise AralikDisi(
            "{}={!r} Q1.17'ye sığmıyor: q={} ∉ [{}, {}]. "
            "Geçerli aralık [-1, {:.8f}]. Ölçekleme atlanmış olabilir "
            "(madde H-3: sessiz kırpma yasak).".format(
                ad, x, q, REAL_Q_MIN, REAL_Q_MAX, REAL_Q_MAX / REAL_SCALE)
        )
    return q & MASKE_18


def word_reale(w: int) -> float:
    """`real_worda`'nın tersi — testler ve teşhis için."""
    q = w & MASKE_18
    if q >= (1 << (REAL_BITS - 1)):      # işaret biti
        q -= (1 << REAL_BITS)
    return q / REAL_SCALE


def faz_worda(aci_carpani: float) -> int:
    """Radyan cinsinden faz çarpanını TUR'a indirger (`phase_t`).

    `hls/tb/tb_kernel.cpp::tura_cevir` ile birebir aynı:

        t = fmod(aci/TAU, 1.0);  if (t < 0) t += 1
        q = nearbyint(t * 2^18) % 2^18

    ⚠️ Buradaki sarma **hata değil, istenen davranıştır** (madde H-4).
    Faz mod 1'e indirgendiği için çekirdekteki toplama taşması zaten mod 2π
    olur. Bu yüzden `real_worda`'nın aksine istisna fırlatılmaz.
    """
    if not math.isfinite(aci_carpani):
        raise AralikDisi("faz çarpanı sonlu değil ({})".format(aci_carpani))
    t = math.fmod(aci_carpani / TAU, 1.0)
    if t < 0.0:
        t += 1.0
    q = round(t * PHASE_SCALE) % PHASE_SCALE
    return q & MASKE_18


# =========================================================================
# Ölçekleme protokolü (maddeler H-1, H-2, H-6)
# =========================================================================
def olcek_bul(h: Sequence[float], J: Sequence[Sequence[float]]) -> float:
    """`S = 1.001 * max(|h|, |J|)` — yalnız `a < b` üçgeni sayılır.

    Hepsi sıfırsa `S = 1.0` döner (bölme yok, yol aynı kalır).
    """
    enb = 0.0
    for v in h:
        enb = max(enb, abs(v))
    for a in range(N_QUBITS):
        for b in range(a + 1, N_QUBITS):
            enb = max(enb, abs(J[a][b]))
    if enb == 0.0:
        return 1.0
    return OLCEK_PAYI * enb


def olcekle(h: Sequence[float], J: Sequence[Sequence[float]], S: float):
    """`h/S`, `J/S` döndürür. `J`'nin yalnız `a < b` üçgeni doldurulur."""
    if S <= 0.0 or not math.isfinite(S):
        raise AralikDisi("ölçek S geçersiz: {!r}".format(S))
    ho = [v / S for v in h]
    Jo = [[0.0] * N_QUBITS for _ in range(N_QUBITS)]
    for a in range(N_QUBITS):
        for b in range(a + 1, N_QUBITS):
            Jo[a][b] = J[a][b] / S
    return ho, Jo


# =========================================================================
# Dizi yerleşimi (contracts/axi-register-map.md)
# =========================================================================
def cost_dizisi(h_olcekli: Sequence[float],
                J_olcekli: Sequence[Sequence[float]]) -> list:
    """272 word: `[0..15] = h[k]`, `[16..271] = J[a][b]` → `16 + 16*a + b`.

    `J` yalnız `a < b` için okunur ama **256 word'ün tamamı yazılır**;
    kullanılmayanlar sıfır kalır.
    """
    w = [0] * COST_WORD
    for k in range(N_QUBITS):
        w[k] = real_worda(h_olcekli[k], ad="h[{}]".format(k))
    for a in range(N_QUBITS):
        for b in range(a + 1, N_QUBITS):
            w[COST_H + N_QUBITS * a + b] = real_worda(
                J_olcekli[a][b], ad="J[{}][{}]".format(a, b))
    return w


def phases_dizisi(h_ham: Sequence[float],
                  J_ham: Sequence[Sequence[float]],
                  gammalar: Sequence[float]) -> list:
    """816 word: `[r*272 + 0..15] = h`, `[r*272 + 16..271] = J`, `r = 0..2`.

    ⚠️ **HAM** katsayılar kullanılır, ölçekli olanlar değil — modül başındaki
    açıklamaya bakın. Kullanılmayan katmanlar (r ≥ p) sıfır kalır: çekirdek
    onları okumaz.
    """
    if len(gammalar) > P_MAX:
        raise AralikDisi(
            "gamma sayısı {} > P_MAX={}".format(len(gammalar), P_MAX))
    w = [0] * PHASES_WORD
    for r, gamma in enumerate(gammalar):
        taban = r * COST_WORD
        for k in range(N_QUBITS):
            w[taban + k] = faz_worda(-gamma * h_ham[k])
        for a in range(N_QUBITS):
            for b in range(a + 1, N_QUBITS):
                w[taban + COST_H + N_QUBITS * a + b] = faz_worda(
                    -gamma * J_ham[a][b])
    return w


def real_worda_doyurarak(x: float, *, ad: str):
    """`real_worda` gibi, ama aralık dışında **istisna atmaz — doyurur**.

    Yalnız `cos_beta`/`sin_beta` için kullanılır ve sebebi şudur: C referansı
    (`tb_kernel.cpp:176`) düz atama yapar —

        cos_beta[r] = std::cos(beta);     // real_t, AP_RND_CONV + AP_SAT

    yani `cos(0) = 1,0` orada **sessizce** `1 - 2^-17`'ye doyar. Kodlayıcı
    istisna atsaydı C-sim'den ayrışır ve G2 eşdeğerlik kapısı kırılırdı.

    Madde H-3 buna aykırı değildir: H-3 **katsayılar** içindir; orada aralık
    dışı bir değer ölçekleme hatasının belirtisidir. `cos`/`sin` ise yapısı
    gereği [-1, 1] içindedir; sınıra dayanması hata değil, Q1.17'nin doğal
    kısıtıdır. Yine de **sessiz kalmaz**: doyma bir uyarı olarak döner ve
    `KodlanmisKosum.doyma_uyarilari` içinde saklanır.

    Döner: `(word, uyari)` — `uyari` doyma olmadıysa `None`.
    """
    if not math.isfinite(x):
        raise AralikDisi("{}: sonlu değil ({})".format(ad, x))
    q = round(x * REAL_SCALE)
    uyari = None
    if q > REAL_Q_MAX:
        uyari = "{}={!r} doydu: {} -> {} ({:.8f})".format(
            ad, x, q, REAL_Q_MAX, REAL_Q_MAX / REAL_SCALE)
        q = REAL_Q_MAX
    elif q < REAL_Q_MIN:
        uyari = "{}={!r} doydu: {} -> {} (-1.0)".format(ad, x, q, REAL_Q_MIN)
        q = REAL_Q_MIN
    return q & MASKE_18, uyari


def beta_dizileri(betalar: Sequence[float]):
    """`cos_beta[3]`, `sin_beta[3]` — her biri Q1.17.

    Döner: `(cos_beta, sin_beta, uyarilar)`. `uyarilar` boş değilse en az bir
    değer Q1.17 sınırına dayanmıştır (tipik durum: `beta ≈ 0` → `cos ≈ 1,0`).
    Bu, C referansının davranışıyla aynıdır — ama kayda geçer.
    """
    if len(betalar) > P_MAX:
        raise AralikDisi(
            "beta sayısı {} > P_MAX={}".format(len(betalar), P_MAX))
    c = [0] * BETA_WORD
    s = [0] * BETA_WORD
    uyarilar = []
    for r, beta in enumerate(betalar):
        c[r], u1 = real_worda_doyurarak(math.cos(beta),
                                        ad="cos_beta[{}]".format(r))
        s[r], u2 = real_worda_doyurarak(math.sin(beta),
                                        ad="sin_beta[{}]".format(r))
        uyarilar += [u for u in (u1, u2) if u]
    return c, s, uyarilar


# =========================================================================
# Bir koşumun tam kodlaması
# =========================================================================
@dataclass
class KodlanmisKosum:
    """Karta yazılacak her şey + geri dönüş için gereken defter.

    Madde H-1: `olcek` kaydedilir — yoksa `beklenen_deger_ham` yorumlanamaz.
    Madde H-6: ham ve ölçek geri uygulanmış değerler **ayrı** saklanır.
    """
    cost: list                 # 272 word
    phases: list               # 816 word
    cos_beta: list             # 3 word
    sin_beta: list             # 3 word
    p: int
    olcek: float               # S  (madde H-1)
    h_ham: list = field(default_factory=list)
    J_ham: list = field(default_factory=list)
    gammalar: list = field(default_factory=list)
    betalar: list = field(default_factory=list)
    doyma_uyarilari: list = field(default_factory=list)

    @property
    def yazma_sayisi(self) -> int:
        """Tam çağrı sırasının yazma sayısı — `T_yazma` kapsamının tanımı."""
        return (len(self.phases) + len(self.cost)
                + len(self.cos_beta) + len(self.sin_beta) + 1)

    def ham_bekleneni_coz(self, beklenen_deger_ham: float) -> float:
        """Madde H-6: kartın döndürdüğü ölçekli değeri ham birime çevirir."""
        return beklenen_deger_ham * self.olcek


def kosum_kodla(h: Sequence[float],
                J: Sequence[Sequence[float]],
                gammalar: Sequence[float],
                betalar: Sequence[float],
                p: int) -> KodlanmisKosum:
    """Tam kodlama. `p`, `gammalar`/`betalar` uzunluğuyla tutarlı olmalı."""
    if not (1 <= p <= P_MAX):
        raise AralikDisi("p={} ∉ [1, {}] (madde A-3)".format(p, P_MAX))
    if len(h) != N_QUBITS:
        raise AralikDisi("h uzunluğu {} != {}".format(len(h), N_QUBITS))
    if len(gammalar) != p or len(betalar) != p:
        raise AralikDisi(
            "p={} ama gamma={}, beta={} verildi".format(
                p, len(gammalar), len(betalar)))

    S = olcek_bul(h, J)
    h_olcekli, J_olcekli = olcekle(h, J, S)
    c, s, uyarilar = beta_dizileri(betalar)
    return KodlanmisKosum(
        cost=cost_dizisi(h_olcekli, J_olcekli),
        phases=phases_dizisi(h, J, gammalar),      # HAM — bkz. modül başlığı
        cos_beta=c,
        sin_beta=s,
        p=p,
        olcek=S,
        h_ham=list(h),
        J_ham=[list(satir) for satir in J],
        gammalar=list(gammalar),
        betalar=list(betalar),
        doyma_uyarilari=uyarilar,
    )
