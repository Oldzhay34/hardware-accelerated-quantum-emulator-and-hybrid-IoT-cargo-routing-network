// Doğrulama yüzeyi (FR-016) — contracts/testbench-interface.md
//
// ⚠️ BU DOSYA SENTEZLENMEZ. Tcl akışına `add_files -tb` ile eklenir; sentez
// yolu onu hiç görmez. Sentezlenecek olsaydı `sv_out` bir m_axi portu doğurur
// ve sözleşme maddesi K-1'i (statevector DDR'a taşamaz) ihlal ederdi.
//
// Sözleşme maddesi T-1: `qir_kernel` ile AYNI hesaplama yolunu kullanır —
// ikisi de `qir::run_circuit`'i çağırır. Ayrı bir uygulama olsaydı doğrulama
// hiçbir şey kanıtlamazdı.
#include "../src/qir_kernel.hpp"

void qir_kernel_debug(const qir::cost_phases_t phases[qir::P_MAX],
                      const qir::real_t cos_beta[qir::P_MAX],
                      const qir::real_t sin_beta[qir::P_MAX],
                      int p,
                      qir::amp_t sv_out[qir::N_AMP]) {
    qir::run_circuit(sv_out, phases, cos_beta, sin_beta, p);
}
