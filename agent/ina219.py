"""INA219 sürücüsü, örnekleyici ve saf güç hesapları — görevler T048–T049.

# PYTHON 3.6 UYUMU ZORUNLU — sürücü KARTTA koşar (PYNQ 2.5 / Python 3.6.5).
# Saf fonksiyonlar (dönüşüm, pencere ortalaması) konakta da test edilir.

Kartta `smbus` yok; I2C doğrudan `/dev/i2c-0` üzerinden konuşulur (ioctl
I2C_SLAVE + read/write) — ek paket gerekmez. EMIO I2C0 yalnız **özel
bitstream YÜKLÜYKEN** vardır (T047): önce `Kart(...).yukle()`.

Ölçüm zinciri (kart-enerji-protokolu §3):
    akım = şönt gerilimi (yazmaç 0x01, işaretli, LSB 10 µV) / R_şönt
    güç  = bara gerilimi (yazmaç 0x02, bit 15..3, LSB 4 mV) × akım
INA219'un kendi kalibrasyon/akım/güç yazmaçları KULLANILMAZ: hesap ham
yazmaçlardan, burada, açıkça yapılır — tek yerde ve test edilebilir.
"""
# PYTHON 3.6 UYUMU ZORUNLU (yukarı bakın)
import math
import os
import time

ADRES = 0x40
I2C_YOLU = "/dev/i2c-0"
I2C_SLAVE = 0x0703              # linux/i2c-dev.h
R_SONT_OHM = 0.1                # HW-831B modülü: R100 (nominal; T048 sınar)

YAZMAC_YAPILANDIRMA = 0x00
YAZMAC_SONT = 0x01
YAZMAC_BARA = 0x02
ACILIS_DEGERI = 0x399F          # T047'de okundu (veri sayfasıyla aynı)

# --- yapılandırma (protokol §3) -------------------------------------------
BRNG_16V = 0                    # bara aralığı 16 V (12 V hat için yeterli)
PGA_4 = 2                       # ±160 mV → 0,1 Ω'da ±1,6 A
ADC_128 = 0xF                   # 12 bit, 128 örnek ortalama (68,10 ms)
MOD_SUREKLI = 7                 # sürekli şönt + bara
PGA_TAM_OLCEK_UV = {0: 40000.0, 1: 80000.0, 2: 160000.0, 3: 320000.0}


def yapilandirma_kelimesi(brng=BRNG_16V, pga=PGA_4, badc=ADC_128, sadc=ADC_128,
                          mod=MOD_SUREKLI):
    """Veri sayfası Tablo 3: BRNG bit 13, PG 12–11, BADC 10–7, SADC 6–3, MODE 2–0."""
    return (brng << 13) | (pga << 11) | (badc << 7) | (sadc << 3) | mod


YAPILANDIRMA = yapilandirma_kelimesi()          # 0x17FF


# =========================================================================
# Saf dönüşümler — kart gerekmez
# =========================================================================
def sont_uv(ham):
    """Şönt yazmacı (16 bit, ikiye tümleyen) → µV. LSB 10 µV."""
    ham &= 0xFFFF
    if ham & 0x8000:
        ham -= 0x10000
    return ham * 10.0


def bara(ham):
    """Bara yazmacı → (mV, CNVR, OVF). Değer bit 15..3, LSB 4 mV."""
    ham &= 0xFFFF
    return (ham >> 3) * 4.0, bool(ham & 0x2), bool(ham & 0x1)


def akim_a(sont_uv_deger, r_sont=R_SONT_OHM):
    return sont_uv_deger * 1e-6 / r_sont


def guc_w(bara_mv, sont_uv_deger, r_sont=R_SONT_OHM):
    """Kart girişine giden güç: V(VIN−) × I. Şöntte harcanan güç dahil değil."""
    return bara_mv * 1e-3 * akim_a(sont_uv_deger, r_sont)


def doygun(sont_uv_deger, pga=PGA_4):
    """Şönt okuması PGA tam ölçeğine dayandı mı (%99,5) — o örnek güvenilmez."""
    return abs(sont_uv_deger) >= 0.995 * PGA_TAM_OLCEK_UV[pga]


def pencere_ozeti(ornekler, bas, son, r_sont=R_SONT_OHM, pga=PGA_4):
    """`[bas, son)` aralığındaki örneklerin güç özeti.

    `ornekler`: `[(t_monotonik_s, ham_sont, ham_bara), ...]`. Ortalama gücün
    standart hatası örnekler BAĞIMSIZMIŞ gibi hesaplanır — ardışık örnekler
    ilintili olabildiği için **gösterge** niteliğindedir, güven aralığı değil.
    """
    secili = [o for o in ornekler if bas <= o[0] < son]
    n = len(secili)
    if n == 0:
        return {"n": 0, "bas_s": bas, "son_s": son, "sure_s": son - bas,
                "doygun_ornek": 0, "ovf_ornek": 0}
    p = [guc_w(bara(b)[0], sont_uv(s), r_sont) for _, s, b in secili]
    v = [bara(b)[0] * 1e-3 for _, _, b in secili]
    i = [akim_a(sont_uv(s), r_sont) for _, s, _ in secili]
    ort = sum(p) / n
    std = math.sqrt(sum((x - ort) ** 2 for x in p) / (n - 1)) if n > 1 else 0.0
    return {
        "n": n, "bas_s": bas, "son_s": son, "sure_s": son - bas,
        "ort_guc_w": ort, "std_guc_w": std,
        "se_guc_w": std / math.sqrt(n) if n > 1 else None,
        "min_guc_w": min(p), "maks_guc_w": max(p),
        "ort_gerilim_v": sum(v) / n, "min_gerilim_v": min(v),
        "ort_akim_a": sum(i) / n, "maks_akim_a": max(i),
        "doygun_ornek": sum(1 for _, s, _ in secili if doygun(sont_uv(s), pga)),
        "ovf_ornek": sum(1 for _, _, b in secili if bara(b)[2]),
    }


def enerji_hesabi(bos, yuk, sure_s, kosum_sayisi):
    """Delta yöntemi (FR-009c/d, data-model §3):
    `enerji_j_kosum = (yuk_guc_w - bos_guc_w) * sure_s / kosum_sayisi`."""
    if kosum_sayisi <= 0:
        raise ValueError("kosum_sayisi > 0 olmali")
    fark = yuk["ort_guc_w"] - bos["ort_guc_w"]
    se = None
    if bos.get("se_guc_w") is not None and yuk.get("se_guc_w") is not None:
        se = math.sqrt(bos["se_guc_w"] ** 2 + yuk["se_guc_w"] ** 2)
    return {
        "bos_guc_w": bos["ort_guc_w"], "yuk_guc_w": yuk["ort_guc_w"],
        "guc_farki_w": fark, "guc_farki_se_w": se,
        "sure_s": sure_s, "kosum_sayisi": int(kosum_sayisi),
        "enerji_j_kosum": fark * sure_s / kosum_sayisi,
        "enerji_j_kosum_se": (se * sure_s / kosum_sayisi) if se is not None else None,
    }


def etkin_sont_ohm(ort_akim_nominal_a, ref_akim_a, r_nominal=R_SONT_OHM):
    """v1.2 §12: modülün ETKİN şönt direnci. INA219'un gördüğü gerilim
    (= nominal hesapla bulunan akım × nominal direnç) / bağımsız ölçülen akım."""
    if ref_akim_a <= 0:
        raise ValueError("referans akim > 0 olmali")
    return ort_akim_nominal_a * r_nominal / ref_akim_a


def kalibrasyon_kaydi(bilinen_yuk_w, okunan_w, zaman_damgasi, **ek):
    """`Kalibrasyon` (data-model §3b). Değişmez: sapma ≥ %5 → alet geçersiz."""
    sapma = abs(okunan_w - bilinen_yuk_w) / bilinen_yuk_w * 100.0
    k = {"bilinen_yuk_w": bilinen_yuk_w, "okunan_w": okunan_w,
         "sapma_yuzde": sapma, "gecti": sapma < 5.0, "zaman_damgasi": zaman_damgasi}
    k.update(ek)
    return k


# =========================================================================
# Kart tarafı — /dev/i2c-0
# =========================================================================
class INA219(object):
    """Ham yazmaç erişimi. Okuma: işaretçiyi yaz, 2 bayt oku (MSB önce)."""

    def __init__(self, yol=I2C_YOLU, adres=ADRES):
        import fcntl
        self.fd = os.open(yol, os.O_RDWR)
        fcntl.ioctl(self.fd, I2C_SLAVE, adres)

    def oku(self, yazmac):
        os.write(self.fd, bytes([yazmac]))
        b = os.read(self.fd, 2)
        return (b[0] << 8) | b[1]

    def yaz(self, yazmac, deger):
        os.write(self.fd, bytes([yazmac, (deger >> 8) & 0xFF, deger & 0xFF]))

    def yapilandir(self, kelime=YAPILANDIRMA):
        """Yazar ve GERİ OKUR; uyuşmazsa hata (yanlış yapılandırmayla ölçülmez)."""
        self.yaz(YAZMAC_YAPILANDIRMA, kelime)
        geri = self.oku(YAZMAC_YAPILANDIRMA)
        if geri != kelime:
            raise RuntimeError("INA219 yapilandirma 0x{:04X} yazildi, 0x{:04X} okundu".format(
                kelime, geri))
        return geri

    def ornek(self):
        """(ham_sont, ham_bara) — ikisi de son tamamlanan dönüşüm."""
        return self.oku(YAZMAC_SONT), self.oku(YAZMAC_BARA)

    def kapat(self):
        os.close(self.fd)


def _ornekleyici_govde(dosya, periyot_s, dur, yol, adres):
    """Ayrı SÜREÇTE koşar: ana süreçteki iş yüküyle GIL paylaşmaz. Her örnek
    diske yazılır ve tamponu boşaltılır (çökmede veri kalır — GK-01)."""
    ina = INA219(yol, adres)
    sonraki = time.monotonic()
    with open(dosya, "w") as f:
        f.write("t_monotonik_s,ham_sont,ham_bara\n")
        while not dur.is_set():
            t = time.monotonic()
            s, b = ina.ornek()
            f.write("{:.6f},{},{}\n".format(t, s, b))
            f.flush()
            sonraki += periyot_s
            bekle = sonraki - time.monotonic()
            if bekle > 0:
                time.sleep(bekle)
            else:
                sonraki = time.monotonic()      # gecikme birikmesin
    ina.kapat()


class Ornekleyici(object):
    """Sabit periyotla INA219 örnekleyen ayrı süreç. Boş ve yük pencerelerinde
    AYNI şekilde çalışır — kendi tüketimi delta'da sadeleşir (protokol §3)."""

    def __init__(self, dosya, periyot_s=0.2, yol=I2C_YOLU, adres=ADRES):
        self.dosya = dosya
        self.periyot_s = periyot_s
        self.yol = yol
        self.adres = adres
        self._dur = None
        self._surec = None

    def basla(self, ilk_ornek_zaman_asimi_s=5.0):
        import multiprocessing as mp
        self._dur = mp.Event()
        self._surec = mp.Process(target=_ornekleyici_govde,
                                 args=(self.dosya, self.periyot_s, self._dur, self.yol,
                                       self.adres))
        self._surec.start()
        bitis = time.monotonic() + ilk_ornek_zaman_asimi_s
        while time.monotonic() < bitis:
            if len(Ornekleyici.oku(self.dosya)) > 0:
                return self
            time.sleep(0.1)
        self.durdur()
        raise RuntimeError("ornekleyici {} sn icinde ornek yazmadi".format(
            ilk_ornek_zaman_asimi_s))

    def durdur(self):
        if self._dur is not None:
            self._dur.set()
        if self._surec is not None:
            self._surec.join(10)

    @staticmethod
    def oku(dosya):
        try:
            with open(dosya) as f:
                satirlar = f.read().splitlines()[1:]
        except (IOError, OSError):
            return []
        cikti = []
        for s in satirlar:
            parca = s.split(",")
            if len(parca) == 3:
                cikti.append((float(parca[0]), int(parca[1]), int(parca[2])))
        return cikti
