# Sıcak Başlangıç ve Sabit Açı Ölçüm Protokolü (6D, T074–T077)

| | |
|---|---|
| **Durum** | 📝 **TASLAK — onay bekliyor.** Onaylanıp dondurulmadan ölçüm koşulmaz |
| **Sürüm** | v1.0 (taslak) — kayıtlar `sicak-baslangic-protokolu v1.0` taşır |
| **Onaylanan metin** | — (dondurulunca commit ve git içerik özeti buraya) |
| **Görev** | T074 (taban), T075 (sıcak başlangıç), T076 (sabit açı), T077 (kayıt + [sistem-mimarisi §7](../sistem-mimarisi.md)) |
| **Dayanak** | FR-011, SC-009 (ön kayıt) · [sistem-mimarisi §3 Yol 2, §7](../sistem-mimarisi.md) · amaç fonksiyonu: [native_formulation.py](../../scripts/native_formulation.py) (çekirdeğin Python ikizi) · referans: `services/reference/qaoa_reference.py` |
| **Yürütücü** | [`scripts/sicak_baslangic.py`](../../scripts/sicak_baslangic.py) — tasarım sabitleri ve §6'daki ölçütler **kodda**, protokolle birlikte donar |

**Kural (FR-011, SC-009)**: ilk ölçümden **önce** onaylanıp dondurulur; sonuca
bakıp değiştirilemez, değişiklik yeni sürümdür.

---

## 1. Soru

Artımlı yolda (adres değişikliği, kullanıcı bekliyor) bir alt problemin süresi
= çekirdek çağrısı sayısı × 36,58 ms. Referansta çağrı sayısı 99, yani 3,69 s.
**Sıcak başlangıç** ya da **sabit açı** bu sayıyı düşürür mü, ve **çözüm
kalitesinden ne kadar ödenir**? ⛔ Tek başına çağrı sayısı ölçüt değildir
(tasks.md 6D): her koşulda çağrı sayısı **ve** kalite birlikte raporlanır.

Kart ve FPGA gerekmez. Sonuç çağrı sayısıdır; süre, ölçülmüş kart gecikmesiyle
çarpılarak **türetilir** ve öyle etiketlenir.

---

## 2. Önceden bilinenler — ön kayıt beyanı (2 Eki, protokol yazılmadan önce görüldü)

| Görülen | Değer | Ne anlama geliyor |
|---|---|---|
| Referansın COBYLA'sı neden durdu (Qiskit yolu, I0, tohum 42, bugün yeniden koşuldu) | p=1 **37**, p=2 **99** değerlendirme; ikisi de *"trust region radius reaches its lower bound"*, **tavana çarpmadı**. ⟨E⟩ ve P_opt referansla aynı (−9799,623 / −3950,927; 8,561e-6 / 2,380e-5) | 99 yakınsama sayısıdır, tavan değil |
| Qiskit yolunda tek değerlendirme | p=1 **1,05 s**, p=2 **2,14 s** (Windows `.venv`, `Statevector.from_instruction`) | 20 örnek × 5 tohum × 4 koşul bu yolda saatler sürer → Python ikizi (§3.4) |
| Python ikizinde aynı COBYLA (I0, tohum 42) | p=1 **46** değ., ⟨E⟩ −9178,85; p=2 **66** değ., ⟨E⟩ −4519,55 | Amaç fonksiyonu aynı (rastgele noktalarda fark ≤ 2e-8, göreli ~1e-11), **yol farklı** → optimizasyon bu ayarda 1e-11'lik gürültüye duyarlı |
| ⟨E⟩(γ) taraması, I0, p=1, β=π/8, 4001 nokta | γ∈[0, 0,002]: **15** yerel uç, en iyi −11.016,8 (γ=2,695e-4). γ∈[0, π]: **2889** yerel uç, en iyi −13.283,5 (γ=0,320) | Referansın başlattığı aralıkta manzara COBYLA'nın adım ölçeğinde **sözde rastgele**; pürüzsüz bölge γ ≈ 1e-4 ölçeğinde |
| I0 ölçekleri | spektral genişlik 230.036; max\|h\|,\|J\| = **7512,6**; E_opt = −51.073,53 | Pürüzsüz minimum γ·s ≈ **2,0** → N rejiminin gerekçesi (§3.2) |
| Bunlardan türeyen r (= ⟨E⟩/E_opt) | referans p=1 0,192, p=2 0,077; ikiz p=1 0,180, p=2 0,088 | Rastgele tahmin r = 0 (düzgün süperpozisyonda ⟨E⟩ = 0) |
| Python ikizinde tek değerlendirme (hızlı RX) | p=2 **27,6 ms** | Tüm ölçüm tahminen ~10 dk (8 süreç; planlama tahmini, ölçüm değil) |
| Akış denemesi (`--deneme`) | yalnız I0/I0', 1 tohum, maxiter 5. Kapı geçti, belirlenimcilik aynı. I0' matris değişimi %17, optimum tur aynı. **Kalite değerlerine bakılmadı** (maxiter 5'te anlamsız) | Yürütücü uçtan uca çalışıyor |

⚠️ **Bu bulgunun kendisi bir sonuçtur** ve ölçümden bağımsız olarak raporlanır:
referans, **normalize edilmemiş** Hamiltonyen'de γ'yı [0, π]'den başlatıyor.
Bu, "99 iterasyon" ve P_opt = 2,4e-5'in problemin değil **bu ayarın** özelliği
olabileceğini gösteriyor. Ölçüm bunu sınar (H1, H2).

---

## 3. Tasarım

### 3.1 Problem örnekleri

| | Kural |
|---|---|
| **I1–I20** | `data/synthetic/deliveries.csv`'den (200 teslimat) 5 farklı satır, `default_rng(1000+k).choice(200, 5, replace=False)`; ilk seçilen depo |
| **I_k'** (değişmiş) | I_k'da depo dışındaki bir durağın adresi değişir: konum `default_rng(2000+k).integers(1, 5)`, yeni adres **aynı ilçeden** rastgele bir teslimat (aynı rng); ilçede aday yoksa en yakın teslimat. Matris değişimi ve optimum turun değişip değişmediği kaydedilir |
| **I0** | referans örneği (ilk 5 satır) — yalnız kapıda (§5), istatistiğe girmez |
| Mesafe | `services/reference/cli.py::ornek_matris` (referansla aynı formül; yalnız satır seçimi eklendi, varsayılan çıktı bit bit aynı) |

### 3.2 Rejimler

| Rejim | Açılar | Gerekçe |
|---|---|---|
| **R** (ham) | γ doğrudan, ham H üzerinde — **referansla aynı** | Sistemin bugünkü hâli |
| **N** (normalize) | γ = γ̃ / s, **s = max(\|h_i\|, \|J_ij\|)** örnek başına; optimize edici γ̃ görür | §2'deki tarama. Çekirdek değişmez — yalnız konağın verdiği γ ölçeklenir |

İki rejimde aynı başlangıç sayıları kullanılır (R'de γ, N'de γ̃ olarak) → eşli tasarım.

### 3.3 Koşullar

| Kod | Problem | Başlangıç x0 | rhobeg | Görev |
|---|---|---|---|---|
| **C1** | I_k | soğuk: `default_rng([k, tohum]).uniform(0, π, 2p)` | 1,0 (varsayılan, referansla aynı) | T074 |
| **C1** | I_k' | soğuk (aynı sayılar) | 1,0 | T075 kontrol |
| **C2** | I_k' | soğuk | **0,1** | T075 — rhobeg etkisinin kontrolü |
| **W1** | I_k' | **sıcak**: aynı tohumun I_k'daki C1 sonucu (N'de γ̃ taşınır) | 1,0 | T075 |
| **W2** | I_k' | sıcak | **0,1** | T075 |
| **S** | test kümesi | **sabit açı**: I1–I10'da (eğitim) her örneğin 5 tohumdan en düşük ⟨E⟩'li C1 sonucu → bileşen bileşen **medyan** | — (1 çağrı) | T076 |

- **Neden C2**: küçük rhobeg sıcak başlangıçtan bağımsız olarak çağrı sayısını
  düşürür (güven bölgesi 1e-6'ya daha az adımda iner). Sıcak başlangıcın
  **bilgi taşıyıp taşımadığı** W2 ↔ C2 kıyasıyla (aynı rhobeg) ayrılır.
- **S test kümesi**: I11–I20 ve I11'–I20' (20 problem). Kıyas, aynı problemdeki
  C1'in 5 tohumluk P_opt medyanıyla.
- Tohumlar 0–4; p = **2 (manşet, kart p=2)** ve 1 (ikincil).
- Optimize edici: SciPy COBYLA (PRIMA, scipy 1.18.1), `maxiter` **100**, `tol`
  **1e-6** — referansla aynı. Tavana çarpan koşum (`nfev ≥ 100`) işaretlenir.

Koşum sayısı: T074 2×2×20×5 = 400; T075 2×2×20×5×4 = 1600; T076 2×2×20 = 80 tek değerlendirme.

### 3.4 Amaç fonksiyonu

⟨ψ(θ)|H_C|ψ(θ)⟩, offset'siz (referansın `cost_after`'ı ile aynı tanım),
çekirdeğin Python ikiziyle (`native_formulation`: düzgün süperpozisyon,
köşegen maliyet, kübit başına RX) float64'te. Tek fark: RX vektörleştirildi
(`rx_hizli`). θ sırası Qiskit'inki: [β_0..β_{p−1}, γ_0..γ_{p−1}].

⚠️ §2: tek tek **yollar** Qiskit yolundakiyle aynı çıkmaz (aynı fonksiyon,
1e-11'lik fark, duyarlı optimizasyon). Bu yüzden sonuçlar **dağılım** olarak
raporlanır; tek koşumun Qiskit'le eşleşmesi beklenmez ve iddia edilmez.

---

## 4. Ölçülen büyüklükler (her koşum)

| Büyüklük | Tanım |
|---|---|
| `nfev` | amaç fonksiyonu çağrısı = **çekirdek çağrısı** |
| `durum`, `mesaj`, `tavan` | COBYLA neden durdu; `nfev ≥ 100` mü |
| **r** | ⟨E⟩ / E_opt (E_opt: optimum turun Ising enerjisi, < 0). Rastgele = 0, mükemmel = 1 |
| **P_opt** | optimum tur(lar)ın ölçülme olasılığı (eşit uzunlukta birden fazla optimum varsa toplamı) |
| `P_gecerli` | 24 geçerli turun toplam olasılığı |
| `opt_sira`, `en_olasi_gecerli_optimal` | optimum, geçerli turlar arasında olasılıkça kaçıncı |
| türetilmiş süre | `nfev × 36,578 ms` (kart-gecikme p2 medyanı) — ⚠️ **türetilmiş**, ölçülmüş uçtan uca süre değil |

---

## 5. Kapı — ölçümden önce, hepsi geçmeli (betik denetler, kalırsa durur)

| # | Denetim | Eşik |
|---|---|---|
| G1 | `rx_hizli` = `native_formulation.apply_rx` (rastgele durum, 16 kübit) | ≤ 1e-14 |
| G2 | Hızlı amaç = Qiskit (`QAOAAnsatz` + `Statevector`, referansla aynı kurulum), I0, p=1/2, 4'er rastgele θ | \|fark\| ≤ 1e-6 |
| G3 | I0'da referansın parametreleriyle (`reference_20260915_c6ad872_p{1,2}`) P_opt ve ⟨E⟩ referansla aynı | göreli ≤ 1e-9; ⟨E⟩ ≤ 1e-6 |
| G4 | Her örnekte geçerli turların QUBO enerjisi − tur uzunluğu sabit; E_opt < 0 | ptp ≤ 1e-6 |
| G5 | `maxiter` = 100, `tol` = 1e-6 (referansla aynı) | eşit |

**Sonda belirlenimcilik**: 4 koşum (kodda `TEKRAR`) seri olarak yeniden koşulur;
`x_son`, `nfev`, `E_son` **bit bit** aynı olmalı.

---

## 6. Ön kayıtlı beklentiler (ölçümden ÖNCE; ölçütler kodda `ozet_ve_beklentiler`)

Örnek düzeyi değer = o örneğin 5 tohumunun medyanı (20 değer). Eşli kıyaslar
iki yanlı Wilcoxon işaretli sıra testi, α = 0,05. **Manşet p=2**; p=1 aynı
ölçütlerle hesaplanır, ikincil raporlanır.

| # | Beklenti | Ölçüt | Gerekçe |
|---|---|---|---|
| **H1** | R'de sonuç tohuma N'dekinden **daha duyarlı** | T074 C1: 5 tohumun r aralığı R > N olan örnek sayısı **≥ 15/20** | §2: R manzarası sözde rastgele |
| **H2** | N, R'den **daha iyi** optimum olasılığı verir | T074 C1: P_opt örnek düzeyi medyanı N/R **≥ 2** ve Wilcoxon p < 0,05 | Pürüzsüz bölgede genlik düşük enerjiye sistematik yoğunlaşır. ⚠️ r için öngörü **yok**: R'de sözde rastgele derin noktalar var (§2: −13.284 < −11.017) |
| **H3** | N'de sıcak başlangıç **bilgi taşır** ve çağrıyı **yarıya** indirir | T075 N: r(W2) > r(C2), p < 0,05 **ve** nfev medyanı W2 ≤ 0,5 × C1 | Küçük adres değişikliğinde pürüzsüz manzaranın minimumu az kayar |
| **H4** | R'de sıcak başlangıç **bilgi taşımaz** | T075 R: r(W2) ile r(C2) farkı anlamsız (p ≥ 0,05) | Ham γ'da E'deki küçük değişiklik fazı ≫ 2π kaydırır, manzara ilişkisizleşir |
| **H5** | Sabit açı N'de **işe yarar**, R'de yaramaz | S: P_opt / C1 P_opt medyanı N'de **≥ 0,5**, R'de **< 0,5** | Normalize açılar örnekler arası taşınabilir (parametre yoğunlaşması), ham açılar taşınamaz |
| **H6** | COBYLA'lı **hiçbir** koşul saniyenin altına inmez | Her COBYLA koşulunun nfev medyanı > **27** (27 × 36,578 ms = 0,988 s) | tol 1e-6'ya inmek her başlangıçtan onlarca adım ister; saniye altı yalnız S ile |

⛔ Beklenti tutmazsa **sonuç değişmez, yazılır**. Tutmayan beklenti için
sonradan ölçüt, eşik ya da alt küme değiştirilmez.

---

## 7. Raporlama kuralları

- Her koşul için: nfev, r, P_opt çeyrekleri (25/50/75); P_opt'un düzgün
  dağılıma (1/65536) oranı; tavan oranı; en olası geçerli turun optimum olma
  oranı; türetilmiş kart süresi.
- ⛔ Koşum, örnek ya da tohum **ayıklanmaz**. Tavana çarpan koşumlar dahildir
  (işaretli).
- Kalite ölçütü olmadan çağrı sayısı yazılmaz (6D kuralı).
- [sistem-mimarisi §7](../sistem-mimarisi.md) tablosu ölçülen değerlerle
  güncellenir (T077); hiçbir koşul kazanmazsa bu da yazılır.
- N rejimi kazanırsa bu **konak tarafı** bir değişikliktir (γ ölçeklemesi);
  çekirdek, bitstream ve önceki kart ölçümleri etkilenmez. Referans (altın
  referans) dosyaları değiştirilmez.

---

## 8. Geçerlilik

| Durum | Karar |
|---|---|
| Ağaç kirli (`cpu_load_loop._kod_kirli`: izlenen değişiklik ya da `docs/measurements/` dışında izlenmeyen dosya) | betik **başlamaz** |
| Kapı (§5) kaldı | ölçüm **yapılmaz** |
| Sonda belirlenimcilik farklı | kayıt **geçersiz** (`gecerli: false`), neden araştırılır |
| Herhangi bir koşum hata verdi | ölçümün tamamı **geçersiz**, baştan (kısmi kayıt yok — ölçüm belirlenimci ve ~10 dk) |
| Sonuca bakarak koşum/örnek ayıklama | ⛔ **yapılmaz** |

---

## 9. Çıktı

- `docs/measurements/sicak-baslangic_<tarih>_<git-hash>.json` — kapı, örnekler
  (satırlar, s, E_opt, optimum turlar), değişiklikler, tüm koşumlar, sabit
  açılar, S sonuçları, özet, H1–H6 değerlendirmesi, belirlenimcilik, protokol
  dosyasının git blob özeti.
- Çalıştırma (Windows, temiz ağaç):
  `.venv\Scripts\python.exe scripts\sicak_baslangic.py` (varsayılan 8 süreç).
  `--deneme` yalnız akışı sınar (I0, maxiter 5, çıktı `%TEMP%\qir-6d-deneme`) —
  **ölçüm değildir**.

---

## 10. Kapsam dışı / sınırlar

- **Ölçülmeyen kaldıraçlar**: `tol`'u gevşetmek (1e-6, çekirdeğin faz
  çözünürlüğünün altında olabilir), başka optimize ediciler (SPSA, Nelder–Mead),
  p ≥ 3, literatürdeki sabit açılar (MaxCut içindir, cezalı TSP-QUBO'ya
  doğrudan taşınmaz — bu yüzden S eğitim kümesinden türetilir).
- **Sabit nokta**: ölçüm float64'tedir. Optimize edici döngüsü FPGA'da (18 bit,
  fidelity 0,99998) koşarsa R rejiminde yol, §2'deki duyarlılık nedeniyle
  float64'tekinden tamamen ayrılabilir; N'de daha az beklenir. **Ölçülmedi.**
- Sonuç bu sentetik İstanbul verisi ve N=5 için geçerlidir; genelleme yapılmaz.
- "Çözüm kalitesi" QAOA'nın kalitesidir; kaba kuvvet aynı problemi 43,2 µs'de
  kesin çözer ([neden-fpga §0.5](../neden-fpga.md)). Bu ölçüm o gerçeği
  değiştirmez — artımlı yolun **emülatör tarafının** gecikmesini ölçer.
