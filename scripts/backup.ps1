# Faz 0.5 — git deposunu (kod+specs+docs) iki farklı yere yedekler ve doğrular.
# Büyük ikili dosyalar (artifacts/) bu script'in kapsamı DIŞINDADIR — onlar git'te
# olmadığı için git bundle onları içermez; ayrı elle/otomatik kopya gerekir (bkz. docs/backup.md §2).
[CmdletBinding()]
param(
    [switch]$VerifyOnly
)

$ErrorActionPreference = 'Stop'
$repoRoot = Split-Path $PSScriptRoot -Parent
$stamp = Get-Date -Format 'yyyyMMdd-HHmmss'
$bundleName = "qir-engine-$stamp.bundle"

$destinations = @(
    (Join-Path $env:OneDrive 'yedekler\qir-engine'),   # bulut, fiziksel olarak ayrı
    'D:\yedekler\qir-engine'                             # ikinci sabit disk, farklı fiziksel ortam
)

if (-not $VerifyOnly) {
    Write-Host "=== 1) git bundle olustur ===" -ForegroundColor Cyan
    $tmpBundle = Join-Path $env:TEMP $bundleName
    Push-Location $repoRoot
    try {
        git bundle create $tmpBundle --all
    } finally {
        Pop-Location
    }
    $sizeKB = [math]::Round((Get-Item $tmpBundle).Length / 1KB, 1)
    Write-Host "Bundle: $tmpBundle ($sizeKB KB)" -ForegroundColor Green

    Write-Host "`n=== 2) iki hedefe kopyala ===" -ForegroundColor Cyan
    foreach ($dest in $destinations) {
        if (-not (Test-Path (Split-Path $dest -Parent -ErrorAction SilentlyContinue))) {
            # üst dizin (ör. D:\yedekler) yoksa uyar, atlama - oluştur
        }
        New-Item -ItemType Directory -Force -Path $dest | Out-Null
        Copy-Item $tmpBundle -Destination $dest -Force
        Write-Host "-> $dest\$bundleName" -ForegroundColor Green
    }
    Remove-Item $tmpBundle -Force
}

Write-Host "`n=== 3) DOGRULAMA: en yeni bundle'dan gercekten geri yukle ===" -ForegroundColor Cyan
$latestBundle = Get-ChildItem $destinations[0] -Filter '*.bundle' | Sort-Object LastWriteTime -Descending | Select-Object -First 1
if (-not $latestBundle) { throw "Hicbir bundle bulunamadi: $($destinations[0])" }

$restoreDir = Join-Path $env:TEMP "qir-restore-test-$stamp"
$sw = [System.Diagnostics.Stopwatch]::StartNew()
git clone --quiet $latestBundle.FullName $restoreDir
$sw.Stop()

$commitCount = (git -C $restoreDir log --oneline | Measure-Object -Line).Lines
$headHash = (git -C $restoreDir rev-parse HEAD).Trim()
$origHash = (git -C $repoRoot rev-parse HEAD).Trim()

Write-Host "Geri yukleme suresi: $($sw.Elapsed.TotalSeconds) saniye" -ForegroundColor Yellow
Write-Host "Geri yuklenen commit sayisi: $commitCount" -ForegroundColor Yellow
Write-Host "HEAD eslesiyor mu: $(if ($headHash -eq $origHash) {'EVET'} else {'HAYIR - SORUN VAR'})" -ForegroundColor $(if ($headHash -eq $origHash) {'Green'} else {'Red'})

Remove-Item $restoreDir -Recurse -Force

Write-Host "`n=== OZET ===" -ForegroundColor Cyan
Write-Host "Yedekler: $($destinations -join ', ')"
Write-Host "Son bundle: $($latestBundle.Name)"
Write-Host "Dogrulama: $(if ($headHash -eq $origHash) {'GECTI'} else {'BASARISIZ'})"
