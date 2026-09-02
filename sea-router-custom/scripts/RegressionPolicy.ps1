Set-StrictMode -Version Latest

function Get-PassageRegressionTestId {
    param([Parameter(Mandatory)][string]$PassageId)
    if ($PassageId -eq 'strait-of-messina') { return 'messina' }
    return $PassageId
}

function Get-RegressionPolicy {
    param(
        [Parameter(Mandatory)][object]$Passages,
        [Parameter(Mandatory)][object]$Cases,
        [string[]]$AlwaysRequired = @('messina', 'suez', 'panama', 'corinth')
    )
    $enabled = @{}
    foreach ($case in $Cases.cases) {
        if ([bool]$case.enabled) { $enabled[[string]$case.id] = $true }
    }
    $required = [Collections.Generic.List[string]]::new()
    $diagnostic = [Collections.Generic.List[string]]::new()
    foreach ($id in $AlwaysRequired) {
        if (-not $enabled.ContainsKey($id)) {
            throw "Brak aktywnej obowiązkowej regresji '$id'."
        }
        if (-not $required.Contains($id)) { $required.Add($id) }
    }
    foreach ($passage in $Passages.passages) {
        $statusProperty = $passage.PSObject.Properties['status']
        $status = if ($null -eq $statusProperty -or [string]::IsNullOrWhiteSpace([string]$statusProperty.Value)) {
            'stable'
        } else {
            ([string]$statusProperty.Value).Trim().ToLowerInvariant()
        }
        if ($status -notin @('development', 'stable')) {
            throw "Przejście '$($passage.name)' ma nieprawidłowy status '$status'."
        }
        $testId = Get-PassageRegressionTestId ([string]$passage.id)
        if ($status -eq 'stable') {
            if (-not $enabled.ContainsKey($testId)) {
                throw "Stabilne przejście '$($passage.name)' nie ma aktywnego testu regresji '$testId'."
            }
            if (-not $required.Contains($testId)) { $required.Add($testId) }
        }
        elseif ($enabled.ContainsKey($testId) -and -not $required.Contains($testId)) {
            $diagnostic.Add($testId)
        }
    }
    return [pscustomobject]@{
        RequiredIds = [string[]]$required.ToArray()
        DiagnosticIds = [string[]]$diagnostic.ToArray()
    }
}
