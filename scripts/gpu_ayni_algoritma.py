r"""6B / T065b — çekirdeğin KENDİ algoritması GPU'da (ADR 0010, katman 2).

`hls/src/qir_kernel.cpp`'deki `qir_kernel(...)` çağrısının CUDA karşılığı;
her çekirdek C++ kaynağındaki bir fonksiyonun satır satır karşılığıdır:

  init_uniform      <- statevector.hpp   init_uniform (2^-8, H katmanı yok)
  cost_tables       <- gates_diagonal.hpp apply_cost_layer, tablo_dusuk/yuksek
  cost_amp          <- gates_diagonal.hpp cost_amp_loop (18 bit tur, 13 bit LUT)
  rx                <- gates_pairing.hpp  apply_rx_dyn (k çalışma zamanı)
  exp_tables/exp_amp <- qir_kernel.cpp    expectation_scaled

Girdiler `bench_kernel.cpp` ile AYNI yoldan hazırlanır (tura_cevir, cos/sin β,
ham h/J) ve zamanlamadan önce GPU'ya yüklenir. Sayısal hat `-DQIR_REAL_FLOAT`
ile aynıdır: genlikler `real` (FP32 ya da FP64), faz tamsayı (mod 2^18),
beklenen değer toplamları double.

Protokol: 🔒 gpu-taban-protokolu v1.1 (docs/measurements/gpu-taban-olcum-protokolu.md)
  §5 katman 2 `T_hesap`: ilk çekirdek başlatmasından önce -> tek float konakta
     (senkronizasyon sonrası). ⛔ Senkronizasyonsuz zamanlama yok.
  §6 doğrulama koşumu zamanlanmaz, ilk 3 koşum atılır, sonda bit bit.
  §8 istatistik: kart protokolü §8'in AYNI kodu (agent/measure_latency.py).
  Prensip IV (T066 katman 2): doğrulama koşumunun statevector'ü altın
     referansa karşı; fidelity < 0,999 ise zamanlama BAŞLAMAZ.

Kullanım (WSL, GPU venv):
    /root/qir-gpu-venv/bin/python scripts/gpu_ayni_algoritma.py --hassasiyet 32 --p 2 --yalniz-dogrula
    /root/qir-gpu-venv/bin/python scripts/gpu_ayni_algoritma.py --hassasiyet 32 --p 2 --saniye 300 --etiket seriG32-2
"""
from __future__ import annotations

import argparse
import json
import math
import os
import sys
import time
from pathlib import Path

import numpy as np

KOK = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(KOK))
from services.common import stamp                          # noqa: E402
from services.qubo import qubo as qubo_mod                 # noqa: E402
from services.reference.cli import ornek_matris            # noqa: E402
from agent import measure_latency as ml                    # noqa: E402  (kart §8, AYNI kod)
from scripts import cpu_load_loop as cll                   # noqa: E402  (ortak yardımcılar)

PROTOKOL = "gpu-taban-protokolu v1.1"
KAPSAMLAR = ("hesap",)                  # protokol §5, katman 2: T_hesap

# hls/src/qir_types.hpp ve trig_lut.hpp ile aynı sabitler
N_QUBITS = 16
N_AMP = 1 << N_QUBITS
N_PAIR = N_AMP // 2
YARIM = N_QUBITS // 2
TABLO = 1 << YARIM
PHASE_BITS = 18
TRIG_LUT_BITS = 13
TRIG_LUT_N = 1 << TRIG_LUT_BITS
P_MAX = 3
UNIFORM_AMP = 1.0 / (1 << (N_QUBITS // 2))
TAU = 6.283185307179586476925286766559
BLOK = 256

CUDA_KAYNAK = r"""
// REAL derleme seçeneğiyle gelir: float (FP32) ya da double (FP64).
#define N_AMP   65536
#define N_Q     16
#define YARIM   8
#define TABLO   256
#define MASKE   ((1u << 18) - 1u)          // phase_t: 18 bit, mod 2^18
#define KAYDIR  5                          // 18 - 13
#define LUT_M   8191u
#define CEYREK  2048u

extern "C" {

__global__ void init_uniform(REAL* re, REAL* im, REAL amp) {
    const int i = blockIdx.x * blockDim.x + threadIdx.x;
    if (i >= N_AMP) return;
    re[i] = amp;
    im[i] = (REAL)0;
}

// apply_cost_layer: tablo_dusuk + tablo_yuksek (+ D), katman başına bir kez
__global__ void cost_tables(const unsigned* ph_h, const unsigned* ph_J,
                            unsigned* FL, unsigned* FH, unsigned* D) {
    const int t = blockIdx.x * blockDim.x + threadIdx.x;
    if (t >= TABLO) return;
    unsigned a = 0u;
    for (int k = 0; k < YARIM; ++k)
        a = ((t >> k) & 1) ? (a - ph_h[k]) & MASKE : (a + ph_h[k]) & MASKE;
    for (int x = 0; x < YARIM; ++x)
        for (int y = x + 1; y < YARIM; ++y)
            a = (((t >> x) ^ (t >> y)) & 1) ? (a - ph_J[x * N_Q + y]) & MASKE
                                            : (a + ph_J[x * N_Q + y]) & MASKE;
    FL[t] = a;

    a = 0u;
    for (int k = 0; k < YARIM; ++k)
        a = ((t >> k) & 1) ? (a - ph_h[YARIM + k]) & MASKE : (a + ph_h[YARIM + k]) & MASKE;
    for (int x = 0; x < YARIM; ++x)
        for (int y = x + 1; y < YARIM; ++y)
            a = (((t >> x) ^ (t >> y)) & 1) ? (a - ph_J[(YARIM + x) * N_Q + YARIM + y]) & MASKE
                                            : (a + ph_J[(YARIM + x) * N_Q + YARIM + y]) & MASKE;
    FH[t] = a;

    for (int aa = 0; aa < YARIM; ++aa) {
        unsigned d = 0u;
        for (int b = 0; b < YARIM; ++b)
            d = ((t >> b) & 1) ? (d - ph_J[aa * N_Q + YARIM + b]) & MASKE
                               : (d + ph_J[aa * N_Q + YARIM + b]) & MASKE;
        D[aa * TABLO + t] = d;
    }
}

// cost_amp_loop: faz topla (mod 2^18) -> 13 bit LUT -> genliği döndür
__global__ void cost_amp(REAL* re, REAL* im, const unsigned* FL, const unsigned* FH,
                         const unsigned* D, const REAL* lut) {
    const int i = blockIdx.x * blockDim.x + threadIdx.x;
    if (i >= N_AMP) return;
    const int lo = i & (TABLO - 1);
    const int hi = i >> YARIM;
    unsigned acc = (FL[lo] + FH[hi]) & MASKE;
    for (int aa = 0; aa < YARIM; ++aa)
        acc = ((lo >> aa) & 1) ? (acc - D[aa * TABLO + hi]) & MASKE
                               : (acc + D[aa * TABLO + hi]) & MASKE;
    const unsigned idx_s = (acc >> KAYDIR) & LUT_M;
    const unsigned idx_c = (idx_s + CEYREK) & LUT_M;
    const REAL s = lut[idx_s];
    const REAL c = lut[idx_c];
    const REAL r = re[i], m = im[i];
    re[i] = r * c - m * s;
    im[i] = r * s + m * c;
}

// apply_rx_dyn: RX(2*beta) kübit k'ye; cos_half = cos(beta), sin_half = sin(beta)
__global__ void rx(REAL* re, REAL* im, int k, REAL c, REAL s) {
    const int j = blockIdx.x * blockDim.x + threadIdx.x;
    if (j >= N_AMP / 2) return;
    const int stride = 1 << k;
    const int dusuk = j & (stride - 1);
    const int yuksek = j >> k;
    const int i0 = (yuksek << (k + 1)) | dusuk;
    const int i1 = i0 | stride;
    const REAL ar = re[i0], ai = im[i0];
    const REAL br = re[i1], bi = im[i1];
    re[i0] = c * ar + s * bi;
    im[i0] = c * ai - s * br;
    re[i1] = c * br + s * ai;
    im[i1] = c * bi - s * ar;
}

// expectation_scaled: tablolar (sum_t = double, QIR_REAL_FLOAT ile aynı)
__global__ void exp_tables(const REAL* ch, const REAL* cJ, double* EL, double* EH, double* G) {
    const int t = blockIdx.x * blockDim.x + threadIdx.x;
    if (t >= TABLO) return;
    double a = 0.0;
    for (int k = 0; k < YARIM; ++k)
        a = ((t >> k) & 1) ? a - (double)ch[k] : a + (double)ch[k];
    for (int x = 0; x < YARIM; ++x)
        for (int y = x + 1; y < YARIM; ++y)
            a = (((t >> x) ^ (t >> y)) & 1) ? a - (double)cJ[x * N_Q + y] : a + (double)cJ[x * N_Q + y];
    EL[t] = a;
    a = 0.0;
    for (int k = 0; k < YARIM; ++k)
        a = ((t >> k) & 1) ? a - (double)ch[YARIM + k] : a + (double)ch[YARIM + k];
    for (int x = 0; x < YARIM; ++x)
        for (int y = x + 1; y < YARIM; ++y)
            a = (((t >> x) ^ (t >> y)) & 1) ? a - (double)cJ[(YARIM + x) * N_Q + YARIM + y]
                                            : a + (double)cJ[(YARIM + x) * N_Q + YARIM + y];
    EH[t] = a;
    for (int aa = 0; aa < YARIM; ++aa) {
        double g = 0.0;
        for (int b = 0; b < YARIM; ++b)
            g = ((t >> b) & 1) ? g - (double)cJ[aa * N_Q + YARIM + b] : g + (double)cJ[aa * N_Q + YARIM + b];
        G[aa * TABLO + t] = g;
    }
}

// exp_amp_loop: genlik başına olasilik*E ve olasilik (toplamlar ayrı indirgemede)
__global__ void exp_amp(const REAL* re, const REAL* im, const double* EL, const double* EH,
                        const double* G, double* pay, double* payda) {
    const int i = blockIdx.x * blockDim.x + threadIdx.x;
    if (i >= N_AMP) return;
    const REAL olasilik = re[i] * re[i] + im[i] * im[i];     // acc_t = real
    const int lo = i & (TABLO - 1);
    const int hi = i >> YARIM;
    double E = EL[lo] + EH[hi];
    for (int aa = 0; aa < YARIM; ++aa)
        E = ((lo >> aa) & 1) ? E - G[aa * TABLO + hi] : E + G[aa * TABLO + hi];
    pay[i] = (double)olasilik * E;
    payda[i] = (double)olasilik;
}

}  // extern "C"
"""


def tura_cevir(aci_carpani: float) -> int:
    """bench_kernel.cpp / tb_kernel.cpp::tura_cevir ile BİREBİR (fmod, nearbyint)."""
    t = math.fmod(aci_carpani / TAU, 1.0)
    if t < 0.0:
        t += 1.0
    olcek = float(1 << PHASE_BITS)
    q = int(np.rint(t * olcek))            # nearbyint: yarımda çifte yuvarlama
    q %= 1 << PHASE_BITS
    return q


def param_bul(params: dict, onek: str, r: int) -> float:
    for ad, v in params.items():
        if ad.startswith(onek) and f"[{r}]" in ad:
            return float(v)
    raise KeyError(f"{onek}[{r}]")


class GpuCekirdek:
    """Girdiler GPU'da hazır; `hesapla()` zamanlanan tek çağrı (qir_kernel karşılığı)."""

    def __init__(self, meta: dict, hassasiyet: int):
        import cupy as cp
        self.cp = cp
        self.real = np.float32 if hassasiyet == 32 else np.float64
        tip = "float" if hassasiyet == 32 else "double"
        self.modul = cp.RawModule(code=CUDA_KAYNAK, options=(f"-DREAL={tip}",))
        self.k = {ad: self.modul.get_function(ad) for ad in
                  ("init_uniform", "cost_tables", "cost_amp", "rx", "exp_tables", "exp_amp")}
        self.p = int(meta["p"])
        h = [float(x) for x in meta["ising_h"]]
        J = [[float(x) for x in satir] for satir in meta["ising_J"]]
        self.ph_h, self.ph_J, self.c, self.s = [], [], [], []
        for r in range(self.p):
            gamma = param_bul(meta["params"], "γ", r)
            beta = param_bul(meta["params"], "β", r)
            ph_h = np.array([tura_cevir(-gamma * h[k]) for k in range(N_QUBITS)], dtype=np.uint32)
            ph_J = np.zeros((N_QUBITS, N_QUBITS), dtype=np.uint32)
            for a in range(N_QUBITS):
                for b in range(a + 1, N_QUBITS):
                    ph_J[a, b] = tura_cevir(-gamma * J[a][b])
            self.ph_h.append(cp.asarray(ph_h))
            self.ph_J.append(cp.asarray(ph_J.ravel()))
            self.c.append(self.real(math.cos(beta)))      # real_t(std::cos(beta))
            self.s.append(self.real(math.sin(beta)))
        ch = np.array(h, dtype=self.real)                 # cost.h[k] = real_t(h)
        cJ = np.zeros((N_QUBITS, N_QUBITS), dtype=self.real)
        for a in range(N_QUBITS):
            for b in range(a + 1, N_QUBITS):
                cJ[a, b] = J[a][b]
        self.ch, self.cJ = cp.asarray(ch), cp.asarray(cJ.ravel())
        # gen_trig_lut.py ile aynı tam değerler; real'e dönüşüm = derleme zamanı kuantalaması
        lut = np.array([math.sin(2.0 * math.pi * i / TRIG_LUT_N) for i in range(TRIG_LUT_N)])
        self.lut = cp.asarray(lut.astype(self.real))
        self.re = cp.empty(N_AMP, dtype=self.real)
        self.im = cp.empty(N_AMP, dtype=self.real)
        self.FL = cp.empty(TABLO, dtype=cp.uint32)
        self.FH = cp.empty(TABLO, dtype=cp.uint32)
        self.D = cp.empty(YARIM * TABLO, dtype=cp.uint32)
        self.EL = cp.empty(TABLO, dtype=cp.float64)
        self.EH = cp.empty(TABLO, dtype=cp.float64)
        self.G = cp.empty(YARIM * TABLO, dtype=cp.float64)
        self.pay = cp.empty(N_AMP, dtype=cp.float64)
        self.payda = cp.empty(N_AMP, dtype=cp.float64)
        self.amp = self.real(UNIFORM_AMP)
        self.kler = [np.int32(k) for k in range(N_QUBITS)]
        self.g_amp = ((N_AMP + BLOK - 1) // BLOK,)
        self.g_cift = ((N_PAIR + BLOK - 1) // BLOK,)
        self.g_tablo = ((TABLO + BLOK - 1) // BLOK,)
        self.b = (BLOK,)

    def hesapla(self) -> float:
        """qir_kernel(...) karşılığı. Dönüşte tek float KONAKTA (örtük senkron)."""
        k = self.k
        k["init_uniform"](self.g_amp, self.b, (self.re, self.im, self.amp))
        for r in range(self.p):
            k["cost_tables"](self.g_tablo, self.b, (self.ph_h[r], self.ph_J[r], self.FL, self.FH, self.D))
            k["cost_amp"](self.g_amp, self.b, (self.re, self.im, self.FL, self.FH, self.D, self.lut))
            for kk in self.kler:
                k["rx"](self.g_cift, self.b, (self.re, self.im, kk, self.c[r], self.s[r]))
        k["exp_tables"](self.g_tablo, self.b, (self.ch, self.cJ, self.EL, self.EH, self.G))
        k["exp_amp"](self.g_amp, self.b, (self.re, self.im, self.EL, self.EH, self.G, self.pay, self.payda))
        sonuc = self.pay.sum() / self.payda.sum()
        return float(np.float32(float(sonuc)))       # float(double(pay)/double(payda)); .item() senkronlar

    def statevector(self) -> np.ndarray:
        return self.re.get().astype(np.float64) + 1j * self.im.get().astype(np.float64)


class _Sonuc:
    """cpu_load_loop.dogrula() bir Aer sonucu bekler; yalnız get_statevector() kullanır."""

    def __init__(self, sv):
        self._sv = sv

    def get_statevector(self):
        return self._sv


def _beklenen_numpy(sv: np.ndarray, meta: dict) -> float:
    """Çekirdeğin tanımıyla <psi|H_C|psi> (offset yok), NumPy'da, double."""
    h = np.array(meta["ising_h"], dtype=float)
    J = np.array(meta["ising_J"], dtype=float)
    idx = np.arange(N_AMP)
    z = 1.0 - 2.0 * ((idx[:, None] >> np.arange(N_QUBITS)) & 1)      # bit 0 -> +1
    E = z @ h + np.einsum("ia,ab,ib->i", z, np.triu(J, 1), z)
    pr = np.abs(sv) ** 2
    return float(pr @ E / pr.sum())


def _cupy_ortami(hassasiyet: int) -> dict:
    import cupy as cp
    return {
        "cupy": cp.__version__,
        "cuda_runtime": cp.cuda.runtime.runtimeGetVersion(),
        "cuda_surucu": cp.cuda.runtime.driverGetVersion(),
        "aygit": cp.cuda.runtime.getDeviceProperties(0)["name"].decode(),
        "sm": cp.cuda.Device(0).compute_capability,
        "hassasiyet": f"FP{hassasiyet}",
        "derleme": "NVRTC, varsayilan secenekler (fmad acik)",
        "blok": BLOK,
        "python": sys.version.split()[0],
        "nproc": os.cpu_count(),
        "gpu": cll._gpu_bilgisi(),
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--hassasiyet", type=int, choices=(32, 64), required=True)
    ap.add_argument("--p", type=int, default=2)
    ap.add_argument("--saniye", type=int, default=int(ml.SERI_SURE_S))
    ap.add_argument("--etiket", default="yuk")
    ap.add_argument("--referans", default=None)
    ap.add_argument("--yalniz-dogrula", action="store_true")
    ap.add_argument("--cikti-dizini", default=None)
    a = ap.parse_args()

    cikti_dizini = Path(a.cikti_dizini) if a.cikti_dizini else KOK / "docs" / "measurements"
    resmi = cikti_dizini.resolve() == (KOK / "docs" / "measurements").resolve()
    kod_kirli_bas = cll._kod_kirli()
    if resmi and not a.yalniz_dogrula and kod_kirli_bas:
        raise SystemExit("⛔ commit'lenmemis kod var -- protokol §4: seri temiz agacta kosulur "
                         "(deneme icin --cikti-dizini <baska dizin>)")

    ref_json = cll.referans_bul(a.p, a.referans)
    meta = json.loads(ref_json.read_text(encoding="utf-8"))
    if int(meta["p"]) != a.p:
        raise SystemExit(f"referans p={meta['p']}, istenen p={a.p}")
    cek = GpuCekirdek(meta, a.hassasiyet)
    ortam = _cupy_ortami(a.hassasiyet)
    print(f"GPU ayni algoritma: FP{a.hassasiyet}, p={a.p}, referans {ref_json.name}")

    # §6: dogrulama kosumu -- zamanlanmaz (NVRTC derlemesi + ilk tahsis de burada)
    bd = cek.hesapla()
    sv = cek.statevector()
    problem = qubo_mod.matrix_to_qubo(ornek_matris(5))
    dogrulama = cll.dogrula(_Sonuc(sv), ref_json, meta, problem)
    ref_sv = np.load(ref_json.with_suffix(".npy"))
    bd_np = _beklenen_numpy(sv, meta)
    bd_ref = _beklenen_numpy(ref_sv, meta)
    dogrulama.update({
        "beklenen_deger_gpu": bd,
        "beklenen_deger_numpy_bu_sv": bd_np,
        "beklenen_deger_numpy_referans_sv": bd_ref,
        "beklenen_deger_bagil_hata_referansa": bd / bd_ref - 1.0,
        "referans_cost_after": meta.get("cost_after"),
    })
    print(f"dogrulama      : fidelity {dogrulama['fidelity']:.12f} (1-F {dogrulama['bir_eksi_F']:.2e}), "
          f"P_opt {dogrulama['p_optimum_bu_kosum']:.6e} (ref {dogrulama['p_optimum_referans']:.6e}), "
          f"<E> {bd:.6f} (ref sv {bd_ref:.6f}) -> {'GECTI' if dogrulama['gecti'] else 'KALDI'}")
    if a.yalniz_dogrula or not dogrulama["gecti"]:
        kayit = {"ne": "GPU ayni algoritma, altin referansa karsi (T066 katman 2)",
                 "damga": stamp.stamp(hassasiyet=a.hassasiyet, p=a.p),
                 "kod_kirli": kod_kirli_bas, "ortam": ortam, "dogrulama": dogrulama}
        yol = cikti_dizini / f"{stamp.stamped_name('gpu-ayni-algoritma-dogrulama')}_fp{a.hassasiyet}_p{a.p}.json"
        yol.write_text(json.dumps(kayit, indent=2, ensure_ascii=False), encoding="utf-8")
        print(f"yazildi        : {yol.name}")
        if not dogrulama["gecti"]:
            raise SystemExit("⛔ fidelity H esiginin altinda -- ZAMANLAMA YAPILMADI")
        return 0
    ilk_sv = np.ascontiguousarray(sv).tobytes()

    yol = cikti_dizini / f"{stamp.stamped_name('gpu-ayni-algoritma')}_{a.etiket}_fp{a.hassasiyet}_p{a.p}.json"
    kismi = yol.with_suffix(".kismi.jsonl")
    kosullar_bas = {"zaman": time.strftime("%Y-%m-%dT%H:%M:%S%z"), "loadavg": cll._loadavg(),
                    "gpu": cll._gpu_durumu(), "guc": cll._windows_guc()}
    kismi_f = kismi.open("w", encoding="utf-8")
    kismi_f.write(json.dumps({"ortam": ortam, "p": a.p, "kosullar_bas": kosullar_bas},
                             ensure_ascii=False) + "\n")
    yazilan = 0

    print(f"{PROTOKOL} -- {a.saniye} sn donguye giriliyor... (DOKUNMA)")
    sureler, zamanlar, gpu_okumalari = [], [], []
    bas = time.perf_counter()
    son_pencere = 0.0
    while time.perf_counter() - bas < a.saniye:
        t0 = time.perf_counter()
        cek.hesapla()                       # tek float konakta donene kadar
        t1 = time.perf_counter()
        sureler.append(t1 - t0)
        zamanlar.append(t0 - bas)
        gecen = t1 - bas
        if gecen - son_pencere >= ml.PENCERE_S:
            pencere = sorted(s for s, t in zip(sureler, zamanlar) if t >= son_pencere)
            durum = cll._gpu_durumu()
            gpu_okumalari.append({"t_s": round(gecen, 3), **durum})
            print(f"  {gecen:5.0f} sn   {len(sureler):7d} kosum   "
                  f"pencere medyani {pencere[len(pencere) // 2] * 1000:8.4f} ms   "
                  f"GPU {durum['sicaklik_C']} C")
            son_pencere = gecen
            for t, s in zip(zamanlar[yazilan:], sureler[yazilan:]):
                kismi_f.write(f"[{t:.6f}, {s * 1000:.5f}]\n")
            yazilan = len(sureler)
            kismi_f.flush()
            os.fsync(kismi_f.fileno())
    toplam = time.perf_counter() - bas
    kismi_f.close()

    # §6 sonda: statevector (yerinde; son kosumun durumu) dogrulama kosumununkiyle BIT BIT
    son_kosum_ayni = np.ascontiguousarray(cek.statevector()).tobytes() == ilk_sv
    gecersiz = None if son_kosum_ayni else "son kosumun statevector'u dogrulama kosumununkinden farkli (§6)"
    kosullar_son = {"zaman": time.strftime("%Y-%m-%dT%H:%M:%S%z"), "loadavg": cll._loadavg(),
                    "gpu": cll._gpu_durumu(), "guc": cll._windows_guc()}

    s_ist, z_ist = sureler[ml.ISINMA:], zamanlar[ml.ISINMA:]
    konfig = f"gpu_ayni_algoritma_fp{a.hassasiyet}_n16_p{a.p}"
    kw = {"kapsamlar": KAPSAMLAR, "protokol_surumu": PROTOKOL}
    pen = ml.pencereler(z_ist, s_ist)
    for p_ in pen:
        bitis = p_["bas_s"] + ml.PENCERE_S
        yakin = min(gpu_okumalari, key=lambda g: abs(g["t_s"] - bitis), default=None)
        p_["gpu"] = yakin if yakin and abs(yakin["t_s"] - bitis) <= ml.PENCERE_S / 2 else None

    ozet = {
        "ne": "GPU ayni algoritma gecikme serisi (6B, katman 2, T065b)",
        "protokol_surumu": PROTOKOL,
        "gecerli": gecersiz is None,
        "gecersizlik_nedeni": gecersiz,
        "etiket": a.etiket,
        "damga": stamp.stamp(hassasiyet=a.hassasiyet, saniye=a.saniye, p=a.p),
        "kod_kirli_bas": kod_kirli_bas,
        "kod_kirli_son": cll._kod_kirli(),
        "ortam": ortam,
        "kosullar_bas": kosullar_bas,
        "kosullar_son": kosullar_son,
        "dogrulama": dogrulama,
        "son_kosum_ayni": son_kosum_ayni,
        "p": a.p,
        "toplam_saniye": round(toplam, 3),
        "zamanlanan_kosum": len(sureler),
        "isinma_atilan": min(ml.ISINMA, len(sureler)),
        "verim_kosum_sn": round(len(sureler) / toplam, 3),
        "seri": ml.olcum_serisi(konfig, "hesap", s_ist, **kw),
        "ilk_ve_son": ml.ilk_ve_son(konfig, "hesap", z_ist, s_ist, **kw),
        "pencereler": pen,
        "plato": ml.plato(pen),
        "ham_iz_ms": [[round(t, 6), round(s * 1000, 5)] for t, s in zip(zamanlar, sureler)],
    }
    yol.write_text(json.dumps(ozet, indent=1, ensure_ascii=False), encoding="utf-8")
    kismi.unlink()

    sr, pl = ozet["seri"], ozet["plato"]
    print()
    print(f"gecerli        : {ozet['gecerli']}" + (f"  ({gecersiz})" if gecersiz else ""))
    print(f"kosum          : {len(sureler)} (isinma {ozet['isinma_atilan']} atildi), "
          f"verim {ozet['verim_kosum_sn']} kosum/sn")
    print(f"medyan / IQR   : {sr['medyan_s'] * 1000:.4f} ms / {sr['yayilim_s'] * 1000:.4f} ms  "
          f"(p99 {sr['p99_s'] * 1000:.4f}, maks {sr['max_s'] * 1000:.4f})")
    print(f"plato (±%0,5)  : {pl.get('oturdu')}  "
          f"(en buyuk sapma {pl.get('en_buyuk_sapma_orani', float('nan')):.4f})")
    print(f"son kosum ayni : {son_kosum_ayni}")
    print(f"yazildi        : {yol}")
    return 0 if ozet["gecerli"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
