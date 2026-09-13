# Faz 1 T026 — Altın referansı üretir ve docs/measurements/ altına damgalı yazar.
# Anayasa Prensip II: raporlanan her sayı GERÇEK ÖLÇÜMDEN gelir, tahmin yazılmaz.
[CmdletBinding()]
param(
    [int]$Stops = 5,
    [int[]]$P = @(1, 2),
    [int]$Seed = 42
)

$ErrorActionPreference = 'Stop'
$repoRoot = Split-Path $PSScriptRoot -Parent
Push-Location $repoRoot
try {
    foreach ($p in $P) {
        Write-Host "`n=== Altin referans: $Stops durak, p=$p, seed=$Seed ===" -ForegroundColor Cyan
        & .\.venv\Scripts\python.exe -m services.reference.cli --stops $Stops --p $p --seed $Seed
        if ($LASTEXITCODE -ne 0) { throw "Referans uretimi basarisiz (p=$p)" }
    }
} finally {
    Pop-Location
}
