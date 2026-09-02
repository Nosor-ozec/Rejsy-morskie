[CmdletBinding()]
param(
    [string]$BaseUrl = 'http://127.0.0.1:3001',
    [string]$CasesPath,
    [string[]]$RequiredCaseIds,
    [string[]]$DiagnosticCaseIds,
    [int]$TimeoutSec = 120
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$culture = [Globalization.CultureInfo]::InvariantCulture

if ([string]::IsNullOrWhiteSpace($CasesPath)) {
    $CasesPath = Join-Path (Split-Path $PSScriptRoot -Parent) 'regression-cases.json'
}

function To-Invariant([double]$Value) {
    return $Value.ToString('0.########', $culture)
}

function Get-HaversineKm($First, $Second) {
    $radius = 6371.0088
    $lon1 = [double]$First[0] * [Math]::PI / 180
    $lat1 = [double]$First[1] * [Math]::PI / 180
    $lon2 = [double]$Second[0] * [Math]::PI / 180
    $lat2 = [double]$Second[1] * [Math]::PI / 180
    $dLon = $lon2 - $lon1
    $dLat = $lat2 - $lat1
    $a = [Math]::Pow([Math]::Sin($dLat / 2), 2) +
        [Math]::Cos($lat1) * [Math]::Cos($lat2) * [Math]::Pow([Math]::Sin($dLon / 2), 2)
    return $radius * 2 * [Math]::Asin([Math]::Sqrt($a))
}

function Get-PathLengthKm($Coordinates) {
    $sum = 0.0
    for ($index = 1; $index -lt $Coordinates.Count; $index++) {
        $sum += Get-HaversineKm $Coordinates[$index - 1] $Coordinates[$index]
    }
    return $sum
}

$casesFile = (Resolve-Path -LiteralPath $CasesPath).Path
$configuration = Get-Content -LiteralPath $casesFile -Raw -Encoding UTF8 | ConvertFrom-Json
if ($configuration.schema_version -ne 1 -or $configuration.coordinate_order -ne 'longitude_latitude') {
    throw 'Nieobsługiwana wersja regression-cases.json.'
}

$failures = [Collections.Generic.List[string]]::new()
$diagnosticFailures = [Collections.Generic.List[string]]::new()
$executed = 0
$policySpecified = $PSBoundParameters.ContainsKey('RequiredCaseIds') -or $PSBoundParameters.ContainsKey('DiagnosticCaseIds')
$required = @{}
$diagnostic = @{}
if ($policySpecified) {
    foreach ($id in @($RequiredCaseIds)) { if ($id) { $required[[string]$id] = $true } }
    foreach ($id in @($DiagnosticCaseIds)) { if ($id) { $diagnostic[[string]$id] = $true } }
}
foreach ($case in $configuration.cases) {
    if (-not [bool]$case.enabled) {
        Write-Host "POMINIĘTO [$($case.id)] $($case.name): $($case.status)"
        continue
    }
    $caseId = [string]$case.id
    $isRequired = -not $policySpecified -or $required.ContainsKey($caseId)
    $isDiagnostic = $policySpecified -and $diagnostic.ContainsKey($caseId)
    if (-not $isRequired -and -not $isDiagnostic) {
        Write-Host "POMINIĘTO [$($case.id)] $($case.name): nie dotyczy bieżącej polityki"
        continue
    }
    $executed++
    try {
        $from = '{0},{1}' -f (To-Invariant ([double]$case.start[0])), (To-Invariant ([double]$case.start[1]))
        $to = '{0},{1}' -f (To-Invariant ([double]$case.end[0])), (To-Invariant ([double]$case.end[1]))
        $penalty = To-Invariant ([double]$case.penalty)
        $uri = "$($BaseUrl.TrimEnd('/'))/route?from=$from&to=$to&penalty=$penalty"
        $response = Invoke-RestMethod -Uri $uri -TimeoutSec $TimeoutSec
        $feature = $response.features | Where-Object { $_.properties.name -eq 'final' } | Select-Object -First 1
        if ($null -eq $feature -or $feature.geometry.type -ne 'LineString') {
            throw 'Odpowiedź nie zawiera geometrii final typu LineString.'
        }
        $coordinates = @($feature.geometry.coordinates)
        if ($coordinates.Count -lt 2) {
            throw 'Geometria zawiera mniej niż dwa punkty.'
        }

        $bbox = @($case.allowed_bbox)
        foreach ($point in $coordinates) {
            $lon = [double]$point[0]
            $lat = [double]$point[1]
            if ($lon -lt [double]$bbox[0] -or $lat -lt [double]$bbox[1] -or
                $lon -gt [double]$bbox[2] -or $lat -gt [double]$bbox[3]) {
                throw "Geometria wychodzi poza dozwolony obszar przy punkcie $lon,$lat."
            }
        }

        foreach ($checkpoint in $case.checkpoints) {
            $minimum = [double]::PositiveInfinity
            foreach ($point in $coordinates) {
                $distance = Get-HaversineKm $checkpoint.point $point
                if ($distance -lt $minimum) { $minimum = $distance }
            }
            if ($minimum -gt [double]$checkpoint.max_distance_km) {
                throw ('Trasa omija punkt kontrolny {0},{1}: {2:N2} km > {3:N2} km.' -f
                    $checkpoint.point[0], $checkpoint.point[1], $minimum, $checkpoint.max_distance_km)
            }
        }

        $pathKm = Get-PathLengthKm $coordinates
        $directKm = Get-HaversineKm $case.start $case.end
        $ratio = $pathKm / $directKm
        if ($ratio -gt [double]$case.max_detour_ratio) {
            throw ('Absurdalny objazd: współczynnik {0:N3} > {1:N3}.' -f $ratio, $case.max_detour_ratio)
        }
        Write-Host ('OK [{0}] {1}: {2:N1} km, objazd x{3:N3}, {4} punktów' -f
            $case.id, $case.name, $pathKm, $ratio, $coordinates.Count)
    }
    catch {
        $message = "BŁĄD [$($case.id)] $($case.name): $($_.Exception.Message)"
        if ($isDiagnostic) {
            $diagnosticFailures.Add($message)
            Write-Warning "DIAGNOSTYCZNY $message — przejście development, aktualizacja nie jest blokowana."
        }
        else {
            $failures.Add($message)
            Write-Host $message -ForegroundColor Red
        }
    }
}

if ($executed -eq 0) {
    throw 'Nie uruchomiono żadnego aktywnego testu regresji.'
}
if ($failures.Count -gt 0) {
    throw "Testy regresji nie przeszły ($($failures.Count)/$executed)."
}
if ($diagnosticFailures.Count -gt 0) {
    Write-Warning "Regresje obowiązkowe przeszły; $($diagnosticFailures.Count) regresji development zgłosiło ostrzeżenia."
}
else {
    Write-Host "Wszystkie uruchomione testy regresji przeszły ($executed/$executed)." -ForegroundColor Green
}
