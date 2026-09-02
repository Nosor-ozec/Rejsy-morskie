# Sea-router: architektura i odtwarzanie instalacji

## Rola w projekcie

Sea-router jest lokalną usługą HTTP wyznaczającą rzeczywiste geometrie odcinków morskich. `Uruchom-Rejsy.cmd` korzysta z niej podczas generowania tras. Usługa, dane świata i graf pozostają lokalne; nie są publikowane wraz ze stroną Leaflet.

To jest pierwszy moduł przyszłego pełnego instalatora Rejsy-morskie. Kolejne moduły mają później objąć Pythona, `.venv`, zależności aplikacji i pozostałe komponenty stanowiska.

## Co przechowujemy w projekcie, a co lokalnie

W `sea-router-custom` przechowujemy wyłącznie:

- przypięte wersje, adresy i sumy kontrolne;
- generowaną techniczną definicję własnych przejść; jej źródłem jest arkusz `Lokalizacje`;
- skrypty instalacji i testów;
- dokumentację i lekkie testy konfiguracji.

Poza projektem, w `E:\sea-router`, pozostają kod roboczy upstream, pobrane dane lądowe, cache rastrowy, wygenerowany graf, katalog kompilacji i binarium. Wszystkie te ciężkie elementy można odtworzyć.

## Proces instalacji

### Uruchomienie przez użytkownika

Najprostszy sposób na nowym komputerze to dwuklik:

`Install-SeaRouter.cmd`

Plik znajduje się w katalogu głównym Rejsy-morskie. Sam ustala położenie projektu, dlatego nie ma znaczenia, jaki katalog był aktywny przed jego uruchomieniem. Wywołuje PowerShell z `-ExecutionPolicy Bypass` wyłącznie dla tego jednego procesu — nie zmienia trwałych ustawień systemu. Okno pozostaje otwarte po zakończeniu, aby użytkownik mógł przeczytać wynik.

Tryb kontroli bez instalacji:

```text
Install-SeaRouter.cmd test
```

Wrapper przekazuje kod zakończenia instalatora i nie ukrywa jego komunikatów. Nie usuwa, nie przenosi i nie przemianowuje istniejącego `E:\sea-router`. Nie instaluje też Pythona, `.venv` ani zależności Rejsy-morskie.

`sea-router-custom/scripts/Install-SeaRouter.ps1`:

1. sprawdza Rustup, dokładny toolchain Rust oraz Visual Studio Build Tools z C++ x64;
2. pobiera archiwum dokładnego commita `65cc022269d42f69ffad14fb1b69cce641ee6170`;
3. weryfikuje krytyczne pliki bazowe za pomocą skrótów obiektów Git, bez wykonywania operacji Git;
4. wstrzykuje przejścia z `passages.json` do czystego `canals.rs`;
5. buduje kod w profilu release z przypiętym `Cargo.lock`;
6. pobiera i weryfikuje GeoJSON lądu;
7. generuje graf od zera dla głębokości 16 i wykonuje deterministyczną kontrolę semantyczną węzłów oraz krawędzi;
8. uruchamia własny serwer na porcie testowym i wykonuje testy regresji geometrii;
9. dopiero po sukcesie przenosi gotowy katalog do wskazanego, nieistniejącego celu.

Skrypt nie nadpisuje istniejącej instalacji. Opcja `-ValidateOnly` ogranicza działanie do kontroli wymagań i konfiguracji. Opcja `-InstallMissingTools` może przygotować Rustup oraz Build Tools przez `winget`, ale instalacja narzędzi systemowych powinna być wykonywana świadomie w podniesionej konsoli.

Surowy SHA-256 `sea-graph.json` jest tylko wartością audytową, ponieważ kolejność krawędzi pochodzących z iteracji struktur haszujących nie jest stabilna między procesami. Kontrola instalacyjna wymaga dokładnej liczby węzłów i krawędzi, zgodności przypisania identyfikatorów węzłów do współrzędnych oraz SHA-256 posortowanego multizbioru trójek `(from, to, weight)`. Nie jest to porównanie przybliżone: pojedyncza zmieniona współrzędna, waga, brakująca krawędź albo dodatkowy duplikat zostają odrzucone.

Istniejącą instalację aktualizuje `Aktualizuj-Przejscia-SeaRouter.cmd`. Skrypt generuje `passages.json` z `routes/rejsy.xlsx`, buduje pełnego kandydata w osobnym katalogu i uruchamia kontrolę semantyczną oraz regresje. Zawsze obowiązkowe są Mesyna, Suez, Panama i Korynt. Przejście `stable` dodatkowo wymaga własnego aktywnego testu i jego sukcesu; test przejścia `development`, jeżeli istnieje, jest uruchamiany diagnostycznie i jego błąd daje ostrzeżenie bez blokady. Dopiero po wszystkich kontrolach obowiązkowych skrypt zatrzymuje proces należący dokładnie do aktywnej instalacji, przenosi starą instalację do datowanego backupu i aktywuje kandydata. Nieudana aktywacja wykonuje rollback. Szczegóły pracy iteracyjnej opisuje [`dodawanie-przejsc-sea-router.md`](dodawanie-przejsc-sea-router.md).

`Install-SeaRouter.cmd` jest pierwszym użytkowym elementem przyszłego instalatora projektu. Planowany później `Install-Rejsy.cmd` ma koordynować instalację sea-routera, Pythona, `.venv`, zależności aplikacji i pozostałych komponentów. Pełny instalator nie jest jeszcze częścią tego modułu.

## Testy regresji

`Test-SeaRouter.ps1` nie ogranicza się do kodu HTTP 200. Dla Cieśniny Mesyńskiej, Suezu, Panamy, Koryntu i trasy Puerto Williams–Ushuaia przez Kanał Beagle sprawdza:

- obecność końcowej geometrii LineString;
- przejście w pobliżu kilku punktów kontrolnych;
- pozostanie w dozwolonym obszarze;
- stosunek długości trasy do odległości bezpośredniej, wykrywający absurdalny objazd.

Przypadek Koryntu używa podejść blisko wejść do kanału i `penalty=1`; taki zakres został zweryfikowany dla obecnego grafu. Test Beagle prowadzi od Puerto Williams do Ushuaia i sprawdza wąski korytarz kanału. Ponieważ Beagle ma obecnie status `development`, wynik tego testu jest diagnostycznym ostrzeżeniem, nie warunkiem aktywacji. Po zatwierdzeniu trasy i zmianie statusu na `stable` ten sam test stanie się obowiązkowy. Konfiguracja nadal zawiera wyłączone szkielety dla Cockburn Channel, Magdalena Channel i wejścia do Cieśniny Magellana.

Test działającej usługi:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\sea-router-custom\scripts\Test-SeaRouter.ps1 -BaseUrl http://127.0.0.1:3001
```

## Bezpieczny czysty test

Poniższej procedury nie należy wykonywać bez wcześniejszej zgody i upewnienia się, że sea-router nie jest używany:

1. zakończyć proces obecnego sea-routera;
2. potwierdzić, że `E:\sea-router` jest dokładnym katalogiem źródłowym;
3. wybrać nieistniejącą nazwę, np. `E:\sea-router-backup-20260830`;
4. przemianować `E:\sea-router` na tę nazwę — nie usuwać go;
5. uruchomić instalator z celem `E:\sea-router`;
6. poczekać na pełne pobranie, kompilację, generowanie grafu i cztery testy regresji;
7. uruchomić normalną lokalną generację Rejsy-morskie i porównać wynik;
8. zachować backup do czasu akceptacji użytkownika; jego późniejsze usunięcie jest osobną, ręczną decyzją.

Polecenie dla kroku 5, dopiero po odłożeniu starego katalogu:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\sea-router-custom\scripts\Install-SeaRouter.ps1 -TargetPath E:\sea-router
```

Jeżeli instalacja nie przejdzie, skrypt nie przenosi niepełnej wersji do celu. Katalog roboczy pozostaje do diagnostyki, a backup można przywrócić przez ponowne przemianowanie.
