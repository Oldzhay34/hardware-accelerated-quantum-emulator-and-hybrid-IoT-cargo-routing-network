# `agent/` — PYNQ konak kodu (Faz 5)

⚠️ **Bu dizindeki modüller KARTTA koşar: Python 3.6.5.**
`dataclasses` ve `from __future__ import annotations` (3.7+) **kullanılamaz**.
Konakta 3.13 koşuyor; aynı kod ikisinde de çalışmak zorunda.
⛔ Kartta `sudo` gerekir — `import pynq` root ister.

| Modül | Ne | Kart |
|---|---|---|
| `encoder.py` | Ölçekleme + Q1.17/TUR paketleme (T019–T022) | gerekmez |
| `cost_vectors.py` | İzdüşüm vektörü üreticisi (T023) | gerekmez |
| `board.py` | AXI-Lite sürücüsü, çağrı sırası (T026–T030) | **evet** |
| `run_board.py` | İzdüşüm doğrulaması / G3 kapısı (T031) | **evet** |
| `tests/` | 78 test — **hiçbiri kart istemez** (Prensip V) | gerekmez |

## Doğrulama hattı

İzdüşüm dosyaları `artifacts/` altındadır ve **commit edilmez** — tohumdan
birebir yeniden üretilebilirler. Sıra önemlidir:

```bash
# 1) 20 bagimsiz izdusum vektoru + kodlanmis word'ler (konak)
python -m agent.cost_vectors --cikti artifacts/izdusum_vektorleri.json --adet 20 --tohum 42

# 2) C-sim beklenen degerleri — GERCEK cekirdek cagrilir (WSL)
wsl -d Ubuntu -e bash -c "cd /mnt/c/Users/olcay/IdeaProjects/qir-engine && \
  g++ -std=c++17 -O2 -DQIR_NO_VITIS -DQIR_N_QUBITS=16 -Ihls/src -Ihls/tb \
  hls/tb/izdusum_ref.cpp hls/src/qir_kernel.cpp -o hls/build/izdusum_ref && \
  ./hls/build/izdusum_ref --reference docs/measurements/reference_20260915_c6ad872_p2_n5 \
    --vektorler artifacts/izdusum_vektorleri.json --cikti artifacts/izdusum_beklenen.json"

# 3) Kartta kos ve KARSILASTIR (G3)
sudo python3 -m agent.run_board --bit qir_20260920_d350605.bit \
  --reference reference_20260915_c6ad872_p2_n5 \
  --vektorler izdusum_vektorleri.json --beklenen izdusum_beklenen.json \
  --cikti kart-dogrulama.json
```

### Neden bu sıra

**Tek kaynak ilkesi**: vektörler 1. adımda üretilir ve **dosyaya** yazılır;
2. ve 3. adım aynı dosyayı okur. C++ tarafında RNG'yi yeniden gerçeklemek
sessiz bir ayrışma kaynağı olurdu — karşılaştırma yeşil yanar ama farklı
devreleri kıyaslar.

Aynı sebeple C aracı **ham vektörü değil kodlanmış word'leri** okur:
ölçekleme mantığı yalnız `encoder.py`'de yaşar, C++'ta tekrarlanmaz.

Karşılaştırma **bit düzeyindedir** (IEEE-754 deseni), ondalık metin değil.

## Testler

```bash
python -m pytest agent/tests/ -v
```

En değerli ikisi:

- `test_register_haritasi_baslikla_ayni` — sabitleri IP paketinin kendi
  `xqir_kernel_hw.h`'sine karşı doğrular; elle yazılmış harita sessizce kayar.
- `test_devreyi_kodla_c_dokumuyle_ayni` — koşucunun kurduğu devrenin C-sim'le
  **bit bit** aynı olduğunu gösterir; kartta sapma çıkarsa "donanım mı
  kodlayıcı mı" belirsizliği kalmaz.
