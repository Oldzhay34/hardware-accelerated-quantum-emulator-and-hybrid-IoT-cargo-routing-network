// Çekirdeğin iç arayüzü — sentezlenen taraf ile testbench tarafı arasındaki sınır.
//
// Bu başlık, `run_circuit`'i testbench'in de çağırabilmesi için dışarı açar.
// Doğrulama yüzeyi (`qir_kernel_debug`) ARTIK BU DOSYADA DEĞİL: `hls/tb/` altına
// taşındı ve Tcl akışına `add_files -tb` ile ekleniyor. Böylece sentez yolunda
// hiç derlenmiyor — `#ifdef` disiplinine güvenmek yerine dosya ayrımıyla
// garanti altına alındı (sözleşme maddesi K-1).
#pragma once

#include "qir_types.hpp"
#include "statevector.hpp"
#include "gates_diagonal.hpp"
#include "gates_pairing.hpp"

namespace qir {

/// Beklenen değer akümülatörü. Terimler ~1,5e-5 mertebesinde ve 65536 tanesi
/// toplanıyor; 40 kesir biti çözünürlüğü 9e-13, birikimli hata ~3e-8.
#ifdef QIR_REAL_FLOAT
using sum_t = double;   // float32 65536 terim toplamakta yetersiz kalır
#else
using sum_t = ap_fixed<48, 8, AP_RND_CONV, AP_SAT>;
#endif

/// Ölçeklenmiş Ising katsayıları — beklenen değer yolu için.
///
/// ⚠️ Konak tarafı h ve J'yi `[-1, 1)` aralığına ÖLÇEKLEMEK ZORUNDADIR. Ham
/// hâlleriyle bu problemde ~1e4 mertebesindedirler ve `ap_fixed` doyurması
/// onları SESSİZCE kırpar. Ölçek çarpanı döndürülen skalere geri uygulanır.
struct cost_scaled_t {
    real_t h[N_QUBITS];
    real_t J[N_QUBITS][N_QUBITS];  // yalnızca a < b kullanılır
};

/// Devrenin tamamı: düzgün süperpozisyon -> p kez (maliyet, karıştırıcı).
///
/// ⚠️ Bilinçli olarak `inline` ve BAŞLIKTA. Vitis HLS 2025.2'nin `csim_design`
/// akışı yalnızca testbench dosyalarını derleyip bağlıyor (`csim.mk` içindeki
/// `HLS_SOURCES` tasarım dosyasını içermiyor), dolayısıyla tasarım tarafındaki
/// bir tanıma testbench'ten ERİŞİLEMİYOR — `undefined symbol: qir::run_circuit`.
/// Başlığa alınınca her iki çeviri birimi kendi kopyasını üretir ve çapraz
/// bağlamaya gerek kalmaz. Sözleşme maddesi T-1 korunur: dağıtım arayüzü ile
/// doğrulama yüzeyi hâlâ AYNI kodu çağırır.
inline void run_circuit(amp_t sv[N_AMP],
                        const cost_phases_t phases[P_MAX],
                        const real_t cos_beta[P_MAX],
                        const real_t sin_beta[P_MAX],
                        int p) {
    init_uniform(sv);
layer_loop:
    for (int r = 0; r < P_MAX; ++r) {
        if (r >= p) break;  // p çalışma zamanı, P_MAX derleme zamanı (madde K-2)
        apply_cost_layer(sv, phases[r]);
        apply_mixer_layer(sv, cos_beta[r], sin_beta[r]);
    }
}

/// <psi|H_C|psi>, ölçeklenmiş birimde. Offset DAHİL DEĞİL.
float expectation_scaled(const amp_t sv[N_AMP], const cost_scaled_t& cs);

}  // namespace qir

/// Dağıtım arayüzü (FR-015) — contracts/kernel-interface.md
void qir_kernel(const qir::cost_phases_t phases[qir::P_MAX],
                const qir::real_t cos_beta[qir::P_MAX],
                const qir::real_t sin_beta[qir::P_MAX],
                const qir::cost_scaled_t& cost,
                int p,
                float& beklenen_deger);

