# Faz 1 T005 — OSM dökümünü indirir ve sürümünü MD5 ile doğrular.
# Anayasa Prensip II / spec FR-005: "en güncel veriyi indir" davranışı YASAK.
# MD5 tutmazsa bu betik HATA VERİR ve durur — sessizce yeni sürümü kabul etmez.
[CmdletBinding()]
param(
    [string]$Url = 'https://download.bbbike.org/osm/bbbike/Istanbul/Istanbul.osm.pbf',
    [string]$ExpectedMd5 = 'cb101d9243c3c605907e94f4266159c2',
    [string]$Out = 'data/osm/Istanbul.osm.pbf',
    # Ölçüm sırasında indirilmiş bir kopya varsa oradan al (aynı MD5 doğrulaması yine uygulanır).
    [string]$LocalSource = ''
)

$ErrorActionPreference = 'Stop'
$repoRoot = Split-Path $PSScriptRoot -Parent
$outPath = Join-Path $repoRoot $Out
New-Item -ItemType Directory -Force -Path (Split-Path $outPath -Parent) | Out-Null

if (Test-Path $outPath) {
    $mevcut = (Get-FileHash $outPath -Algorithm MD5).Hash.ToLower()
    if ($mevcut -eq $ExpectedMd5.ToLower()) {
        Write-Host "Zaten var ve MD5 dogru: $Out" -ForegroundColor Green
        exit 0
    }
    Write-Warning "Mevcut dosyanin MD5'i farkli, yeniden alinacak."
}

if ($LocalSource -and (Test-Path $LocalSource)) {
    Write-Host "Yerel kopyadan aliniyor: $LocalSource"
    Copy-Item $LocalSource $outPath -Force
} else {
    Write-Host "Indiriliyor: $Url"
    $sw = [System.Diagnostics.Stopwatch]::StartNew()
    Invoke-WebRequest -Uri $Url -OutFile $outPath -UseBasicParsing
    $sw.Stop()
    Write-Host ("Indirme suresi: {0:N1} sn" -f $sw.Elapsed.TotalSeconds)
}

$md5 = (Get-FileHash $outPath -Algorithm MD5).Hash.ToLower()
$mb = [math]::Round((Get-Item $outPath).Length / 1MB, 1)

if ($md5 -ne $ExpectedMd5.ToLower()) {
    Remove-Item $outPath -Force
    throw @"
MD5 UYUSMAZLIGI — veri surumu degismis.
  beklenen : $ExpectedMd5
  bulunan  : $md5
Bu bir hata degil, bir KAPIDIR (spec FR-005): olcumlerin dayandigi veri
surumu sessizce degisemez. Yeni surumu bilincli olarak kabul edecekseniz
-ExpectedMd5 parametresini guncelleyin ve karari kayda gecirin.
"@
}

Write-Host "MD5 dogrulandi: $md5 ($mb MB)" -ForegroundColor Green
