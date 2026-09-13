# Faz 1 T040 — Tek komutla uçtan uca kurulum (spec US4, SC-005).
[CmdletBinding()]
param([switch]$SkipReference)

$ErrorActionPreference = 'Stop'
$repoRoot = Split-Path $PSScriptRoot -Parent
Push-Location $repoRoot
$sw = [System.Diagnostics.Stopwatch]::StartNew()
try {
    Write-Host "=== 1/4: OSM verisi ===" -ForegroundColor Cyan
    & "$PSScriptRoot\fetch_osm.ps1"

    Write-Host "`n=== 2/4: OSRM on isleme (extract+partition+customize) ===" -ForegroundColor Cyan
    docker compose -f infra/docker/docker-compose.yml --profile prepare up osrm-prepare
    if ($LASTEXITCODE -ne 0) { throw "osrm-prepare basarisiz" }

    Write-Host "`n=== 3/4: OSRM + matrix servisleri ===" -ForegroundColor Cyan
    docker compose -f infra/docker/docker-compose.yml up -d osrm matrix
    if ($LASTEXITCODE -ne 0) { throw "servisler baslatilamadi" }

    Write-Host "matrix servisinin /health ucu bekleniyor..." -ForegroundColor Yellow
    $hazir = $false
    for ($i = 0; $i -lt 30; $i++) {
        try {
            $r = Invoke-WebRequest -Uri "http://localhost:8090/health" -UseBasicParsing -TimeoutSec 3
            if ($r.StatusCode -eq 200) { $hazir = $true; break }
        } catch {}
        Start-Sleep -Seconds 2
    }
    if (-not $hazir) { throw "matrix servisi 60 saniyede hazir olmadi" }
    Write-Host "Hazir." -ForegroundColor Green

    if (-not $SkipReference) {
        Write-Host "`n=== 4/4: Altin referans (5 durak, p=1,2) ===" -ForegroundColor Cyan
        & "$PSScriptRoot\run_reference.ps1" -Stops 5 -P 1, 2 -Seed 42
    }
} finally {
    Pop-Location
}
$sw.Stop()
Write-Host "`n=== TOPLAM SURE: $([math]::Round($sw.Elapsed.TotalSeconds,1)) sn ===" -ForegroundColor Green
