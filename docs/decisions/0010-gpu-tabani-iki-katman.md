# ADR 0010 — GPU tabanı iki katmanlı ölçülür: Aer (kütüphane) + aynı algoritma (çekirdek)

**Tarih**: 2026-09-27 · **Faz**: 5 (Phase 6B) · **Durum**: Kabul edildi

## Bağlam

Phase 6B (T064–T069) GPU tabanını ölçmek için yazıldı; T065 Qiskit Aer'in
`cpu_load_loop.py` döngüsüne `--device` eklemeyi öngörüyordu. İki sorun çıktı:

1. **Aer tabanı FPGA'yla kıyaslanamaz.** Aer QAOA'yı p=2'de 384 kapı olarak
   uygular; çekirdek maliyet katmanını tek köşegen geçişe füzyonlar. CPU'da bu
   fark 12× algoritmik farktı ve Faz 2'nin *"başabaş"* sonucunu üretmişti
   ([hatalar #5](../hatalar-ve-duzeltmeler.md)). Aynı şey GPU'da tekrarlanırdı.
2. **Aynı algoritma Aer-GPU'da kurulamıyor.** Maliyet katmanını tek 16
   kübitlik `Diagonal` kapısı olarak yazmak GPU'da out-of-memory veriyor
   ([dead-ends.md](dead-ends.md), 27 Eyl). Ayrıca PyPI'daki en yeni GPU
   tekeri `qiskit-aer-gpu` 0.15.1 → Qiskit 1.x zorunlu; Windows ortamı 2.x.

## Seçenekler

1. **Yalnız Aer** (yazıldığı gibi) — ucuz; ama çıkan sayı FPGA'yla kıyaslanamaz.
2. **Yalnız aynı algoritma** — çekirdeğin algoritması GPU'da doğrudan yazılır
   (CuPy); FPGA kıyası için yeterli, Aer içi GPU/CPU oranı yok.
3. **İkisi birden** — Aer (CPU ve GPU aynı WSL ortamında) + aynı algoritma.
4. **6B'yi durdur** — GPU ölçülmez.

## Karar

**Seçenek 3 — ikisi birden** (kullanıcı onayı, 2026-09-27).

## Gerekçe

- **Katman 1 — Aer, kütüphane düzeyi**: aynı devre, aynı kütüphane, aynı
  ortam; **yalnız cihaz değişir**. "Hazır bir simülatörde GPU CPU'dan ne kadar
  hızlı" sorusunu cevaplar. FPGA'yla **kıyaslanmaz**, raporda yalnız Aer
  içi oran olarak kullanılır.
- **Katman 2 — aynı algoritma**: CPU'daki adil tabanın
  (`hls/tb/bench_kernel.cpp`, 3,273 ms) GPU karşılığı. FPGA'yla kıyaslanabilen
  **tek** GPU sayısı budur. Altın referansa karşı doğrulanmadan süre
  kaydedilmez (Prensip IV).
- Prensip II (ölçüm dürüstlüğü): sonuç ne çıkarsa çıksın raporlanır.
- Prensip VI (takvim): toplam ~1 gün; kart gerektirmez, öbek 6'nın
  donanım beklemesiyle paralel.

## Sonuç

- `scripts/cpu_load_loop.py`: `--device {CPU,GPU}` (T065, ayrı betik yok).
  CPU ve GPU koşuları **aynı** WSL venv'inde (`/root/qir-gpu-venv`,
  Qiskit 1.4.6 / Aer-GPU 0.15.1); Windows'taki eski Aer rakamları bu kıyasa
  girmez.
- Yeni: çekirdeğin GPU gerçeklemesi (CuPy, WSL venv'e). CuPy repo
  bağımlılığı değildir; venv repo dışıdır.
- `tasks.md` Phase 6B görevleri buna göre güncellendi.

## Tekrar değerlendirilmeli mi?

Aer'in 0.17+ GPU tekeri PyPI'a gelir ve 16 kübit köşegeni GPU'da uygularsa
katman 2, Aer'in `Diagonal` kapısıyla yeniden kurulabilir (tek kütüphane,
daha az kendi kodu). Bu takvimde beklenmiyor.
