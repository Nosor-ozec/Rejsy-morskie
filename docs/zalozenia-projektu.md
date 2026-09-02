# Założenia projektu Rejsy-morskie

## Cel

Celem jest odtwarzalna prezentacja rejsu na mapie Leaflet, najpierw w pełni sprawdzana lokalnie, a dopiero później przygotowywana do ręcznej publikacji.

## Źródła danych

Obowiązują dokładnie dwa skoroszyty:

- `routes/rejsy.xlsx` — arkusze `Rejsy`, `Porty`, referencyjne `Lokalizacje` i aktualizowany w miejscu arkusz `Etapy`;
- `routes/media.xlsx` — arkusz `Filmy` z identyfikatorami wewnętrznymi, opisami, URL i pozycją względem portu.

Nie są źródłami danych `filmy-test.xlsx`, `rejsy-z-etapami.xlsx` ani folder `rejsy-filmy`.

## Rozdzielenie generowania od publikacji

- `Uruchom-Rejsy.cmd` generuje trasy i kompletny wynik `outputs/podglad-leaflet`, a następnie otwiera go lokalnie.
- `Publikuj-Rejsy.cmd` kopiuje do `docs` dokładnie sprawdzony wynik na podstawie manifestu sum kontrolnych.
- Lokalna i publiczna mapa używają tego samego `index.html`, `app.js`, stylów, danych i geometrii; nie istnieją dwie implementacje prezentacji.
- Żaden ze skryptów nie wykonuje commit ani push.

## Bezpieczeństwo danych

`rejsy.xlsx` pozostaje jednym głównym skoroszytem. Program tworzy lokalny `rejsy.bak.xlsx`, zapisuje plik tymczasowy, a dopiero potem atomowo zastępuje właściwy plik. Zapisane `Porty.Lat/Lon` są używane bez ponownego geokodowania. Gdy są puste, program szuka dokładnej nazwy w trwałej bazie `Lokalizacje`; zwykły port może następnie skorzystać z geokodera, ale punkt trasy nigdy nie jest geokodowany.

`Lokalizacje` łączy w jednej bazie porty, kotwicowiska, wyspy, punkty trasy i inne specjalne miejsca. Kluczem jest `Nazwa`, porównywana bez uwzględniania wielkości liter i skrajnych spacji, bez zgadywania podobnych nazw. Współrzędne w bazie są ręcznie zatwierdzonymi danymi użytkownika. Generator ich nie nadpisuje, nie usuwa ani nie poprawia; mapowy `Edytuj-Porty.cmd` może je świadomie utworzyć lub zmienić po przeciągnięciu/kliknięciu użytkownika. `Porty.Lat/Lon` pozostaje odtwarzalnym cache.

Rozdzielenie odpowiedzialności jest stałe: `Lokalizacje` mówi **gdzie**, `Porty` mówi **kiedy i w jakiej kolejności**, a `media.xlsx` mówi **co pokazać dla danej nazwy lokalizacji**. Powtórzone wizyty tej samej nazwy używają jednej lokalizacji oraz jednego kompletu mediów. `Kolejnosc_wizyty` nie steruje już przypisaniem mediów.

Ten sam arkusz jest źródłem prawdy dla ręcznych przejść sea-routera: `Przejscie` grupuje punkty, a `Przejscie_lp` określa ich kolejność. JSON w `sea-router-custom` jest zawsze odtwarzalnym wynikiem generatora. Aktywny graf jest wymieniany dopiero po zbudowaniu osobnego kandydata, ścisłej kontroli semantycznej oraz testach długości, objazdu i korytarza.

`Porty.Lat/Lon` są odtwarzalnym wynikiem pomocniczym. Także dla punktu trasy mogą pozostać puste: program najpierw rozwiązuje nazwę przez `Lokalizacje`, a dopiero potem sprawdza, czy współrzędne nadal są niedostępne. Geokoder jest ostatnią możliwością wyłącznie dla zwykłego portu.

Kolumny `Porty.Kiedy` i `Porty.Postoj_dni` są wyłącznie wejściem użytkownika i program nigdy ich nie przekształca ani nie nadpisuje. `Kiedy` ma format tekstowy i przyjmuje tylko `RRRR-MM-DD`, `N` albo `+N`. Dla `+N` obowiązuje wzór `data_bieżącego = data_poprzedniego + N + max(Postoj_dni - 1, 0)`: postój 0 lub 1 nie przesuwa dodatkowo harmonogramu, a każdy kolejny dzień postoju dodaje jeden dzień. Data albo `N` bez znaku jest niezależną kotwicą; podlega kontroli chronologii, lecz nie musi być równa dacie wyprowadzonej z poprzedniego portu bez znanego czasu żeglugi. Wyliczone daty trafiają tylko do przebudowywanego arkusza `Etapy` i innych danych wynikowych.

Szczególny przypadek `N=0` nie zależy od położenia wiersza: `0` zawsze znaczy `Data_startu + 0 dni` i nie nadaje wierszowi roli portu startowego ani pierwszego punktu. `+0` ma inną semantykę — zależy od bezpośredniego poprzednika i daje jego datę powiększoną o `max(Postoj_dni_poprzedniego - 1, 0)`. Zwykłe porty oraz oba typy punktów trasy korzystają z tych samych reguł.

Ta sama semantyka `Kiedy` obowiązuje zwykłe porty oraz `Punkt_trasy` i `Punkt_trasy_ukryty`; `+0` może zachować dzień poprzedniego wiersza. Punkty techniczne mają postój 0 i współrzędne pochodzące z ręcznych `Porty.Lat/Lon` albo z `Lokalizacje`. Uczestniczą w chronologii oraz wymuszają geometrię, lecz nie tworzą osobnych `Etapy`. Widoczny punkt ma odrębny znacznik poza listą portów, a ukryty wpływa wyłącznie na geometrię i media.

## Prezentacja

Docelową prezentacją jest Leaflet — lokalnie i po ręcznej publikacji. KML jest tylko pomocniczym wynikiem kontroli. Media są zwykłymi opisowymi linkami HTTPS otwieranymi w nowej karcie; strona ich nie osadza i nie interpretuje nazwy pliku na Drive. Porty z postojem dłuższym niż jeden dzień otrzymują odmienny znacznik i informację o długości postoju; jest to cecha wizyty z `Porty`, nie wspólnej lokalizacji.
