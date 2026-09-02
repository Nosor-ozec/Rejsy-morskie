[CmdletBinding()]
param(
    [string]$ProjectRoot,
    [string]$TargetPath = 'E:\sea-router',
    [string]$WorkbookPath,
    [switch]$ValidateOnly,
    [switch]$NoActivate,
    [int]$TestPort = 3102
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
if ([string]::IsNullOrWhiteSpace($ProjectRoot)) { $ProjectRoot = Split-Path (Split-Path $PSScriptRoot -Parent) -Parent }
$project = [IO.Path]::GetFullPath($ProjectRoot)
$target = [IO.Path]::GetFullPath($TargetPath)
$module = Split-Path $PSScriptRoot -Parent
$python = Join-Path $project '.venv\Scripts\python.exe'
if ([string]::IsNullOrWhiteSpace($WorkbookPath)) { $WorkbookPath = Join-Path $project 'routes\rejsy.xlsx' }
$workbook = [IO.Path]::GetFullPath($WorkbookPath)
$passagesPath = Join-Path $module 'passages.json'
$casesPath = Join-Path $module 'regression-cases.json'
$env:PYTHONUTF8 = '1'
if (-not (Test-Path -LiteralPath $python -PathType Leaf)) { throw "Brak środowiska Pythona projektu: $python" }
if (-not (Test-Path -LiteralPath $workbook -PathType Leaf)) { throw "Brak skoroszytu: $workbook" }

Write-Host '1/4 Odczyt Lokalizacje i generowanie technicznego passages.json...'
& $python -m rejsy_morskie.cli passages $workbook $passagesPath
if ($LASTEXITCODE -ne 0) { throw 'Nie udało się wygenerować passages.json.' }

$passages = Get-Content -LiteralPath $passagesPath -Raw -Encoding UTF8 | ConvertFrom-Json
$cases = Get-Content -LiteralPath $casesPath -Raw -Encoding UTF8 | ConvertFrom-Json
. (Join-Path $PSScriptRoot 'RegressionPolicy.ps1')
$policy = Get-RegressionPolicy -Passages $passages -Cases $cases
$requiredText = @($policy.RequiredIds) -join ', '
$diagnosticText = @($policy.DiagnosticIds) -join ', '
Write-Host "2/4 OK: dane techniczne kompletne. Regresje obowiązkowe: $requiredText."
if ($diagnosticText) {
    Write-Host "Regresje diagnostyczne development (nie blokują aktualizacji): $diagnosticText" -ForegroundColor Yellow
}

$installer = Join-Path $PSScriptRoot 'Install-SeaRouter.ps1'
if ($ValidateOnly) {
    & $installer -TargetPath $target -ValidateOnly -PassagesPath $passagesPath -TestPort $TestPort
    if ($LASTEXITCODE -ne 0) { throw 'Walidacja wstępna instalatora nie przeszła.' }
    Write-Host 'Tryb test zakończony. Nie zbudowano ani nie aktywowano grafu.' -ForegroundColor Green
    exit 0
}
if (-not (Test-Path -LiteralPath $target -PathType Container)) { throw "Brak aktywnej instalacji: $target" }

$parent = Split-Path $target -Parent
$stamp = [DateTime]::Now.ToString('yyyyMMdd-HHmmss')
$candidate = Join-Path $parent "sea-router-update-candidate-$stamp"
$buildStage = Join-Path $parent "sea-router-update-staging-$stamp"
Write-Host "3/4 Budowanie i testowanie pełnego kandydata: $candidate"
& $installer -TargetPath $candidate -StagingPath $buildStage -PassagesPath $passagesPath -TestPort $TestPort
if ($LASTEXITCODE -ne 0) { throw 'Budowa kandydata nie przeszła. Aktywna instalacja pozostała bez zmian.' }
if ($NoActivate) {
    Write-Host "Kandydat przeszedł walidację i pozostał w $candidate. Aktywna instalacja nie została zmieniona." -ForegroundColor Green
    exit 0
}

. (Join-Path $PSScriptRoot 'ProcessCleanup.ps1')
$activeExe = [IO.Path]::GetFullPath((Join-Path $target 'rust\target\release\sea-router-rs.exe'))
$running = @()
try { $running = @(Get-Process -Name 'sea-router-rs' -ErrorAction SilentlyContinue | Where-Object { $_.Path -and [IO.Path]::GetFullPath($_.Path) -eq $activeExe }) } catch { $running = @() }
foreach ($process in $running) { Stop-TestServerProcess -Process $process }
$backup = Join-Path $parent "sea-router-update-backup-$stamp"
Write-Host "4/4 Aktywacja po sukcesie; poprzednia wersja: $backup"
$oldMoved = $false
try {
    Move-Item -LiteralPath $target -Destination $backup
    $oldMoved = $true
    Move-Item -LiteralPath $candidate -Destination $target
}
catch {
    if ($oldMoved -and -not (Test-Path -LiteralPath $target) -and (Test-Path -LiteralPath $backup)) {
        Move-Item -LiteralPath $backup -Destination $target
    }
    throw "Nie udało się aktywować kandydata; przywrócono poprzednią instalację. $($_.Exception.Message)"
}
if ($running.Count -gt 0) {
    $newExe = Join-Path $target 'rust\target\release\sea-router-rs.exe'
    Start-Process -FilePath $newExe -ArgumentList @('serve', (Join-Path $target 'data')) -WorkingDirectory (Join-Path $target 'rust') -WindowStyle Hidden | Out-Null
}
Write-Host "Nowy graf jest aktywny. Poprzednia kompletna instalacja pozostała w $backup" -ForegroundColor Green
