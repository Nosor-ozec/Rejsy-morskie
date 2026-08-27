# Założenia projektu Rejsy-morskie

## Cel

Celem jest odtwarzalna prezentacja rejsu na mapie Leaflet. Program łączy trasę i porty z opisowymi linkami do mediów, a wynik publikuje jako statyczną stronę GitHub Pages.

## Źródła danych

Obowiązują dokładnie dwa skoroszyty:

- `routes/rejsy.xlsx` — arkusze `Rejsy`, `Porty` i aktualizowany w miejscu arkusz `Etapy`;
- `routes/media.xlsx` — arkusz `Filmy` z identyfikatorami wewnętrznymi, opisami, URL i pozycją względem portu.

Nie są źródłami danych `filmy-test.xlsx`, `rejsy-z-etapami.xlsx` ani folder `rejsy-filmy`.

## Rozdzielenie funkcji

- Trasa zmienia się rzadko. Jej generowanie może wymagać geokodera i lokalnego sea-routera, ale zgodne GeoJSON są używane ponownie.
- Media można zmieniać bez ponownego liczenia trasy. Program czyta wyłącznie bieżący `media.xlsx`.
- Stronę można przebudować z zapisanej geometrii i danych bez uruchamiania sea-routera.

## Bezpieczeństwo danych

`rejsy.xlsx` pozostaje jednym głównym skoroszytem. Program najpierw tworzy kopię bezpieczeństwa, zapisuje i sprawdza plik tymczasowy, a dopiero potem atomowo zastępuje właściwy plik. Zapisane `Lat`/`Lon` są używane bez ponownego geokodowania.

## Prezentacja

Docelową prezentacją jest Leaflet na GitHub Pages. Google Earth, KML i `NetworkLink` nie należą do bieżącej architektury. Media są zwykłymi linkami HTTPS otwieranymi w nowej karcie; strona ich nie osadza i nie interpretuje nazwy pliku na Drive.
