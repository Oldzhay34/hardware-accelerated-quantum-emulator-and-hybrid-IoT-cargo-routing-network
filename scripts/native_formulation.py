"""HLS çekirdeğinin Python ikizi — "yerleşik" (native) QAOA formülasyonu.

Bu dosya, `hls/src/` altındaki C++ çekirdeğinin ALGORİTMA ŞARTNAMESİDİR.
Qiskit'e karşı doğrulanır; C++ buna karşı doğrulanır. Böylece bir uyuşmazlık
çıktığında "formülasyonu mu yanlış anladım, kodu mu yanlış yazdım" sorusu
ikiye ayrılmış olur.

Yerleşik formülasyon (ADR 0008 / research.md R-4):
  - Başlangıç: H^(x)n yerine DOĞRUDAN düzgün süperpozisyon. n çift olduğu için
    2^(-n/2) tam temsil edilebilir (16 kübitte 2^-8), yani H katmanı hem
    gereksiz hem de sabit-nokta hatasız atlanabilir.
  - Maliyet katmanı: RZZ'yi CX-RZ-CX'e AYRIŞTIRMADAN, tek köşegen geçiş.
    Köşegen matrislerin çarpımı köşegendir; 100 Pauli terimi bedelsiz füzyonlanır.
  - Karıştırıcı: her kübite RX. Eşleme (i, i XOR 2^k) YALNIZCA burada olur.

Kullanım:
    .venv/Scripts/python.exe scripts/native_formulation.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from services.common import stamp
from services.reference import amplitudes


# --------------------------------------------------------------- çekirdek
def init_uniform(n_qubits: int) -> np.ndarray:
    """Düzgün süperpozisyon. H katmanının yerine geçer.

    n çift ise 2^(-n/2) ikinin kuvvetidir ve Q1.17'de TAM temsil edilir —
    bu yüzden başlangıçta hiç kuantalama hatası oluşmaz. Ayrıca |0...0>'ın
    genliği olan 1,0 hiç belleğe yazılmaz; Q1.17 aralığı [-1, 1) olduğu için
    bu ayrıca AP_WRAP tuzağını da ortadan kaldırır.
    """
    return np.full(1 << n_qubits, 2.0 ** (-n_qubits / 2), dtype=np.complex128)


def enerji_tablosu(h: np.ndarray, J: np.ndarray, n_qubits: int) -> np.ndarray:
    """Her temel durum için E(z) = sum_i h_i z_i + sum_{i<j} J_ij z_i z_j.

    z_i = 1 - 2*bit_i  (x_i = 0 -> z_i = +1). Offset DAHİL DEĞİL: global faz
    olduğu için genlikleri değiştirmez, fidelity'yi etkilemez.

    NOT: Bu tablo C-sim kolaylığı içindir. Donanımda 65536 girdilik bir tablo
    +64 BRAM bloğu demek ve SC-002'yi zorlar (NC-2, research.md R-5). Çekirdek
    bunu ya yerinde hesaplayacak ya Gray-kod ile artımlı güncelleyecek — karar
    sentez raporundan sonra.
    """
    idx = np.arange(1 << n_qubits, dtype=np.int64)
    z = 1 - 2 * ((idx[:, None] >> np.arange(n_qubits)) & 1).astype(np.float64)
    E = z @ h
    for i in range(n_qubits):
        for j in range(i + 1, n_qubits):
            if J[i, j] != 0.0:
                E += J[i, j] * z[:, i] * z[:, j]
    return E


def apply_cost_layer(sv: np.ndarray, E: np.ndarray, gamma: float) -> np.ndarray:
    """exp(-i * gamma * H_C) — köşegen, eşleme yok, erişim sıralı."""
    return sv * np.exp(-1j * gamma * E)


def apply_rx(sv: np.ndarray, theta: float, k: int, n_qubits: int) -> np.ndarray:
    """RX(theta) kübit k'ye. Eşlemeli kapı: (i, i XOR 2^k) çiftleri.

    Çift indeksleme `scripts/banking_analysis.py`'deki `pair_index` ile AYNI
    olmalıdır — bankalama analizi ile uygulama aynı erişim desenini paylaşır.
    """
    c = np.cos(theta / 2.0)
    s = np.sin(theta / 2.0)
    out = sv.copy()
    yarim = 1 << (n_qubits - 1)
    j = np.arange(yarim, dtype=np.int64)
    dusuk = j & ((1 << k) - 1)
    yuksek = j >> k
    i0 = (yuksek << (k + 1)) | dusuk          # bit k = 0
    i1 = i0 | (1 << k)                        # bit k = 1
    a, b = sv[i0], sv[i1]
    out[i0] = c * a - 1j * s * b
    out[i1] = -1j * s * a + c * b
    return out


def run_circuit(
    h: np.ndarray, J: np.ndarray, gamma: list[float], beta: list[float],
    n_qubits: int, *, kuantize=None,
) -> np.ndarray:
    """Tam QAOA devresi, yerleşik formülasyonla.

    `kuantize` verilirse HER KAPIDAN SONRA uygulanır — donanımın sabit-nokta
    davranışını taklit eder. None ise tam duyarlık (referans yolu).
    """
    sv = init_uniform(n_qubits)
    E = enerji_tablosu(h, J, n_qubits)
    q = kuantize if kuantize is not None else (lambda v: v)
    sv = q(sv)
    for r in range(len(gamma)):
        sv = q(apply_cost_layer(sv, E, gamma[r]))
        for k in range(n_qubits):
            sv = q(apply_rx(sv, 2.0 * beta[r], k, n_qubits))
    return sv


def beklenen_deger(sv: np.ndarray, E: np.ndarray, offset: float = 0.0) -> float:
    """<psi|H_C|psi> — dağıtım arayüzünün döndürdüğü tek skaler (FR-015).

    ⚠️ OFFSET DAHİL DEĞİL (varsayılan). Çekirdek **Ising beklentisini** döndürür;
    referansın `cost_after` alanı da budur. QUBO enerjisine çevirmek isteyen
    konak tarafı `+ offset` ekler — offset zaten konakta bilinen bir sabittir ve
    çekirdeğe taşınması hem gereksiz hem de sabit-nokta aralığını zorlar
    (bu problemde offset ≈ 35.303, genliklerin aralığından dört kat büyük).
    """
    p = np.abs(sv) ** 2
    return float(np.sum(p * E) / np.sum(p) + offset)


# --------------------------------------------------------------- doğrulama
def fidelity(a: np.ndarray, b: np.ndarray) -> float:
    a = a / np.linalg.norm(a)
    b = b / np.linalg.norm(b)
    return float(abs(np.vdot(a, b)) ** 2)


def _params_ayikla(params: dict[str, float], p: int) -> tuple[list[float], list[float]]:
    """`{'β[0]':…, 'γ[0]':…}` -> (gamma listesi, beta listesi). Sıraya güvenilmez."""
    g, b = [], []
    for r in range(p):
        gk = [k for k in params if k.startswith(("γ", "gamma")) and f"[{r}]" in k]
        bk = [k for k in params if k.startswith(("β", "beta")) and f"[{r}]" in k]
        if len(gk) != 1 or len(bk) != 1:
            raise KeyError(f"r={r} icin parametre bulunamadi. Mevcut: {list(params)}")
        g.append(params[gk[0]])
        b.append(params[bk[0]])
    return g, b


def main() -> None:
    kok = Path(__file__).resolve().parents[1]
    olcum = stamp.measurements_dir(kok)
    sonuc = {}

    for p in (1, 2):
        aday = sorted(olcum.glob(f"reference_*_p{p}_n5.json"))
        ref_yol = None
        for a in reversed(aday):                      # en yeni, params ICEREN
            if json.loads(a.read_text(encoding="utf-8")).get("params"):
                ref_yol = a.with_suffix("")
                break
        if ref_yol is None:
            print(f"p={p}: params iceren referans YOK — atlaniyor")
            continue

        ref = amplitudes.load(ref_yol)
        h = np.array(ref.ising_h)
        J = np.array(ref.ising_J)
        gamma, beta = _params_ayikla(ref.params, p)
        n = ref.n_qubits

        sv = run_circuit(h, J, gamma, beta, n)
        f = fidelity(np.asarray(ref.amplitudes), sv)
        sapma = float(np.max(np.abs(np.abs(sv) - np.abs(np.asarray(ref.amplitudes)))))

        E = enerji_tablosu(h, J, n)
        bd = beklenen_deger(sv, E)                      # offset YOK — cost_after ile ayni kural
        bd_hata = abs(bd - ref.cost_after)

        print(f"p={p}  ({ref_yol.name})")
        print(f"   fidelity (yerlesik vs Qiskit) : {f:.15f}")
        print(f"   azami genlik buyukluk sapmasi : {sapma:.3e}")
        print(f"   beklenen deger (yerlesik)     : {bd:.6f}")
        print(f"   referansin cost_after         : {ref.cost_after:.6f}")
        print(f"   fark                          : {bd_hata:.3e}"
              f"   {'TUTUYOR' if bd_hata < 1e-6 else '!! SAPMA'}")
        sonuc[f"p={p}"] = {
            "fidelity": f, "genlik_sapmasi": sapma,
            "beklenen_deger": bd, "referans_cost_after": ref.cost_after,
            "beklenen_deger_hatasi": bd_hata, "ising_offset": ref.ising_offset,
            "referans": ref_yol.name,
        }

    meta = stamp.stamp(not_="yerlesik formulasyon Qiskit'e karsi dogrulandi")
    meta["sonuclar"] = sonuc
    yol = olcum / f"{stamp.stamped_name('native-formulation')}.json"
    yol.write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\nYazildi: {yol.name}")


if __name__ == "__main__":
    main()
