[CmdletBinding()]
param(
    [string]$TargetPath = 'E:\sea-router',
    [string]$StagingPath,
    [switch]$ValidateOnly,
    [switch]$InstallMissingTools,
    [string]$PassagesPath,
    [int]$TestPort = 3101
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$moduleRoot = Split-Path $PSScriptRoot -Parent
$lockPath = Join-Path $moduleRoot 'sea-router.lock.json'
$lock = Get-Content -LiteralPath $lockPath -Raw -Encoding UTF8 | ConvertFrom-Json
. (Join-Path $PSScriptRoot 'HashValidation.ps1')
. (Join-Path $PSScriptRoot 'ProcessCleanup.ps1')
. (Join-Path $PSScriptRoot 'GraphValidation.ps1')
$targetFull = [IO.Path]::GetFullPath($TargetPath)

# Najpierw chronimy istniejącą instalację. Ta kontrola musi poprzedzać
# instalowanie narzędzi, pobieranie kodu i tworzenie katalogu roboczego.
if (-not $ValidateOnly -and (Test-Path -LiteralPath $targetFull)) {
    throw "Katalog docelowy już istnieje: $targetFull. Skrypt celowo go nie nadpisuje. W czystym teście najpierw odłóż go jako backup zgodnie z dokumentacją."
}

function Assert-Command([string]$Name, [string]$InstallHint) {
    if (-not (Get-Command $Name -ErrorAction SilentlyContinue)) {
        throw "Brak wymaganego narzędzia '$Name'. $InstallHint"
    }
}

function Get-Sha256([string]$Path) {
    return (Get-FileHash -LiteralPath $Path -Algorithm SHA256).Hash.ToUpperInvariant()
}

function Get-GitBlobSha1([string]$Path) {
    $bytes = [IO.File]::ReadAllBytes($Path)
    $header = [Text.Encoding]::ASCII.GetBytes("blob $($bytes.Length)`0")
    $stream = [IO.MemoryStream]::new()
    try {
        $stream.Write($header, 0, $header.Length)
        $stream.Write($bytes, 0, $bytes.Length)
        $stream.Position = 0
        $sha1 = [Security.Cryptography.SHA1]::Create()
        try {
            return ([BitConverter]::ToString($sha1.ComputeHash($stream))).Replace('-', '').ToLowerInvariant()
        }
        finally { $sha1.Dispose() }
    }
    finally { $stream.Dispose() }
}

function Expand-Gzip([string]$Source, [string]$Destination) {
    $input = [IO.File]::OpenRead($Source)
    try {
        $gzip = [IO.Compression.GZipStream]::new($input, [IO.Compression.CompressionMode]::Decompress)
        try {
            $output = [IO.File]::Create($Destination)
            try { $gzip.CopyTo($output) }
            finally { $output.Dispose() }
        }
        finally { $gzip.Dispose() }
    }
    finally { $input.Dispose() }
}

function Invoke-Checked([string]$Program, [string[]]$Arguments, [string]$WorkingDirectory) {
    Push-Location -LiteralPath $WorkingDirectory
    try {
        & $Program @Arguments
        if ($LASTEXITCODE -ne 0) {
            throw "Polecenie '$Program $($Arguments -join ' ')' zakończyło się kodem $LASTEXITCODE."
        }
    }
    finally { Pop-Location }
}

if ($InstallMissingTools) {
    Assert-Command 'winget.exe' 'Zainstaluj App Installer albo uruchom skrypt bez -InstallMissingTools po ręcznej instalacji narzędzi.'
    if (-not (Get-Command rustup.exe -ErrorAction SilentlyContinue)) {
        Invoke-Checked 'winget.exe' @('install', '--id', 'Rustlang.Rustup', '-e', '--accept-source-agreements', '--accept-package-agreements') $PWD.Path
    }
    $vswhere = Join-Path ${env:ProgramFiles(x86)} 'Microsoft Visual Studio\Installer\vswhere.exe'
    $vcFound = Test-Path -LiteralPath $vswhere -PathType Leaf
    if ($vcFound) {
        $vcFound = [bool](& $vswhere -products '*' -requires Microsoft.VisualStudio.Component.VC.Tools.x86.x64 -property installationPath)
    }
    if (-not $vcFound) {
        Invoke-Checked 'winget.exe' @(
            'install', '--id', 'Microsoft.VisualStudio.2022.BuildTools', '-e',
            '--accept-source-agreements', '--accept-package-agreements',
            '--override', '--wait --quiet --add Microsoft.VisualStudio.Workload.VCTools --includeRecommended'
        ) $PWD.Path
    }
}

Assert-Command 'rustup.exe' 'Zainstaluj rustup (np. winget install Rustlang.Rustup).'
$vswherePath = Join-Path ${env:ProgramFiles(x86)} 'Microsoft Visual Studio\Installer\vswhere.exe'
if (-not (Test-Path -LiteralPath $vswherePath -PathType Leaf)) {
    throw 'Brak Visual Studio Installer/vswhere. Wymagane są Visual Studio Build Tools 2022 z narzędziami C++ x64.'
}
$vcInstall = & $vswherePath -products '*' -requires Microsoft.VisualStudio.Component.VC.Tools.x86.x64 -property installationPath | Select-Object -First 1
if (-not $vcInstall) {
    throw 'Nie znaleziono Visual Studio Build Tools z komponentem Microsoft.VisualStudio.Component.VC.Tools.x86.x64.'
}

$toolchain = [string]$lock.toolchain.rustup_toolchain
$installedToolchains = (& rustup.exe toolchain list) -join "`n"
$effectiveToolchain = $toolchain
if ($installedToolchains -notmatch [regex]::Escape($toolchain)) {
    if ($ValidateOnly) {
        $activeToolchain = ((& rustup.exe show active-toolchain) -split '\s+')[0]
        $activeRustc = (& rustup.exe run $activeToolchain rustc --version).Trim()
        $activeCargo = (& rustup.exe run $activeToolchain cargo --version).Trim()
        if ($activeRustc -ne [string]$lock.toolchain.rustc_version -or $activeCargo -ne [string]$lock.toolchain.cargo_version) {
            throw "Brak przypiętego toolchainu Rust $toolchain. Zainstaluj: rustup toolchain install $toolchain"
        }
        $effectiveToolchain = $activeToolchain
        Write-Host "Uwaga: wersja jest dostępna jako '$activeToolchain', bez osobnego aliasu '$toolchain'."
    }
    else {
        Invoke-Checked 'rustup.exe' @('toolchain', 'install', $toolchain, '--profile', 'minimal') $PWD.Path
    }
}
$rustcActual = (& rustup.exe run $effectiveToolchain rustc --version).Trim()
$cargoActual = (& rustup.exe run $effectiveToolchain cargo --version).Trim()
if ($rustcActual -ne [string]$lock.toolchain.rustc_version -or $cargoActual -ne [string]$lock.toolchain.cargo_version) {
    throw "Niezgodny toolchain Rust. rustc='$rustcActual', cargo='$cargoActual'."
}

if ([string]::IsNullOrWhiteSpace($PassagesPath)) { $PassagesPath = Join-Path $moduleRoot 'passages.json' }
$passages = Get-Content -LiteralPath $PassagesPath -Raw -Encoding UTF8 | ConvertFrom-Json
$cases = Get-Content -LiteralPath (Join-Path $moduleRoot 'regression-cases.json') -Raw -Encoding UTF8 | ConvertFrom-Json
if ($passages.schema_version -ne 1 -or $cases.schema_version -ne 1) {
    throw 'Nieobsługiwana wersja konfiguracji własnych przejść lub testów.'
}
. (Join-Path $PSScriptRoot 'RegressionPolicy.ps1')
$regressionPolicy = Get-RegressionPolicy -Passages $passages -Cases $cases
$requiredRegressionIds = [string[]]@($regressionPolicy.RequiredIds)
$diagnosticRegressionIds = [string[]]@($regressionPolicy.DiagnosticIds)
Write-Host "OK: narzędzia, konfiguracja i wymagana wersja Rust są dostępne ($effectiveToolchain)."
if ($ValidateOnly) {
    Write-Host 'Walidacja wstępna zakończona. Nie pobrano, nie zbudowano ani nie zastąpiono instalacji.'
    exit 0
}

$targetParent = Split-Path $targetFull -Parent
if (-not (Test-Path -LiteralPath $targetParent -PathType Container)) {
    throw "Nie istnieje katalog nadrzędny celu: $targetParent"
}
if ([string]::IsNullOrWhiteSpace($StagingPath)) {
    $StagingPath = Join-Path $targetParent ('sea-router-install-staging-' + [DateTime]::Now.ToString('yyyyMMdd-HHmmss'))
}
$stageFull = [IO.Path]::GetFullPath($StagingPath)
if (Test-Path -LiteralPath $stageFull) {
    throw "Katalog roboczy już istnieje: $stageFull"
}
New-Item -ItemType Directory -Path $stageFull | Out-Null
Write-Host "Katalog roboczy: $stageFull"

$archivePath = Join-Path $stageFull 'sea-router-source.zip'
Write-Host "Pobieranie przypiętego kodu: $($lock.upstream.archive_url)"
Invoke-WebRequest -Uri ([string]$lock.upstream.archive_url) -OutFile $archivePath
$expandedPath = Join-Path $stageFull 'expanded'
Expand-Archive -LiteralPath $archivePath -DestinationPath $expandedPath
$sourceRoot = Get-ChildItem -LiteralPath $expandedPath -Directory | Select-Object -First 1
if ($null -eq $sourceRoot) { throw 'Archiwum kodu nie zawiera katalogu źródłowego.' }
$sourceRoot = $sourceRoot.FullName

foreach ($property in $lock.upstream.critical_git_blob_sha1.PSObject.Properties) {
    $relative = $property.Name.Replace('/', [IO.Path]::DirectorySeparatorChar)
    $sourceFile = Join-Path $sourceRoot $relative
    if (-not (Test-Path -LiteralPath $sourceFile -PathType Leaf)) {
        throw "Brak krytycznego pliku bazowego: $($property.Name)"
    }
    $actualBlob = Get-GitBlobSha1 $sourceFile
    Assert-GitObjectIdMatch -Actual $actualBlob -Expected $property.Value -Label "kod bazowy $($property.Name)"
}
Write-Host "OK: krytyczne pliki odpowiadają commitowi $($lock.upstream.commit)."

& (Join-Path $PSScriptRoot 'Apply-CustomPassages.ps1') -SourceRoot $sourceRoot -PassagesPath $PassagesPath
if ($LASTEXITCODE -ne 0) { throw 'Nie udało się zastosować własnych przejść.' }

$rustRoot = Join-Path $sourceRoot 'rust'
Invoke-Checked 'rustup.exe' @('run', $toolchain, 'cargo', 'build', '--release', '--locked') $rustRoot
$binaryPath = Join-Path $rustRoot 'target\release\sea-router-rs.exe'
if (-not (Test-Path -LiteralPath $binaryPath -PathType Leaf)) { throw 'Kompilacja nie utworzyła sea-router-rs.exe.' }
$binaryHash = Get-Sha256 $binaryPath
if ($binaryHash -ne [string]$lock.expected_custom_build.binary_sha256_observed) {
    Write-Warning "Binarium nie jest bitowo zgodne z zaobserwowanym ($binaryHash zamiast $($lock.expected_custom_build.binary_sha256_observed)). Ścieżka kompilacji może wpływać na plik EXE; kod, toolchain, graf i regresja nadal podlegają ścisłej kontroli."
}

$dataPath = Join-Path $sourceRoot 'data'
$graphPath = Join-Path $dataPath 'graph'
New-Item -ItemType Directory -Path $graphPath -Force | Out-Null
$landGzip = Join-Path $dataPath 'osm_land_simplified.geojson.json.gz'
$landJson = Join-Path $dataPath 'osm_land_simplified.geojson.json'
Write-Host "Pobieranie danych lądowych: $($lock.land_data.release_asset_url)"
Invoke-WebRequest -Uri ([string]$lock.land_data.release_asset_url) -OutFile $landGzip
if ((Get-Sha256 $landGzip) -ne [string]$lock.land_data.gzip_sha256) {
    throw 'Niezgodna suma SHA-256 pobranych skompresowanych danych lądowych.'
}
Expand-Gzip $landGzip $landJson
if ((Get-Sha256 $landJson) -ne [string]$lock.land_data.uncompressed_sha256) {
    throw 'Niezgodna suma SHA-256 rozpakowanych danych lądowych.'
}

$depth = [string]$lock.graph_generation.depth
Invoke-Checked $binaryPath @('generate', $depth, $dataPath) $rustRoot
$generatedGraph = Join-Path $graphPath 'sea-graph.json'
$rawGraphHash = Get-Sha256 $generatedGraph
if ($rawGraphHash -ne [string]$lock.expected_custom_build.graph_sha256) {
    Write-Warning "Surowy JSON grafu ma inny SHA-256 ($rawGraphHash). Kolejność krawędzi jest niedeterministyczna; o akceptacji decyduje ścisła kontrola semantyczna poniżej."
}

$canonicalizerSource = Join-Path $moduleRoot 'tools\GraphSemanticCanonicalizer.rs'
if (-not (Test-Path -LiteralPath $canonicalizerSource -PathType Leaf)) {
    throw "Brak analizatora semantycznego grafu: $canonicalizerSource"
}
$canonicalizerExe = Join-Path $stageFull 'GraphSemanticCanonicalizer.exe'
$canonicalNodes = Join-Path $stageFull 'graph-nodes.canonical.bin'
$canonicalEdges = Join-Path $stageFull 'graph-edges.canonical.bin'
Invoke-Checked 'rustup.exe' @(
    'run', $toolchain, 'rustc', '--edition=2021', '-O',
    $canonicalizerSource, '-o', $canonicalizerExe
) $stageFull
Invoke-Checked $canonicalizerExe @($generatedGraph, $canonicalNodes, $canonicalEdges) $stageFull

$expectedNodeCount = [int64]$lock.base_graph_asset.node_count
$expectedEdgeCount = [int64]$lock.base_graph_asset.edge_count
foreach ($passage in $passages.passages) {
    $expectedNodeCount += [int64]$passage.observed_graph_delta.nodes
    $expectedEdgeCount += [int64]$passage.observed_graph_delta.edges
}
$expectedNodeBytes = 12L + ($expectedNodeCount * 24L)
$expectedEdgeBytes = 12L + ($expectedEdgeCount * 12L)
$actualNodeBytes = (Get-Item -LiteralPath $canonicalNodes).Length
$actualEdgeBytes = (Get-Item -LiteralPath $canonicalEdges).Length
if ($actualNodeBytes -ne $expectedNodeBytes) {
    throw "Niezgodna liczba węzłów grafu: plik kanoniczny ma $actualNodeBytes bajtów zamiast $expectedNodeBytes dla $expectedNodeCount węzłów."
}
if ($actualEdgeBytes -ne $expectedEdgeBytes) {
    throw "Niezgodna liczba krawędzi grafu: plik kanoniczny ma $actualEdgeBytes bajtów zamiast $expectedEdgeBytes dla $expectedEdgeCount krawędzi."
}
$nodeSemanticHash = Get-Sha256 $canonicalNodes
$edgeSemanticHash = Get-Sha256 $canonicalEdges
Assert-CustomPassageGraph -CanonicalNodes $canonicalNodes -CanonicalEdges $canonicalEdges -Passages $passages.passages -BaseNodeCount ([int64]$lock.base_graph_asset.node_count) -BaseEdgeCount ([int64]$lock.base_graph_asset.edge_count)
$sourcePassagesHash = Get-Sha256 $PassagesPath
if ($sourcePassagesHash -eq [string]$lock.expected_custom_build.source_passages_sha256) {
    if ($nodeSemanticHash -ne [string]$lock.expected_custom_build.semantic_graph.ordered_nodes_sha256) {
        throw "Semantycznie niezgodne węzły referencyjnego grafu: $nodeSemanticHash."
    }
    if ($edgeSemanticHash -ne [string]$lock.expected_custom_build.semantic_graph.sorted_edges_sha256) {
        throw "Semantycznie niezgodny multizbiór krawędzi referencyjnego grafu: $edgeSemanticHash."
    }
    Write-Host 'OK: konfiguracja referencyjna ma także oczekiwane pełne hashe semantyczne.'
}
Write-Host "OK: graf semantycznie zgodny ($expectedNodeCount węzłów, $expectedEdgeCount krawędzi)."

# Są to duże, odtwarzalne pliki tymczasowe utworzone w kontrolowanym stagingu.
Remove-Item -LiteralPath $canonicalNodes, $canonicalEdges, $canonicalizerExe -Force

$stdoutLog = Join-Path $sourceRoot 'sea-router-test.stdout.log'
$stderrLog = Join-Path $sourceRoot 'sea-router-test.stderr.log'
$processInfo = [Diagnostics.ProcessStartInfo]::new()
$processInfo.FileName = $binaryPath
$processInfo.Arguments = 'serve "' + $dataPath.Replace('"', '\"') + '"'
$processInfo.WorkingDirectory = $rustRoot
$processInfo.UseShellExecute = $false
$processInfo.EnvironmentVariables['PORT'] = [string]$TestPort
$processInfo.RedirectStandardOutput = $true
$processInfo.RedirectStandardError = $true
$server = [Diagnostics.Process]::new()
$server.StartInfo = $processInfo
if (-not $server.Start()) { throw 'Nie udało się uruchomić serwera testowego.' }
$stdoutTask = $server.StandardOutput.ReadToEndAsync()
$stderrTask = $server.StandardError.ReadToEndAsync()
try {
    $baseUrl = "http://127.0.0.1:$TestPort"
    $ready = $false
    for ($attempt = 0; $attempt -lt 120; $attempt++) {
        if ($server.HasExited) { throw "Serwer testowy zakończył się przed testami (kod $($server.ExitCode))." }
        try {
            Invoke-WebRequest -Uri "$baseUrl/route?from=15.50,38.05&to=15.78,38.34&penalty=5" -TimeoutSec 2 | Out-Null
            $ready = $true
            break
        }
        catch { Start-Sleep -Seconds 1 }
    }
    if (-not $ready) { throw 'Serwer testowy nie zgłosił gotowości w ciągu 120 sekund.' }
    & (Join-Path $PSScriptRoot 'Test-SeaRouter.ps1') -BaseUrl $baseUrl `
        -RequiredCaseIds $requiredRegressionIds `
        -DiagnosticCaseIds $diagnosticRegressionIds
    if ($LASTEXITCODE -ne 0) { throw 'Testy regresji sea-routera nie przeszły.' }
}
finally {
    Stop-TestServerProcess -Process $server
    [IO.File]::WriteAllText($stdoutLog, $stdoutTask.Result, [Text.UTF8Encoding]::new($false))
    [IO.File]::WriteAllText($stderrLog, $stderrTask.Result, [Text.UTF8Encoding]::new($false))
    $server.Dispose()
}

Move-Item -LiteralPath $sourceRoot -Destination $targetFull
Write-Host "Sea-router został odtworzony i zweryfikowany w: $targetFull" -ForegroundColor Green
Write-Host "Katalog roboczy pozostał w $stageFull (archiwum kodu i katalog expanded bez przeniesionego źródła)."
