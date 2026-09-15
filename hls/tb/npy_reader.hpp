// Bağımlılıksız NumPy `.npy` okuyucu (complex128, C-sırası).
//
// Faz 1'in `docs/measurements/reference_*.npy` altın referansını okur.
// Sentezlenmez — yalnızca testbench tarafı.
#pragma once

#include <complex>
#include <cstdint>
#include <cstring>
#include <fstream>
#include <stdexcept>
#include <string>
#include <vector>

namespace tbnpy {

/// complex128 bir .npy dosyasını okur. Şekil (N,) olmak zorundadır.
inline std::vector<std::complex<double>> load_complex128(const std::string& yol) {
    std::ifstream f(yol, std::ios::binary);
    if (!f) throw std::runtime_error("npy acilamadi: " + yol);

    char sihir[6];
    f.read(sihir, 6);
    if (std::memcmp(sihir, "\x93NUMPY", 6) != 0)
        throw std::runtime_error("npy sihirli sayisi yanlis: " + yol);

    uint8_t majör = 0, minör = 0;
    f.read(reinterpret_cast<char*>(&majör), 1);
    f.read(reinterpret_cast<char*>(&minör), 1);

    uint32_t basluk_uzunlugu = 0;
    if (majör == 1) {
        uint16_t u = 0;
        f.read(reinterpret_cast<char*>(&u), 2);
        basluk_uzunlugu = u;
    } else {
        f.read(reinterpret_cast<char*>(&basluk_uzunlugu), 4);
    }

    std::string basluk(basluk_uzunlugu, '\0');
    f.read(&basluk[0], basluk_uzunlugu);

    // Tip DOĞRULANIR, varsayılmaz: yanlış dtype sessizce çöp genlik verirdi.
    if (basluk.find("'<c16'") == std::string::npos &&
        basluk.find("\"<c16\"") == std::string::npos)
        throw std::runtime_error("npy dtype complex128 (<c16) degil: " + basluk);
    if (basluk.find("'fortran_order': True") != std::string::npos)
        throw std::runtime_error("npy fortran_order=True destegi yok: " + yol);

    const size_t sp = basluk.find("'shape':");
    if (sp == std::string::npos) throw std::runtime_error("npy shape yok: " + basluk);
    const size_t ap = basluk.find('(', sp);
    const size_t kp = basluk.find(')', ap);
    std::string sekil = basluk.substr(ap + 1, kp - ap - 1);
    if (sekil.find(',') != sekil.rfind(','))  // birden fazla virgul -> cok boyutlu
        throw std::runtime_error("npy yalnizca 1 boyutlu destekleniyor: " + sekil);
    const size_t n = static_cast<size_t>(std::stoull(sekil));

    std::vector<std::complex<double>> v(n);
    f.read(reinterpret_cast<char*>(v.data()),
           static_cast<std::streamsize>(n * sizeof(std::complex<double>)));
    if (!f) throw std::runtime_error("npy veri okumasi eksik: " + yol);
    return v;
}

}  // namespace tbnpy
