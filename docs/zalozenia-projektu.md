# Założenia projektu Rejsy-morskie

## Cel

Celem jest odtwarzalna prezentacja rejsu na mapie Leaflet, najpierw w pełni sprawdzana lokalnie, a dopiero później przygotowywana do ręcznej publikacji.

## Źródła danych

Obowiązują dokładnie dwa skoroszyty:

- `routes/rejsy.xlsx` — arkusze `Rejsy`, `Porty` i aktualizowany w miejscu arkusz `Etapy`;
- `routes/media.xlsx` — arkusz `Filmy` z identyfikatorami wewnętrznymi, opisami, URL i pozycją względem portu.

Nie są źródłami danych `filmy-test.xlsx`, `rejsy-z-etapami.xlsx` ani folder `rejsy-filmy`.

## Rozdzielenie generowania od publikacji

- `Uruchom-Rejsy.cmd` generuje trasy i kompletny wynik `outputs/podglad-leaflet`, a następnie otwiera go lokalnie.
- `Publikuj-Rejsy.cmd` kopiuje do `docs` dokładnie sprawdzony wynik na podstawie manifestu sum kontrolnych.
- Lokalna i publiczna mapa używają tego samego `index.html`, `app.js`, stylów, danych i geometrii; nie istnieją dwie implementacje prezentacji.
- Żaden ze skryptów nie wykonuje commit ani push.

## Bezpieczeństwo danych

`rejsy.xlsx` pozostaje jednym głównym skoroszytem. Program tworzy lokalny `rejsy.bak.xlsx`, zapisuje plik tymczasowy, a dopiero potem atomowo zastępuje właściwy plik. Zapisane `Lat`/`Lon` są używane bez ponownego geokodowania.

## Prezentacja

Docelową prezentacją jest Leaflet — lokalnie i po ręcznej publikacji. KML jest tylko pomocniczym wynikiem kontroli. Media są zwykłymi opisowymi linkami HTTPS otwieranymi w nowej karcie; strona ich nie osadza i nie interpretuje nazwy pliku na Drive.
