# Rejsy-morskie

Narzędzie do przygotowywania morskich tras rejsów na podstawie skoroszytu Excel. Program uzupełnia współrzędne portów, oblicza dni i daty, wyznacza odcinki przez sea-router oraz eksportuje KML do Google My Maps / Google Earth.

## Dokumentacja projektu

- [Założenia projektu](docs/zalozenia-projektu.md) — cel, docelowy rezultat, zasada odtwarzalności i planowane funkcje.
- [Organizacja pracy](docs/organizacja-pracy.md) — gdzie przechowywane są dane, kto i jak je zmienia oraz jak uruchamia się generator.
- [Specyfikacja Excela](docs/specyfikacja-excel.md) — techniczna definicja arkuszy, kolumn i reguł.

## Stan projektu

Generator obsługuje cały podstawowy przepływ: sprawdza harmonogram, uzupełnia współrzędne z cache/Nominatim, wyznacza odcinki przez lokalny `sea-router`, liczy długości, zapisuje GeoJSON oraz tworzy wynikowy Excel i KML.

Planowanym kolejnym rozszerzeniem jest przypisywanie filmów do portów przez pole `Filmy_grupa`. Uzgodniona koncepcja jest opisana w `docs/zalozenia-projektu.md`; nie jest jeszcze zaimplementowana w bieżącej wersji programu.

## Dane wejściowe

Głównym plikiem danych projektu jest:

`routes/rejsy.xlsx`

Skoroszyt zawiera trzy arkusze:

- **Rejsy** — jeden wiersz na rejs;
- **Porty** — porty w kolejności odwiedzin;
- **Etapy** — wynik generowany przez program.

`routes/rejsy.xlsx` jest częścią projektu i ma być przechowywany w GitHubie razem z kodem i dokumentacją. Lokalna kopia robocza znajduje się standardowo w `E:\Rejsy-morskie\routes\rejsy.xlsx`.

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
- Zmiana struktury Excela wymaga równoczesnej aktualizacji specyfikacji, kodu i danych wejściowych.

## Przepływ

1. Użytkownik wprowadza lub poprawia dane w `routes/rejsy.xlsx`.
2. Program wczytuje i waliduje Excel.
3. Normalizuje `Kiedy`, daty i postoje.
4. Uzupełnia brakujące współrzędne.
5. Tworzy etapy pomiędzy kolejnymi portami.
6. Wyznacza geometrię przez lokalny sea-router.
7. Zapisuje wynikowy skoroszyt, GeoJSON i KML w `outputs/`.
8. KML jest sprawdzany/importowany w Google My Maps / Google Earth.

Zwykłe dopisywanie danych rejsu nie wymaga zmiany programu. Zmiana struktury skoroszytu jest zmianą programu i powinna zostać wykonana razem z aktualizacją dokumentacji oraz testów.

## Uruchomienie

Wymagany jest Python 3.11+.

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -e ".[dev]"
```

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
- `outputs/<Rejs_ID>/trasa.kml` — plik do Google My Maps / Google Earth;
- `outputs/geocoding-cache.json` — lokalny cache współrzędnych.

Codex/Work może wykonywać i testować ten proces podczas rozwoju programu, ale do zwykłego generowania wyników nie jest wymagany — program działa lokalnie na komputerze z odpowiednim środowiskiem i danymi sea-routera.

### Geokodowanie OpenStreetMap

Domyślnym geokoderem jest publiczny Nominatim. Program wysyła zapytania pojedynczo (maksymalnie jedno na sekundę), identyfikuje aplikację i zapisuje wyniki w cache. Dane: © OpenStreetMap contributors, ODbL. Przy większej lub komercyjnej skali należy skonfigurować własną instancję albo innego dostawcę.

## Struktura

- `src/rejsy_morskie/excel_io.py` — odczyt i zapis skoroszytu;
- `src/rejsy_morskie/schedule.py` — obliczenia dni, dat i etapów;
- `src/rejsy_morskie/geocoding.py` — cache i interfejs geokodera;
- `src/rejsy_morskie/sea_router.py` — interfejs adaptera sea-routera;
- `src/rejsy_morskie/kml.py` — eksport KML;
- `src/rejsy_morskie/cli.py` — polecenia programu;
- `routes/rejsy.xlsx` — wersjonowane dane wejściowe rejsów;
- `docs/` — założenia, organizacja pracy i specyfikacja danych.

## Dane lokalne i wyniki

Do repozytorium nie trafiają duże dane OSM, grafy routingu ani wygenerowane wyniki. Domyślne miejsca to `local-data/`, `data/` i `outputs/`.

Repozytorium GitHub jest podstawowym trwałym zapisem projektu. Istotne decyzje powinny być zapisywane w dokumentacji, a ukończone zmiany kodu i danych wejściowych commitowane do repozytorium; historia rozmów lub sesja Work nie zastępuje dokumentacji projektu.
