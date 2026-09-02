# Własna warstwa sea-routera

Ten katalog jest małym, wersjonowalnym modułem odtwarzającym używaną przez projekt wersję sea-routera. Nie zawiera grafu świata, danych OSM, cache ani binariów.

## Zawartość

- `sea-router.lock.json` — przypięty commit bazowego projektu, toolchain, adresy danych, parametry oraz sumy kontrolne;
- `passages.json` — generowany z `routes/rejsy.xlsx / Lokalizacje`; zawiera przejścia dodane lokalnie i ich status;
- `regression-cases.json` — testy geometrii istniejących kanałów i miejsca na następne przypadki;
- `scripts/Apply-CustomPassages.ps1` — nakłada dane z `passages.json` na czysty kod bazowy;
- `scripts/Install-SeaRouter.ps1` — odtwarza sea-router od zera na Windows;
- `scripts/Test-SeaRouter.ps1` — sprawdza geometrię tras przez oczekiwane obszary;
- `tools/GraphSemanticCanonicalizer.rs` — tworzy deterministyczny odcisk węzłów i krawędzi niezależny od kolejności krawędzi w JSON;
- `INWENTARYZACJA.md` — dowody i ograniczenia rekonstrukcji obecnej instalacji.

Bazowy commit zawiera już ręczne definicje Kanału Sueskiego, Kanału Panamskiego i Kanału Korynckiego. Nie są one dublowane w `passages.json`. Warstwa projektu zawiera stabilną Cieśninę Mesyńską oraz projektowane przejście Beagle.

## Sposób nakładania przejść

Skrypt odtworzeniowy pobiera archiwum dokładnego commita i kontroluje skróty obiektów krytycznych plików. Następnie `Apply-CustomPassages.ps1` generuje z JSON blok `CanalPassage` i wstawia go do `rust/src/canals.rs`. Bazowy algorytm tworzenia grafu:

1. dodaje każdy waypoint jako węzeł;
2. łączy kolejne waypointy w łańcuch;
3. łączy pierwszy i ostatni waypoint z pięcioma najbliższymi węzłami bazowego grafu, o ile są bliżej niż 100 km.

Definicje służą wyłącznie do routingu i wizualizacji, nie do nawigacji.

Status `development` pozwala budować i technicznie weryfikować przejście bez blokady ze strony jego diagnostycznej regresji geograficznej. Status `stable` wymaga aktywnego, przechodzącego testu. Niezależnie od statusu obowiązują ścisła kontrola węzłów i krawędzi oraz bazowe regresje Mesyny, Suezu, Panamy i Koryntu.

Generator używa struktur haszujących, dlatego kolejność części krawędzi w surowym JSON może zmieniać się między uruchomieniami. Instalator nadal zapisuje stary SHA-256 JSON jako informację audytową, ale akceptuje graf wyłącznie po zgodności liczności i dwóch kanonicznych SHA-256: uporządkowanych węzłów `(id → lon, lat, depth)` oraz posortowanego multizbioru krawędzi `(from, to, weight)`. Zmiana współrzędnej, identyfikatora, wagi, brak lub dodatkowy duplikat krawędzi powoduje błąd.

## Użycie

Sama kontrola narzędzi i konfiguracji, bez pobierania oraz budowania:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\sea-router-custom\scripts\Install-SeaRouter.ps1 -ValidateOnly
```

Pełna instalacja jest przeznaczona dopiero do czystego testu opisanego w `docs/sea-router-instalacja.md`. Skrypt odmawia nadpisania istniejącego `E:\sea-router`.

Test już uruchomionego serwera:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\sea-router-custom\scripts\Test-SeaRouter.ps1 -BaseUrl http://127.0.0.1:3001
```
