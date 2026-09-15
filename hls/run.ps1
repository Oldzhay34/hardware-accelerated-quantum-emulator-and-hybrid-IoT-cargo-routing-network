<#
.SYNOPSIS
    Vitis HLS akışını uçtan uca koşar: csim -> csynth -> cosim -> export (FR-017).

.DESCRIPTION
    Elle arayüz tıklamak hata kaynağıdır ve bu fazda çok sayıda sentez turu
    atılacak (K-03: 3 bankalama denemesi, K-04: 4 II turu). SC-005 ayrıca iki
    ardışık koşumun AYNI II ve kaynak sayılarını vermesini istiyor — bu ancak
    akış betikleştirilirse anlamlı biçimde sınanabilir.

    Varsayılan olarak cosim ATLANIR: çok uzun sürer ve bu makinede Smart App
    Control (SK-05) tarafından engellenebilir. Kritik ölçütler (SC-002, SC-003)
    csynth'ten geldiği için bu bir kayıp değildir.

.EXAMPLE
    .\hls\run.ps1                      # csim + csynth
    .\hls\run.ps1 -Cosim -Export       # tam zincir
    .\hls\run.ps1 -Only csynth         # yalnizca sentez
#>
[CmdletBinding()]
param(
    [switch]$Cosim,
    [switch]$Export,
    [ValidateSet('csim', 'csynth', 'cosim', 'export')]
    [string]$Only
)

$ErrorActionPreference = 'Stop'

# --- Depo kökünden koş ----------------------------------------------------
$kok = Split-Path -Parent $PSScriptRoot
Set-Location $kok
if (-not (Test-Path "$kok\hls\src\qir_kernel.cpp")) {
    Write-Host "HATA: depo koku bulunamadi ($kok)" -ForegroundColor Red
    exit 2
}

# --- HLS calistiricisini bul ----------------------------------------------
# 2025.2'de HLS komut satiri `vitis-run`dur; eski surumlerdeki `vitis_hls.bat`
# ARTIK YOK. Cagri sekli de farkli:
#     yeni : vitis-run --mode hls --tcl <script>
#     eski : vitis_hls -f <script>
# Ikisi de destekleniyor ki runbook eski bir kuruluma da uygulanabilsin.
$vitis = $null
$mod = $null

foreach ($ad in @('vitis-run', 'vitis_hls')) {
    $c = (Get-Command $ad -ErrorAction SilentlyContinue).Source
    if ($c) { $vitis = $c; $mod = $ad; break }
}
if (-not $vitis) {
    foreach ($kk in @('D:\Xilinx', 'C:\Xilinx', 'D:\AMDDesignTools', 'C:\AMDDesignTools')) {
        if (-not (Test-Path $kk)) { continue }
        foreach ($ad in @('vitis-run.bat', 'vitis_hls.bat')) {
            $bulunan = Get-ChildItem $kk -Recurse -Filter $ad -ErrorAction SilentlyContinue |
                       Select-Object -ExpandProperty FullName | Sort-Object | Select-Object -Last 1
            if ($bulunan) { $vitis = $bulunan; $mod = $ad -replace '\.bat$', ''; break }
        }
        if ($vitis) { break }
    }
}
if (-not $vitis) {
    Write-Host "HATA: vitis-run / vitis_hls bulunamadi." -ForegroundColor Red
    Write-Host "      Kurulum tamamlandi mi? Bkz. docs/runbooks/vitis-hls-kurulum.md" -ForegroundColor Red
    Write-Host "      SK-04 hala ACIK demektir." -ForegroundColor Red
    exit 2
}
Write-Host "HLS       : $vitis  (mod: $mod)" -ForegroundColor Cyan
Write-Host "depo      : $kok" -ForegroundColor Cyan
Write-Host ""

# --- Hangi adımlar --------------------------------------------------------
if ($Only) {
    $adimlar = @($Only)
} else {
    $adimlar = @('csim', 'csynth')
    if ($Cosim)  { $adimlar += 'cosim' }
    if ($Export) { $adimlar += 'export' }
}

$ozet = @()
foreach ($adim in $adimlar) {
    $tcl = "$kok\hls\tcl\$adim.tcl"
    if (-not (Test-Path $tcl)) {
        Write-Host "HATA: $tcl yok" -ForegroundColor Red
        exit 2
    }
    Write-Host ("=" * 70)
    Write-Host "ADIM: $adim" -ForegroundColor Yellow
    Write-Host ("=" * 70)

    $sw = [Diagnostics.Stopwatch]::StartNew()
    if ($mod -eq 'vitis-run') {
        & $vitis --mode hls --tcl $tcl
    } else {
        & $vitis -f $tcl
    }
    $kod = $LASTEXITCODE
    $sw.Stop()

    $ozet += [PSCustomObject]@{
        Adim   = $adim
        Durum  = $(if ($kod -eq 0) { 'TAMAM' } else { "HATA ($kod)" })
        Sure   = "{0:N0} sn" -f $sw.Elapsed.TotalSeconds
    }

    if ($kod -ne 0) {
        Write-Host ""
        Write-Host "ADIM BASARISIZ: $adim (cikis kodu $kod)" -ForegroundColor Red
        if ($adim -eq 'cosim') {
            Write-Host "NOT: cosim kullanici kodundan ikili uretip CALISTIRIR." -ForegroundColor Yellow
            Write-Host "     Smart App Control (SK-05) engellemis olabilir. Kayip sinirli:" -ForegroundColor Yellow
            Write-Host "     yalnizca SC-005 duser; SC-002 ve SC-003 csynth'ten gelir." -ForegroundColor Yellow
        }
        $ozet | Format-Table -AutoSize
        exit 1
    }
    Write-Host ""
}

Write-Host ("=" * 70)
$ozet | Format-Table -AutoSize

# --- Sentez raporunu isaret et -------------------------------------------
$rapor = Get-ChildItem "$kok\hls\build\qir_hls" -Recurse -Filter '*_csynth.rpt' -ErrorAction SilentlyContinue |
         Sort-Object LastWriteTime | Select-Object -Last 1
if ($rapor) {
    Write-Host "Sentez raporu: $($rapor.FullName)" -ForegroundColor Green
    Write-Host ""
    Write-Host "OKUMA SIRASI (docs/measurements/faz2-sentez.md'ye yazilacak):" -ForegroundColor Green
    Write-Host "  1. BRAM_18K   -> esik 238 (=%85 x 280). BUTCE 280'DIR, 140 DEGIL." -ForegroundColor Green
    Write-Host "  2. II (k=0 ve k=15 AYRI AYRI) -> esik 4" -ForegroundColor Green
    Write-Host "  3. Fmax       -> NC-4'u cozer" -ForegroundColor Green
    Write-Host ""
    Write-Host "Rakamlar ELLE SABITLENMEZ; gercek rapordan kopyalanir (Prensip II)." -ForegroundColor Green
}
