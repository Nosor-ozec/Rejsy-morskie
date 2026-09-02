# Dodawanie własnych przejść sea-routera

## Źródło danych

Jedynym źródłem ręcznie zatwierdzonych punktów jest arkusz `Lokalizacje` w `routes/rejsy.xlsx`. Kolumny `Lat` i `Lon` są danymi użytkownika i żaden skrypt ich nie nadpisuje. Zwykłe lokalizacje mają puste `Przejscie`, `Przejscie_lp` i `Przejscie_status`.

Punkty jednego przejścia otrzymują identyczne `Przejscie` i `Przejscie_status` oraz kolejne całkowite `Przejscie_lp` od 1 bez luk. `development` służy do iteracyjnego projektowania, a `stable` do ochrony zatwierdzonej geometrii obowiązkową regresją. Nazwa przejścia jest techniczną nazwą wstrzykiwaną do bazowego `canals.rs`. Potrzebne są co najmniej dwa punkty. Nie należy zaczynać od dużej liczby punktów: dodajemy minimalny, świadomie zatwierdzony zestaw i rozszerzamy go tylko po ocenie wyniku.

`sea-router-custom/passages.json` jest plikiem wynikowym. Polecenie `rejsy-morskie passages` czyta Excel, grupuje punkty, sortuje je, sprawdza współrzędne i kolejność, a następnie atomowo zapisuje JSON. Nie edytujemy go ręcznie.

## Edycja na mapie

Do codziennej pracy nie trzeba ręcznie przepisywać współrzędnych w Excelu:

1. Uruchom przez dwuklik `Edytuj-Przejscia.cmd`.
2. Wybierz przejście albo użyj `Nowe przejście`.
3. Włącz `Dodaj punkt` i klikaj mapę. Punkty są natychmiast numerowane, a linia pokazuje ich kolejność.
4. Aby poprawić przebieg, przeciągnij znacznik. Możesz też zaznaczyć punkt na liście, usunąć go, wstawić nowy bezpośrednio po nim albo przesunąć go wyżej/niżej.
5. Dla projektowanego przejścia pozostaw status `development` i kliknij `Zapisz`. Edytor nada nazwy `<Przejscie> 01`, `<Przejscie> 02` itd. i zapisze ciągłe `Przejscie_lp = 1..N`.
6. Uruchom `Aktualizuj-Przejscia-SeaRouter.cmd`; wcześniej możesz wykonać wariant `test` albo zbudować kandydata przez `-NoActivate`.
7. Uruchom `Uruchom-Rejsy.cmd` i oceń trasę na pełnej lokalnej mapie.
8. Jeżeli przebieg jest zły, wróć do edytora, popraw pojedynczy punkt i powtórz aktualizację oraz ocenę.

Edytor działa wyłącznie na komputerze lokalnym. `Lokalizacje` nadal jest jedynym źródłem prawdy; nie powstaje dodatkowy CSV, JSON ani Excel. `passages.json` nadal tworzy dopiero istniejący generator. Sam edytor nie przebudowuje ani nie aktywuje sea-routera.

To narzędzie nie edytuje arkusza `Porty`. Porty i punkty konkretnego rejsu obsługuje osobne `Edytuj-Porty.cmd`; nie należy mieszać obu workflow.

Po wybraniu przejścia odczytywane są tylko jego punkty posortowane po `Przejscie_lp`. Zapis zastępuje wyłącznie wiersze tego przejścia; zwykłe lokalizacje, inne przejścia i pozostałe arkusze pozostają zachowane. Wymagane są co najmniej dwa punkty, poprawne zakresy `Lat/Lon` i ciągła kolejność. Przed zmianą tworzona jest kopia `routes/rejsy.editor.bak.xlsx`, a nowa wersja przechodzi zapis tymczasowy i kontrolny odczyt przed atomowym zastąpieniem skoroszytu. Równoległa zmiana Excela jest wykrywana i wymaga `Anuluj / odśwież`. Otwarcie i zapis bez zmian nie zapisuje pliku ponownie.

## Zwykły cykl aktualizacji

1. Użyj `Edytuj-Przejscia.cmd` (albo świadomie edytuj `routes/rejsy.xlsx / Lokalizacje`).
2. Dodaj niewielką liczbę zatwierdzonych punktów; edytor uzupełni `Nazwa`, `Przejscie`, `Przejscie_lp`, `Lat` i `Lon`.
3. Dla statusu `development` nie edytuj ręcznie `regression-cases.json`. Uruchom najpierw `Aktualizuj-Przejscia-SeaRouter.cmd test`, a następnie właściwą aktualizację.
4. Skrypt zbuduje oddzielnego kandydata, sprawdzi dokładne źródła, wszystkie waypointy i połączenia łańcucha, treść grafu oraz obowiązkowe regresje Mesyny, Suezu, Panamy i Koryntu.
5. Jeżeli istnieje aktywny test projektowanego przejścia, zostanie pokazany jako diagnostyka. Jego błąd nie zablokuje aktualizacji `development`.
6. Uruchom `Uruchom-Rejsy.cmd` i oceń wynik. Przy złej geometrii wróć do edytora i popraw pojedynczy punkt.
7. Jeżeli kontrola techniczna albo regresja obowiązkowa zawiedzie, aktywna instalacja pozostaje nietknięta.
8. Jeżeli kontrole obowiązkowe przejdą, kandydat zostanie aktywowany, a wcześniejsza kompletna instalacja pozostanie jako datowany backup.

Mesyna jest przejściem `stable` i referencją mechanizmu. Jej 12 punktów w `Lokalizacje` odtwarza dokładnie dotychczasowy wpis i pełne znane hashe semantyczne grafu. Jej regresja jest obowiązkowa. Beagle ma status `development`; jego aktywny test pozostaje diagnostyczny i nie blokuje iteracyjnej aktualizacji.

## Zatwierdzenie przejścia

Decyzja o przejściu do `stable` zawsze należy do użytkownika:

1. zakończ projektowanie i wizualnie zaakceptuj przebieg;
2. ustal oraz zatwierdź aktywny test regresji z korytarzem, limitem objazdu i punktami kontrolnymi;
3. w edytorze zmień status przejścia na `stable` i zapisz;
4. uruchom aktualizację ponownie — od tej chwili brak lub błąd tej regresji blokuje kandydata.

Nie zmieniaj statusu na `stable` przed zatwierdzeniem testu. Program nie promuje przejścia automatycznie.

## Sprawdzanie zbędnego punktu

Procedura jest celowo kontrolowana, a nie automatycznym optymalizatorem:

1. Utwórz roboczą kopię `rejsy.xlsx`; nie edytuj od razu źródła.
2. Usuń z kopii jeden badany punkt przejścia i przenumeruj dalsze `Przejscie_lp`, aby znów tworzyły ciąg `1..N`.
3. Uruchom `sea-router-custom\scripts\Update-SeaRouterPassages.ps1 -WorkbookPath <pełna-ścieżka-kopii.xlsx> -NoActivate`. Kandydat ma zostać zbudowany i przetestowany, ale nie wolno aktywować go podczas tej próby.
4. Punkt wolno uznać za zbędny wyłącznie wtedy, gdy przechodzą wszystkie regresje danego przejścia: limit długości, współczynnik objazdu, wszystkie punkty kontrolne i dozwolony korytarz. Sam kod HTTP 200 nie wystarcza.
5. Przy sukcesie powtórz próbę kontrolną i dopiero potem usuń punkt w głównym Excelu. Przy błędzie odrzuć kopię i pozostaw punkt.

`-NoActivate` zawsze pozostawia aktywny `E:\sea-router` bez zmian. Katalog kandydata pozostaje do oględzin.

## Przejścia Patagonii

Test `Puerto Williams → Ushuaia` jest aktywny: wymaga Kanału Beagle, przejścia w pobliżu zatwierdzonych punktów i pozostania w dozwolonym korytarzu, przez co zabrania opływania Isla Navarino. Konfiguracja ma nadal wyłączone miejsca na Cockburn, Magdalena oraz wejście do Cieśniny Magellana. Docelowy test `Ushuaia → Punta Arenas` ma wymagać wyjścia na zachód, właściwego systemu kanałów i wejścia do Cieśniny Magellana od zachodu lub południowego zachodu, a zabraniać objazdu Atlantykiem po wschodniej stronie Ziemi Ognistej. Ich korytarze i waypointy zostaną dodane dopiero po zatwierdzeniu przez użytkownika.
