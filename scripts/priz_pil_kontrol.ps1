<#
.SYNOPSIS
    6B ek kontrol - prizde/pilde gecikme farki (priz-pil-kontrol-protokolu v1.0).

.DESCRIPTION
    docs/measurements/priz-pil-kontrol-protokolu.md. Dort blok ABAB:
      AC1 -> (fisi cek) -> DC1 -> (fisi tak) -> AC2 -> (fisi cek) -> DC2
    Her blok: istenen guc durumu beklenir, 180 sn bekleme,
      G: gpu_ayni_algoritma FP32 p=2, 300 sn (T067 G32-2 ile ayni)
      K: bench_kernel float tek is parcacigi, 120 sn
    KULLANICI CALISTIRIR: betik fisi takmasini/cekmesini bip ve mesajla ister.
    Klavye/fare kullanilmaz. Sure ~45 dk. Bir blok gecersizse olcum durur.

.EXAMPLE
    powershell -ExecutionPolicy Bypass -File scripts\priz_pil_kontrol.ps1
    # akis sinamasi: kisa sureler, fis beklenmez, cikti repo DISINA
    powershell -ExecutionPolicy Bypass -File scripts\priz_pil_kontrol.ps1 -Deneme
#>
param([switch]$Deneme)
$ErrorActionPreference = 'Stop'
$KOK = Split-Path -Parent $PSScriptRoot
Set-Location $KOK
$PROTOKOL = 'priz-pil-kontrol-protokolu v1.0'
$G_S = 300; $K_S = 120; $BEKLE_S = 180          # protokol 3
$WSL_KOK = '/mnt/c/Users/olcay/IdeaProjects/qir-engine'
$PY = '/root/qir-gpu-venv/bin/python'
$BENCH = '/root/bench_float_kontrol'
$REF = 'docs/measurements/reference_20260915_c6ad872_p2_n5'
$BEKLENEN_BD = '-3950.989990234'                # CPU float modelinin p=2 ciktisi (T065b)
$OLCUM = Join-Path $KOK 'docs\measurements'
$WSL_CIKTI = ''
$BLOKLAR = @(@{ ad = 'AC1'; priz = $true }, @{ ad = 'DC1'; priz = $false },
             @{ ad = 'AC2'; priz = $true }, @{ ad = 'DC2'; priz = $false })
if ($Deneme) {
    # OLCUM DEGIL: yalniz akisi sinar. Fis durumu beklenmez, cikti repo disina.
    $G_S = 8; $K_S = 5; $BEKLE_S = 2
    $OLCUM = Join-Path $env:LOCALAPPDATA 'Temp\qir-kontrol-deneme'
    New-Item -ItemType Directory -Force $OLCUM | Out-Null
    $WSL_CIKTI = ' --cikti-dizini /mnt/c/Users/olcay/AppData/Local/Temp/qir-kontrol-deneme'
    Write-Host '*** DENEME KIPI - OLCUM DEGIL (fis durumu beklenmez) ***' -ForegroundColor Yellow
}

function Batarya {
    $b = Get-CimInstance -Namespace root\wmi -ClassName BatteryStatus | Select-Object -First 1
    $f = Get-CimInstance -Namespace root\wmi -ClassName BatteryFullChargedCapacity | Select-Object -First 1
    [pscustomobject]@{
        Yuzde  = [math]::Round(100.0 * $b.RemainingCapacity / $f.FullChargedCapacity, 1)
        Prizde = [bool]$b.PowerOnline
    }
}

function Durum([string]$blok, [string]$an) {
    $b = Batarya
    [ordered]@{
        blok = $blok; an = $an; zaman = (Get-Date).ToString('o'); deneme = [bool]$Deneme
        prizde = $b.Prizde; batarya_yuzde = $b.Yuzde
        ekran_uyku_engeli = [bool]($uyanik -and -not $uyanik.HasExited)
        wsl_acik = [bool]($wslAcik -and -not $wslAcik.HasExited)
    }
}

function WslKos([string]$komut) {
    # enerji_serileri.ps1 ile ayni: GIT_CONFIG_* (CRLF), Out-Host (yalniz cikis kodu doner)
    & wsl -d Ubuntu -u root --cd $WSL_KOK -e env GIT_CONFIG_COUNT=1 GIT_CONFIG_KEY_0=core.autocrlf GIT_CONFIG_VALUE_0=true bash -c $komut | Out-Host
    return $LASTEXITCODE
}

function FisBekle([bool]$priz, [string]$ad) {
    if ($Deneme) { return }
    $ne = if ($priz) { 'FISI TAK' } else { 'FISI CEK' }
    $i = 0
    while ((Batarya).Prizde -ne $priz) {
        if ($i % 15 -eq 0) {
            Write-Host ">>> $ad icin $ne  (bekleniyor, $(Get-Date -Format HH:mm:ss))" -ForegroundColor Cyan
            [console]::Beep(880, 400); [console]::Beep(660, 400)
        }
        $i++
        Start-Sleep -Seconds 2
    }
    Write-Host ">>> $ad guc durumu tamam: prizde=$priz ($(Get-Date -Format HH:mm:ss)) - DOKUNMA" -ForegroundColor Green
}

# --- on kosullar -------------------------------------------------------------
if (-not $Deneme) {
    $kirli = git status --porcelain | Where-Object { $_ -notmatch '^\?\? "?docs/measurements/' }
    if ($kirli) { Write-Host "HATA: commit'lenmemis kod var" -ForegroundColor Red; exit 1 }
}

# --- ekran acik, uyku yok; WSL acik (enerji_serileri.ps1 v1.1 ile ayni duzenek)
# Bu planda prizde de ekran 180 sn sonra kapanir, makine 180 sn sonra uyur.
$UYANIK_PY = 'import ctypes,sys,time; r=ctypes.windll.kernel32.SetThreadExecutionState(0x80000003); print(r, flush=True); time.sleep(7200) if r else sys.exit(1)'
$uyanik = Start-Process -FilePath (Join-Path $KOK '.venv\Scripts\python.exe') -ArgumentList '-c', "`"$UYANIK_PY`"" `
    -WindowStyle Hidden -PassThru -RedirectStandardOutput (Join-Path $env:TEMP 'qir-kontrol-uyanik.txt')
Start-Sleep -Seconds 3
if ($uyanik.HasExited) { Write-Host 'HATA: ekran/uyku engeli kurulamadi' -ForegroundColor Red; exit 1 }
$WSL_PID = '/run/qir-kontrol-wsl-acik.pid'
$wslAcik = Start-Process -FilePath 'wsl.exe' -WindowStyle Hidden -PassThru `
    -ArgumentList '-d', 'Ubuntu', '-u', 'root', '-e', 'bash', '-c', "`"echo `$`$ > $WSL_PID; exec sleep 7200`""
Start-Sleep -Seconds 8
if ($wslAcik.HasExited) {
    Stop-Process -Id $uyanik.Id -Force -ErrorAction SilentlyContinue
    Write-Host 'HATA: WSL acik tutulamadi' -ForegroundColor Red; exit 1
}

try {
    $GIT = (git rev-parse --short HEAD).Trim()
    $TARIH = (Get-Date).ToUniversalTime().ToString('yyyyMMdd')     # stamp.stamped_name ile ayni (UTC)
    Write-Host "=== $PROTOKOL basladi $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss'), git $GIT, batarya %$((Batarya).Yuzde)"

    if ((WslKos "g++ -std=c++17 -O3 -DQIR_NO_VITIS -DQIR_N_QUBITS=16 -DQIR_REAL_FLOAT -Ihls/src -Ihls/tb hls/tb/bench_kernel.cpp hls/src/qir_kernel.cpp -o $BENCH") -ne 0) {
        Write-Host 'HATA: bench_kernel derlenemedi' -ForegroundColor Red; exit 1
    }

    $durumlar = New-Object System.Collections.Generic.List[object]
    $durumYol = Join-Path $OLCUM "priz-pil-kontrol-kosullar_$($TARIH)_$($GIT).json"

    foreach ($blk in $BLOKLAR) {
        $ad = $blk.ad; $priz = $blk.priz
        FisBekle $priz $ad
        if (-not $Deneme -and -not $priz -and (Batarya).Yuzde -lt 30) {
            Write-Host "HATA: $ad basinda batarya < %30 - DURDU" -ForegroundColor Red; exit 1
        }
        $durumlar.Add((Durum $ad 'bas'))
        ($durumlar | ConvertTo-Json -Depth 4) | Out-File -Encoding utf8 $durumYol

        Write-Host "=== $ad bekleme $BEKLE_S sn ($(Get-Date -Format HH:mm:ss))"
        Start-Sleep -Seconds $BEKLE_S

        Write-Host "=== $ad G: GPU ayni algoritma FP32 p=2, $G_S sn ($(Get-Date -Format HH:mm:ss))"
        if ((WslKos "$PY scripts/gpu_ayni_algoritma.py --hassasiyet 32 --p 2 --saniye $G_S --etiket kontrol$ad$WSL_CIKTI") -ne 0) {
            Write-Host "HATA: $ad G basarisiz/gecersiz - DURDU" -ForegroundColor Red; exit 1
        }

        Write-Host "=== $ad K: bench_kernel float tek is parcacigi, $K_S sn ($(Get-Date -Format HH:mm:ss))"
        $cikti = & wsl -d Ubuntu -u root --cd $WSL_KOK -e bash -c "$BENCH --reference $REF --saniye $K_S --isinma 3"
        $kod = $LASTEXITCODE
        $cikti | Out-File -Encoding utf8 (Join-Path $OLCUM "bench-kontrol_$($TARIH)_$($GIT)_$ad.txt")
        $bd = ($cikti | Select-String 'beklenen_deger') -replace '.*:\s*(\S+).*', '$1'
        if ($kod -ne 0 -or $bd -ne $BEKLENEN_BD) {
            Write-Host "HATA: $ad K gecersiz (kod $kod, beklenen_deger $bd) - DURDU" -ForegroundColor Red; exit 1
        }

        $son = Durum $ad 'son'
        $durumlar.Add($son)
        ($durumlar | ConvertTo-Json -Depth 4) | Out-File -Encoding utf8 $durumYol
        if (-not $Deneme -and $son.prizde -ne $priz) {
            Write-Host "HATA: $ad sirasinda guc durumu degisti - blok GECERSIZ, DURDU" -ForegroundColor Red; exit 1
        }
        Write-Host "=== $ad bitti ($(Get-Date -Format HH:mm:ss))"
    }

    $ozetArg = @('scripts\priz_pil_kontrol_ozet.py', '--dizin', $OLCUM, '--tarih', $TARIH, '--git', $GIT)
    if ($Deneme) { $ozetArg += '--deneme' }
    & (Join-Path $KOK '.venv\Scripts\python.exe') @ozetArg
    if ($LASTEXITCODE -ne 0) { Write-Host 'HATA: ozet yazilamadi' -ForegroundColor Red; exit 1 }
    Write-Host "=== HEPSI BITTI $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss') - fisi takabilirsin" -ForegroundColor Green
    [console]::Beep(660, 300); [console]::Beep(880, 300); [console]::Beep(1100, 500)
} finally {
    Stop-Process -Id $uyanik.Id -Force -ErrorAction SilentlyContinue
    & wsl -d Ubuntu -u root -e bash -c "kill `$(cat $WSL_PID 2>/dev/null) 2>/dev/null; rm -f $WSL_PID" | Out-Null
    Stop-Process -Id $wslAcik.Id -Force -ErrorAction SilentlyContinue
}
