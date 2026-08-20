# Specyfikacja danych Excel — wersja 0.1

## Założenia ogólne

Nazwy arkuszy i kolumn są stałe. Daty powinny być komórkami typu data Excela lub tekstem ISO `RRRR-MM-DD`. Identyfikatory `Rejs_ID` są tekstem. Puste komórki opcjonalne są dozwolone.

Dzień zawierający `Data_startu` ma numer 1.

## Arkusz Rejsy

Jeden wiersz opisuje jeden rejs.

| Kolumna | Wymagana | Typ | Znaczenie |
|---|---|---|---|
| Rejs_ID | tak | tekst | Unikalny identyfikator, np. `R2026-01`. |
| Nazwa_rejsu | tak | tekst | Nazwa widoczna w wynikach i KML. |
| Data_startu | tak | data | Pierwszy dzień rejsu. |
| Kolor_trasy | nie | tekst | Kolor `#RRGGBB`; domyślnie `#0057B8`. |
| CA | nie | tekst | Pole użytkownika; program zachowuje je bez interpretacji. |
| Uwagi | nie | tekst | Notatki dotyczące całego rejsu. |

## Arkusz Porty

Każdy wiersz opisuje jedno zawinięcie do portu.

| Kolumna | Wymagana | Typ | Znaczenie |
|---|---|---|---|
| Rejs_ID | tak | tekst | Odwołanie do arkusza `Rejsy`. |
| Kolejnosc | tak | liczba całkowita | Kolejność portu w rejsie, od 1. |
| Port | tak | tekst | Nazwa portu. |
| Kraj | zalecana | tekst | Kraj lub region ułatwiający jednoznaczne geokodowanie. |
| Kiedy | tak | data lub `+N` | Data wpływu albo numer dnia wpływu. |
| Postoj_dni | nie | liczba całkowita >= 0 | Długość postoju; puste = 1. |
| Lat | nie | liczba | Szerokość geograficzna od -90 do 90. |
| Lon | nie | liczba | Długość geograficzna od -180 do 180. |
| Uwagi | nie | tekst | Notatki o zawinięciu. |

Para `Lat`/`Lon` jest podawana razem albo obie wartości pozostają puste.

### Interpretacja Kiedy

- `+1` oznacza `Data_startu`;
- `+N` oznacza `Data_startu + (N-1) dni`;
- konkretna data daje dzień `(data - Data_startu) + 1`;
- data wcześniejsza od startu oraz `+0` są błędami;
- porty są sortowane po `Kolejnosc`, a wyliczone terminy nie mogą się cofać.

### Postój i rozpoczęcie etapu

Dzień wyjścia z portu to dzień wpływu + `Postoj_dni`. Przykład: wpływ w dniu 2 i postój 1 dzień oznacza rozpoczęcie kolejnego etapu w dniu 3. Dla portu początkowego można użyć postoju 0.

## Arkusz Etapy

Arkusz jest generowany od nowa przez program. Jeden wiersz odpowiada trasie pomiędzy dwiema kolejnymi pozycjami w `Porty`.

| Kolumna | Znaczenie |
|---|---|
| Rejs_ID | Identyfikator rejsu. |
| Etap_nr | Numer etapu od 1. |
| Port_start | Port początkowy. |
| Port_koniec | Port końcowy. |
| Nazwa_etapu | Np. `Dubrovnik → Catania`. |
| Dzien_od | Dzień wyjścia z portu początkowego. |
| Dzien_do | Dzień wpływu do portu końcowego. |
| Data_od | Data odpowiadająca `Dzien_od`. |
| Data_do | Data wpływu do portu końcowego. |
| Zakres_dni | Np. `Dni 3–4`. |
| Zakres_dat | Czytelny zakres dat. |
| Dystans_nm | Długość trasy w milach morskich, jeśli zwróci ją router. |
| GeoJSON_path | Ścieżka do geometrii etapu. |
| Status | Np. `gotowy`, `brak_wspolrzednych`, `brak_trasy`. |
| Uwagi | Ostrzeżenia i informacje diagnostyczne. |

## Geokodowanie i utrwalanie

1. Jeśli `Lat` i `Lon` są podane, program ich nie nadpisuje.
2. W przeciwnym razie szuka portu po nazwie i kraju/regionie.
3. Wynik jednoznaczny zapisuje do cache oraz wynikowego XLSX.
4. Wiele sensownych wyników powoduje status wymagający zatwierdzenia.
5. Cache powinien przechowywać zapytanie, współrzędne, źródło i datę pobrania.

Program nie powinien modyfikować pliku wejściowego w miejscu. Domyślny wynik to `outputs/<Rejs_ID>/rejs-uzupelniony.xlsx`.

## Sea-router i eksport

Adapter sea-routera otrzymuje współrzędne początku i końca, a zwraca linię GeoJSON i opcjonalnie dystans. Graf routingu i dane OSM są lokalną zależnością, nie częścią repozytorium.

KML zawiera folder rejsu, punkty portów i osobne linie etapów. Kolor `#RRGGBB` jest konwertowany do formatu KML `aabbggrr`. Wynik musi dać się zaimportować do Google My Maps.

## Walidacja minimalna

Błędem są między innymi: brak arkusza lub wymaganej kolumny, powtórzony `Rejs_ID`, nieciągła lub powtórzona `Kolejnosc`, nieznany rejs w `Porty`, niepoprawne `Kiedy`, ujemny postój, połowa pary Lat/Lon oraz termin kolejnego portu wcześniejszy niż możliwe wyjście z poprzedniego.
