# Inwentaryzacja działającego `E:\sea-router`

Stan odczytano 30 sierpnia 2026 r. bez modyfikowania instalacji.

## Pochodzenie i wersja

- repozytorium bazowe: `https://github.com/Lvdwardt/sea-router.git`;
- gałąź zapisana w metadanych instalacji: `main`;
- dokładny commit kodu: `65cc022269d42f69ffad14fb1b69cce641ee6170`;
- tag wydania danych widoczny w konfiguracji projektu bazowego: `graph-depth-16`;
- commit wskazywany przez ten tag w lokalnych metadanych: `b97958666a3ce1fbd86823b2f144c1fce4f125c0`.

Tag danych nie jest identyfikatorem kodu użytego lokalnie: zasoby wydania pod tym stałym tagiem mogły być zastępowane przez workflow. Dlatego instalator przypina commit kodu i sumy kontrolne plików/danych, a nie polega wyłącznie na tagu.

Historia terminala potwierdza sklonowanie wskazanego repozytorium, wejście do `sea-router\rust` i `cargo build --release`. Pierwsza próba poprzedzała instalację Visual Studio Build Tools, kolejna nastąpiła po niej.

## Narzędzia i budowa

- Rust toolchain: `1.97.1-x86_64-pc-windows-msvc`;
- `rustc 1.97.1 (8bab26f4f 2026-07-14)`;
- `cargo 1.97.1 (c980f4866 2026-06-30)`;
- Visual Studio Build Tools 2022: 17.14.39 (instalacja 17.14.37614.0), komponent C++ x86/x64;
- zależności Rust przypina istniejący `rust/Cargo.lock`;
- profil release: `opt-level=3`, `lto=true`, `codegen-units=1`;
- odtworzona komenda: `rustup run 1.97.1-x86_64-pc-windows-msvc cargo build --release --locked`.

Obecne binarium `rust/target/release/sea-router-rs.exe` ma 1 653 248 bajtów i SHA-256 `24095FFD645780969A99C08A3ED5AD8551FF652BADC7AAC45A7F95AEA37AE703`.

Skrót binarium jest wartością audytową, a nie przenośnym warunkiem instalacji: ścieżka katalogu kompilacji może wpływać na bajty EXE. Ścisłymi warunkami są kod, toolchain, dane wejściowe i wynikowy graf; zachowanie potwierdza regresja geometrii.

## Dane i graf

Wejściem jest `data/osm_land_simplified.geojson.json`:

- skompresowany zasób: `https://github.com/Lvdwardt/sea-router/releases/download/graph-depth-16/osm_land_simplified.geojson.json.gz`;
- SHA-256 gzip: `E36737C0EE4CB85AB42C421DCEFC076E7D5D15E4A94FDD730766A016B7F48D1E`;
- SHA-256 po rozpakowaniu: `A61AAA5684AA18BCC7C0F7F6A73A6537F1556440E463B5FBA38DD6391713A3F7`;
- pierwotne źródło deklarowane przez workflow: `https://osmdata.openstreetmap.de/download/land-polygons-complete-4326.zip`;
- deklarowana konwersja: `ogr2ogr -f GeoJSON osm_land_simplified.geojson.json land-polygons-complete-4326/land_polygons.shp`.

`osm_land_simplified.geojson.json.raster` jest generowanym, odtwarzalnym cache: komórka 0,02°, 18 000 × 9 000, format 3. Jego zaobserwowany SHA-256 to `A84FA75294BE022B7FA5FC0F813560F346A35780739230404ABF99AF107ED180`.

Graf powstał dla głębokości 16. Odtworzona komenda to `sea-router-rs.exe generate 16 <data-dir>`. Parametry zaszyte w przypiętym kodzie obejmują: światowy bbox, maksymalną próbkę adaptacyjną 0,25°, do 20 przebiegów łączenia otwartego oceanu, próbkę krawędzi 0,5 km, dla krawędzi krótszych niż 3 km próbkę 0,05 km oraz przybliżony bufor wybrzeża 1,5 km.

Zachowany graf bazowy ma 5 786 546 węzłów, 9 379 126 krawędzi i SHA-256 `2B319816A77EB372907EA10FEB20DBCA7DF0A6B208A4EA6B4D9BE3FEAA5AE649`. Graf po dodaniu Cieśniny Mesyńskiej ma 5 786 558 węzłów, 9 379 147 krawędzi i SHA-256 `544C9AF131A50C85B500F5A9D44CD12B7A8A666E793E66393FC69FBF1E5F6406`.

## Przejścia ręczne

| Przejście | Pochodzenie | Waypointy | Krawędzie dodane do zachowanego grafu | Uzasadnienie zapisane w kodzie/danych |
|---|---:|---:|---:|---|
| Kanał Sueski | kod bazowy | 28 | 37 | oś z OSM, uproszczona z 92 węzłów metodą Douglas–Peucker, epsilon 0,001 |
| Kanał Panamski | kod bazowy | 14 | 23 | ręczna oś, według komentarza sprawdzona względem map ACP |
| Kanał Koryncki | kod bazowy | 4 | 13 | ręczne przejście przez kanał niewidoczny dla bazowej rozdzielczości grafu |
| Cieśnina Mesyńska | zmiana Rejsy-morskie | 12 | 21 | przybliżona oś północnego pasa TSS, zapewniająca stabilne przejście wąskiej cieśniny |

Pełne współrzędne lokalnej Cieśniny Mesyńskiej są w `passages.json`. Współrzędne trzech przejść bazowych pozostają w przypiętym `rust/src/canals.rs`; ich integralność zabezpiecza hash obiektu zapisany w lockfile. Analiza kodu, różnicy względem indeksu źródeł i delta grafu nie wykazała innych ręcznie wstrzykniętych przejść.

Współrzędne poniżej mają kolejność `[Lon, Lat]` i zostały odczytane z działającego kodu:

- Suez (28): `[32.3263,31.2757]`, `[32.3067,31.2505]`, `[32.3047,31.2402]`, `[32.3043,31.2200]`, `[32.3177,30.8114]`, `[32.3353,30.7482]`, `[32.3437,30.7128]`, `[32.3440,30.7050]`, `[32.3243,30.6200]`, `[32.3048,30.5809]`, `[32.3039,30.5656]`, `[32.3088,30.5496]`, `[32.3342,30.5181]`, `[32.3390,30.5061]`, `[32.3500,30.4522]`, `[32.3578,30.4352]`, `[32.3729,30.3606]`, `[32.4428,30.2827]`, `[32.5292,30.2532]`, `[32.5387,30.2429]`, `[32.5654,30.2010]`, `[32.5685,30.1865]`, `[32.5731,30.0537]`, `[32.5868,29.9728]`, `[32.5841,29.9576]`, `[32.5805,29.9506]`, `[32.5759,29.9436]`, `[32.5607,29.9303]`;
- Panama (14): `[-79.917,9.383]`, `[-79.913,9.360]`, `[-79.907,9.280]`, `[-79.870,9.210]`, `[-79.820,9.190]`, `[-79.760,9.160]`, `[-79.710,9.130]`, `[-79.680,9.090]`, `[-79.640,9.050]`, `[-79.600,9.020]`, `[-79.580,8.990]`, `[-79.560,8.960]`, `[-79.540,8.940]`, `[-79.530,8.900]`;
- Korynt (4): `[22.953,37.941]`, `[22.966,37.938]`, `[22.984,37.935]`, `[23.003,37.918]`;
- Mesyna (12): `[15.61879,38.14900]`, `[15.61625,38.16500]`, `[15.61378,38.18100]`, `[15.61486,38.19500]`, `[15.61650,38.21100]`, `[15.61798,38.23070]`, `[15.63144,38.23800]`, `[15.65029,38.24500]`, `[15.66914,38.25200]`, `[15.68799,38.25900]`, `[15.69622,38.26600]`, `[15.69986,38.27050]`.

## Źródłowe, generowane i lokalne

- ponownie pobieralne: archiwum kodu przypiętego commita, paczka danych lądowych;
- źródłowe dla odtworzenia: lockfile, `passages.json`, kod bazowy, GeoJSON lądu;
- generowane: `.raster`, `data/graph/sea-graph.json`, `rust/target`, binarium, logi serwera;
- zmiana własna: wyłącznie Cieśnina Mesyńska w `passages.json`;
- przejścia bazowe: Suez, Panama i Korynt — część wskazanego commita upstream.

## Czego nie dało się dowieść

- nie zachował się dokładny tekst polecenia generującego obecny graf; polecenie i głębokość odtworzono z kodu, czasu plików, liczności i bitowo zgodnych wyników;
- nie ma logu rozstrzygającego, czy lokalny GeoJSON pobrano jako gotowy zasób wydania, czy przygotowano z pierwotnego ZIP OSM; jego treść jest jednoznacznie określona sumą SHA-256;
- komentarze upstream podają pochodzenie osi Suezu i Panamy, lecz instalacja nie zawiera osobnych plików roboczych ani zewnętrznego audytu tych punktów;
- dokładny historyczny zestaw opcji instalatora Visual Studio nie zachował się; można dowieść obecności wymaganych narzędzi C++ i wersji instalacji.
