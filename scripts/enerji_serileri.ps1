<#
.SYNOPSIS
    6B / T068 - GPU tabani enerji protokolu v1.0: dort seri (E1..E4), batarya delta.

.DESCRIPTION
    docs/measurements/gpu-enerji-protokolu.md (kilitli surum). Her seri:
      [bos: 180 sn kayit, is yuku YOK] -> [yuk: 180 sn kayit + is yuku]
    Kaydedici Windows'ta (scripts/battery_logger.ps1, DEGISMEZ), is yuku WSL'de.
    Sira SABIT: E1 Aer CPU, E2 Aer GPU, E3 ayni algoritma GPU FP32,
    E4 ayni algoritma CPU float (tek is parcacigi). p=2, Aer T=4.

    Bir seri gecersiz/hatali biterse sonrakiler KOSMAZ (protokol 6).

    ON KOSUL: dizustu FISTEN CIKIK, batarya >= %80, kod commit'lenmis,
    harici monitor yok. Sure ~26 dk. DOKUNMA.

.EXAMPLE
    powershell -ExecutionPolicy Bypass -File scripts\enerji_serileri.ps1
    # akis sinamasi (fis takiliyken): sahte kaydedici, kisa sureler, cikti repo DISINA
    powershell -ExecutionPolicy Bypass -File scripts\enerji_serileri.ps1 -Deneme
#>
param([switch]$Deneme)
$ErrorActionPreference = 'Stop'
$KOK = Split-Path -Parent $PSScriptRoot
Set-Location $KOK
$PROTOKOL = 'gpu-enerji-protokolu v1.0'
$KAYIT_S = 180
$YUK_S = 170; $YUK_BENCH_S = 175       # protokol 5
$WSL_KOK = '/mnt/c/Users/olcay/IdeaProjects/qir-engine'
$PY = '/root/qir-gpu-venv/bin/python'
$BENCH = '/tmp/bench_float_enerji'
$REF = 'docs/measurements/reference_20260915_c6ad872_p2_n5'
$BEKLENEN_BD = '-3950.989990234'      # CPU float modelinin p=2 ciktisi (T065b)
$OLCUM = Join-Path $KOK 'docs\measurements'
$WSL_CIKTI = ''
if ($Deneme) {
    # OLCUM DEGIL: yalniz akisi sinar. Kaydedici yerine sahte veri, cikti repo disina.
    $KAYIT_S = 12; $YUK_S = 6; $YUK_BENCH_S = 8
    $OLCUM = Join-Path $env:LOCALAPPDATA 'Temp\qir-enerji-deneme'
    New-Item -ItemType Directory -Force $OLCUM | Out-Null
    $WSL_CIKTI = ' --cikti-dizini /mnt/c/Users/olcay/AppData/Local/Temp/qir-enerji-deneme'
    Write-Host '*** DENEME KIPI - OLCUM DEGIL ***' -ForegroundColor Yellow
}

function Batarya {
    $b = Get-CimInstance -Namespace root\wmi -ClassName BatteryStatus | Select-Object -First 1
    $f = Get-CimInstance -Namespace root\wmi -ClassName BatteryFullChargedCapacity | Select-Object -First 1
    [pscustomobject]@{
        KalanMwh = [int]$b.RemainingCapacity
        Yuzde    = [math]::Round(100.0 * $b.RemainingCapacity / $f.FullChargedCapacity, 1)
        Prizde   = [bool]$b.PowerOnline
    }
}

function Kosullar([string]$seri) {
    $b = Batarya
    $parlaklik = $null
    try { $parlaklik = (Get-CimInstance -Namespace root\WMI -ClassName WmiMonitorBrightness -ErrorAction Stop | Select-Object -First 1).CurrentBrightness } catch {}
    $dc = (reg query 'HKLM\SYSTEM\CurrentControlSet\Control\Power\User\PowerSchemes' /v ActiveOverlayDcPowerScheme | Select-String 'REG_SZ') -replace '.*REG_SZ\s+', ''
    [ordered]@{
        seri = $seri; zaman = (Get-Date).ToString('o'); deneme = [bool]$Deneme
        batarya_mwh = $b.KalanMwh; batarya_yuzde = $b.Yuzde; prizde = $b.Prizde
        ekran_parlaklik = $parlaklik; guc_modu_dc_overlay = "$dc".Trim()
        ekran_uyku_engeli = [bool]($uyanik -and -not $uyanik.HasExited)
    }
}

function WslKos([string]$komut) {
    # GIT_CONFIG_*: WSL git'i Windows checkout'unu (CRLF) dogru gorsun.
    # Out-Host: cikti fonksiyonun donus degerine karismasin, yalniz cikis kodu donsun.
    & wsl -d Ubuntu -u root --cd $WSL_KOK -e env GIT_CONFIG_COUNT=1 GIT_CONFIG_KEY_0=core.autocrlf GIT_CONFIG_VALUE_0=true bash -c $komut | Out-Host
    return $LASTEXITCODE
}

function SahteKayit([int]$sn, [string]$csv, [int]$mw, [int]$kalan) {
    # YALNIZ -Deneme: kaydedicinin CSV bicimi, sabit guc. OLCUM DEGIL.
    $t0 = Get-Date
    $satirlar = foreach ($i in 0..($sn - 1)) {
        [pscustomobject]@{ Zaman = $t0.AddSeconds($i).ToString('o'); DesarjMw = $mw; SarjMw = 0
                           KalanMwh = $kalan - [int]($i * $mw / 3600); GerilimMv = 15000
                           PrizdeMi = $false; DesarjEdiyor = $true }
    }
    $satirlar | Export-Csv -Path $csv -NoTypeInformation -Encoding utf8
}

# --- on kosullar -------------------------------------------------------------
if (-not $Deneme) {
    $kirli = git status --porcelain | Where-Object { $_ -notmatch '^\?\? "?docs/measurements/' }
    if ($kirli) { Write-Host "HATA: commit'lenmemis kod var (protokol 4)" -ForegroundColor Red; exit 1 }
    $b0 = Batarya
    if ($b0.Prizde) { Write-Host 'HATA: dizustu PRIZE TAKILI - adaptoru cikar.' -ForegroundColor Red; exit 1 }
    if ($b0.Yuzde -lt 80) { Write-Host ("HATA: batarya %{0} < %80 (protokol 4)" -f $b0.Yuzde) -ForegroundColor Red; exit 1 }
}


# --- ekran acik, uyku yok -----------------------------------------------------
# 3 Eki on denetim: bu planda pilde ekran 180 sn sonra kapanir ve makine 180 sn
# sonra uyur; olcum 26 dk dokunulmadan surer. SetThreadExecutionState
# (ES_CONTINUOUS|ES_SYSTEM_REQUIRED|ES_DISPLAY_REQUIRED) ile engellenir: KALICI
# ayar degismez, istek onu tutan surec bitince kalkar (finally). Bos ve yuk
# pencerelerinde ayni durum -> delta'da sadelesir.
$UYANIK_PY = 'import ctypes,sys,time; r=ctypes.windll.kernel32.SetThreadExecutionState(0x80000003); print(r, flush=True); time.sleep(7200) if r else sys.exit(1)'
$uyanik = Start-Process -FilePath (Join-Path $KOK '.venv\Scripts\python.exe') -ArgumentList '-c', "`"$UYANIK_PY`"" `
    -WindowStyle Hidden -PassThru -RedirectStandardOutput (Join-Path $env:TEMP 'qir-enerji-uyanik.txt')
Start-Sleep -Seconds 3
if ($uyanik.HasExited) { Write-Host 'HATA: ekran/uyku engeli kurulamadi' -ForegroundColor Red; exit 1 }

try {
    $GIT = (git rev-parse --short HEAD).Trim()
    $TARIH = (Get-Date).ToUniversalTime().ToString('yyyyMMdd')     # stamp.stamped_name ile ayni (UTC)
    Write-Host "=== $PROTOKOL basladi $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss'), git $GIT, batarya %$((Batarya).Yuzde)"

    if ((WslKos "g++ -std=c++17 -O3 -DQIR_NO_VITIS -DQIR_N_QUBITS=16 -DQIR_REAL_FLOAT -Ihls/src -Ihls/tb hls/tb/bench_kernel.cpp hls/src/qir_kernel.cpp -o $BENCH") -ne 0) {
        Write-Host 'HATA: bench_kernel derlenemedi' -ForegroundColor Red; exit 1
    }

    $SERILER = @(
        @{ ad = 'E1'; komut = "$PY scripts/cpu_load_loop.py --device CPU --p 2 --saniye $YUK_S --is-parcacigi 4 --etiket enerjiE1$WSL_CIKTI"; desen = "cpu-yuk-dongu_*_$($GIT)_enerjiE1_p2.json" },
        @{ ad = 'E2'; komut = "$PY scripts/cpu_load_loop.py --device GPU --p 2 --saniye $YUK_S --is-parcacigi 4 --etiket enerjiE2$WSL_CIKTI"; desen = "gpu-yuk-dongu_*_$($GIT)_enerjiE2_p2.json" },
        @{ ad = 'E3'; komut = "$PY scripts/gpu_ayni_algoritma.py --hassasiyet 32 --p 2 --saniye $YUK_S --etiket enerjiE3$WSL_CIKTI"; desen = "gpu-ayni-algoritma_*_$($GIT)_enerjiE3_fp32_p2.json" },
        @{ ad = 'E4'; komut = "$BENCH --reference $REF --saniye $YUK_BENCH_S --isinma 1"; desen = $null }
    )
    $kosullar = New-Object System.Collections.Generic.List[object]
    $kosullarYol = Join-Path $OLCUM "enerji-kosullar_$($TARIH)_$($GIT).json"

    foreach ($s in $SERILER) {
        $ad = $s.ad
        if (-not $Deneme) {
            $b = Batarya
            if ($b.Prizde) { Write-Host "HATA: $ad basinda prize takili" -ForegroundColor Red; exit 1 }
            if ($b.Yuzde -lt 30) { Write-Host ("HATA: $ad basinda batarya %{0} < %30 - DURDU" -f $b.Yuzde) -ForegroundColor Red; exit 1 }
        }
        $kosullar.Add((Kosullar $ad))
        ($kosullar | ConvertTo-Json -Depth 4) | Out-File -Encoding utf8 $kosullarYol

        $bosCsv = Join-Path $OLCUM "batarya-bos_$($TARIH)_$($GIT)_$ad.csv"
        $yukCsv = Join-Path $OLCUM "batarya-yuk_$($TARIH)_$($GIT)_$ad.csv"

        Write-Host "=== $ad BOS kayit $KAYIT_S sn ($(Get-Date -Format HH:mm:ss))"
        if ($Deneme) {
            SahteKayit $KAYIT_S $bosCsv 20000 30000
        } else {
            & powershell -NoProfile -ExecutionPolicy Bypass -File scripts\battery_logger.ps1 -Saniye $KAYIT_S -Cikti $bosCsv
            if ($LASTEXITCODE -ne 0) { Write-Host "HATA: $ad bos kayit" -ForegroundColor Red; exit 1 }
        }

        Write-Host "=== $ad YUK kayit $KAYIT_S sn + is yuku ($(Get-Date -Format HH:mm:ss))"
        $job = Start-Job -ScriptBlock {
            param($kok, $csv, $sn, $deneme)
            Set-Location $kok
            if ($deneme) {
                # YALNIZ -Deneme: sahte kayit (OLCUM DEGIL), gercek kaydedici kadar surer
                $t0 = Get-Date
                $satirlar = foreach ($i in 0..($sn - 1)) {
                    [pscustomobject]@{ Zaman = $t0.AddSeconds($i).ToString('o'); DesarjMw = 30000; SarjMw = 0
                                       KalanMwh = 29000 - [int]($i * 30000 / 3600); GerilimMv = 15000
                                       PrizdeMi = $false; DesarjEdiyor = $true }
                }
                Start-Sleep -Seconds $sn
                $satirlar | Export-Csv -Path $csv -NoTypeInformation -Encoding utf8
                0
            } else {
                & powershell -NoProfile -ExecutionPolicy Bypass -File scripts\battery_logger.ps1 -Saniye $sn -Cikti $csv
                $LASTEXITCODE
            }
        } -ArgumentList $KOK, $yukCsv, $KAYIT_S, [bool]$Deneme

        if ($ad -eq 'E4') {
            $cikti = & wsl -d Ubuntu -u root --cd $WSL_KOK -e bash -c $s.komut
            $kod = $LASTEXITCODE
            $cikti | Out-File -Encoding utf8 (Join-Path $OLCUM "bench-enerji_$($TARIH)_$($GIT)_E4.txt")
        } else {
            $kod = WslKos $s.komut
        }
        $jobKod = Receive-Job -Job (Wait-Job $job) | Select-Object -Last 1
        Remove-Job $job
        if ($kod -ne 0) { Write-Host "HATA: $ad is yuku basarisiz/gecersiz (kod $kod) - DURDU" -ForegroundColor Red; exit 1 }
        if ($jobKod -ne 0) { Write-Host "HATA: $ad yuk kaydi basarisiz (kod $jobKod) - DURDU" -ForegroundColor Red; exit 1 }

        # kosum sayisi ve is yuku dogrulamasi
        if ($ad -eq 'E4') {
            $N = [int](($cikti | Select-String 'kosum_sayisi') -replace '.*:\s*(\d+).*', '$1')
            $bd = ($cikti | Select-String 'beklenen_deger') -replace '.*:\s*(\S+).*', '$1'
            if ($bd -ne $BEKLENEN_BD) { Write-Host "HATA: E4 beklenen_deger $bd != $BEKLENEN_BD - GECERSIZ" -ForegroundColor Red; exit 1 }
            $isYuku = "bench-enerji_$($TARIH)_$($GIT)_E4.txt"
        } else {
            $js = Get-ChildItem $OLCUM -Filter $s.desen | Sort-Object LastWriteTime | Select-Object -Last 1
            if (-not $js) { Write-Host "HATA: $ad is yuku kaydi yok" -ForegroundColor Red; exit 1 }
            $d = Get-Content $js.FullName -Raw -Encoding UTF8 | ConvertFrom-Json
            if (-not $d.gecerli) { Write-Host "HATA: $ad is yuku GECERSIZ" -ForegroundColor Red; exit 1 }
            $N = [int]$d.zamanlanan_kosum
            $isYuku = $js.Name
        }

        & (Join-Path $KOK '.venv\Scripts\python.exe') scripts\battery_energy.py --bos $bosCsv --yuk $yukCsv --kosum $N `
            --git-hash $GIT --ad "enerji-batarya_$($TARIH)_$($GIT)_$ad" --protokol $PROTOKOL --is-yuku $isYuku `
            --cikti-dizini $OLCUM
        if ($LASTEXITCODE -ne 0) {
            # protokol 6: A/B > %10 -> guvenilmez (raporlanir), P_yuk <= P_bos -> gecersiz. Uyari JSON'da.
            Write-Host "UYARI: $ad enerji hesabi uyari verdi - JSON'daki 'uyarilar' alanina bak" -ForegroundColor Yellow
        }
        Write-Host "=== $ad bitti ($(Get-Date -Format HH:mm:ss)), N=$N"
    }
    $kosullar.Add((Kosullar 'SON'))
    ($kosullar | ConvertTo-Json -Depth 4) | Out-File -Encoding utf8 $kosullarYol
    Write-Host "=== HEPSI BITTI $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')"
} finally {
    Stop-Process -Id $uyanik.Id -Force -ErrorAction SilentlyContinue
}
