# Specyfikacja danych Excel — wersja 1.7

## `routes/rejsy.xlsx`

### Arkusz `Rejsy`

| Kolumna | Wymagana | Znaczenie |
|---|---:|---|
| `Rejs_ID` | tak | Unikalny identyfikator rejsu. |
| `Nazwa_rejsu` | tak | Nazwa widoczna na stronie. |
| `Data_startu` | tak | Pierwszy dzień rejsu. |
| `Kolor_trasy` | nie | `#RRGGBB` albo obsługiwana polska nazwa koloru. |
| `CA` | nie | Dodatni parametr odsunięcia przekazywany sea-routerowi. |
| `Uwagi` | nie | Notatki. |

### Arkusz `Porty`

| Kolumna | Wymagana | Znaczenie |
|---|---:|---|
| `Rejs_ID` | w pierwszym wierszu rejsu | Puste dziedziczy poprzednią wartość. |
| `Kolejnosc` | tak | Ciągła kolejność od 1. |
| `Port` | tak | Docelowa nazwa portu, np. `Katania`. |
| `Kraj` | nie | Pomaga w pierwszym geokodowaniu. |
| `Kiedy` | tak | Pole tekstowe: `RRRR-MM-DD`, `N` albo `+N`. |
| `Postoj_dni` | nie | Liczba całkowita >= 0; puste oznacza 1. |
| `Lat`, `Lon` | razem albo oba puste | Zatwierdzone współrzędne. Jeśli istnieją, program ich nie przelicza. |
| `Uwagi` | nie | Notatki. |
| `Typ` | nie | Puste = port; `Punkt_trasy` = widoczny punkt techniczny; `Punkt_trasy_ukryty` = niewidoczny punkt techniczny. |

### Arkusz `Lokalizacje`

Arkusz jest trwałą bazą referencyjną ręcznie zatwierdzonych miejsc. Może zawierać zwykłe porty, kotwicowiska i redy, małe wyspy, punkty trasy oraz inne miejsca potrzebne geometrii lub prezentacji.

| Kolumna | Wymagana | Znaczenie |
|---|---:|---|
| `Nazwa` | tak | Główny identyfikator lokalizacji. |
| `Kraj` | nie | Informacja pomocnicza do kontroli; nie jest częścią podstawowego klucza. |
| `Lat`, `Lon` | tak | Ręcznie zatwierdzone współrzędne liczbowe. |
| `Typ` | nie | Opis, np. `Port`, `Kotwicowisko`, `Punkt_trasy` albo `Wyspa`. |
| `Uwagi` | nie | Informacje pomocnicze o lokalizacji lub pochodzeniu danych. |
| `Przejscie` | nie | Wspólna nazwa własnego przejścia sea-routera; puste dla zwykłej lokalizacji. |
| `Przejscie_lp` | razem z `Przejscie` | Dodatnia, unikalna i ciągła kolejność punktu w danym przejściu: `1..N`. |
| `Przejscie_status` | dla przejścia | `development` (projektowane) albo `stable` (zatwierdzone i chronione regresją); wszystkie punkty przejścia muszą mieć tę samą wartość. |

Wyszukiwanie odbywa się po `Nazwa`. Normalizacja usuwa spacje z początku i końca oraz ignoruje wielkość liter. Nie usuwa znaków diakrytycznych, nie zmienia pisowni i nie dopasowuje nazw podobnych. Dwie nazwy równe po tej normalizacji są błędem walidacji.

Kolejność ustalania współrzędnych wiersza `Porty`:

1. kompletne `Porty.Lat/Lon` — użycie bez jakiejkolwiek zmiany;
2. dokładne dopasowanie `Port` do `Lokalizacje.Nazwa` — użycie zatwierdzonych współrzędnych z bazy;
3. geokoder — wyłącznie dla zwykłego portu nieobecnego w bazie;
4. czytelny błąd, jeśli zwykłego portu nie znaleziono albo punkt trasy nie ma współrzędnych w dwóch pierwszych źródłach.

Generator rejsu nigdy nie geokoduje wpisów `Lokalizacje`, nie koryguje ich i nie zapisuje do tego arkusza. Podczas normalnego przebiegu może skopiować znalezione współrzędne do pustych komórek `Porty.Lat/Lon`. Pole `Lokalizacje.Typ` jest opisowe; o zachowaniu wiersza rejsu nadal decyduje `Porty.Typ`.

Wiersze z uzupełnionymi `Przejscie` i `Przejscie_lp` są także źródłem własnych przejść sea-routera. Generator grupuje je po dokładnej nazwie `Przejscie`, sortuje po `Przejscie_lp`, wymaga co najmniej dwóch punktów, kompletnych `Lat/Lon`, jednego statusu oraz ciągu bez luk i duplikatów. Wynikowy `sea-router-custom/passages.json` jest plikiem technicznym; źródłem prawdy pozostaje ten arkusz. Dla zgodności ze starszym skoroszytem brak kolumny lub pusta wartość statusu jest traktowana zachowawczo jako `stable`.

`development` nie wyłącza walidacji technicznej ani bazowych regresji Mesyny, Suezu, Panamy i Koryntu; jedynie własna regresja geograficzna tego projektowanego przejścia jest opcjonalna i nieblokująca. `stable` wymaga aktywnej, zakończonej sukcesem regresji o identyfikatorze przejścia (Mesyna używa historycznego identyfikatora `messina`).

`Edytuj-Przejscia.cmd` jest wyłącznie mapowym interfejsem zapisu do tej samej tabeli. Dla wybranego przejścia automatycznie tworzy `Nazwa` w formie `<Przejscie> NN`, współrzędne z kliknięć, `Przejscie_lp = 1..N` i zapisuje wybrany `Przejscie_status`; zachowuje jego `Kraj`, `Typ` i `Uwagi`, a pozostałych lokalizacji i arkuszy nie zmienia. Zapis wymaga co najmniej dwóch punktów i prawidłowych współrzędnych, tworzy `rejsy.editor.bak.xlsx`, używa pliku tymczasowego oraz kontroli wersji skoroszytu. Identyczny zapis jest operacją bez zmian. Edytor nie generuje ani nie aktywuje grafu sea-routera.

`Edytuj-Porty.cmd` zapisuje kolejność i harmonogram wybranego rejsu w `Porty`, a ręcznie wskazaną pozycję utrwala w `Lokalizacje` pod tą samą nazwą. Jedna `Lokalizacje.Nazwa` oznacza jedno miejsce geograficzne i może obsługiwać dowolną liczbę wizyt w `Porty`. Edytor nie usuwa lokalizacji przy usunięciu wizyty, nie przebudowuje `Etapy` i nie zmienia innych rejsów. Przed zapisem tworzy `rejsy.ports-editor.bak.xlsx`, kontroluje wersję, zapisuje przez plik tymczasowy i ponownie waliduje dane oraz harmonogram.

Puste `Porty.Lat/Lon` nie są samodzielnie błędem punktu trasy. Walidacja braku współrzędnych następuje dopiero po dokładnym wyszukaniu jego nazwy w `Lokalizacje`. Dzięki temu wartości skopiowane wcześniej do `Porty` mogą zostać usunięte i odtworzone przy następnym normalnym przebiegu bez utraty trwałej lokalizacji.

### `Kiedy`

Cała kolumna ma format tekstowy i identyczną semantykę dla portów oraz obu typów punktów trasy. Dozwolone są dokładnie trzy formy tekstu:

- `RRRR-MM-DD`, np. `2024-12-10` — bezwzględna data wpływu;
- `N`, gdzie `N` składa się wyłącznie z cyfr, np. `0`, `3` lub `10` — wpływ `N` dni po `Data_startu`; wpis ustanawia kotwicę względem początku rejsu;
- `+N`, gdzie `N` składa się wyłącznie z cyfr, np. `+2` — osiągnięcie bieżącego wiersza po `N` dniach względem poprzedniego wiersza, z uwzględnieniem dodatkowych pełnych dni jego postoju.

`0` jest niezależną kotwicą i w każdym wierszu oznacza dokładnie `Data_startu + 0 dni`. Nie oznacza, że dany wiersz jest portem startowym, pierwszym punktem rejsu ani początkiem nowego odcinka. `+0` jest odrębną wartością względną: wyznacza datę poprzedniego wiersza z uwzględnieniem składnika `max(Postoj_dni_poprzedniego - 1, 0)`. Gdy postój nie wnosi dodatkowego przesunięcia, `+0` daje dokładnie tę samą datę co poprzedni wiersz. Język `Kiedy` działa identycznie dla zwykłych portów i obu typów punktów trasy.

W konsekwencji późniejszy wiersz z `0` nadal wskazuje datę rozpoczęcia rejsu i może zostać odrzucony przez kontrolę chronologii. Program nie interpretuje go wtedy jako skrótu „ten sam dzień”; do tego służy wyłącznie `+0`.

Jedynym dozwolonym tekstowym formatem daty jest `RRRR-MM-DD`. Zapisy takie jak `10.12.2024`, `12/10/2024`, liczby dziesiętne, liczby ujemne, spacje i inne niejednoznaczne wartości są błędem. Format tekstowy kolumny zapobiega usuwaniu znaku `+` przez Excel.

Wzór dla bieżącego wiersza z `+N`:

`data_bieżącego = data_poprzedniego + N + max(Postoj_dni_poprzedniego - 1, 0)`

Znaczenie postoju poprzedniego portu:

- `Postoj_dni = 0` — krótki postój nie dodaje dnia;
- `Postoj_dni = 1` — dzień wpływu jest dniem portowym, więc nie dodaje kolejnego dnia;
- `Postoj_dni = 2` — dodaje 1 pełny dzień;
- większa wartość dodaje zawsze `Postoj_dni - 1` dni.

Kolejne wpisy `+N` tworzą łańcuch zależności uwzględniający tę regułę dla każdego postoju. Zmiana wcześniejszego portu albo jego `Postoj_dni` przelicza wszystkie kolejne zależne porty.

Data `RRRR-MM-DD` i liczba bez znaku `N` są niezależnymi kotwicami harmonogramu. Nie wymagają równości z datą wyprowadzoną wyłącznie z poprzedniego portu, ponieważ bez `+N` czas żeglugi do kotwicy nie jest znany. Kotwica musi jedynie zachować chronologię: nie może być wcześniejsza niż data umożliwiająca zakończenie `Postoj_dni` poprzedniego portu ani cofać czasu.

`+N` w pierwszym porcie jest błędem, ponieważ nie istnieje poprzedni port ani jego postój. Pierwszy port musi używać daty `RRRR-MM-DD` albo liczby bez znaku `N`.

`Kiedy` i `Postoj_dni` są wyłącznie polami wejściowymi użytkownika. Program nigdy ich nie nadpisuje ani nie normalizuje. Po obliczeniach `+2` nadal jest tekstem `+2`, `2024-12-10` nadal jest tekstem `2024-12-10`, a postój zachowuje wpisaną wartość. Obliczone numery dni i daty są przechowywane w strukturach programu oraz w arkuszu `Etapy`.

### Typy wierszy `Porty`

- puste `Typ`: zwykły port;
- `Punkt_trasy`: widoczny techniczny punkt geometrii;
- `Punkt_trasy_ukryty`: techniczny punkt geometrii bez znacznika.

Oba punkty techniczne mają `Postoj_dni = 0` oraz wymagają kompletu `Lat` i `Lon`, podanego bezpośrednio w `Porty` albo znalezionego w `Lokalizacje`. Puste komórki w `Porty` są dozwolone, jeżeli baza zawiera dokładnie dopasowaną nazwę. Punktów trasy program nigdy nie przekazuje do geokodera; dopiero brak współrzędnych w obu źródłach jest błędem. Zwykły port może dodatkowo skorzystać z geokodera.

### Dni wpływu

Dzień wpływu jest liczony od 1:

`dzien_wpływu = (data_wpływu - Data_startu) + 1`

Dla `+N` data wpływu powstaje według wzoru:

`wpływ_bieżący = wpływ_poprzedni + N + max(Postoj_dni_poprzedniego - 1, 0)`

Kotwica datowa albo liczba bez znaku wyznacza własną datę wpływu, a następnie przechodzi kontrolę podstawowej chronologii względem poprzedniego postoju.

### Arkusz `Etapy`

Program aktualizuje go w tym samym `rejsy.xlsx`. Każdy wiersz opisuje jeden odcinek i zawiera: identyfikator, numer, port początkowy i końcowy, nazwę, dni i daty, dystans, względną ścieżkę GeoJSON, status i uwagi.

`Etapy` powstają wyłącznie pomiędzy zwykłymi portami. Wszystkie punkty trasy znajdujące się pomiędzy nimi wymuszają kolejność fragmentów sea-routera, ale nie tworzą osobnych wierszy `Etapy`. Fragmenty są łączone w jedną ciągłą geometrię GeoJSON logicznego etapu port–port.

Dla odcinka od portu startowego do końcowego:

- `Dzien_do = dzień wpływu do portu końcowego`;
- gdy `Postoj_dni` portu startowego jest większy od 0: `Dzien_od = dzień wpływu do portu startowego + Postoj_dni`;
- gdy `Postoj_dni` portu startowego wynosi 0: `Dzien_od = dzień wpływu do portu startowego`.

`Postoj_dni = 0` oznacza krótki postój, który nie przesuwa początku etapu na następny dzień. `Etapy` jest wynikiem przebudowywanym przy każdym przebiegu wyłącznie z aktualnych `Rejsy` i `Porty`; dotychczasowe wartości dni i dat w `Etapy` nie są wczytywane jako źródło harmonogramu.

Przed zapisem powstaje lokalna kopia `routes/rejsy.bak.xlsx`, a wymiana właściwego pliku jest atomowa. Nie tworzy się dodatkowego skoroszytu wynikowego.

## `routes/media.xlsx`

Arkusz nazywa się `Filmy` ze względu na zgodność istniejących danych, ale może zawierać filmy MP4/MOV i zdjęcia.

| Kolumna | Wymagana | Znaczenie |
|---|---:|---|
| `Film_ID` | tak | Wewnętrzne `<nazwa_bazy>_<numer>`, np. `KATANIA_1` albo `Horn1_1`. Bazą może być port lub dowolny punkt trasy. |
| `Kolejnosc_wizyty` | nie | Historyczna kolumna zgodności wstecznej; obecnie ignorowana. Media nie zależą od numeracji `Porty`. |
| `Typ` | nie | Pole informacyjne; format pliku nie steruje sposobem linkowania. |
| `Powiazanie` | nie | Pole zgodności istniejącego arkusza. |
| `Dzien_od_portu` | nie | Czas w dniach od bazowego portu/punktu; `0.25` oznacza 6 godzin. |
| `Opis` | tak | Tekst linku w dymku. |
| `URL_Google_Drive` | tak | Pełny publiczny URL używany bezpośrednio przez stronę. |
| `Aktywny` | tak | `TAK` włącza wpis. |

### `Film_ID`

Część przed końcowym `_numer` musi wskazywać istniejącą nazwę portu, `Punkt_trasy` albo `Punkt_trasy_ukryty` z arkusza `Porty`. Identyfikator nie jest nazwą rzeczywistego pliku i nie jest pokazywany odbiorcy. Nazwa pliku na Drive może być dowolna.

Powtarzające się nazwy w `Porty` są dozwolone, a konkretne wizyty nadal rozróżnia para `Rejs_ID` + `Kolejnosc` na potrzeby harmonogramu, tras i prezentacji. Media nie korzystają jednak z tej tożsamości: baza `Film_ID` jest nazwą lokalizacji i ten sam wpis pojawia się przy każdej wizycie o tej nazwie. `Barcelona_1`, `Barcelona_2` i `Barcelona_3` oznaczają trzy media Barcelony, niezależnie od liczby wizyt. Reguła obejmuje porty oraz oba typy punktów trasy.

### `Dzien_od_portu`

- puste lub `0`: dokładne współrzędne bazowego portu albo punktu trasy;
- wartość `> 0`: czas w dniach po osiągnięciu bazy, a nie procent długości;
- akceptowane są liczby dziesiętne, również zapis `2,4`;
- dla punktu trasy czas bazowy wynosi `T * L1/L`, gdzie `T` to czas całego etapu, `L` jego długość, a `L1` dystans od portu początkowego do punktu;
- czas medium to `czas_bazowy + Dzien_od_portu`, przeliczany na pozycję na całej połączonej geometrii przy stałym średnim tempie;
- wartość wykraczająca poza czas etapu, brak bazy, brak następnego etapu lub brak geometrii są błędami — program nie zgaduje.

Medium z wartością `0` dla zwykłego portu pozostaje w popupie portu. Dla widocznego punktu trasy trafia do popupu jego technicznego znacznika. Ukryty punkt nie otrzymuje znacznika technicznego; jego medium pozostaje widoczne jako istniejący punkt `Na morzu`. Każda wartość `> 0` używa znacznika `Na morzu`.

## Walidacja

Błędem są m.in. brak wymaganej kolumny, nieznany port/punkt w `Film_ID`, powtórzony identyfikator, niepoprawny URL, ujemny dzień, przekroczenie etapu, nieciągła kolejność, niepełna para `Lat`/`Lon`, brak współrzędnych punktu trasy, niezerowy postój punktu, niepełny wpis `Lokalizacje` oraz powtórzona `Lokalizacje.Nazwa` po normalizacji.
