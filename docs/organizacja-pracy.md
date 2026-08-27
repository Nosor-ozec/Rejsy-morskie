# Organizacja pracy i publikacja

## Zwykła aktualizacja mediów

1. Zmień opisy, aktywność lub URL w `routes/media.xlsx`.
2. Uruchom:

```powershell
rejsy-morskie media routes\rejsy.xlsx routes\media.xlsx docs
```

3. Zapisz i opublikuj zmieniony `routes/media.xlsx` oraz `docs/data/media.json`.

Sea-router nie jest uruchamiany. Nazwa pliku na Drive nie ma znaczenia; publiczny URL w arkuszu jest jedynym połączeniem z medium.

## Zmiana portów lub trasy

Uruchom lokalny sea-router, a następnie:

```powershell
rejsy-morskie route routes\rejsy.xlsx docs
rejsy-morskie media routes\rejsy.xlsx routes\media.xlsx docs
rejsy-morskie web routes\rejsy.xlsx docs
```

Pierwsze polecenie korzysta z istniejącego GeoJSON, jeśli współrzędne końców i parametr trasy nadal pasują. `rejsy.xlsx` jest aktualizowany w miejscu po wykonaniu bezpiecznej kopii.

## Przebudowa samej strony

```powershell
rejsy-morskie web routes\rejsy.xlsx docs
```

To polecenie nie uruchamia sea-routera i nie modyfikuje skoroszytów.

## GitHub Pages

Repozytorium `Nosor-ozec/Rejsy-morskie` powinno publikować katalog `/docs` z gałęzi `main`. Po wypchnięciu zmian GitHub Pages udostępnia stronę zwykle pod adresem:

`https://nosor-ozec.github.io/Rejsy-morskie/`

Publikację uznaje się za zakończoną dopiero po sprawdzeniu, że adres odpowiada i ładuje `data/route.json` oraz `data/media.json`.

## Zakres repozytorium

W repozytorium przechowujemy kod, testy, oba źródłowe XLSX, dokumentację, GeoJSON i pliki statycznej strony. Lokalne dane sea-routera, cache geokodowania i kopie `routes/.backups/` pozostają niewersjonowane.
