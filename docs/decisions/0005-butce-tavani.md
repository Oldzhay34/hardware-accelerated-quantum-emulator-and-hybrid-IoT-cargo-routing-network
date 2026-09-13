# ADR 0005 — Bütçe tavanı: 0 TL, son 1-2 ay Railway Hobby (~$5/ay) istisnası

**Tarih**: 2026-09-13 · **Faz**: 0.6 · **Durum**: Kabul edildi

## Bağlam

Hiçbir dış servis henüz kurulu değil. Bütçe tavanını Faz 3+ Railway/Cloudflare gerçekten
kurulduktan sonra tartışmak, o an acil bir karara dönüşür — bugün, maliyet sıfırken karar
vermek daha ucuz.

## Seçenekler

1. **Tamamen 0 TL, istisnasız** — en güvenli, ama teslimat döneminde (H12-H14) ücretsiz
   katmanın kredi/kota tükenmesi demo'yu riske atabilir.
2. **Sabit aylık bütçe (ör. 200 TL/ay), baştan itibaren** — esneklik sağlar ama kart bağlamayı
   erken gerektirir, otomatik faturalama riskini erken açar.
3. **0 TL + son 1-2 ay küçük istisna** — riski teslimat penceresine kadar sıfırda tutar, tam o
   dönemde (demo/kıyas kesintisiz kalmalı) küçük bir esneklik tanır.

## Karar

**(3).** Aylık tavan 0 TL; H12-H14 civarında (teslimat penceresi) Railway Hobby planı
(~$5/ay) kullanıcı tarafından onaylandı.

## Gerekçe

- Kredi kartı hiçbir serviste bağlı değil (2026-09-13 itibariyle doğrulandı) — otomatik
  faturalama riski bugün **sıfır**, ve bu tavan boyunca da öyle kalıyor.
- Demo ve kıyas koşumlarının en kritik olduğu dönem tam olarak son 1-2 ay; ücretsiz
  katmanın "durur ama ücretlendirmez" davranışı bu dönemde en pahalıya patlar (jüri günü
  servisin durması).
- Küçük ($5) ve geç (yalnızca gerekirse) bir esneklik, riski büyütmeden bu senaryoyu kapatıyor.

## Sonuç

- [docs/cost.md](../cost.md) §5'te tavan ve gerekçe kayıtlı.
- Risk kaydına `MC-01`..`MC-03` eklendi ([docs/risk-register.md](../risk-register.md) §8c); MC-03 (kart bağlı değil) aynı gün kapandı.
- Haftalık ritüel maddesi 1'e MC-XX kontrolü eklendi ([schedule.md §4](../specs/000-kapsam-takvim/schedule.md)) — yeni madde açmadan, mevcut kapsamı genişleterek (10 dakikalık ritüel korunuyor).

## Tekrar değerlendirilmeli mi?

Evet, şu koşulda: bir servise kart bağlanırsa (MC-03 yeniden açılır, harcama limiti o an
ayarlanır) veya Hobby planına geçiş tarihi netleşince (H12 civarı hatırlatılacak).
