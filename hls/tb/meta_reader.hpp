// Altın referansın `.json` metadata'sını okur. Sentezlenmez.
//
// Sözleşme maddesi T-2: kübit sıralama konvansiyonu metadata'dan **OKUNUR**,
// varsayılmaz (FR-009). DG-02 riski tam da varsaymaktan doğuyor.
//
// Küçük, bağımlılıksız bir JSON ayrıştırıcı içerir — harici kütüphane
// eklememek için (FR-018: standart g++ ile derlenebilmeli).
#pragma once

#include <cctype>
#include <fstream>
#include <map>
#include <sstream>
#include <stdexcept>
#include <string>
#include <vector>

namespace tbjson {

struct Value {
    enum Type { NUL, BOOL, NUM, STR, ARR, OBJ } type = NUL;
    bool b = false;
    double num = 0.0;
    std::string str;
    std::vector<Value> arr;
    std::map<std::string, Value> obj;

    const Value& at(const std::string& k) const {
        auto it = obj.find(k);
        if (it == obj.end()) throw std::runtime_error("json anahtari yok: " + k);
        return it->second;
    }
    bool has(const std::string& k) const { return obj.count(k) != 0; }
};

class Parser {
public:
    explicit Parser(const std::string& s) : s_(s) {}
    Value parse() {
        atla();
        Value v = deger();
        return v;
    }

private:
    const std::string& s_;
    size_t i_ = 0;

    void atla() {
        while (i_ < s_.size() && std::isspace(static_cast<unsigned char>(s_[i_]))) ++i_;
    }
    char bak() {
        if (i_ >= s_.size()) throw std::runtime_error("json beklenmedik son");
        return s_[i_];
    }
    void bekle(char c) {
        atla();
        if (bak() != c)
            throw std::runtime_error(std::string("json '") + c + "' bekleniyordu");
        ++i_;
    }

    Value deger() {
        atla();
        const char c = bak();
        if (c == '{') return nesne();
        if (c == '[') return dizi();
        if (c == '"') { Value v; v.type = Value::STR; v.str = metin(); return v; }
        if (c == 't' || c == 'f') {
            Value v; v.type = Value::BOOL;
            v.b = (c == 't');
            i_ += (c == 't') ? 4 : 5;
            return v;
        }
        if (c == 'n') { i_ += 4; return Value{}; }  // null
        // JSON standardında NaN/Infinity YOKTUR, ama Python'un json.dumps'ı
        // bunları yazabiliyor. Çökmek yerine "tanımsız" olarak ele alınır;
        // `HATA: stod` gibi hiçbir şey anlatmayan bir hata vermemek için.
        if (c == 'N') { i_ += 3; Value v; v.type = Value::NUL; return v; }
        if (c == 'I') { i_ += 8; Value v; v.type = Value::NUL; return v; }
        if (c == '-' && i_ + 1 < s_.size() && s_[i_ + 1] == 'I') {
            i_ += 9; Value v; v.type = Value::NUL; return v;
        }
        return sayi();
    }

    Value nesne() {
        Value v; v.type = Value::OBJ;
        bekle('{');
        atla();
        if (bak() == '}') { ++i_; return v; }
        while (true) {
            atla();
            std::string k = metin();
            bekle(':');
            v.obj[k] = deger();
            atla();
            if (bak() == ',') { ++i_; continue; }
            bekle('}');
            break;
        }
        return v;
    }

    Value dizi() {
        Value v; v.type = Value::ARR;
        bekle('[');
        atla();
        if (bak() == ']') { ++i_; return v; }
        while (true) {
            v.arr.push_back(deger());
            atla();
            if (bak() == ',') { ++i_; continue; }
            bekle(']');
            break;
        }
        return v;
    }

    /// UTF-8 bayt dizisi olarak okunur — `β[0]`, `γ[0]` gibi anahtarlar
    /// yorumlanmadan aynen taşınır (Python tarafı ensure_ascii=False yazıyor).
    std::string metin() {
        bekle('"');
        std::string out;
        while (true) {
            if (i_ >= s_.size()) throw std::runtime_error("json metin kapanmadi");
            const char c = s_[i_++];
            if (c == '"') break;
            if (c == '\\') {
                const char e = s_[i_++];
                switch (e) {
                    case 'n': out += '\n'; break;
                    case 't': out += '\t'; break;
                    case 'r': out += '\r'; break;
                    case 'b': out += '\b'; break;
                    case 'f': out += '\f'; break;
                    case 'u': {
                        // \uXXXX -> UTF-8. ensure_ascii=False ile normalde
                        // gelmez ama gelirse sessizce bozmayalim.
                        const unsigned cp =
                            std::stoul(s_.substr(i_, 4), nullptr, 16);
                        i_ += 4;
                        if (cp < 0x80) {
                            out += char(cp);
                        } else if (cp < 0x800) {
                            out += char(0xC0 | (cp >> 6));
                            out += char(0x80 | (cp & 0x3F));
                        } else {
                            out += char(0xE0 | (cp >> 12));
                            out += char(0x80 | ((cp >> 6) & 0x3F));
                            out += char(0x80 | (cp & 0x3F));
                        }
                        break;
                    }
                    default: out += e; break;
                }
            } else {
                out += c;
            }
        }
        return out;
    }

    Value sayi() {
        const size_t bas = i_;
        while (i_ < s_.size() &&
               (std::isdigit(static_cast<unsigned char>(s_[i_])) || s_[i_] == '-' ||
                s_[i_] == '+' || s_[i_] == '.' || s_[i_] == 'e' || s_[i_] == 'E'))
            ++i_;
        Value v; v.type = Value::NUM;
        v.num = std::stod(s_.substr(bas, i_ - bas));
        return v;
    }
};

inline Value dosyadan(const std::string& yol) {
    std::ifstream f(yol);
    if (!f) throw std::runtime_error("json acilamadi: " + yol);
    std::stringstream ss;
    ss << f.rdbuf();
    const std::string s = ss.str();
    return Parser(s).parse();
}

// Yunan harflerinin UTF-8 baytları — parametre adlarını tanımak için.
inline const char* GAMMA_UTF8() { return "\xCE\xB3"; }  // γ
inline const char* BETA_UTF8()  { return "\xCE\xB2"; }  // β

}  // namespace tbjson
