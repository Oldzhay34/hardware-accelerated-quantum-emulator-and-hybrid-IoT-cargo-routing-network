<#
.SYNOPSIS
    Dizustu bataryasinin anlik desarj gucunu saniyede bir CSV'ye yazar.

.DESCRIPTION
    Faz 5 / US3 enerji olcumu icin. NEDEN BATARYA: CPU tarafinin enerjisini
    olcmenin alternatifi, 120 W'lik adaptor kablosunu kesip araya akim sensoru
    koymakti. Batarya sayaci AYNI kapsami (tum dizustu) olcuyor, cozunurlugu
    5 dakikalik bir olcum icin fazlasiyla yeterli ve riski SIFIR.

    IKI bagimsiz enerji hesabi yapilabilsin diye iki alan birden kaydedilir:
      DischargeRate     anlik guc (mW)  -> zamana gore integral
      RemainingCapacity kalan enerji (mWh) -> bas/son farki
    Ikisi birbirini dogrular. Anlamli olcude ayrisiyorlarsa olcume guvenilmez.

.PARAMETER Saniye
    Kayit suresi. Varsayilan 300 (5 dakika).

.PARAMETER Cikti
    CSV dosya yolu.

.EXAMPLE
    .\scripts\battery_logger.ps1 -Saniye 300 -Cikti bos.csv
#>
param(
    [int]$Saniye = 300,
    [Parameter(Mandatory = $true)][string]$Cikti
)

$ErrorActionPreference = 'Stop'

function Oku {
    $b = Get-CimInstance -Namespace root\wmi -ClassName BatteryStatus -ErrorAction Stop | Select-Object -First 1
    [pscustomobject]@{
        Zaman        = (Get-Date).ToString('o')
        DesarjMw     = [int]$b.DischargeRate
        SarjMw       = [int]$b.ChargeRate
        KalanMwh     = [int]$b.RemainingCapacity
        GerilimMv    = [int]$b.Voltage
        PrizdeMi     = [bool]$b.PowerOnline
        DesarjEdiyor = [bool]$b.Discharging
    }
}

# --- On kosul: FISTEN CIKMIS OLMALI ---
# Prizdeyken batarya desarj olmaz, DischargeRate 0 gelir ve olcum anlamsizdir.
$ilk = Oku
if ($ilk.PrizdeMi) {
    Write-Host "HATA: Bilgisayar PRIZE TAKILI." -ForegroundColor Red
    Write-Host "      Batarya yontemi yalnizca fisten cikmisken calisir."
    Write-Host "      Adaptoru cikarip tekrar calistir."
    exit 1
}
if ($ilk.KalanMwh -le 0) {
    Write-Host "HATA: Batarya kapasitesi okunamiyor (RemainingCapacity = 0)." -ForegroundColor Red
    Write-Host "      Bu dizustu WMI uzerinden mWh raporlamiyor olabilir."
    exit 2
}

Write-Host "Kayit basliyor: $Saniye saniye -> $Cikti"
Write-Host ("Baslangic kapasitesi: {0} mWh" -f $ilk.KalanMwh)
Write-Host "DOKUNMA: fare/klavye kullanma, ekran parlakligini degistirme."
Write-Host ""

$satirlar = New-Object System.Collections.Generic.List[object]
$bas = Get-Date
$i = 0
while (((Get-Date) - $bas).TotalSeconds -lt $Saniye) {
    $s = Oku
    $satirlar.Add($s)
    if ($s.PrizdeMi) {
        Write-Host "UYARI: olcum sirasinda prize takildi - bu kayit GECERSIZ." -ForegroundColor Yellow
    }
    $i++
    if ($i % 30 -eq 0) {
        $gecen = [int]((Get-Date) - $bas).TotalSeconds
        Write-Host ("  {0,3} sn   anlik {1,6} mW   kalan {2} mWh" -f $gecen, $s.DesarjMw, $s.KalanMwh)
    }
    Start-Sleep -Seconds 1
}

$satirlar | Export-Csv -Path $Cikti -NoTypeInformation -Encoding utf8
$son = $satirlar[-1]
$dusen = $ilk.KalanMwh - $son.KalanMwh
Write-Host ""
Write-Host ("Bitti. {0} ornek yazildi -> {1}" -f $satirlar.Count, $Cikti)
Write-Host ("Kapasite dususu: {0} mWh" -f $dusen)
if ($dusen -le 0) {
    Write-Host "UYARI: kapasite dusmemis. Sure cok kisa olabilir veya batarya raporlamasi kaba." -ForegroundColor Yellow
}
