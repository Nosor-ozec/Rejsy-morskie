Set-StrictMode -Version Latest

function Assert-CustomPassageGraph {
    param(
        [Parameter(Mandatory)][string]$CanonicalNodes,
        [Parameter(Mandatory)][string]$CanonicalEdges,
        [Parameter(Mandatory)][object]$Passages,
        [Parameter(Mandatory)][int64]$BaseNodeCount,
        [Parameter(Mandatory)][int64]$BaseEdgeCount
    )
    $expectedCustomNodes = 0L
    $expectedCustomEdges = 0L
    foreach ($passage in $Passages) {
        $count = [int64]$passage.waypoints.Count
        $expectedCustomNodes += $count
        $expectedCustomEdges += ($count - 1L + 10L)
    }
    $nodeStream = [IO.File]::OpenRead($CanonicalNodes)
    $reader = [IO.BinaryReader]::new($nodeStream)
    try {
        if ([Text.Encoding]::ASCII.GetString($reader.ReadBytes(4)) -ne 'SRN1') { throw 'Nieprawidłowy nagłówek kanonicznych węzłów.' }
        $nodeCount = $reader.ReadInt64()
        if ($nodeCount -ne $BaseNodeCount + $expectedCustomNodes) { throw "Niezgodna liczba węzłów: $nodeCount." }
        $nodeStream.Position = 12L + ($BaseNodeCount * 24L)
        foreach ($passage in $Passages) {
            foreach ($point in $passage.waypoints) {
                $actualLon = $reader.ReadDouble(); $actualLat = $reader.ReadDouble(); $actualDepth = $reader.ReadDouble()
                $expectedLon = [Math]::Round([double]$point[0], 5); $expectedLat = [Math]::Round([double]$point[1], 5)
                if ([Math]::Abs($actualLon - $expectedLon) -gt 0.000000001 -or [Math]::Abs($actualLat - $expectedLat) -gt 0.000000001 -or [Math]::Abs($actualDepth - 1.0) -gt 0.000000001) {
                    throw "Węzeł przejścia '$($passage.name)' nie odpowiada zatwierdzonym współrzędnym."
                }
            }
        }
    }
    finally { $reader.Dispose(); $nodeStream.Dispose() }

    $ranges = @(); $next = $BaseNodeCount
    foreach ($passage in $Passages) {
        $ranges += [pscustomobject]@{ Passage=$passage; First=$next; Last=$next + $passage.waypoints.Count - 1; External=@{}; Chains=@{}; Connected=0 }
        $next += $passage.waypoints.Count
    }
    $edgeStream = [IO.File]::OpenRead($CanonicalEdges); $edgeReader = [IO.BinaryReader]::new($edgeStream)
    try {
        if ([Text.Encoding]::ASCII.GetString($edgeReader.ReadBytes(4)) -ne 'SRE1') { throw 'Nieprawidłowy nagłówek kanonicznych krawędzi.' }
        $edgeCount = $edgeReader.ReadInt64()
        if ($edgeCount -ne $BaseEdgeCount + $expectedCustomEdges) { throw "Niezgodna liczba krawędzi: $edgeCount." }
        for ($index = 0L; $index -lt $edgeCount; $index++) {
            $from = [int64]$edgeReader.ReadUInt32(); $to = [int64]$edgeReader.ReadUInt32(); $null = $edgeReader.ReadUInt32()
            if ($from -lt $BaseNodeCount -and $to -lt $BaseNodeCount) { continue }
            $owner = $null
            foreach ($range in $ranges) {
                if (($from -ge $range.First -and $from -le $range.Last) -or ($to -ge $range.First -and $to -le $range.Last)) { $owner = $range; break }
            }
            if ($null -eq $owner) { throw 'Krawędź wskazuje nieznany własny węzeł.' }
            $owner.Connected++
            $fromCustom = $from -ge $owner.First -and $from -le $owner.Last
            $toCustom = $to -ge $owner.First -and $to -le $owner.Last
            if ($fromCustom -and $toCustom) {
                if ([Math]::Abs($from - $to) -ne 1) { throw "Przejście '$($owner.Passage.name)' ma nieoczekiwaną krawędź wewnętrzną." }
                $key = [string][Math]::Min($from, $to); $old = 0; if ($owner.Chains.ContainsKey($key)) { $old = [int]$owner.Chains[$key] }; $owner.Chains[$key] = 1 + $old
            } else {
                $customId = if ($fromCustom) { $from } else { $to }
                if ($customId -ne $owner.First -and $customId -ne $owner.Last) { throw "Przejście '$($owner.Passage.name)' łączy bazowy graf z punktem wewnętrznym." }
                $key = [string]$customId; $old = 0; if ($owner.External.ContainsKey($key)) { $old = [int]$owner.External[$key] }; $owner.External[$key] = 1 + $old
            }
        }
    }
    finally { $edgeReader.Dispose(); $edgeStream.Dispose() }
    foreach ($range in $ranges) {
        $expected = $range.Last - $range.First + 10
        if ($range.Connected -ne $expected) { throw "Przejście '$($range.Passage.name)' ma $($range.Connected) krawędzi zamiast $expected." }
        for ($id = $range.First; $id -lt $range.Last; $id++) { $chainCount = 0; if ($range.Chains.ContainsKey([string]$id)) { $chainCount = [int]$range.Chains[[string]$id] }; if ($chainCount -ne 1) { throw "Brak jednoznacznego odcinka $id-$($id+1)." } }
        $firstCount = 0; $lastCount = 0
        if ($range.External.ContainsKey([string]$range.First)) { $firstCount = [int]$range.External[[string]$range.First] }
        if ($range.External.ContainsKey([string]$range.Last)) { $lastCount = [int]$range.External[[string]$range.Last] }
        if ($firstCount -ne 5 -or $lastCount -ne 5) { throw "Końce przejścia '$($range.Passage.name)' nie mają po 5 połączeń z grafem bazowym." }
    }
}
