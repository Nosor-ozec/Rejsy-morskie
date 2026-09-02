# Mapowy edytor portów i punktów rejsu

`Edytuj-Porty.cmd` jest osobnym narzędziem od `Edytuj-Przejscia.cmd`:

- `Edytuj-Przejscia.cmd` projektuje trwałą infrastrukturę sea-routera w `Lokalizacje`;
- `Edytuj-Porty.cmd` zmienia listę i kolejność pozycji konkretnego rejsu w `Porty`.

Nie powstaje nowy arkusz ani dodatkowy plik danych. `Lokalizacje` pozostaje biblioteką miejsc, `Porty` harmonogramem rejsu, a `Etapy` wynikiem późniejszego przeliczenia.

## Uruchomienie

Uruchom dwuklikiem `Edytuj-Porty.cmd`, a następnie wybierz rejs. Lista i mapa pokazują zwykłe porty, `Punkt_trasy` oraz `Punkt_trasy_ukryty`. Wybrana pozycja ma wyróżniony znacznik i linię do bezpośrednich sąsiadów. Kliknięcie listy przesuwa mapę bez agresywnej zmiany zoomu.

## Dostępne operacje

- przeciągnięcie znacznika zmienia ręczną pozycję;
- `Dodaj port`, `Dodaj punkt trasy` i `Dodaj ukryty punkt` wstawiają nowy wiersz po zaznaczonym albo na końcu;
- `Przesuń wyżej/niżej` zmienia kolejność;
- `Usuń pozycję` wymaga potwierdzenia;
- `Anuluj / odśwież` porzuca zmiany i ponownie czyta Excel;
- `Zapisz` nadaje `Kolejnosc = 1,2,3,...` i sprawdza harmonogram.

Dla nowego portu podaje się nazwę, kraj, `Kiedy`, `Postoj_dni` i opcjonalne uwagi. Punkt trasy wymaga nazwy i `Kiedy`, ma automatycznie `Postoj_dni=0` oraz wybrany `Typ`.

## Wspólna lokalizacja

Jedna `Lokalizacje.Nazwa` oznacza jedno miejsce geograficzne. Jeśli Barcelona występuje dwa razy w `Porty`, obie wizyty korzystają z tego samego wpisu `Barcelona`. Przeciągnięcie jednej wizyty aktualizuje współrzędne obu wizyt w edytorze i zapisuje jedną lokalizację. Dwa różne miejsca wymagają dwóch różnych nazw.

Nowa lub przeciągnięta pozycja jest zapisywana trwale do `Lokalizacje`; `Porty.Lat/Lon` jest jednocześnie odświeżane jako cache. Usunięcie współrzędnych z `Porty` nie traci miejsca — zwykły generator odtworzy je po nazwie. Usunięcie wizyty z `Porty` nigdy nie usuwa wiersza `Lokalizacje`.

Jeżeli podana nazwa już istnieje w `Lokalizacje`, edytor pokazuje jej współrzędne. Użytkownik wybiera użycie zatwierdzonej pozycji albo świadome zastąpienie jej klikniętym miejscem.

## Bezpieczeństwo zapisu

Przed rzeczywistą zmianą powstaje `routes/rejsy.ports-editor.bak.xlsx`. Backend kontroluje sumę bieżącej wersji skoroszytu, zapisuje plik tymczasowy, ponownie czyta wszystkie pola, sprawdza `Kolejnosc`, typy, współrzędne i harmonogram, a dopiero potem atomowo zastępuje `rejsy.xlsx`. Błąd nie pozostawia częściowego zapisu. `Etapy`, inne rejsy i niezwiązane lokalizacje pozostają bez zmian.

Po sukcesie edytor wyświetla: `Dane zapisane. Uruchom Uruchom-Rejsy.cmd, aby przeliczyć Etapy i mapę.`

## Media

Media są przypisane do nazwy lokalizacji, nie do numeru wizyty. Wszystkie wizyty `Barcelona` pokazują wszystkie aktywne `Barcelona_1`, `Barcelona_2` itd. Przenumerowanie `Porty.Kolejnosc` nie wymaga zmiany `media.xlsx`; historyczna kolumna `Kolejnosc_wizyty` jest ignorowana.
