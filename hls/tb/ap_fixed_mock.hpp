// Vitis HLS'in ap_fixed / ap_uint tiplerinin standart C++ taklidi.
//
// NEDEN VAR: Anayasa Prensip V ve FR-018 — kart VE Vitis HLS olmadan da
// çekirdek derlenip doğrulanabilmeli. Vitis kurulu değilken (`-DQIR_NO_VITIS`)
// bu başlık devreye girer ve `g++` ile derleme mümkün olur.
//
// ⚠️ TEHLİKE: Bu mock gerçek `ap_fixed`'den SESSİZCE farklı davranırsa bütün
// C-sim doğrulaması yanıltıcı olur — fidelity "geçti" der ama donanım başka
// sonuç üretir. Bu yüzden T040 mock'u gerçek `ap_fixed`'e karşı ayrıca
// doğrular; o doğrulama yapılana kadar C-sim sonuçları KOŞULLUDUR.
//
// Tasarım: aritmetik `operator double()` üzerinden çift duyarlıkta yapılır ve
// kuantalama YALNIZCA atamada uygulanır — gerçek `ap_fixed`'in semantiği de
// budur. İki 18-bit değerin çarpımı 36 bittir ve double'ın 53-bit mantisine
// TAM sığar, dolayısıyla ara sonuçlar bit-birebir aynıdır.
#pragma once

#include <cmath>
#include <cstdint>

enum ap_q_mode {
    AP_RND, AP_RND_ZERO, AP_RND_MIN_INF, AP_RND_INF, AP_RND_CONV, AP_TRN, AP_TRN_ZERO
};
enum ap_o_mode { AP_SAT, AP_SAT_ZERO, AP_SAT_SYM, AP_WRAP, AP_WRAP_SM };

template <int W, int I, ap_q_mode Q = AP_TRN, ap_o_mode O = AP_WRAP>
class ap_fixed {
public:
    static constexpr int     F     = W - I;                        // kesir biti
    static constexpr double  SCALE = double(int64_t(1) << F);
    static constexpr int64_t MAXR  = (int64_t(1) << (W - 1)) - 1;
    static constexpr int64_t MINR  = -(int64_t(1) << (W - 1));

    int64_t raw;

    ap_fixed() : raw(0) {}
    ap_fixed(double v) : raw(kuantize(v)) {}
    ap_fixed(int v) : raw(kuantize(double(v))) {}

    operator double() const { return double(raw) / SCALE; }
    ap_fixed& operator=(double v) { raw = kuantize(v); return *this; }

    // Bileşik atamalar. Gerçek `ap_fixed`'de bunlar sabit noktada yapılır ve
    // sonuç hedef tipe kuantalanır; burada çift duyarlıkta yapılıp aynı şekilde
    // kuantalanır. Operand ap_fixed ise `operator double()` ile dönüşür.
    ap_fixed& operator+=(double v) { raw = kuantize(double(*this) + v); return *this; }
    ap_fixed& operator-=(double v) { raw = kuantize(double(*this) - v); return *this; }
    ap_fixed& operator*=(double v) { raw = kuantize(double(*this) * v); return *this; }
    ap_fixed& operator/=(double v) { raw = kuantize(double(*this) / v); return *this; }

    // Vitis varsayılanları AP_TRN + AP_WRAP'tir. Bu projede ikisi de
    // KULLANILMIYOR — ölçümle elendiler (docs/measurements/apfixed-kip_*.json):
    //   AP_TRN  -> fidelity 0,999607 (AP_RND_CONV 0,999917; hata ~5x)
    //   AP_WRAP -> 1,0 genliği -1,0'a sarar; sessiz ve ölümcül
    // Yine de ikisi de burada uygulanmıştır ki o ölçüm tekrarlanabilsin.
    static int64_t kuantize(double v) {
        const double s = v * SCALE;
        int64_t q;
        switch (Q) {
            case AP_TRN:      q = int64_t(std::floor(s));       break;
            case AP_RND:      q = int64_t(std::floor(s + 0.5)); break;
            // AP_RND_CONV = yakına yuvarlama, yarım ise çifte.
            // std::nearbyint varsayılan kipte (FE_TONEAREST) tam olarak budur
            // ve numpy'nin np.round'u ile aynıdır — ölçümle uyum böyle sağlanır.
            case AP_RND_CONV: q = int64_t(std::nearbyint(s));   break;
            default:          q = int64_t(std::nearbyint(s));   break;
        }
        if (O == AP_SAT) {
            if (q > MAXR) q = MAXR;
            if (q < MINR) q = MINR;
        } else {  // AP_WRAP — iki'ye tümleyen sarma
            const int64_t M = int64_t(1) << W;
            q = ((q % M) + M) % M;
            if (q > MAXR) q -= M;
        }
        return q;
    }
};

// W-bitlik işaretsiz tamsayı. Toplamada taşma DOĞAL olarak mod 2^W verir —
// faz akümülatörü için istenen davranış tam olarak budur (mod 2*pi).
template <int W>
class ap_uint {
public:
    static constexpr uint64_t MASK = (W >= 64) ? ~uint64_t(0) : ((uint64_t(1) << W) - 1);
    uint64_t v;

    ap_uint() : v(0) {}
    ap_uint(uint64_t x) : v(x & MASK) {}
    operator uint64_t() const { return v; }
    ap_uint& operator+=(uint64_t x) { v = (v + x) & MASK; return *this; }
    ap_uint& operator-=(uint64_t x) { v = (v - x) & MASK; return *this; }
};
