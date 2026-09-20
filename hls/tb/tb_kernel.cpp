// C-simülasyon testbench'i — altın referansa karşı genlik düzeyinde doğrulama.
//
// US1 / SC-001. Kart ve Vitis HLS GEREKMEZ (Anayasa Prensip V):
//   g++ -std=c++17 -O2 -DQIR_VERIFICATION -DQIR_NO_VITIS ...
//
// Sözleşme: contracts/testbench-interface.md
#include <algorithm>
#include <cmath>
#include <complex>
#include <cstdio>
#include <cstring>
#include <ctime>
#include <fstream>
#include <iostream>
#include <string>
#include <vector>

#include "../src/qir_types.hpp"
#include "../src/gates_diagonal.hpp"
#include "../src/qir_kernel.hpp"
#include "meta_reader.hpp"
#include "npy_reader.hpp"

// qir_kernel.cpp içinde tanımlı (aynı hesaplama yolu — sözleşme maddesi T-1)
void qir_kernel_debug(const qir::cost_phases_t phases[qir::P_MAX],
                      const qir::real_t cos_beta[qir::P_MAX],
                      const qir::real_t sin_beta[qir::P_MAX],
                      int p,
                      qir::amp_t sv_out[qir::N_AMP]);

namespace {

constexpr double TAU = 6.283185307179586476925286766559;

/// Terim başına fazı TUR cinsinden `PHASE_BITS`-bit sabit noktaya indirger.
///
/// Neden konakta: E(i) ~1e4 mertebesinde; `gamma*E`'yi sabit noktada tutmak
/// ~44 bit isterdi. Terim başına mod 1'e indirgenince çekirdekteki toplama
/// taşması ZATEN mod 2*pi olur.
qir::phase_t tura_cevir(double aci_carpani) {
    double t = std::fmod(aci_carpani / TAU, 1.0);
    if (t < 0.0) t += 1.0;
    const double olcek = qir::PHASE_SCALE;
    long long q = static_cast<long long>(std::nearbyint(t * olcek));
    q %= static_cast<long long>(olcek);
    if (q < 0) q += static_cast<long long>(olcek);
    return qir::phase_t(static_cast<uint64_t>(q));
}

double fidelity(const std::vector<std::complex<double>>& a,
                const std::vector<std::complex<double>>& b) {
    double na = 0.0, nb = 0.0;
    std::complex<double> ic(0.0, 0.0);
    for (size_t i = 0; i < a.size(); ++i) {
        na += std::norm(a[i]);
        nb += std::norm(b[i]);
        ic += std::conj(a[i]) * b[i];
    }
    if (na == 0.0 || nb == 0.0) return 0.0;
    return std::norm(ic) / (na * nb);
}

/// `params` içinden r'inci katmanın gamma/beta değerini adıyla bulur.
/// Sıraya GÜVENİLMEZ — Faz 1 parametreleri adıyla kaydediyor.
double param_bul(const tbjson::Value& params, const char* onek_utf8, int r) {
    const std::string koseli = "[" + std::to_string(r) + "]";
    for (const auto& kv : params.obj) {
        if (kv.first.rfind(onek_utf8, 0) == 0 &&
            kv.first.find(koseli) != std::string::npos)
            return kv.second.num;
    }
    throw std::runtime_error(std::string("parametre bulunamadi: onek=") +
                             onek_utf8 + " r=" + std::to_string(r));
}

std::string bugun() {
    std::time_t t = std::time(nullptr);
    char buf[16];
    std::strftime(buf, sizeof(buf), "%Y%m%d", std::localtime(&t));
    return buf;
}

}  // namespace

int main(int argc, char** argv) {
    std::string ref_taban;
    std::string git_hash = "unknown";
    std::string cikti_dizin = "docs/measurements";
    std::string dump_yolu;
    std::string words_yolu;   // --dump-words: G2 kapisi (gorev T025)
    int beklenen_n = qir::N_QUBITS;

    for (int i = 1; i < argc; ++i) {
        const std::string a = argv[i];
        if (a == "--reference" && i + 1 < argc) ref_taban = argv[++i];
        else if (a == "--git-hash" && i + 1 < argc) git_hash = argv[++i];
        else if (a == "--out-dir" && i + 1 < argc) cikti_dizin = argv[++i];
        else if (a == "--n" && i + 1 < argc) beklenen_n = std::stoi(argv[++i]);
        else if (a == "--dump" && i + 1 < argc) dump_yolu = argv[++i];
        else if (a == "--dump-words" && i + 1 < argc) words_yolu = argv[++i];
        else { std::cerr << "bilinmeyen argüman: " << a << "\n"; return 2; }
    }
    if (ref_taban.empty()) {
        std::cerr << "kullanim: tb_kernel --reference <yol/reference_..._pN_n5> "
                     "[--n 16] [--git-hash h] [--out-dir d] [--dump-words w.json]\n";
        return 2;
    }
    // ".npy"/".json" uzantısı verilmişse at
    for (const char* uz : {".npy", ".json"}) {
        const size_t L = std::strlen(uz);
        if (ref_taban.size() > L && ref_taban.compare(ref_taban.size() - L, L, uz) == 0)
            ref_taban.resize(ref_taban.size() - L);
    }

    try {
        const tbjson::Value meta = tbjson::dosyadan(ref_taban + ".json");
        const auto ref = tbnpy::load_complex128(ref_taban + ".npy");

        const int n = static_cast<int>(meta.at("n_qubits").num);
        const int p = static_cast<int>(meta.at("p").num);
        const std::string kubit_sirasi = meta.at("qubit_order").str;

        // --- Ön koşullar AÇIKÇA denetlenir; sessizce yanlış devre koşulmaz ---
        if (beklenen_n != qir::N_QUBITS) {
            std::cerr << "HATA: --n " << beklenen_n << " verildi ama ikili "
                      << qir::N_QUBITS << " kubit icin derlenmis.\n"
                      << "      Kubit sayisi DERLEME ZAMANI parametresidir (FR-003):\n"
                      << "      g++ ... -DQIR_N_QUBITS=" << beklenen_n << " ...\n";
            return 1;
        }
        if (n != qir::N_QUBITS) {
            std::cerr << "HATA: referans " << n << " kubit, ikili "
                      << qir::N_QUBITS << " kubit icin derlenmis.\n";
            return 1;
        }
        if (static_cast<int>(ref.size()) != qir::N_AMP) {
            std::cerr << "HATA: referans " << ref.size() << " genlik, beklenen "
                      << qir::N_AMP << ".\n";
            return 1;
        }
        // Sözleşme maddesi T-2 / FR-009: konvansiyon OKUNUR, varsayilmaz.
        if (kubit_sirasi != "little") {
            std::cerr << "HATA: qubit_order='" << kubit_sirasi
                      << "'. Cekirdek little-endian varsayar (bit k <-> kubit k).\n"
                      << "      Donusum UYGULANMADAN kiyas yapilamaz (DG-02).\n";
            return 1;
        }
        if (!meta.has("params") || meta.at("params").obj.empty()) {
            std::cerr << "HATA: referansta 'params' yok. Faz 2 oncesi uretilmis "
                         "bir dosya olabilir.\n"
                      << "      Bu dosyayla ayni devre KOSULAMAZ — referansi "
                         "yeniden uretin.\n";
            return 1;
        }
        if (p < 1 || p > qir::P_MAX) {
            std::cerr << "HATA: p=" << p << ", desteklenen 1.." << qir::P_MAX << "\n";
            return 1;
        }

        // --- Faz sabitlerini ve karıştırıcı açılarını hazırla ---
        const auto& h_j = meta.at("ising_h").arr;
        const auto& J_j = meta.at("ising_J").arr;
        if (static_cast<int>(h_j.size()) != n)
            throw std::runtime_error("ising_h uzunlugu n ile uyusmuyor");

        static qir::cost_phases_t phases[qir::P_MAX];
        qir::real_t cos_beta[qir::P_MAX], sin_beta[qir::P_MAX];

        for (int r = 0; r < p; ++r) {
            const double gamma = param_bul(meta.at("params"), tbjson::GAMMA_UTF8(), r);
            const double beta = param_bul(meta.at("params"), tbjson::BETA_UTF8(), r);
            for (int k = 0; k < n; ++k)
                phases[r].h[k] = tura_cevir(-gamma * h_j[k].num);
            for (int a = 0; a < n; ++a)
                for (int b = a + 1; b < n; ++b)
                    phases[r].J[a][b] = tura_cevir(-gamma * J_j[a].arr[b].num);
            // exp(-i*beta*X) = RX(2*beta) -> cos(2*beta/2) = cos(beta)
            cos_beta[r] = std::cos(beta);
            sin_beta[r] = std::sin(beta);
        }

        // --- Çekirdeği koş ---
        static qir::amp_t sv[qir::N_AMP];
        qir_kernel_debug(phases, cos_beta, sin_beta, p, sv);

        // --- SENTEZLENEN ust fonksiyon da cagrilir (COSIM icin ZORUNLU) ---
        //
        // Dogrulama `qir_kernel_debug` uzerinden yapilir cunku statevector'u
        // disari veren yalnizca odur; ama o SENTEZLENMEZ (`add_files -tb`).
        // cosim, sentezlenen ust fonksiyon testbench'te cagrilmazsa RTL'i hic
        // kosturmaz:
        //   ERROR: [COSIM 212-330] top function 'qir_kernel' is not invoked
        //                          in the test bench
        // Ikisi de `qir::run_circuit`'i cagirir (sozlesme maddesi T-1), yani
        // ayni devredir; bu cagri fazladan bir dogrulama degil, cosim'in
        // calisabilmesi icin gereken kancadir.
        static qir::cost_scaled_t cost;
        for (int k = 0; k < n; ++k)
            cost.h[k] = qir::real_t(h_j[k].num);
        for (int a = 0; a < n; ++a)
            for (int b = a + 1; b < n; ++b)
                cost.J[a][b] = qir::real_t(J_j[a].arr[b].num);

        // --- G2 kapisi: paketlenmis word'leri dok (gorev T025) ---
        //
        // Konak kodlayicisi (agent/encoder.py) bu ciktiya karsi BIT BIT
        // dogrulanir. Hesabi DEGISTIRMEZ; yalniz yukarida uretilmis olani
        // yazar. Bayrak verilmezse hicbir sey yapmaz.
        //
        // ⚠️ Tip ICI erisim kullanilmaz (mock'ta .v/.raw, Vitis'te range()):
        // bu dosya hem QIR_NO_VITIS taklidiyle hem gercek Vitis tipleriyle
        // derleniyor, arayuzleri ayni degil. Sayisal degerden geri hesaplamak
        // iki tarafta da ayni sonucu verir.
        if (!words_yolu.empty()) {
            std::ofstream wf(words_yolu);
            if (!wf) {
                std::cerr << "UYARI: --dump-words yazilamadi: " << words_yolu << "\n";
            } else {
                auto fw = [](qir::phase_t x) -> unsigned long {
                    return static_cast<unsigned long>(
                               static_cast<unsigned long long>(x)) & 0x3FFFFul;
                };
                auto rw = [](qir::real_t x) -> unsigned long {
                    // double(x) tam olarak raw/2^17'dir; yuvarlama kipi onemsiz.
                    const long long q = std::llround(double(x) * 131072.0);
                    return static_cast<unsigned long>(q) & 0x3FFFFul;
                };
                const int NW = qir::N_QUBITS * (qir::N_QUBITS + 1);   // 272
                wf << "{\n  \"p\": " << p << ",\n  \"n_qubits\": " << n << ",\n";
                wf << "  \"phases\": [";
                for (int r = 0; r < qir::P_MAX; ++r)
                    for (int k = 0; k < NW; ++k) {
                        unsigned long v = 0;
                        if (r < p) {
                            if (k < qir::N_QUBITS) {
                                v = fw(phases[r].h[k]);
                            } else {
                                const int t = k - qir::N_QUBITS;
                                v = fw(phases[r].J[t / qir::N_QUBITS][t % qir::N_QUBITS]);
                            }
                        }
                        if (r || k) wf << ",";
                        wf << v;
                    }
                wf << "],\n  \"cost\": [";
                for (int k = 0; k < NW; ++k) {
                    const int t = k - qir::N_QUBITS;
                    const qir::real_t rv = (k < qir::N_QUBITS)
                        ? cost.h[k]
                        : cost.J[t / qir::N_QUBITS][t % qir::N_QUBITS];
                    if (k) wf << ",";
                    wf << rw(rv);
                }
                wf << "],\n  \"cos_beta\": [";
                for (int r = 0; r < qir::P_MAX; ++r)
                    wf << (r ? "," : "") << rw(cos_beta[r]);
                wf << "],\n  \"sin_beta\": [";
                for (int r = 0; r < qir::P_MAX; ++r)
                    wf << (r ? "," : "") << rw(sin_beta[r]);
                wf << "]\n}\n";
                std::printf("Words           : %s\n", words_yolu.c_str());
            }
        }

        float beklenen_deger = 0.0f;
        qir_kernel(phases, cos_beta, sin_beta, cost, p, beklenen_deger);

        std::vector<std::complex<double>> cikti(qir::N_AMP);
        for (int i = 0; i < qir::N_AMP; ++i)
            cikti[i] = {double(sv[i].re), double(sv[i].im)};

        // --dump: çekirdeğin ham çıktısını .npy olarak yazar. Python ikizi
        // (scripts/compare_amplitudes.py) buna karşı BİT DÜZEYİNDE kıyas yapar;
        // fidelity tek başına ince hataları gizleyebilir.
        if (!dump_yolu.empty()) {
            std::ofstream d(dump_yolu, std::ios::binary);
            if (!d) {
                std::cerr << "UYARI: dump yazilamadi: " << dump_yolu << "\n";
            } else {
                std::string basluk = "{'descr': '<c16', 'fortran_order': False, "
                                     "'shape': (" + std::to_string(qir::N_AMP) + ",), }";
                // Başlık, 16 baytın katına kadar boşlukla doldurulup \n ile biter
                size_t toplam = 10 + basluk.size() + 1;
                while (toplam % 16) { basluk += ' '; ++toplam; }
                basluk += '\n';
                const uint16_t hlen = static_cast<uint16_t>(basluk.size());
                d.write("\x93NUMPY", 6);
                const char sur[2] = {1, 0};
                d.write(sur, 2);
                d.write(reinterpret_cast<const char*>(&hlen), 2);
                d.write(basluk.data(), static_cast<std::streamsize>(basluk.size()));
                d.write(reinterpret_cast<const char*>(cikti.data()),
                        static_cast<std::streamsize>(cikti.size() * sizeof(std::complex<double>)));
                std::printf("Dump            : %s\n", dump_yolu.c_str());
            }
        }

        // --- Ölçütler ---
        const double f = fidelity(ref, cikti);

        // DG-02 ayırt etme: büyüklükler doğru ama fidelity ~0 ise sorun
        // sayısal değil, kübit SIRALAMASIDIR (sözleşme maddesi T-6).
        double n_ref = 0.0, n_out = 0.0;
        for (int i = 0; i < qir::N_AMP; ++i) { n_ref += std::norm(ref[i]); n_out += std::norm(cikti[i]); }
        n_ref = std::sqrt(n_ref); n_out = std::sqrt(n_out);
        double buyukluk_sapmasi = 0.0;
        for (int i = 0; i < qir::N_AMP; ++i)
            buyukluk_sapmasi = std::max(
                buyukluk_sapmasi,
                std::abs(std::abs(ref[i]) / n_ref - std::abs(cikti[i]) / n_out));

        const bool gecti_M = f >= 0.99;
        const bool gecti_H = f >= 0.999;
        const char* teshis =
            (f < 0.5 && buyukluk_sapmasi < 1e-3)
                ? "DG-02 SUPHESI: buyuklukler dogru, fidelity dusuk -> kubit sirasi ters"
                : (gecti_H ? "gecti (H)" : (gecti_M ? "gecti (yalnizca M)" : "KALDI"));

        std::printf("Referans        : %s\n", ref_taban.c_str());
        std::printf("Kubit / p       : %d / %d   (sira: %s)\n", n, p, kubit_sirasi.c_str());
        std::printf("Format          : Q1.17 (ap_fixed<18,1,AP_RND_CONV,AP_SAT>)\n");
        std::printf("Fidelity        : %.9f\n", f);
        std::printf("Buyukluk sapmasi: %.3e\n", buyukluk_sapmasi);
        std::printf("M (>=0,99)      : %s\n", gecti_M ? "GECTI" : "KALDI");
        std::printf("H (>=0,999)     : %s\n", gecti_H ? "GECTI" : "KALDI");
        std::printf("Teshis          : %s\n", teshis);
        std::printf("Beklenen deger  : %.9f  (qir_kernel, sentezlenen ust)\n",
                    beklenen_deger);

        // --- Damgalı çıktı (VR-03): tarih + git hash + konfig ---
        const std::string ad = cikti_dizin + "/csim-fidelity_" + bugun() + "_" +
                               git_hash + "_n" + std::to_string(n) + "_p" +
                               std::to_string(p) + ".json";
        std::ofstream o(ad);
        if (!o) {
            std::cerr << "UYARI: cikti yazilamadi: " << ad << "\n";
        } else {
            o.precision(17);
            o << "{\n"
              << "  \"stamped_date\": \"" << bugun() << "\",\n"
              << "  \"git_hash\": \"" << git_hash << "\",\n"
              << "  \"fidelity\": " << f << ",\n"
              << "  \"buyukluk_sapmasi\": " << buyukluk_sapmasi << ",\n"
              << "  \"referans_dosya\": \"" << ref_taban << ".npy\",\n"
              << "  \"kubit_konvansiyonu\": \"" << kubit_sirasi << "\",\n"
              << "  \"n_qubits\": " << n << ",\n"
              << "  \"p\": " << p << ",\n"
              << "  \"format\": \"Q1.17\",\n"
              << "  \"phase_bits\": " << qir::PHASE_BITS << ",\n"
              << "  \"banks\": " << qir::BANKS << ",\n"
              << "  \"gecti_M\": " << (gecti_M ? "true" : "false") << ",\n"
              << "  \"gecti_H\": " << (gecti_H ? "true" : "false") << ",\n"
              << "  \"teshis\": \"" << teshis << "\"\n"
              << "}\n";
            std::printf("Yazildi         : %s\n", ad.c_str());
        }

        return gecti_M ? 0 : 1;
    } catch (const std::exception& e) {
        std::cerr << "HATA: " << e.what() << "\n";
        return 1;
    }
}
