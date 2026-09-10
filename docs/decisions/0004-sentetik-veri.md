# ADR 0004 — Tamamen sentetik teslimat/şoför verisi

**Tarih**: 2026-09-10 · **Faz**: 0.4 · **Durum**: Kabul edildi

## Bağlam

Sistem tasarımı kişisel veri içeriyor: şoför kimlikleri, teslimat adresleri, araç konum geçmişi,
kullanıcı hesapları, denetim kayıtları. Bir bitirme projesi de olsa bu veriler gerçekse KVKK
kapsamına girer. Karar veri modelini (Faz 7.2) etkilediği için ondan önce verilmelidir.

## Seçenekler

1. **Tamamen sentetik** — İstanbul'da gerçekçi ama uydurma koordinat ve isimler.
2. **Anonimleştirilmiş gerçek veri** — varsa gerçek bir küme, kimlik alanları çıkarılmış.
3. **Gerçek veri** — yalnızca açık rıza ve gerekçeyle.

## Karar

**(1) Tamamen sentetik.** Gerçek teslimat adresi ve gerçek şoför bilgisi kullanılmayacaktır.

## Gerekçe

- Hukuki risk sıfır; 14 hafta kısıtı altında (Prensip VI) rıza/anonimleştirme süreci dönem içinde bitmez.
- **Ölçüm gerçekçiliği zarar görmüyor**, çünkü gerçekçilik iki kaynaktan geliyor ve kritik olan sentetik değil:
  - *Yol ağı topolojisi* (mesafe matrisi, tek yönlü yollar, Boğaz geçişleri) → **OSM/OSRM gerçek verisi**, Faz 1.1.
  - *Nokta kümelenme deseni* → sentetik üretici, ama **uniform rastgele değil**: 20 ilçe merkezi etrafında ağırlıklı Gauss. Ölçülen yoğunluk oranı 5.7x (uniform'da ~1x olurdu).
- Jüri odasında ve tez ekran görüntülerinde kişisel veri görünme riski baştan ortadan kalkıyor.

## Sonuç

- [`scripts/generate_synthetic_data.py`](../../scripts/generate_synthetic_data.py) — deterministik (sabit seed), MANIFEST'e seed + Faker sürümü yazıyor.
- `data/synthetic/` **commit edilir** — sentetik olduğu için güvenli, ve ölçüm girdisinin sabit kalmasını garanti eder (Prensip II).
- "Gerekmeyen alan toplanmaz" kuralı uygulandı: **telefon alanı üreticiden ve gelecek şemadan çıkarıldı** (bu projede sevkiyat/bildirim akışı yok).
- Saklama süreleri, `DEMO_MODE` gereksinimi, silme talebi prosedürü ve tez Yöntem paragrafı [docs/data-governance.md](../data-governance.md)'de.

## Tekrar değerlendirilmeli mi?

Evet, şu koşulda: problem formülasyonuna **zaman penceresi** eklenirse. Sentetik verinin yakalamadığı
tek yapı zamansal desenlerdir (teslimat pencereleri, saat bazlı trafik); taban plan bunu modellemediği
için bugün sorun değil, ama kapsam o yöne genişlerse veri kaynağı yeniden tartışılmalıdır.
