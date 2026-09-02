# Rejsy-morskie

Narzędzie do przygotowywania morskich tras rejsów i kompletnej prezentacji Leaflet na podstawie dwóch skoroszytów Excel. Program uzupełnia współrzędne portów, oblicza dni i daty, wyznacza odcinki przez sea-router, łączy media z portami i punktami `Na morzu` oraz buduje pełny podgląd lokalny.

## Dokumentacja projektu

- [Założenia projektu](docs/zalozenia-projektu.md) — cel, docelowy rezultat, zasada odtwarzalności i planowane funkcje.
- [Organizacja pracy](docs/organizacja-pracy.md) — gdzie przechowywane są dane, kto i jak je zmienia oraz jak uruchamia się generator.
- [Specyfikacja Excela](docs/specyfikacja-excel.md) — techniczna definicja arkuszy, kolumn i reguł.
- [Mapowy edytor portów](docs/edytor-portow.md) — bezpieczna edycja `Porty` i trwałych współrzędnych `Lokalizacje`.

## Stan projektu

Generator obsługuje cały przepływ: aktualizuje `routes/rejsy.xlsx` w miejscu, zapisuje rzeczywiste GeoJSON i pomocniczy KML, czyta `routes/media.xlsx` oraz przygotowuje lokalną stronę Leaflet. Publikacja jest osobnym, świadomym krokiem i nie wykonuje operacji Git.

## Dane wejściowe

Głównym plikiem danych projektu jest:

`routes/rejsy.xlsx`

Skoroszyt zawiera cztery arkusze:

- **Rejsy** — jeden wiersz na rejs;
- **Porty** — porty i techniczne punkty trasy w kolejności osiągania;
- **Lokalizacje** — trwała baza ręcznie zatwierdzonych współrzędnych;
- **Etapy** — wynik generowany przez program.

`routes/rejsy.xlsx` jest częścią projektu i ma być przechowywany w GitHubie razem z kodem i dokumentacją. Lokalna kopia robocza znajduje się standardowo w `E:\Rejsy-morskie\routes\rejsy.xlsx`.

Pełna definicja kolumn i reguł: [docs/specyfikacja-excel.md](docs/specyfikacja-excel.md).

## Najważniejsze zasady

- Cała kolumna `Porty.Kiedy` ma format tekstowy. Jedyny dozwolony zapis daty to `RRRR-MM-DD`, np. `2024-12-10`; oznacza on bezwzględną datę wpływu.
- Tekst `N` złożony wyłącznie z cyfr oznacza wpływ `N` dni po `Data_startu`; `0` oznacza datę startu.
- `Kiedy` ma identyczne znaczenie dla portów i obu typów punktów trasy. `0` jest kotwicą daty startu, ale nie nadaje wierszowi roli portu startowego; `+0` zachowuje dzień względem poprzedniego wiersza zgodnie z regułą postoju.
- `0` i `+0` nie są zamienne. `0` w dowolnym wierszu zawsze oznacza dokładnie `Data_startu + 0 dni`, niezależnie od jego pozycji; nie oznacza „pierwszego portu”. `+0` jest wartością względną i oznacza datę poprzedniego wiersza powiększoną o `max(Postoj_dni_poprzedniego - 1, 0)`. Dlatego późniejszy wiersz z `0` może ujawnić błąd chronologii zamiast przejąć datę poprzednika.
- Tekst `+N` oznacza `N` dni względem poprzedniego wiersza `Porty`, z uwzględnieniem dodatkowych pełnych dni jego postoju. Obowiązuje wzór: `data_bieżącego = data_poprzedniego + N + max(Postoj_dni_poprzedniego - 1, 0)`.
- `Postoj_dni = 0` ani `Postoj_dni = 1` nie dodają osobnego dnia do harmonogramu; przy `Postoj_dni = 2` dochodzi 1 dzień, przy `3` dochodzą 2 dni itd. Dzień wpływu jest już pierwszym dniem portowym.
- Kolejne wpisy `+N` tworzą łańcuch uwzględniający tę regułę dla każdego postoju. Data `RRRR-MM-DD` i tekst `N` bez znaku są niezależnymi kotwicami: mogą obejmować dowolny czas żeglugi, którego nie opisano przez `+N`. Program sprawdza tylko chronologię — kotwica nie może cofać czasu ani nakładać się na postój poprzedniego portu.
- `Kiedy` jest wyłącznie wejściem użytkownika. Program nigdy nie zmienia, nie normalizuje ani nie zastępuje wpisanych wartości; `+2` pozostaje `+2`, a `2024-12-10` pozostaje tekstem. Wyliczone daty zapisuje wyłącznie w danych wynikowych i arkuszu `Etapy`.
- Tekstowe daty w innych formatach, m.in. `DD.MM.RRRR` i zapisy ze slashami, są błędem.
- W `Porty` puste `Rejs_ID` oznacza tę samą wartość co w poprzednim niepustym wierszu.
- Puste `Postoj_dni` oznacza 1. W obliczeniu kolejnego portu postój wnosi `max(Postoj_dni - 1, 0)` dodatkowych dni.
- Ręczne `Porty.Lat/Lon` mają pierwszeństwo. Jeśli są puste, program szuka dokładnej nazwy w `Lokalizacje`; dopiero później geokoduje zwykły port.
- `Lokalizacje` przechowuje porty, kotwicowiska, wyspy, punkty trasy i inne zatwierdzone miejsca. Dopasowanie pola `Port` do `Nazwa` ignoruje wielkość liter oraz spacje na początku i końcu, ale nie zgaduje podobnych nazw.
- Dla `Punkt_trasy` i `Punkt_trasy_ukryty` współrzędne mogą znajdować się bezpośrednio w `Porty` albo w `Lokalizacje`. Punktów trasy program nigdy nie geokoduje. `Postoj_dni` takiego punktu musi wynosić 0.
- Puste `Porty.Lat/Lon` punktu trasy są poprawnym wejściem. Program najpierw próbuje odtworzyć je z `Lokalizacje`, a dopiero po nieudanym wyszukaniu zgłasza brak współrzędnych; walidacja nie wymaga wcześniejszego ręcznego kopiowania wartości do `Porty`.
- Dane `Lokalizacje.Lat/Lon` są nienaruszalnym wejściem użytkownika: program ich nie poprawia, nie usuwa ani nie nadpisuje. Może jedynie skopiować je do pustych `Porty.Lat/Lon`.
- Niejednoznacznego portu program nie wybiera automatycznie — wymaga zatwierdzenia.
- `Kraj` warto uzupełnić, ponieważ rozróżnia miasta o tych samych nazwach.
- `Kolor_trasy` może być kodem `#RRGGBB` albo polską nazwą, np. `Niebieski`.
- Ciężkie grafy sea-routera i dane OSM pozostają lokalne i są ignorowane przez Git.
- Lekki moduł `sea-router-custom` przypina bazową wersję, zapisuje własne przejścia oraz zawiera skrypt odtworzenia i testy regresji. Szczegóły: [`docs/sea-router-instalacja.md`](docs/sea-router-instalacja.md).
- Punkty własnych przejść są utrzymywane wyłącznie w `Lokalizacje` (`Przejscie`, `Przejscie_lp`, `Przejscie_status`). `development` oznacza projektowanie z nieblokującą regresją diagnostyczną, a `stable` — zatwierdzone przejście chronione obowiązkową regresją. `sea-router-custom/passages.json` jest generowany automatycznie i nie powinien być edytowany ręcznie. Procedura: [`docs/dodawanie-przejsc-sea-router.md`](docs/dodawanie-przejsc-sea-router.md).
- Punkty i status przejść można wygodnie edytować na mapie przez `Edytuj-Przejscia.cmd`. Edytor nie tworzy dodatkowej bazy: czyta i atomowo zapisuje wyłącznie wiersze wybranego przejścia w `routes/rejsy.xlsx / Lokalizacje`.
- Porty i punkty konkretnego rejsu edytuje osobne `Edytuj-Porty.cmd`. `Porty` odpowiada za kolejność i harmonogram, a przeciągnięte lub dodane współrzędne są utrwalane pod nazwą w `Lokalizacje`.
- Zmiana struktury Excela wymaga równoczesnej aktualizacji specyfikacji, kodu i danych wejściowych.

### Dzień wpływu i zakres etapu

- Dzień wpływu ma numer `(data wpływu - Data_startu) + 1`; dzień startu to dzień 1.
- Dla `+N`: `wpływ_bieżący = wpływ_poprzedni + N + max(Postoj_dni_poprzedniego - 1, 0)`.
- `Dzien_do` etapu jest dniem wpływu do portu końcowego.
- Gdy port startowy ma `Postoj_dni > 0`, `Dzien_od = dzień wpływu do portu startowego + Postoj_dni`.
- Gdy port startowy ma `Postoj_dni = 0`, `Dzien_od = dzień wpływu do portu startowego`. Krótki postój nie przesuwa początku odcinka na następny dzień.
- Arkusz `Etapy` jest za każdym razem przebudowywany z aktualnych danych `Porty`; stare dni i daty z `Etapy` nie są źródłem obliczeń.

### Punkty trasy

- Puste `Typ` oznacza zwykły port.
- `Punkt_trasy` wymusza przebieg geometrii i jest widoczny na mapie jako specjalny techniczny znacznik, ale nie występuje na liście portów.
- `Punkt_trasy_ukryty` wymusza identyczny przebieg geometrii, lecz nie ma technicznego znacznika.
- Sekwencja `Ushuaia → Horn1 → Horn2 → Puerto Montt` tworzy jeden logiczny `Etap` `Ushuaia → Puerto Montt`. Sea-router oblicza kolejne fragmenty, a program łączy je w jeden GeoJSON.
- Media mogą wskazywać port lub punkt trasy po nazwie lokalizacji. Gdy nazwa występuje w `Porty` kilka razy, każda wizyta otrzymuje ten sam komplet mediów. Historyczna kolumna `Kolejnosc_wizyty` jest ignorowana i może pozostać dla zgodności. `Dzien_od_portu` jest czasem w dniach, np. `0.25` oznacza 6 godzin. Dla punktu trasy czas bazowy wynika z jego udziału w długości całej geometrii przy stałym średnim tempie etapu; następnie dodawane jest `Dzien_od_portu`.

## Przepływ

1. Użytkownik wprowadza lub poprawia dane w `routes/rejsy.xlsx`.
2. Program wczytuje i waliduje Excel.
3. Interpretuje `Kiedy` bez zmiany wartości wejściowych oraz sprawdza daty i postoje.
4. Uzupełnia brakujące współrzędne w kolejności `Porty.Lat/Lon → Lokalizacje → geokoder zwykłego portu → błąd`.
5. Tworzy etapy pomiędzy kolejnymi portami.
6. Wyznacza geometrię przez lokalny sea-router.
7. Aktualizuje `routes/rejsy.xlsx` w miejscu i zachowuje `routes/rejsy.bak.xlsx`.
8. Buduje `outputs/podglad-leaflet` z portami, trasami, mediami i punktami `Na morzu`.
9. Uruchamia lokalny serwer WWW i otwiera Leaflet w przeglądarce.

Zwykłe dopisywanie danych rejsu nie wymaga zmiany programu. Zmiana struktury skoroszytu jest zmianą programu i powinna zostać wykonana razem z aktualizacją dokumentacji oraz testów.

## Uruchomienie

Wymagany jest Python 3.11+.

### Instalacja sea-routera

Na nowym komputerze użytkownik może uruchomić instalację przez dwuklik pliku:

`Install-SeaRouter.cmd`

Wrapper działa niezależnie od bieżącego katalogu, uruchamia właściwy skrypt PowerShell i domyślnie przygotowuje `E:\sea-router`. Nie zmienia trwale systemowej polityki wykonywania PowerShell. Jeżeli `E:\sea-router` już istnieje, instalator bezpiecznie odmawia nadpisania go — wrapper nie usuwa ani nie przemianowuje istniejącej instalacji.

Kontrolę wymagań bez pobierania, budowania i instalacji można uruchomić poleceniem:

```text
Install-SeaRouter.cmd test
```

`Install-SeaRouter.cmd` jest pierwszym użytkowym elementem przyszłego pełnego instalatora. Planowany później `Install-Rejsy.cmd` obejmie również Pythona, `.venv`, zależności projektu i pozostałe komponenty; na obecnym etapie nie są one instalowane przez wrapper sea-routera.

Aktualizację samych własnych przejść istniejącej instalacji uruchamia się przez dwuklik `Aktualizuj-Przejscia-SeaRouter.cmd`. Wariant `Aktualizuj-Przejscia-SeaRouter.cmd test` tylko regeneruje konfigurację i sprawdza wymagania. Pełny wariant buduje oddzielnego kandydata i zawsze wykonuje ścisłą kontrolę techniczną grafu oraz obowiązkowe regresje Mesyny, Suezu, Panamy i Koryntu. Regresja przejścia `development` jest tylko diagnostyczna; regresja `stable` jest obowiązkowa i jej brak lub błąd blokuje aktywację. Aktywny `E:\sea-router` jest zastępowany dopiero po sukcesie, z zachowaniem kompletnego backupu.

### Mapowy edytor przejść

Uruchom przez dwuklik:

`Edytuj-Przejscia.cmd`

W przeglądarce otworzy się lokalna mapa. Wybierz istniejące przejście albo utwórz nowe, wybierz jego status, a następnie dodawaj punkty kliknięciem, przeciągaj znaczniki, usuwaj punkty, wstawiaj punkt po zaznaczonym lub zmieniaj kolejność przyciskami. `Zapisz` automatycznie nadaje nazwy, np. `Beagle 01`, oraz ciągłe `Przejscie_lp = 1..N`. Nowe przejście otrzymuje `development`.

Przed rzeczywistą zmianą powstaje `routes/rejsy.editor.bak.xlsx`, zapis odbywa się przez plik tymczasowy i kontrolne ponowne odczytanie. Zmiana Excela wykonana poza edytorem podczas otwartej sesji blokuje zapis do czasu odświeżenia. `Anuluj / odśwież` tylko ponownie czyta skoroszyt. Zapis identycznego przejścia jest operacją bez zmian w pliku.

Edytor nie generuje `passages.json`, nie przebudowuje grafu i nie uruchamia regresji. Pełny cykl użytkownika to:

`Edytuj-Przejscia.cmd → Zapisz → Aktualizuj-Przejscia-SeaRouter.cmd → Uruchom-Rejsy.cmd → oceń wizualnie`

Po zatwierdzeniu geometrii użytkownik przygotowuje i zatwierdza test regresji, a następnie świadomie zmienia status na `stable`. Program nigdy nie wykonuje tej decyzji automatycznie.

### Mapowy edytor portów rejsu

Uruchom przez dwuklik:

`Edytuj-Porty.cmd`

Edytor pokazuje wszystkie porty oraz oba typy punktów trasy wybranego rejsu. Pozwala przeciągać pozycje, dodawać port lub punkt po zaznaczonym wierszu, usuwać po potwierdzeniu oraz zmieniać kolejność. Zapis nadaje `Kolejnosc = 1..N`, aktualizuje tylko wybrany rejs w `Porty` i utrwala ręcznie wskazane współrzędne po nazwie w `Lokalizacje`. Usunięcie wizyty nie usuwa lokalizacji.

Jeżeli ta sama nazwa, np. `Barcelona`, występuje kilka razy, wszystkie wizyty korzystają z jednej `Lokalizacje.Nazwa`. Przeciągnięcie jednej Barcelony przesuwa wspólną lokalizację i obie wizyty. Szczegóły: [`docs/edytor-portow.md`](docs/edytor-portow.md).

Na mapie wynikowej port z `Postoj_dni > 1` otrzymuje odmienny pomarańczowo-czerwony znacznik i informację `Postój: N dni` w popupie. Kolor jest cechą konkretnej wizyty, dlatego powtórzone wizyty tego samego portu mogą wyglądać inaczej.

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -e ".[dev]"
```

Uruchom:

`Uruchom-Rejsy.cmd`

Powstaną:

- `routes/rejsy.xlsx` — ten sam skoroszyt z uzupełnionymi współrzędnymi i arkuszem `Etapy`;
- `routes/rejsy.bak.xlsx` — lokalna kopia stanu sprzed ostatniego zapisu;
- `outputs/<Rejs_ID>/geojson/*.geojson` — geometria każdego etapu;
- `outputs/<Rejs_ID>/trasa.kml` — pomocniczy wynik kontroli;
- `outputs/podglad-leaflet/` — kompletna lokalna wersja strony;
- `outputs/geocoding-cache.json` — lokalny cache współrzędnych.

Po sprawdzeniu mapy uruchom `Publikuj-Rejsy.cmd`. Skrypt kopiuje dokładnie sprawdzony wynik do `docs`, ale nie wykonuje `commit` ani `push`. Użytkownik robi to ręcznie w GitHub Desktop.

Codex/Work może wykonywać i testować ten proces podczas rozwoju programu, ale do zwykłego generowania wyników nie jest wymagany — program działa lokalnie na komputerze z odpowiednim środowiskiem i danymi sea-routera.

### Geokodowanie OpenStreetMap

Domyślnym geokoderem jest publiczny Nominatim. Program wysyła zapytania pojedynczo (maksymalnie jedno na sekundę), identyfikuje aplikację i zapisuje wyniki w cache. Dane: © OpenStreetMap contributors, ODbL. Przy większej lub komercyjnej skali należy skonfigurować własną instancję albo innego dostawcę.

## Struktura

- `src/rejsy_morskie/excel_io.py` — odczyt i zapis skoroszytu;
- `src/rejsy_morskie/schedule.py` — obliczenia dni, dat i etapów;
- `src/rejsy_morskie/geocoding.py` — cache i interfejs geokodera;
- `src/rejsy_morskie/sea_router.py` — interfejs adaptera sea-routera;
- `src/rejsy_morskie/kml.py` — eksport KML;
- `src/rejsy_morskie/web.py` — wspólne dane i pliki lokalnej/publicznej mapy Leaflet;
- `src/rejsy_morskie/passage_editor.py` i `passage-editor/` — lokalny mapowy edytor punktów w `Lokalizacje`;
- `src/rejsy_morskie/cli.py` — polecenia programu;
- `routes/rejsy.xlsx` — wersjonowane dane rejsów wraz z trwałą bazą `Lokalizacje`;
- `docs/` — założenia, organizacja pracy i specyfikacja danych.

## Dane lokalne i wyniki

Do repozytorium nie trafiają duże dane OSM, grafy routingu ani wygenerowane wyniki. Domyślne miejsca to `local-data/`, `data/` i `outputs/`.

GitHub nie jest synchronizowany automatycznie. Istotne decyzje są zapisywane w dokumentacji, a commit i push użytkownik wykonuje ręcznie w GitHub Desktop.
