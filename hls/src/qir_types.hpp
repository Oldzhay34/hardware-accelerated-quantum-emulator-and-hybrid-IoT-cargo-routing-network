// Çekirdek tipleri ve derleme zamanı sabitleri.
//
// Onaylanan mimari: ADR 0008 — A1 (naif cyclic F=16 + yerinde) + B4 (Q1.17)
// + C1 (QAOA'ya özel). Buradaki her genişlik ÖLÇÜMLE seçilmiştir; hiçbiri
// tahmin değildir (Anayasa Prensip II).
#pragma once

#ifdef QIR_NO_VITIS
#include "../tb/ap_fixed_mock.hpp"
#else
#include <ap_fixed.h>
#include <ap_int.h>
#endif

namespace qir {

// Kübit sayısı derleme zamanı parametresidir (FR-003). n=8/12/16 ile ayrı ayrı
// koşulur (SC-001) — `-DQIR_N_QUBITS=12` ile değiştirilir.
#ifndef QIR_N_QUBITS
#define QIR_N_QUBITS 16
#endif

constexpr int N_QUBITS = QIR_N_QUBITS;
constexpr int N_AMP    = 1 << N_QUBITS;
constexpr int N_PAIR   = N_AMP / 2;

// Bankalama: cyclic partition faktörü. 65536/16 = 4096 = 4 x 1024, tam bölünüyor
// — tek BRAM bloğu bile israf olmuyor. Parçalanma uçurumu F > 64'te başlar.
constexpr int BANKS = 16;
// Yerinde güncellemede çift başına DÖRT erişim gerekir (oku i, oku i', yaz i,
// yaz i'), dolayısıyla tavan BANKS*port/4 = 8 çift/çevrim.
constexpr int LANES = BANKS * 2 / 4;

constexpr int P_MAX = 3;

static_assert(N_QUBITS >= 2 && N_QUBITS <= 16,
              "Anayasa Prensip III: ust sinir 16 kubit");
static_assert(N_QUBITS % 2 == 0,
              "n cift olmali ki 2^(-n/2) ikinin kuvveti olsun ve baslangic "
              "durumu Q1.17'de TAM temsil edilsin");

// --- Sayı formatı: Q1.17 (ADR 0008 / plan.md Tablo B) -----------------------
// Üç bağımsız kısıt tam burada buluşuyor:
//   fidelity H eşiği  -> EN AZ Q1.17 (Q1.15 = 0,998674, kalıyor)
//   BRAM 36-bit kelime -> EN ÇOK Q1.17 (Q1.19 iki kelime ister)
//   DSP48E1 18-bit B portu -> EN ÇOK Q1.17 (Q1.19 = 20 bit, tek DSP'ye sığmaz)
//
// Kipler Vitis VARSAYILANI DEĞİLDİR ve bu bilinçlidir
// (docs/measurements/apfixed-kip_*.json):
//   AP_RND_CONV: AP_TRN 0,999607 verirken bu 0,999917 veriyor — hata ~5x az.
//   AP_SAT:      AP_WRAP 1,0 genliğini -1,0'a sarar. Bu devrede ölçüm fark
//                göstermedi, çünkü emülasyon başlangıç durumunu kuantalamıyor;
//                donanım ise onu belleğe YAZAR. Sarmanın hata kipi sessiz ve
//                ölümcül, doyurmanınki 7,6e-6'lık bir sapma.
// ⚙️ QIR_REAL_FLOAT — YALNIZCA PS↔PL taban ölçümü için (görev T045b).
// ARM'da adil bir taban gerekiyor: `ap_fixed_mock` her işlemi double'da yapıp
// kuantalar ve Cortex-A9'un NEON'u çift duyarlık DESTEKLEMEZ. O kodu ARM'da
// ölçmek, "yazılım FPU'sunda fixed-point emülasyonu"nu ölçmek olur ve
// hızlanmayı 10-50 kat ŞİŞİRİR. Bu bayrak, aynı algoritmayı yerel float ile
// derler — yetkin bir ARM gerçeklemesinin yapacağı şey.
// ⛔ SENTEZDE KULLANILMAZ. Donanım yolu her zaman Q1.17'dir.
#ifdef QIR_REAL_FLOAT
using real_t = float;
#else
using real_t = ap_fixed<18, 1, AP_RND_CONV, AP_SAT>;
#endif

// Ara sonuç: iki Q1.17 değerinin çarpımı Q2.34'tür; RX'te iki çarpım toplanır,
// büyüklük 2'yi aşmaz -> 2 tam sayı biti yeter.
#ifdef QIR_REAL_FLOAT
using acc_t = float;
#else
using acc_t = ap_fixed<36, 2, AP_RND_CONV, AP_SAT>;
#endif

// --- Faz temsili: TUR (turn) cinsinden ---------------------------------------
// E(i) bu problemde ~1e4 mertebesinde (ceza katsayısı). gamma*E'yi doğrudan
// sabit noktada tutmak ~44 bitlik akümülatör isterdi. Bunun yerine faz TUR
// cinsinden (0..1 = 0..2*pi) tutulur; terim başına fazlar konakta mod 1'e
// indirgenir ve çekirdek onları toplarken TAŞMA zaten mod 2*pi demektir.
// Yani burada sarma hata değil, istenen davranıştır.
//
// 18 bit ölçümle seçildi (docs/measurements/faz-bit-genisligi_*.json):
//   12 bit -> 0,999950   16 bit -> 0,9999999   18 bit -> 0,999999995
// Faz darboğaz değil; genlik kuantalaması (0,999917) baskın hata kaynağı.
constexpr int PHASE_BITS = 18;
constexpr double PHASE_SCALE = double(1 << PHASE_BITS);
using phase_t = ap_uint<PHASE_BITS>;

// Başlangıç genliği: 2^(-n/2). n çift olduğu için ikinin kuvveti, yani Q1.17'de
// TAM temsil edilir. H katmanı uygulanmaz — hem gereksiz hem de bu sayede
// |0...0>'ın 1,0 genliği hiç belleğe yazılmaz (Q1.17 aralığı [-1, 1)).
constexpr double UNIFORM_AMP = 1.0 / double(1 << (N_QUBITS / 2));

struct amp_t {
    real_t re;
    real_t im;
};

}  // namespace qir
