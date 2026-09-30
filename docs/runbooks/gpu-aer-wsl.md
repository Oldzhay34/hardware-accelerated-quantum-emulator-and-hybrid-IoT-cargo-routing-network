# GPU tabanı — Qiskit Aer GPU kurulumu (WSL2)

**Amaç**: Faz 5 Phase 6B (T064–T069) — GPU tabanını ölçmek için Qiskit Aer'in
GPU yolunu WSL2'de kurmak ve doğrulamak.

**Durum**: ✅ T064 geçti (2026-09-27).

## Ortam (kurulum günü)

| | |
|---|---|
| GPU | NVIDIA GeForce RTX 4060 Laptop, 8 GB, güç sınırı **45 W** |
| Windows sürücüsü | KMD 616.92, CUDA UMD 13.4 (`nvidia-smi` WSL içinden) |
| WSL | Ubuntu 24.04.3 LTS, Python 3.12.3, `/dev/dxg` mevcut |
| `nvidia-smi` | `/usr/lib/wsl/lib/nvidia-smi` (PATH'te değil) |
| Venv | `/root/qir-gpu-venv` — **repoda değil**, WSL ext4'te |
| CuPy (katman 2, T065b) | `cupy-cuda12x` **14.2.0** — `pip install cupy-cuda12x`; NVRTC pip'teki CUDA 12.9 kütüphanelerinden, nvcc gerekmez (30 Eyl) |
| WSL işlemci | `.wslconfig` `processors=16` (28 Eyl, protokol K1; önceden 6). `wsl --shutdown` sonrası `nproc` = 16 |
| Paketler | `qiskit` 1.4.6, `qiskit-aer-gpu` 0.15.1, pip'ten CUDA 12.9 çalışma zamanı (`nvidia-*-cu12`), `cuquantum-cu12` 26.9.0 |

## Kurulum

```bash
# WSL (root). python3.12-venv yoksa venv pip'siz oluşur.
apt-get install -y python3.12-venv
python3 -m venv /root/qir-gpu-venv
/root/qir-gpu-venv/bin/python -m pip install 'qiskit-aer-gpu==0.15.1' 'qiskit>=1.1,<2'
```

CUDA araç zinciri (nvcc) **gerekmez**: çalışma zamanı kütüphaneleri pip
bağımlılığı olarak gelir, sürücü Windows'tan `/usr/lib/wsl/lib` ile görünür.

## ⚠️ Sürüm kısıtı — kıyası doğrudan etkiler

PyPI'daki en yeni `qiskit-aer-gpu` **0.15.1**'dir (0.17.x GPU tekeri yok) ve
Qiskit **1.x** ister. Windows `.venv`'inde ise `qiskit` 2.5.2 + `qiskit-aer`
0.17.2 var.

**Sonuç**: GPU'yu Windows'ta ölçülmüş CPU Aer rakamlarıyla (32,75 / 41,93 ms)
kıyaslamak **üç değişkeni birden** değiştirir (cihaz, işletim sistemi, Aer
sürümü). CPU tarafı **bu venv'de, `device="CPU"` ile yeniden ölçülür** —
`qiskit-aer-gpu` paketi CPU yolunu da içerir. Yalnız cihaz değişmeli.

## Doğrulama (T064)

16 kübitlik duman testi (dolanıklık + döndürmeler, milisaniyelik iş):

```
qiskit 1.4.6 | qiskit-aer-gpu 0.15.1
available_devices: ('CPU', 'GPU')
CPU success: True | metadata: {"device": "CPU", ... "fusion": {"enabled": true, "threshold": 14, "max_fused_qubits": 5}}
GPU success: True | metadata: {"device": "GPU", "cuStateVec_enable": false, ...}
CPU-GPU fidelity: 1.000000000000000
max |fark|: 0.0
```

`available_devices()` tek başına yetmez: sonucun metadata'sında
`"device": "GPU"` görülmeli (işin gerçekten GPU'da koştuğunun kanıtı).

## ⛔ Bilinen sınır: 16 kübitlik köşegen GPU'da koşmuyor

Maliyet katmanını tek `Diagonal` kapısı olarak yazmak (çekirdekle aynı
algoritma) GPU'da `cudaErrorMemoryAllocation: out of memory` veriyor; füzyon
ve cuStateVec ayarları değiştirmiyor. CPU'da çalışıyor. Ayrıntı:
[dead-ends.md](../decisions/dead-ends.md) (27 Eyl, 6B).

## Ölçümde kaydedilecek değişkenler

- `cuStateVec_enable` — varsayılan **kapalı**; cuQuantum kurulu olduğu için
  açılabilir. Açık/kapalı ayrı bir yapılandırmadır, hangisiyle ölçüldüğü
  sonuç dosyasına yazılır.
- `precision` (double varsayılan / single), `fusion` ayarları — CPU ve GPU
  koşularında **aynı** olmalı.
- Sürücü sürümü ve güç sınırı (`nvidia-smi`), dizüstü prizde mi.

## Risk

**GK-01** ([risk-register.md](../risk-register.md)): makine `nvlddmkm.sys`
yüzünden günde ~1 çöküyor. Uzun GPU yükü bunu tetikleyebilir → ölçüm serisi
**koşum başına** diske yazılmalı; çökme olursa kendisi bir veri noktasıdır.
