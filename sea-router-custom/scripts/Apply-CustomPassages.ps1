[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [string]$SourceRoot,

    [string]$PassagesPath
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

if ([string]::IsNullOrWhiteSpace($PassagesPath)) {
    $PassagesPath = Join-Path (Split-Path $PSScriptRoot -Parent) 'passages.json'
}

$source = (Resolve-Path -LiteralPath $SourceRoot).Path
$passagesFile = (Resolve-Path -LiteralPath $PassagesPath).Path
$canalsPath = Join-Path $source 'rust\src\canals.rs'
if (-not (Test-Path -LiteralPath $canalsPath -PathType Leaf)) {
    throw "Nie znaleziono bazowego pliku: $canalsPath"
}

$config = Get-Content -LiteralPath $passagesFile -Raw -Encoding UTF8 | ConvertFrom-Json
if ($config.schema_version -ne 1 -or $config.coordinate_order -ne 'longitude_latitude') {
    throw 'Nieobsługiwana wersja passages.json albo kolejność współrzędnych.'
}

$culture = [Globalization.CultureInfo]::InvariantCulture
function Format-RustNumber([double]$Value) {
    return $Value.ToString('0.00000', $culture)
}

$sourceText = [IO.File]::ReadAllText($canalsPath, [Text.Encoding]::UTF8)
$arrayMarker = 'pub static CANALS: &[CanalPassage] = &['
if (-not $sourceText.Contains($arrayMarker)) {
    throw 'Bazowy canals.rs nie zawiera oczekiwanej tablicy CANALS.'
}
$insertAt = $sourceText.LastIndexOf('];', [StringComparison]::Ordinal)
if ($insertAt -lt 0) {
    throw 'Nie znaleziono końca tablicy CANALS w canals.rs.'
}

$blocks = [Collections.Generic.List[string]]::new()
foreach ($passage in $config.passages) {
    $name = [string]$passage.name
    if ([string]::IsNullOrWhiteSpace($name)) {
        throw 'Przejście bez nazwy w passages.json.'
    }
    if ($sourceText.Contains(('name: "{0}"' -f $name))) {
        throw "Bazowy kod zawiera już przejście '$name'; odmowa podwójnego wstrzyknięcia."
    }
    if ($passage.waypoints.Count -lt 2) {
        throw "Przejście '$name' musi zawierać co najmniej dwa punkty."
    }

    $lines = [Collections.Generic.List[string]]::new()
    $lines.Add('    CanalPassage {')
    $lines.Add(('        name: "{0}",' -f $name.Replace('"', '\"')))
    $lines.Add('        // Injected from Rejsy-morskie/sea-router-custom/passages.json.')
    $lines.Add('        // Routing and map visualization only; not for navigation.')
    $lines.Add('        waypoints: &[')
    foreach ($point in $passage.waypoints) {
        if ($point.Count -ne 2) {
            throw "Przejście '$name' zawiera punkt inny niż [lon, lat]."
        }
        $lon = [double]$point[0]
        $lat = [double]$point[1]
        if ($lon -lt -180 -or $lon -gt 180 -or $lat -lt -90 -or $lat -gt 90) {
            throw "Przejście '$name' zawiera współrzędne poza zakresem: $lon, $lat."
        }
        $lines.Add(('            [{0}, {1}],' -f (Format-RustNumber $lon), (Format-RustNumber $lat)))
    }
    $lines.Add('        ],')
    $lines.Add('    },')
    $blocks.Add(($lines -join "`n"))
}

if ($blocks.Count -eq 0) {
    Write-Host 'Brak własnych przejść do wstrzyknięcia.'
    exit 0
}

$insertion = ($blocks -join "`n") + "`n"
$updated = $sourceText.Insert($insertAt, $insertion)
[IO.File]::WriteAllText($canalsPath, $updated, [Text.UTF8Encoding]::new($false))
Write-Host "Wstrzyknięto $($blocks.Count) własnych przejść do $canalsPath"
