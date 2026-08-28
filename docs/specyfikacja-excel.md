# Specyfikacja danych Excel — wersja 1.0

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
| `Kiedy` | tak | Data albo całkowita liczba dni od `Data_startu`. |
| `Postoj_dni` | nie | Liczba całkowita >= 0; puste oznacza 1. |
| `Lat`, `Lon` | razem albo oba puste | Zatwierdzone współrzędne. Jeśli istnieją, program ich nie przelicza. |
| `Uwagi` | nie | Notatki. |

Liczba `0` w `Kiedy` oznacza datę startu, a `N` oznacza `Data_startu + N dni`. Tekst `+N` jest zgodny wstecznie. Konkretna data jest punktem kontrolnym. Harmonogram nie może cofać się po uwzględnieniu postoju.

### Arkusz `Etapy`

Program aktualizuje go w tym samym `rejsy.xlsx`. Każdy wiersz opisuje jeden odcinek i zawiera: identyfikator, numer, port początkowy i końcowy, nazwę, dni i daty, dystans, względną ścieżkę GeoJSON, status i uwagi.

Przed zapisem powstaje lokalna kopia `routes/rejsy.bak.xlsx`, a wymiana właściwego pliku jest atomowa. Nie tworzy się dodatkowego skoroszytu wynikowego.

## `routes/media.xlsx`

Arkusz nazywa się `Filmy` ze względu na zgodność istniejących danych, ale może zawierać filmy MP4/MOV i zdjęcia.

| Kolumna | Wymagana | Znaczenie |
|---|---:|---|
| `Film_ID` | tak | Wewnętrzne `<nazwa_portu>_<numer>`, np. `KATANIA_1`. Dopasowanie nazwy portu nie rozróżnia wielkości liter. |
| `Typ` | nie | Pole informacyjne; format pliku nie steruje sposobem linkowania. |
| `Powiazanie` | nie | Pole zgodności istniejącego arkusza. |
| `Dzien_od_portu` | nie | Puste/0 = przy porcie; dodatnia liczba = pozycja na odcinku do następnego portu. |
| `Opis` | tak | Tekst linku w dymku. |
| `URL_Google_Drive` | tak | Pełny publiczny URL używany bezpośrednio przez stronę. |
| `Aktywny` | tak | `TAK` włącza wpis. |

### `Film_ID`

Część przed końcowym `_numer` musi wskazywać istniejącą nazwę z arkusza `Porty`. Identyfikator nie jest nazwą rzeczywistego pliku i nie jest pokazywany odbiorcy. Nazwa pliku na Drive może być dowolna.

### `Dzien_od_portu`

- puste lub `0`: współrzędne portu;
- wartość `> 0`: udział `wartość / liczba_dni_etapu` wzdłuż całej linii GeoJSON, liczony według długości jej segmentów;
- akceptowane są liczby dziesiętne, również zapis `2,4`;
- wartość większa od czasu etapu, brak portu, brak następnego etapu lub brak geometrii są błędami — program nie zgaduje.

## Walidacja

Błędem są m.in. brak wymaganej kolumny, nieznany port w `Film_ID`, powtórzony identyfikator, niepoprawny URL, ujemny dzień, przekroczenie etapu, nieciągła kolejność portów i niepełna para `Lat`/`Lon`.
