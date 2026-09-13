# Specification Quality Checklist: Faz 1 — Veri Hattı ve Altın Referans

**Purpose**: Validate specification completeness and quality before proceeding to planning
**Created**: 2026-09-13
**Feature**: [spec.md](../spec.md)

## Content Quality

- [x] No implementation details (languages, frameworks, APIs) — *bilinçli istisna, bkz. Not 1*
- [x] Focused on user value and business needs
- [x] Written for non-technical stakeholders — *koşullu, bkz. Not 2*
- [x] All mandatory sections completed

## Requirement Completeness

- [x] No [NEEDS CLARIFICATION] markers remain
- [x] Requirements are testable and unambiguous
- [x] Success criteria are measurable
- [x] Success criteria are technology-agnostic (no implementation details)
- [x] All acceptance scenarios are defined
- [x] Edge cases are identified
- [x] Scope is clearly bounded
- [x] Dependencies and assumptions identified

## Feature Readiness

- [x] All functional requirements have clear acceptance criteria
- [x] User scenarios cover primary flows
- [x] Feature meets measurable outcomes defined in Success Criteria
- [x] No implementation details leak into specification

## Notes

**Not 1 — Teknoloji seçimi bilinçli olarak BOŞ bırakıldı.**
Prompt'un çalışma kuralı (ARAŞTIR → KIYASLA → ONAY BEKLE → KODLA) ve Anayasa Prensip I gereği,
rotalama motoru (OSRM/Valhalla/GraphHopper) ve kuantum kütüphanesi (Qiskit Aer/PennyLane) seçimi
bu spec'te **yapılmadı**. Gereksinimler "gerçek yol ağından türeyen süre", "ham genliklere erişim"
gibi **yetenek** düzeyinde yazıldı — hangi aracın bunu sağladığı `/speckit-plan` işidir.
Bu, "no implementation details" maddesinin ihlali değil, tam tersine doğru uygulanmasıdır.

**Not 2 — Kaçınılmaz alan terimleri.**
"QUBO", "kübit", "one-hot TSP", "QAOA derinliği (p)" gibi terimler geçiyor. Bunlar seçilmiş
teknolojiler değil, **problemin kendisinin dili**. Anayasa (Prensip III, IV) bu terimleri kısıt
olarak zaten sabitlemiş durumda. Spec'i bunlardan arındırmak ölçütleri ölçülemez hale getirirdi.

**Not 3 — Anayasa ile açık bir gerilim kayıt altına alındı.**
Prompt "Qiskit vs PennyLane" karşılaştırması istiyor; Anayasa Prensip IV ise Qiskit'i adıyla
bağlayıcı kılıyor. Spec bunu Assumptions bölümünde açıkça işaretledi. `/speckit-plan` aşamasında
kullanıcıya sunulacak: karşılaştırma yapılacak, ama Qiskit dışına çıkmak **anayasa değişikliği**
gerektirir ve `plan.md` Complexity Tracking'de gerekçelendirilmelidir.

**Not 4 — Problem boyutu donanımdan türetildi (yeni bulgu).**
"5 durak" sayısının `(N−1)² = 16 kübit` aritmetiğinden geldiği ve Anayasa Prensip III tavanına
**birebir** oturduğu bu spec sırasında doğrulandı. 6 durak 25 kübit ister ve tavanı %56 aşar.
[memory-budget.md](../../../docs/memory-budget.md) bulgusuyla birleşince: Faz 1'in referansı,
Faz 2'nin **en zor** konfigürasyonunu hedefliyor.

**Not 5 — Doğrulanması gereken varsayım.**
Matris servisi için hedef üst sınır 30 durak olarak alındı (prompt'un araştırma kriterinden
türetildi, kullanıcı açıkça belirtmedi). Faz 10'un klasik kıyası daha büyük bir ölçek isterse
bu güncellenmelidir.

**Sonuç**: 16/16 madde geçti (3'ü gerekçeli koşullu). Spec `/speckit-plan` için hazır.
Plan aşaması **araştırma + karşılaştırma tabloları + onay kapısı** ile başlamalıdır.
