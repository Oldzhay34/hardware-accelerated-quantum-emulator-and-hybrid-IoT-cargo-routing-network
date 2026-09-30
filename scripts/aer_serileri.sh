#!/usr/bin/env bash
# 6B / T067 — GPU tabanı protokolü v1.1 (🔒), katman 1.
# docs/measurements/gpu-taban-olcum-protokolu.md §6 ve §12:
#   Aşama 0 — Aer CPU iş parçacığı taraması (§12 Δ2): T sırası SABİT
#             6 16 1 10 2 8 4, her nokta 60 sn, aralarda 2 dk; ardından
#             ön kayıtlı kuralla T seçilir (scripts/aer_is_parcacigi_sec.py).
#   Aşama 1 — dört seri, seçilen T ile: A-CPU, A-GPU, B-CPU, B-GPU; her biri
#             300 sn, aralarda (ve taramadan sonra) ≥ 5 dk soğuma.
#
# Kullanım (WSL, temiz ağaçta; ~65 dk — makineye DOKUNMA, prizde):
#   nohup bash scripts/aer_serileri.sh > /root/aer-serileri.log 2>&1 &
#
# Bir nokta ya da seri geçersiz/hatalı biterse sonrakiler KOŞMAZ (§7, §12).
set -uo pipefail
# WSL git'i Windows checkout'unu doğru görsün: Windows tarafı core.autocrlf=true
# ile CRLF çıkarıyor; WSL git'inde bu ayar yok ve 84 dosyayı "değişmiş" sanıyordu
# (28 Eyl). Kalıcı config değil, yalnız bu süreç ağacı için ortamdan verilir.
export GIT_CONFIG_COUNT=1 GIT_CONFIG_KEY_0=core.autocrlf GIT_CONFIG_VALUE_0=true
KOK="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$KOK"
PY="${QIR_GPU_PY:-/root/qir-gpu-venv/bin/python}"
TARAMA_SIRASI=(6 16 1 10 2 8 4)
TARAMA_S=60
TARAMA_ARA_S=120
SOGUMA_S=300
SERILER=("A-CPU CPU 2" "A-GPU GPU 2" "B-CPU CPU 1" "B-GPU GPU 1")

# §4 / §12 Δ1: "temiz ağaç" = izlenen dosyalar; önceki çıktılar (izlenmeyen) sayılmaz
if [ -n "$(git status --porcelain --untracked-files=no)" ]; then
    echo "⛔ izlenen dosyalarda degisiklik var — protokol §4: seriler temiz agacta"; exit 1
fi
GIT="$(git rev-parse --short HEAD)"
# dosya adlarındaki tarih stamp.stamped_name ile aynı (UTC)
TARIH="$("$PY" -c "import sys; sys.path.insert(0, '.'); from services.common import stamp; print(stamp.stamped_name('x').split('_')[1])")"
echo "=== protokol v1.1 basladi $(date '+%F %T'), git $GIT, dosya tarihi $TARIH"

echo "=== ASAMA 0: is parcacigi taramasi (${TARAMA_SIRASI[*]})"
ilk=1
for T in "${TARAMA_SIRASI[@]}"; do
    if [ $ilk -eq 0 ]; then echo "--- ara ${TARAMA_ARA_S} sn"; sleep "$TARAMA_ARA_S"; fi
    ilk=0
    echo "=== tarama T=$T basladi $(date '+%T')"
    if ! "$PY" scripts/cpu_load_loop.py --device CPU --p 2 --saniye "$TARAMA_S" \
            --is-parcacigi "$T" --etiket "taramaT$T"; then
        echo "⛔ tarama T=$T basarisiz ya da gecersiz — tarama ve seriler DURDU ($(date '+%T'))"
        exit 1
    fi
done
if ! SECIM="$("$PY" scripts/aer_is_parcacigi_sec.py "$TARIH" "$GIT")"; then
    echo "$SECIM"; echo "⛔ T secimi yapilamadi — seriler KOSULMADI"; exit 1
fi
echo "$SECIM"
T_SECILEN="$(echo "$SECIM" | tail -1)"
echo "=== secilen T = $T_SECILEN"

echo "=== ASAMA 1: dort seri, T=$T_SECILEN"
for s in "${SERILER[@]}"; do
    read -r ad cihaz p <<< "$s"
    echo "--- soguma ${SOGUMA_S} sn ($(date '+%T'))"
    sleep "$SOGUMA_S"
    echo "=== $ad ($cihaz, p=$p, T=$T_SECILEN) basladi $(date '+%T')"
    if ! "$PY" scripts/cpu_load_loop.py --device "$cihaz" --p "$p" --saniye 300 \
            --is-parcacigi "$T_SECILEN" --etiket "seri${ad}-v11"; then
        echo "⛔ $ad basarisiz ya da gecersiz — sonraki seriler KOSULMADI ($(date '+%T'))"
        exit 1
    fi
    echo "=== $ad bitti $(date '+%T')"
done
echo "=== HEPSI BITTI $(date '+%F %T')"
