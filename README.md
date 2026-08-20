# Rejsy-morskie

Narzędzie do przygotowywania morskich tras rejsów na podstawie skoroszytu Excel. Program ma uzupełniać współrzędne portów, obliczać dni i daty, wyznaczać odcinki przez sea-router oraz eksportować KML do Google My Maps.

## Stan projektu

To pierwsza wersja specyfikacji i szkieletu aplikacji. Obliczenia kalendarza są zaimplementowane; integracje z geokoderem i sea-routerem mają jawne interfejsy i wymagają wyboru konkretnego dostawcy lub lokalnego programu.

## Dane wejściowe

Skoroszyt zawiera trzy arkusze:

- **Rejsy** — jeden wiersz na rejs;
- **Porty** — porty w kolejności odwiedzin;
- **Etapy** — wynik generowany przez program.

Pełna definicja kolumn i reguł: [docs/specyfikacja-excel.md](docs/specyfikacja-excel.md).

## Najważniejsze zasady

- `Kiedy=+N` oznacza wpływ do portu w N-tym dniu rejsu.
- Konkretna data w `Kiedy` jest przeliczana względem `Data_startu`; dzień startu to dzień 1.
- Puste `Postoj_dni` oznacza 1.
- `Lat` i `Lon` są opcjonalne. Program korzysta z nich, a brakujące wartości pobiera i utrwala w wynikowym skoroszycie.
- Niejednoznacznego portu program nie wybiera automatycznie — wymaga zatwierdzenia.
- Ciężkie grafy sea-routera i dane OSM pozostają lokalne i są ignorowane przez Git.

## Planowany przepływ

1. Wczytanie i walidacja Excela.
2. Normalizacja `Kiedy`, dat i postojów.
3. Uzupełnienie brakujących współrzędnych.
4. Utworzenie etapów pomiędzy kolejnymi portami.
5. Wyznaczenie geometrii przez sea-router.
6. Zapis skoroszytu wynikowego, GeoJSON i KML.

## Uruchomienie szkieletu

Wymagany jest Python 3.11+.

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -e ".[dev]"
rejsy-morskie validate examples/rejs-przyklad.xlsx
```

Plik XLSX nie jest jeszcze przechowywany w repozytorium; układ przykładu jest opisany w [examples/README.md](examples/README.md).

## Struktura

- `src/rejsy_morskie/excel_io.py` — odczyt i zapis skoroszytu;
- `src/rejsy_morskie/schedule.py` — obliczenia dni, dat i etapów;
- `src/rejsy_morskie/geocoding.py` — cache i interfejs geokodera;
- `src/rejsy_morskie/sea_router.py` — interfejs adaptera sea-routera;
- `src/rejsy_morskie/kml.py` — eksport KML;
- `src/rejsy_morskie/cli.py` — polecenia programu;
- `src/geojson_to_kml.ps1` — istniejący pomocniczy konwerter PowerShell.

## Duże dane

Do repozytorium nie trafiają lokalne dane OSM, grafy routingu ani wygenerowane wyniki. Domyślne miejsca to `local-data/`, `data/` i `outputs/`.
