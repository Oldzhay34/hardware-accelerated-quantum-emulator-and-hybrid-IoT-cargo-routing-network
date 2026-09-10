# Specification Quality Checklist: Faz 0 — Kapsam Triyajı, Takvim ve Kesme Planı

**Purpose**: Validate specification completeness and quality before proceeding to planning
**Created**: 2026-09-10
**Feature**: [spec.md](../spec.md)

## Content Quality

- [x] No implementation details (languages, frameworks, APIs) — *koşullu geçti, bkz. Not 1*
- [x] Focused on user value and business needs
- [x] Written for non-technical stakeholders — *koşullu geçti, bkz. Not 1*
- [x] All mandatory sections completed

## Requirement Completeness

- [x] No [NEEDS CLARIFICATION] markers remain
- [x] Requirements are testable and unambiguous
- [x] Success criteria are measurable
- [x] Success criteria are technology-agnostic (no implementation details) — *koşullu geçti, bkz. Not 1*
- [x] All acceptance scenarios are defined
- [x] Edge cases are identified
- [x] Scope is clearly bounded
- [x] Dependencies and assumptions identified

## Feature Readiness

- [x] All functional requirements have clear acceptance criteria
- [x] User scenarios cover primary flows
- [x] Feature meets measurable outcomes defined in Success Criteria
- [x] No implementation details leak into specification — *koşullu geçti, bkz. Not 1*

## Notes

**Not 1 — "Teknolojiden bağımsızlık" maddelerinin koşullu geçmesi (bilinçli sapma).**
Spec içinde BRAM, HLS, FPGA, Qiskit, INA219 gibi terimler geçiyor. Normalde bunlar bir spec'te implementasyon sızıntısı sayılır. Burada sayılmıyorlar çünkü **projenin kendisi bir donanım tasarım problemidir** ve bu terimler proje anayasasında (Prensip II, III, IV) *kısıt* olarak sabitlenmiştir — spec'in seçtiği teknolojiler değil, spec'in içinde çalıştığı verilerdir. BRAM sınırını spec'ten çıkarmak, ölçütleri ölçülemez hale getirirdi. Bu sapma bilinçlidir ve `/speckit-plan` aşamasında yeniden gözden geçirilmesi gerekmez.

**Not 2 — Bu faz kod üretmez.**
Çıktı üç karar belgesidir. `/speckit-plan` bu spec için çalıştırılırsa, üreteceği plan bir *uygulama planı* değil, belgelerin **onaylanması ve sonraki fazlara uygulanması** planı olmalıdır.

**Not 3 — Onay bekleniyor.**
Anayasa Prensip I gereği belgeler kullanıcı onaylamadan bağlayıcı değildir. Onaydan önce `/speckit-plan`'a geçilmemelidir.

**Not 4 — Doğrulanması gereken varsayımlar.**
`spec.md` → Assumptions bölümündeki şu üç madde kullanıcı tarafından teyit edilmeli: (a) düşük kapasite haftalarının ≈%40 oranı, (b) 29 Ekim dışında resmi tatil olmadığı, (c) deponun private olacağı. Yanlışsa takvim ve 0.3 etiketi güncellenir.

**Sonuç**: 16/16 madde geçti (4'ü koşullu, gerekçeleri yukarıda). Spec `/speckit-plan` için hazır — **ancak kullanıcı onayı sonrası**.
