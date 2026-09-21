// PS↔PL taban ölçümü — görev T045b.
//
// Aynı `qir_kernel` çağrısını KONAK İŞLEMCİDE zamanlar. Amaç, FPGA'nın
// 37,28 ms'lik çağrısıyla kıyaslanabilir tek bir sayı üretmek.
//
// NEDEN AYRI DOSYA: `tb_kernel.cpp` doğrulanmış bir dosyadır (C-sim regresyon
// kapısı ona bağlı). Zamanlama kodu oraya karışmaz.
//
// İKİ VARYANT — ikisi de ölçülür, çünkü aralarındaki fark büyüktür:
//
//   (a) VARSAYILAN  : `ap_fixed_mock`, yani Q1.17. Donanımla AYNI aritmetik.
//                     ⚠️ Ama taklit sınıf her işlemi `double`'da yapıp
//                     kuantalar. Cortex-A9'un NEON'u çift duyarlık DESTEKLEMEZ
//                     → bu varyant ARM'da yazılım FPU'sunda sürünür ve
//                     hızlanmayı ŞİŞİRİR. Üst sınır olarak raporlanır.
//
//   (b) -DQIR_REAL_FLOAT : yerel `float`. Yetkin bir ARM gerçeklemesinin
//                     yapacağı şey. **Manşet hızlanma buna karşı hesaplanır.**
//
// Derleme (kartta):
//   g++ -std=c++17 -O3 -DQIR_NO_VITIS -DQIR_N_QUBITS=16 \
//       -Ihls/src -Ihls/tb hls/tb/bench_kernel.cpp hls/src/qir_kernel.cpp \
//       -o bench_q117
//   ... aynısı + -DQIR_REAL_FLOAT -o bench_float
#include <algorithm>
#include <chrono>
#include <cmath>
#include <cstdio>
#include <cstring>
#include <string>
#include <vector>

#include "../src/qir_types.hpp"
#include "../src/gates_diagonal.hpp"
#include "../src/qir_kernel.hpp"
#include "meta_reader.hpp"

namespace {

constexpr double TAU = 6.283185307179586476925286766559;

// tb_kernel.cpp::tura_cevir ile BİREBİR aynı — kopya değil, aynı davranış
// olması şart; yoksa farklı bir devre ölçülür.
qir::phase_t tura_cevir(double aci_carpani) {
    double t = std::fmod(aci_carpani / TAU, 1.0);
    if (t < 0.0) t += 1.0;
    const double olcek = qir::PHASE_SCALE;
    long long q = static_cast<long long>(std::nearbyint(t * olcek));
    q %= static_cast<long long>(olcek);
    if (q < 0) q += static_cast<long long>(olcek);
    return qir::phase_t(static_cast<uint64_t>(q));
}

double param_bul(const tbjson::Value& params, const char* onek, int r) {
    const std::string koseli = "[" + std::to_string(r) + "]";
    for (const auto& kv : params.obj)
        if (kv.first.rfind(onek, 0) == 0 && kv.first.find(koseli) != std::string::npos)
            return kv.second.num;
    throw std::runtime_error("parametre bulunamadi");
}

double yuzdelik(std::vector<double> v, double p) {
    std::sort(v.begin(), v.end());
    if (v.empty()) return 0.0;
    const double idx = p * (double(v.size()) - 1.0);
    const size_t lo = size_t(std::floor(idx)), hi = size_t(std::ceil(idx));
    return v[lo] + (v[hi] - v[lo]) * (idx - double(lo));
}

}  // namespace

int main(int argc, char** argv) {
    std::string ref_taban;
    int tekrar = 30, isinma = 3;

    for (int i = 1; i < argc; ++i) {
        const std::string a = argv[i];
        if (a == "--reference" && i + 1 < argc) ref_taban = argv[++i];
        else if (a == "--tekrar" && i + 1 < argc) tekrar = std::stoi(argv[++i]);
        else if (a == "--isinma" && i + 1 < argc) isinma = std::stoi(argv[++i]);
        else { std::fprintf(stderr, "bilinmeyen argüman: %s\n", a.c_str()); return 2; }
    }
    if (ref_taban.empty()) {
        std::fprintf(stderr,
            "kullanim: bench_kernel --reference <yol/reference_..._p2_n5> "
            "[--tekrar 30] [--isinma 3]\n");
        return 2;
    }
    for (const char* uz : {".npy", ".json"}) {
        const size_t L = std::strlen(uz);
        if (ref_taban.size() > L && ref_taban.compare(ref_taban.size() - L, L, uz) == 0)
            ref_taban.resize(ref_taban.size() - L);
    }

    try {
        const tbjson::Value meta = tbjson::dosyadan(ref_taban + ".json");
        const int n = static_cast<int>(meta.at("n_qubits").num);
        const int p = static_cast<int>(meta.at("p").num);
        if (n != qir::N_QUBITS) {
            std::fprintf(stderr, "HATA: referans %d kubit, ikili %d icin derlenmis\n",
                         n, qir::N_QUBITS);
            return 1;
        }

        const auto& h_j = meta.at("ising_h").arr;
        const auto& J_j = meta.at("ising_J").arr;

        static qir::cost_phases_t phases[qir::P_MAX];
        qir::real_t cos_beta[qir::P_MAX], sin_beta[qir::P_MAX];
        for (int r = 0; r < p; ++r) {
            const double gamma = param_bul(meta.at("params"), tbjson::GAMMA_UTF8(), r);
            const double beta  = param_bul(meta.at("params"), tbjson::BETA_UTF8(), r);
            for (int k = 0; k < n; ++k)
                phases[r].h[k] = tura_cevir(-gamma * h_j[k].num);
            for (int a = 0; a < n; ++a)
                for (int b = a + 1; b < n; ++b)
                    phases[r].J[a][b] = tura_cevir(-gamma * J_j[a].arr[b].num);
            cos_beta[r] = std::cos(beta);
            sin_beta[r] = std::sin(beta);
        }

        static qir::cost_scaled_t cost;
        for (int k = 0; k < n; ++k) cost.h[k] = qir::real_t(h_j[k].num);
        for (int a = 0; a < n; ++a)
            for (int b = a + 1; b < n; ++b)
                cost.J[a][b] = qir::real_t(J_j[a].arr[b].num);

#ifdef QIR_REAL_FLOAT
        const char* varyant = "float (yerel, yetkin ARM gerceklemesi)";
#else
        const char* varyant = "Q1.17 (ap_fixed_mock; her islem double'da -> ARM'da YAVAS)";
#endif
        std::printf("varyant   : %s\n", varyant);
        std::printf("n=%d  p=%d  tekrar=%d  isinma=%d\n", n, p, tekrar, isinma);

        float bd = 0.0f;
        for (int i = 0; i < isinma; ++i)
            qir_kernel(phases, cos_beta, sin_beta, cost, p, bd);

        std::vector<double> ms;
        ms.reserve(size_t(tekrar));
        for (int i = 0; i < tekrar; ++i) {
            const auto t0 = std::chrono::steady_clock::now();
            qir_kernel(phases, cos_beta, sin_beta, cost, p, bd);
            const auto t1 = std::chrono::steady_clock::now();
            ms.push_back(std::chrono::duration<double, std::milli>(t1 - t0).count());
        }

        const double p50 = yuzdelik(ms, 0.50);
        const double p25 = yuzdelik(ms, 0.25);
        const double p75 = yuzdelik(ms, 0.75);
        const double mn  = *std::min_element(ms.begin(), ms.end());
        const double mx  = *std::max_element(ms.begin(), ms.end());

        std::printf("beklenen_deger : %.9f  (dogruluk kontrolu)\n", double(bd));
        std::printf("medyan  : %10.3f ms\n", p50);
        std::printf("IQR     : %10.3f ms  (p25=%.3f  p75=%.3f)\n", p75 - p25, p25, p75);
        std::printf("min/maks: %10.3f / %.3f ms\n", mn, mx);
        std::printf("jitter  : %10.3f ms\n", mx - mn);
        std::printf("FPGA    : %10.3f ms  (sentez tahmini, p=2)\n", 37.28);
        std::printf("ORAN    : %10.2f x\n", p50 / 37.28);
        return 0;
    } catch (const std::exception& e) {
        std::fprintf(stderr, "HATA: %s\n", e.what());
        return 1;
    }
}
