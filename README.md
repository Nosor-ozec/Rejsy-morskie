# Rejsy-morskie

Narzędzie do przygotowywania morskich tras rejsów na podstawie skoroszytu Excel. Program ma uzupełniać współrzędne portów, obliczać dni i daty, wyznaczać odcinki przez sea-router oraz eksportować KML do Google My Maps.

## Stan projektu

Generator obsługuje cały przepływ: sprawdza harmonogram, uzupełnia współrzędne z cache/Nominatim, wyznacza odcinki przez lokalny `sea-router`, liczy długości, zapisuje GeoJSON oraz tworzy wynikowy Excel i KML.

## Dane wejściowe

Skoroszyt zawiera trzy arkusze:

- **Rejsy** — jeden wiersz na rejs;
- **Porty** — porty w kolejności odwiedzin;
- **Etapy** — wynik generowany przez program.

Pełna definicja kolumn i reguł: [docs/specyfikacja-excel.md](docs/specyfikacja-excel.md).

## Najważniejsze zasady

- Liczba `N` w `Kiedy` oznacza wpływ do portu `N` dni po `Data_startu`; `0` oznacza datę startu. Zapis `+N` jest akceptowany dla zgodności wstecznej.
- Konkretna data w `Kiedy` jest punktem kontrolnym harmonogramu; dzień startu ma w wynikach numer 1.
- W `Porty` puste `Rejs_ID` oznacza tę samą wartość co w poprzednim niepustym wierszu.
- Puste `Postoj_dni` oznacza 1.
- `Lat` i `Lon` są opcjonalne. Program korzysta z nich, a brakujące wartości pobiera i utrwala w wynikowym skoroszycie.
- Niejednoznacznego portu program nie wybiera automatycznie — wymaga zatwierdzenia.
- `Kraj` warto uzupełnić, ponieważ rozróżnia miasta o tych samych nazwach.
- `Kolor_trasy` może być kodem `#RRGGBB` albo polską nazwą, np. `Niebieski`.
- Ciężkie grafy sea-routera i dane OSM pozostają lokalne i są ignorowane przez Git.

## Przepływ

1. Wczytanie i walidacja Excela.
2. Normalizacja `Kiedy`, dat i postojów.
3. Uzupełnienie brakujących współrzędnych.
4. Utworzenie etapów pomiędzy kolejnymi portami.
5. Wyznaczenie geometrii przez sea-router.
6. Zapis skoroszytu wynikowego, GeoJSON i KML.

## Uruchomienie

Wymagany jest Python 3.11+.

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -e ".[dev]"
rejsy-morskie validate examples/rejs-przyklad.xlsx
```

Plik XLSX nie jest jeszcze przechowywany w repozytorium; układ przykładu jest opisany w [examples/README.md](examples/README.md).

Uruchom lokalny router w osobnym oknie:

```powershell
E:\sea-router\rust\target\release\sea-router-rs.exe serve E:\sea-router\data
```

Następnie wygeneruj komplet wyników:

```powershell
rejsy-morskie generate E:\Rejsy-morskie\routes\rejsy.xlsx E:\Rejsy-morskie\outputs
```

Powstaną:

- `outputs/rejs-uzupelniony.xlsx` — współrzędne, daty, etapy, dystanse i statusy;
- `outputs/<Rejs_ID>/geojson/*.geojson` — geometria każdego etapu;
- `outputs/<Rejs_ID>/trasa.kml` — plik do Google My Maps;
- `outputs/geocoding-cache.json` — lokalny cache współrzędnych.

### Geokodowanie OpenStreetMap

Domyślnym geokoderem jest publiczny Nominatim. Program wysyła zapytania pojedynczo (maksymalnie jedno na sekundę), identyfikuje aplikację i zapisuje wyniki w cache. Dane: © OpenStreetMap contributors, ODbL. Przy większej lub komercyjnej skali należy skonfigurować własną instancję albo innego dostawcę. Zasady: https://operations.osmfoundation.org/policies/nominatim/

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


