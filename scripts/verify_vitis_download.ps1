<#
.SYNOPSIS
    Vitis HLS yükleyicisinin sağlamasını AMD'nin imzalı .digests dosyasına karşı doğrular.

.DESCRIPTION
    Bozuk bir installer'la 25-40 GB'lik kurulumun ortasinda kalmak, 10 saniyelik
    kontrolden cok daha pahalidir. Ayni disiplin scripts/fetch_osm.ps1'de OSM
    dokumu icin zaten uygulaniyor (spec FR-005).

    Beklenen degerler ELLE YAZILMAZ: yanindaki .digests dosyasindan okunur.
    Boylece surum degisince betik de kendiliginden dogru kalir.

.EXAMPLE
    .\scripts\verify_vitis_download.ps1
#>
[CmdletBinding()]
param(
    [string]$Dizin = "$env:USERPROFILE\Downloads",
    [string]$Desen = "FPGAs_AdaptiveSoCs_Unified_SDI_*_Win64.exe"
)

$ErrorActionPreference = 'Stop'

$exe = Get-ChildItem -Path $Dizin -Filter $Desen -File -ErrorAction SilentlyContinue |
       Sort-Object LastWriteTime | Select-Object -Last 1

if (-not $exe) {
    Write-Host "Yukleyici bulunamadi: $Dizin\$Desen" -ForegroundColor Yellow
    $kismi = Get-ChildItem -Path $Dizin -File -ErrorAction SilentlyContinue |
             Where-Object { $_.Name -match '\.(crdownload|part|partial|opdownload)$' }
    if ($kismi) {
        Write-Host "Yarim inmis dosya var - indirme devam ediyor olabilir:" -ForegroundColor Yellow
        $kismi | ForEach-Object { "   {0}  {1:N2} GB" -f $_.Name, ($_.Length / 1GB) }
    } else {
        Write-Host "Yarim inmis dosya da yok - indirme hic baslamamis." -ForegroundColor Yellow
        Write-Host "NOT: Sayfadaki 'Digest' butonu yalnizca ~1,4 KB'lik .digests dosyasini indirir." -ForegroundColor Yellow
        Write-Host "     Asil installer icin 'Windows Self Extracting Web Installer' satirini kullan." -ForegroundColor Yellow
    }
    exit 2
}

$digests = "$($exe.FullName).digests"
if (-not (Test-Path $digests)) {
    Write-Host "HATA: .digests dosyasi yok -> $digests" -ForegroundColor Red
    Write-Host "      Beklenen degerler elle yazilmaz; AMD'nin imzali dosyasindan okunur." -ForegroundColor Red
    exit 2
}

# .digests PGP imzali metindir; satirlar "<hash> *<dosyaadi>" seklinde.
$satirlar = Get-Content $digests | Where-Object { $_ -match '^[0-9a-f]{32,128}\s+\*' }
$beklenen = @{}
foreach ($s in $satirlar) {
    $h = ($s -split '\s+')[0]
    switch ($h.Length) {
        32  { $beklenen['MD5']    = $h }
        40  { $beklenen['SHA1']   = $h }
        64  { $beklenen['SHA256'] = $h }
        128 { $beklenen['SHA512'] = $h }
    }
}

Write-Host ("Dosya : {0}" -f $exe.Name)
Write-Host ("Boyut : {0:N2} GB" -f ($exe.Length / 1GB))
Write-Host ("Tarih : {0}" -f $exe.LastWriteTime)
Write-Host ""

$tumu = $true
foreach ($alg in @('MD5', 'SHA1', 'SHA256')) {
    if (-not $beklenen.ContainsKey($alg)) { continue }
    $olculen = (Get-FileHash $exe.FullName -Algorithm $alg).Hash.ToLower()
    $ok = ($olculen -eq $beklenen[$alg].ToLower())
    if (-not $ok) { $tumu = $false }
    $renk = if ($ok) { 'Green' } else { 'Red' }
    Write-Host ("{0,-7} {1}" -f $alg, $(if ($ok) { 'TUTUYOR' } else { 'TUTMUYOR' })) -ForegroundColor $renk
    if (-not $ok) {
        Write-Host ("        beklenen: {0}" -f $beklenen[$alg])
        Write-Host ("        olculen : {0}" -f $olculen)
    }
}

Write-Host ""
if ($tumu) {
    Write-Host "SAGLAMA DOGRULANDI - kuruluma gecilebilir." -ForegroundColor Green
    Write-Host "Sonraki adim: yukleyiciyi calistir, hedef D:\Xilinx\, cihaz ailesi YALNIZCA Zynq-7000." -ForegroundColor Green
    Write-Host "Ayrinti: docs/runbooks/vitis-hls-kurulum.md"
    exit 0
} else {
    Write-Host "SAGLAMA TUTMADI - KURULUMA BASLAMA. Dosyayi sil ve yeniden indir." -ForegroundColor Red
    exit 1
}
