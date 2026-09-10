<!--
Sync Impact Report
Version change: [TEMPLATE] → 1.0.0
Modified principles: N/A (initial ratification)
Added sections: Core Principles (6), Governance
Removed sections: none
Templates requiring updates: plan-template.md (⚠ pending manual review for Complexity Tracking gate), spec-template.md (✅ no changes needed), tasks-template.md (✅ no changes needed)
Follow-up TODOs: none
-->

# Kuantum-Esinli Rota Optimizasyon Motoru Constitution

## Core Principles

### I. Onay Kapısı (Pazarlıksız)
Hiçbir teknoloji, kütüphane veya mimari karar, karşılaştırmalı analiz raporu sunulup kullanıcı
açıkça onaylamadan koda dökülemez. Her /speckit-plan aşaması, ilgili karar noktalarında en az
iki alternatifi karşılaştıran bir tablo üretmeden implementasyona geçemez. Rationale: 14 haftalık
tek geliştirici kapasitesinde geri dönüşü pahalı hatalar, erken ve gerekçeli onay disipliniyle
önlenir.

### II. Ölçüm Dürüstlüğü
Enerji ve gecikme rakamları gerçek ölçüme (INA219 shunt, donanım sayaçları) dayanmalıdır;
tahmini veya simüle edilmiş değerler nihai rapora yazılamaz. "Kuantum üstünlüğü" iddiası
yasaktır; kullanılabilecek tek iddia "kuantum-esinli hızlandırma"dır. Rationale: Bilimsel
dürüstlük ve savunulabilir sonuçlar, bitirme projesinin akademik geçerliliği için zorunludur.

### III. Donanım Bütçesi Önce
Statevector çip-içi bellekte (BRAM/URAM) kalmalıdır, DDR'a taşamaz. Üst sınır 16 qubit'tir.
Her tasarım kararı, uygulanmadan önce bellek bütçesine karşı doğrulanmalıdır. Rationale: PYNQ-Z2
üzerindeki sınırlı çip-içi bellek, mimari kapsamın gerçekçi kalmasını zorunlu kılar.

### IV. Altın Referans
Her hızlandırıcı çıktısı, Qiskit referans simülasyonuna karşı doğrulanmadan "çalışıyor" olarak
kabul edilemez. Rationale: Donanım hızlandırmasının doğruluğu, bağımsız ve güvenilir bir
referansla karşılaştırma olmadan iddia edilemez.

### V. Donanımsız Süreklilik
Kart gecikse veya erişilemez olsa dahi geliştirme, HLS C-simülasyonu/cosim ve mock arayüzlerle
sürebilmelidir; fiziksel donanıma erişim hiçbir modülün derlenmesi için ön koşul olamaz.
Rationale: Tek donanım biriminin (PYNQ-Z2) kullanılamadığı dönemlerde proje takviminin
durmaması gerekir.

### VI. 14 Hafta Kısıtı
Her öneri, kalan takvim ve tek geliştirici kapasitesi bağlamında değerlendirilmelidir. Kapsam
her zaman M (çekirdek) / H (hedef) / İ (iddialı) olarak etiketlenir. Rationale: Kapsam
etiketlemesi olmadan tek geliştiricilik ve sabit teslim tarihi çatışması proje sonunda
keşfedilir; erken etiketleme riski öne çeker.

## Kısıtlar ve Kapsam

Proje donanımı: PYNQ-Z2 (Xilinx Zynq-7000). Geliştirme ortamı bu bilgisayar üzerinde yürütülür;
kart henüz fiziksel olarak bağlı değildir, bu nedenle Prensip V (Donanımsız Süreklilik) proje
başlangıcından itibaren aktif olarak uygulanır. Yazılım tarafı Python (PYNQ, Qiskit, ölçüm/analiz
araçları) ve C/C++ (HLS çekirdekleri, cosim) dillerini kapsar.

## Geliştirme İş Akışı

Her faz kendi `specs/00X-.../` klasörüne yazılır; `spec.md`, `plan.md` ve `tasks.md` o fazın
kalıcı hafızasıdır. `/speckit-plan` aşamasında Prensip I–VI otomatik olarak denetlenir; bir
ilke ihlal edilecekse bu yalnızca `plan.md` içindeki Complexity Tracking tablosunda açıkça
gerekçelendirilerek yapılabilir.

## Governance

Bu anayasa, projenin tüm fazlarını bağlar ve diğer tüm pratiklerin üzerindedir. Değişiklik
(amendment), yeni bir versiyon numarası ile bu dosyanın güncellenmesini ve Sync Impact
Report'un üst kısma eklenmesini gerektirir. Versiyonlama semantik kurallara tabidir: ilke
kaldırma/yeniden tanımlama MAJOR, yeni ilke/bölüm ekleme MINOR, ifade/açıklık düzeltmeleri
PATCH sayılır. Her `/speckit-plan` çalıştırması, üretilen planın bu anayasadaki altı ilkeyle
uyumlu olduğunu doğrulamalıdır; uyumsuzluklar Complexity Tracking tablosunda gerekçelendirilmeden
implementasyona geçilemez.

**Version**: 1.0.0 | **Ratified**: 2026-09-10 | **Last Amended**: 2026-09-10
