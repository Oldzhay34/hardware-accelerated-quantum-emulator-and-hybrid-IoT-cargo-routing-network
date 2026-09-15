"""PYNQ-Z2 (XC7Z020) statevector bellek bütçesi. Faz 0 ucuz sigortası S-3.

Anayasa Prensip III: statevector çip-içi bellekte kalmalı, DDR'a taşamaz.
Bu script sentez GEREKTİRMEZ — saf aritmetik. Amaç, 16 kübitin sığıp sığmadığını
ilk sentez raporundan (H4) haftalar önce söylemek.

Kullanım:
    .venv/Scripts/python.exe scripts/memory_budget.py
"""
from __future__ import annotations

# --- XC7Z020 (PYNQ-Z2 üzerindeki Zynq-7000) -----------------------------------
# Kaynak: DS190 "Zynq-7000 SoC Data Sheet: Overview", Z-7020 sutunu.
#   Total Block RAM (# 36Kb Blocks): 4.9Mb (140)
#   DSP Slices: 220 | LUTs: 53,200 | Flip-Flops: 106,400 | PL: Artix-7
# 2026-09-15'te resmi veri sayfasindan dogrulandi.
#
# NOT 1: Zynq-7000 ailesinde URAM (UltraRAM) YOKTUR — URAM UltraScale+ ozelligidir.
#        Anayasa Prensip III "BRAM/URAM" diyor; bu cipte tek secenek BRAM.
# NOT 2: Vitis HLS kaynak tablosunda BRAM'i 18Kb birimiyle (BRAM_18K) raporlar.
#        Butce o birimde 280'dir (140 x 2). Sentez raporunu okurken 140'a degil
#        280'e bolmek gerekir — bkz. docs/memory-budget.md.
BRAM36_COUNT = 140
BRAM18K_COUNT = BRAM36_COUNT * 2  # HLS raporunun kullandigi birim
BRAM36_BITS = 36 * 1024
TOTAL_BRAM_BYTES = BRAM36_COUNT * BRAM36_BITS // 8  # 645_120 B ≈ 630 KB

# Yerleştirme/yönlendirme ve diğer modüller için pay. cut-plan.md K-02 ölçütü.
USABLE_FRACTION = 0.85

# (etiket, gerçek başına bayt)
FORMATS = [
    ("double (64-bit)", 8),
    ("float (32-bit)", 4),
    ("Q1.31 sabit nokta", 4),
    ("Q1.15 sabit nokta", 2),
]

QUBITS = [12, 14, 16]

# Kapı uygulaması sırasında ikinci tampon gerekip gerekmediği.
# in-place: dikkatli bankalama ile tek tampon; ping-pong: okuma/yazma ayrı.
BUFFERING = [("yerinde (in-place)", 1), ("ping-pong (çift tampon)", 2)]


def statevector_bytes(n_qubits: int, bytes_per_real: int, buffers: int) -> int:
    """Bir statevector: 2^n karmaşık genlik, her genlik 2 reel sayı."""
    return (2**n_qubits) * 2 * bytes_per_real * buffers


def blok_analizi() -> None:
    """BRAM'i BAYT degil BLOK duzeyinde hesaplar — sentezde onemli olan budur.

    BRAM36'nin azami kelime genisligi 36 bittir. Bir genlik (reel+sanal) 36 biti
    asiyorsa yan yana BIRDEN FAZLA blok gerekir ve artan bitler israf olur.
    Bayt düzeyindeki hesap bu granulariteyi gormez ve doluluğu OLDUGUNDAN AZ gosterir.
    """
    kelime = 36
    blok_basina_kelime = BRAM36_BITS // kelime  # 1024
    n = 2**16

    print("\n=== BRAM BLOK duzeyinde (36-bit kelime granularitesi) ===")
    print(f"{'format':>9} {'bit/genlik':>11} {'blok(yerinde)':>14} {'%':>7} "
          f"{'ping-pong':>10} {'%':>7} {'israf bit':>10}")
    for ad, bit in [("Q1.11", 24), ("Q1.13", 28), ("Q1.15", 32), ("Q1.17", 36),
                    ("Q1.19", 40), ("Q1.23", 48), ("float32", 64)]:
        paralel = -(-bit // kelime)                      # kac blok yan yana
        blok = -(-n // blok_basina_kelime) * paralel
        israf = paralel * kelime - bit
        pp = blok * 2
        print(f"{ad:>9} {bit:>11} {blok:>14} {100*blok/BRAM36_COUNT:>6.1f}% "
              f"{pp:>10} {100*pp/BRAM36_COUNT:>6.1f}% {israf:>10}")

    print("\nNOT: Q1.11-Q1.17 ayni blok sayisini kullanir (hepsi tek 36-bit kelimeye sigar).")
    print("     Q1.17 israfsiz olan tek format; daha dar formatlar BRAM kazandirmaz.")
    print("     Q1.19 ve ustu (float32 dahil) iki kelime ister -> blok sayisi ikiye katlanir.")
    print("\nUYARI: Bu birinci-dereceden bir tahmindir. ARRAY_PARTITION ile bankalama")
    print("       yapildiginda dizi parcalara ayrilir ve blok sayisi DEGISIR.")
    print("       Kesin sayi yalnizca sentez raporundan okunur (Prensip II).")


def main() -> None:
    budget = int(TOTAL_BRAM_BYTES * USABLE_FRACTION)

    print(f"PYNQ-Z2 / XC7Z020")
    print(f"  Toplam BRAM      : {BRAM36_COUNT} x 36Kb = {TOTAL_BRAM_BYTES:,} B ({TOTAL_BRAM_BYTES/1024:.0f} KB)")
    print(f"  URAM             : YOK (Zynq-7000'de UltraRAM bulunmaz)")
    print(f"  Kullanilabilir   : %{USABLE_FRACTION*100:.0f} -> {budget:,} B ({budget/1024:.0f} KB)")
    print()

    header = f"{'kubit':>5} {'format':<20} {'tamponlama':<24} {'boyut':>12} {'BRAM %':>8}  durum"
    print(header)
    print("-" * len(header))

    for n in QUBITS:
        for fmt_label, bpr in FORMATS:
            for buf_label, buf in BUFFERING:
                size = statevector_bytes(n, bpr, buf)
                pct = size / TOTAL_BRAM_BYTES * 100
                if size <= budget:
                    status = "SIGIYOR" if pct < 60 else "SIGIYOR (dar)"
                else:
                    status = "SIGMIYOR"
                print(
                    f"{n:>5} {fmt_label:<20} {buf_label:<24} "
                    f"{size/1024:>9.0f} KB {pct:>7.1f}%  {status}"
                )
        print()


if __name__ == "__main__":
    main()
    blok_analizi()
