# SOPS+age ile şifrelenmiş sırları yönetir. Ayrıntı: docs/secrets-audit.md
[CmdletBinding()]
param(
    [Parameter(Mandatory, Position = 0)]
    [ValidateSet('edit', 'env', 'check')]
    [string]$Command,

    [string]$File = 'secrets.enc.yaml',
    [string]$Out = '.env'
)

$ErrorActionPreference = 'Stop'
$repoRoot = Split-Path $PSScriptRoot -Parent
$encPath = Join-Path $repoRoot $File

if (-not (Test-Path $encPath)) { throw "Şifreli dosya bulunamadı: $encPath" }

$keyFile = Join-Path $env:APPDATA 'sops\age\keys.txt'
if (-not (Test-Path $keyFile)) {
    throw @"
age özel anahtarı bulunamadı: $keyFile
Bu anahtar olmadan sırlar çözülemez. Yedekten geri yükle (bkz. docs/backup.md).
Anahtarı kaybettiysen sırlar KURTARILAMAZ — yeniden üretilip rotasyon gerekir.
"@
}

switch ($Command) {
    # Şifreli dosyayı editörde aç; kaydedince SOPS otomatik yeniden şifreler.
    'edit' {
        sops $encPath
    }

    # Yerel geliştirme için düz .env üret. Bu dosya .gitignore'dadır.
    'env' {
        $outPath = Join-Path $repoRoot $Out
        $yaml = sops --decrypt $encPath
        $lines = @('# OTOMATİK ÜRETİLDİ — scripts/secrets.ps1 env. Elle düzenleme, commit etme.')
        $section = ''
        foreach ($line in $yaml -split "`r?`n") {
            if ($line -match '^([a-z0-9_]+):\s*$') { $section = $matches[1]; continue }
            if ($line -match '^\s+([a-z0-9_]+):\s*(.+)$') {
                # Invariant şart: Türkçe locale'de ToUpper() 'i' harfini 'İ' yapar
                # ve geçersiz env değişken adı üretir (AUTH_JWT_SİGNİNG_KEY gibi).
                $name = "$($section)_$($matches[1])".ToUpperInvariant()
                $lines += "$name=$($matches[2])"
            }
        }
        Set-Content -Path $outPath -Value $lines -Encoding utf8
        Write-Host "$($lines.Count - 1) değişken yazıldı -> $Out" -ForegroundColor Green
    }

    # Çözme çalışıyor mu ve depoda düz sır kaldı mı — ikisini birden doğrula.
    'check' {
        sops --decrypt $encPath | Out-Null
        Write-Host "Çözme: OK" -ForegroundColor Green

        # Git modu şart: --no-git .gitignore'u atlar ve .venv'deki üçüncü parti
        # test sabitlerini sızıntı sanar (39 yanlış pozitif). Bkz. docs/secrets-audit.md §1.
        gitleaks detect --source $repoRoot --no-banner
        if ($LASTEXITCODE -ne 0) { throw "gitleaks sızıntı buldu — yukarı bak." }
        Write-Host "gitleaks: temiz" -ForegroundColor Green
    }
}
