# Specification Quality Checklist: Faz 2 — FPGA Statevector Hızlandırıcı Çekirdeği

**Purpose**: Validate specification completeness and quality before proceeding to planning
**Created**: 2026-09-13
**Feature**: [spec.md](../spec.md)

## Content Quality

- [x] No implementation details (languages, frameworks, APIs) — *koşullu, bkz. Not 1*
- [x] Focused on user value and business needs
- [x] Written for non-technical stakeholders — *koşullu, bkz. Not 1*
- [x] All mandatory sections completed

## Requirement Completeness

- [x] No [NEEDS CLARIFICATION] markers remain
- [x] Requirements are testable and unambiguous
- [x] Success criteria are measurable
- [x] Success criteria are technology-agnostic (no implementation details) — *koşullu, bkz. Not 1*
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

**Not 1 — Donanım terimleri kaçınılmaz ve kısıt statüsünde.**
"BRAM", "II (initiation interval)", "kübit", "statevector", "bankalama" terimleri geçiyor. Bunlar
seçilmiş teknolojiler değil, **problemin ve Anayasa'nın dili**: Prensip III doğrudan BRAM bütçesini,
Prensip IV doğrulama zorunluluğunu sabitliyor. Bu terimlerden arındırmak ölçütleri **ölçülemez**
hale getirirdi (örn. "BRAM ≤ %85" yerine "yeterince az bellek kullanır" denemez).

**Not 2 — Bankalama ve format seçimi bilinçli olarak BOŞ.**
Prompt'un çalışma kuralı (ARAŞTIR → KIYASLA → ONAY BEKLE → KODLA) ve Anayasa Prensip I gereği
seçim `/speckit-plan` işidir. Gereksinimler yetenek düzeyinde yazıldı (FR-004 "çip-içi kalmalı",
FR-016 "iç genlik dizisine erişim") — hangi şemanın bunu sağladığı plan aşamasında karara bağlanır.

**Not 3 — Spec sırasında çıkan bulgu: iki tablo bağımsız değil.**
Prompt (A) bankalama ve (B) format için iki ayrı tablo istiyor. [memory-budget.md](../../../docs/memory-budget.md)
aritmetiği bunların **bağlı** olduğunu gösteriyor: 16 kübitte ping-pong'a yalnızca Q1.15 ile para
yetiyor, yani "kolay bankalama" ile "iyi doğruluk" aynı anda seçilemiyor. Tablolar ayrı doldurulup
sonra birleştirilemez; **kombinasyon olarak** değerlendirilmelidir. Bu `/speckit-plan` için bağlayıcı
bir kısıt olarak spec'e yazıldı.

**Not 4 — NFR-02 ile genlik kıyası arasındaki görünür çelişki çözüldü.**
Prompt dağıtım arayüzünün yalnızca skaler döndürmesini istiyor; Faz 1 ise genlik-genlik kıyası için
tam vektör üretti. Çelişki değil: **iki ayrı yüzey** var (dağıtım IP'si vs. doğrulama testbench'i).
FR-015 ve FR-016 bunu ayrı ayrı yazıyor ki ileride "genlik kıyası imkânsız" yanılgısı doğmasın.

**Not 5 — Bu spec'in ölçütlerinin bir kısmı şu an DOĞRULANAMAZ.**
Vitis HLS kurulu değil ([SK-04](../../../docs/risk-register.md)). SC-002, SC-003, SC-005 sentez
gerektiriyor. Bu bir spec kusuru değil, ortamın mevcut durumu — spec'te "yapılabilir / yapılamaz"
tablosu olarak açıkça yazıldı. Anayasa Prensip V gereği **duracak iş yok**, sadece henüz
doğrulanamayacak ölçüt var.

**Sonuç**: 16/16 madde geçti (4'ü gerekçeli koşullu). Spec `/speckit-plan` için hazır —
ancak plan aşamasının sentez ölçümleri Vitis HLS kurulumunu bekler.
