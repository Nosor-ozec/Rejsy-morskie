function ConvertTo-NormalizedGitObjectId {
    param(
        [AllowNull()]
        [object]$Value,
        [string]$Label = 'identyfikator Git'
    )

    if ($null -eq $Value) {
        throw "Brak wartości: $Label."
    }
    $normalized = ([string]$Value).Trim()
    if ($normalized -cnotmatch '^[0-9a-fA-F]{40}$') {
        throw "Nieprawidłowy ${Label}: oczekiwano dokładnie 40 znaków hex po Trim(), otrzymano $($normalized.Length)."
    }
    return $normalized.ToLowerInvariant()
}

function Assert-GitObjectIdMatch {
    param(
        [AllowNull()]
        [object]$Actual,
        [AllowNull()]
        [object]$Expected,
        [string]$Label = 'kod bazowy'
    )

    $actualNormalized = ConvertTo-NormalizedGitObjectId -Value $Actual -Label "$Label (wynik)"
    $expectedNormalized = ConvertTo-NormalizedGitObjectId -Value $Expected -Label "$Label (lockfile)"
    if (-not [string]::Equals($actualNormalized, $expectedNormalized, [StringComparison]::Ordinal)) {
        throw "Niezgodny ${Label}: $actualNormalized zamiast $expectedNormalized."
    }
}
