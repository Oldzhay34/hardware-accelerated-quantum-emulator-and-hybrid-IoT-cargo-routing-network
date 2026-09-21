// Izdusum referans degerleri — gorev T031/T033'un C-sim tarafi.
//
// 20 izdusum `cost` vektorunun her biri icin, GERCEK cekirdegi (`qir_kernel`)
// cagirip `beklenen_deger`i uretir. Kart bu degerlerle BIREBIR tutmak zorunda
// (SC-003).
//
// ⚠️ HAM VEKTOR DEGIL, KODLANMIS WORD OKUR.
// `agent/cost_vectors.py --cikti ...` her vektoru kodlayicinin KENDISIYLE
// olcekleyip 272 word olarak yaziyor. Bu arac o word'leri okuyup `real_t`'ye
// geri aciyor. Boylece:
//   * olcekleme mantigi C++ tarafinda TEKRARLANMAZ (sessiz ayrisma kaynagi),
//   * kart ve C-sim BIT BIT ayni girdiyi gorur.
//
// Derleme:
//   g++ -std=c++17 -O2 -DQIR_NO_VITIS -DQIR_N_QUBITS=16 -Ihls/src -Ihls/tb \
//       hls/tb/izdusum_ref.cpp hls/src/qir_kernel.cpp -o hls/build/izdusum_ref
#include <cmath>
#include <cstdio>
#include <cstring>
#include <fstream>
#include <string>
#include <vector>

#include "../src/qir_types.hpp"
#include "../src/gates_diagonal.hpp"
#include "../src/qir_kernel.hpp"
#include "meta_reader.hpp"

namespace {

constexpr double TAU = 6.283185307179586476925286766559;

// tb_kernel.cpp::tura_cevir ile BIREBIR ayni.
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

// Q1.17 word -> double. `agent/encoder.py::word_reale` ile ayni.
double word_reale(unsigned long w) {
    long q = static_cast<long>(w & 0x3FFFFul);
    if (q >= (1L << 17)) q -= (1L << 18);          // isaret biti
    return double(q) / double(1L << 17);
}

}  // namespace

int main(int argc, char** argv) {
    std::string ref_taban, vek_yolu, cikti_yolu;
    for (int i = 1; i < argc; ++i) {
        const std::string a = argv[i];
        if (a == "--reference" && i + 1 < argc) ref_taban = argv[++i];
        else if (a == "--vektorler" && i + 1 < argc) vek_yolu = argv[++i];
        else if (a == "--cikti" && i + 1 < argc) cikti_yolu = argv[++i];
        else { std::fprintf(stderr, "bilinmeyen argüman: %s\n", a.c_str()); return 2; }
    }
    if (ref_taban.empty() || vek_yolu.empty() || cikti_yolu.empty()) {
        std::fprintf(stderr,
            "kullanim: izdusum_ref --reference <ref_taban> "
            "--vektorler <izdusum.json> --cikti <beklenen.json>\n");
        return 2;
    }
    for (const char* uz : {".npy", ".json"}) {
        const size_t L = std::strlen(uz);
        if (ref_taban.size() > L && ref_taban.compare(ref_taban.size() - L, L, uz) == 0)
            ref_taban.resize(ref_taban.size() - L);
    }

    try {
        // --- devre: phases / beta / p  (izdusumler arasinda DEGISMEZ) ---
        const tbjson::Value meta = tbjson::dosyadan(ref_taban + ".json");
        const int n = static_cast<int>(meta.at("n_qubits").num);
        const int p = static_cast<int>(meta.at("p").num);
        if (n != qir::N_QUBITS) {
            std::fprintf(stderr, "HATA: referans %d kubit, ikili %d\n", n, qir::N_QUBITS);
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

        // --- izdusum vektorleri (kodlanmis word) ---
        const tbjson::Value vek = tbjson::dosyadan(vek_yolu);
        const auto& kodlu = vek.at("kodlu").arr;
        const int adet = static_cast<int>(kodlu.size());
        const int NW = qir::N_QUBITS * (qir::N_QUBITS + 1);   // 272
        std::printf("izdusum sayisi : %d\n", adet);
        std::printf("tohum          : %d\n", int(vek.at("tohum").num));

        std::ofstream of(cikti_yolu);
        if (!of) { std::fprintf(stderr, "HATA: cikti yazilamadi\n"); return 1; }
        of << "{\n  \"kaynak\": \"izdusum_ref.cpp (C-sim, gercek qir_kernel)\",\n";
        of << "  \"tohum\": " << int(vek.at("tohum").num) << ",\n";
        of << "  \"n_qubits\": " << n << ",\n  \"p\": " << p << ",\n";
        of << "  \"beklenen\": [";

        static qir::cost_scaled_t cost;
        for (int v = 0; v < adet; ++v) {
            const auto& w = kodlu[v].at("words").arr;
            if (static_cast<int>(w.size()) != NW) {
                std::fprintf(stderr, "HATA: izdusum %d, %d word (beklenen %d)\n",
                             v, int(w.size()), NW);
                return 1;
            }
            for (int k = 0; k < qir::N_QUBITS; ++k)
                cost.h[k] = qir::real_t(word_reale((unsigned long)w[k].num));
            for (int a = 0; a < qir::N_QUBITS; ++a)
                for (int b = 0; b < qir::N_QUBITS; ++b)
                    cost.J[a][b] = qir::real_t(
                        word_reale((unsigned long)w[qir::N_QUBITS
                                                   + qir::N_QUBITS * a + b].num));

            float bd = 0.0f;
            qir_kernel(phases, cos_beta, sin_beta, cost, p, bd);

            // Bit deseni de yazilir: kiyas float metniyle degil, BIT ile yapilir.
            unsigned int bits;
            std::memcpy(&bits, &bd, sizeof(bits));
            of << (v ? ",\n    " : "\n    ")
               << "{\"i\": " << v
               << ", \"beklenen_deger\": " << std::scientific << double(bd)
               << ", \"bits\": " << bits << "}";
            std::printf("  [%2d] %.9g   0x%08X\n", v, double(bd), bits);
        }
        of << "\n  ]\n}\n";
        std::printf("yazildi: %s\n", cikti_yolu.c_str());
        return 0;
    } catch (const std::exception& e) {
        std::fprintf(stderr, "HATA: %s\n", e.what());
        return 1;
    }
}
