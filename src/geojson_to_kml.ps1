$inputFile = Join-Path $PSScriptRoot "dubrovnik-catania-civitavecchia.geojson"
$outputFile = Join-Path $PSScriptRoot "dubrovnik-catania-civitavecchia.kml"

$json = Get-Content $inputFile -Raw -Encoding UTF8 | ConvertFrom-Json

$final = $json.features |
    Where-Object { $_.properties.name -eq "final" } |
    Select-Object -First 1

if (-not $final) {
    throw "Nie znaleziono warstwy final w pliku GeoJSON."
}

$inv = [System.Globalization.CultureInfo]::InvariantCulture

$coords = ($final.geometry.coordinates | ForEach-Object {
    [string]::Format($inv, "{0},{1},0", $_[0], $_[1])
}) -join "`r`n"

$kml = @"
<?xml version="1.0" encoding="UTF-8"?>
<kml xmlns="http://www.opengis.net/kml/2.2">
<Document>
    <name>Dubrovnik - Catania - Civitavecchia</name>

    <Style id="routeStyle">
        <LineStyle>
            <color>ff0000ff</color>
            <width>4</width>
        </LineStyle>
    </Style>

    <Placemark>
        <name>Trasa morska</name>
        <styleUrl>#routeStyle</styleUrl>
        <LineString>
            <tessellate>1</tessellate>
            <altitudeMode>clampToGround</altitudeMode>
            <coordinates>
$coords
            </coordinates>
        </LineString>
    </Placemark>

    <Placemark>
        <name>Dubrovnik</name>
        <Point><coordinates>18.09,42.64,0</coordinates></Point>
    </Placemark>

    <Placemark>
        <name>Catania</name>
        <Point><coordinates>15.0998,37.4982,0</coordinates></Point>
    </Placemark>

    <Placemark>
        <name>Civitavecchia</name>
        <Point><coordinates>11.755,42.108,0</coordinates></Point>
    </Placemark>

</Document>
</kml>
"@

Set-Content -Path $outputFile -Value $kml -Encoding UTF8

Write-Host "Gotowe:"
Write-Host $outputFile
Write-Host "Liczba punktow trasy:" $final.geometry.coordinates.Count