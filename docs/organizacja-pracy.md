# Organizacja pracy i publikacja

## Stały sposób pracy

- Główny Chat służy do ustalania wymagań i podejmowania decyzji.
- Istnieje jeden stały lokalny wątek Work `Rejsy-morskie — WORK`, pracujący na `E:\Rejsy-morskie`.
- Kolejne zadania Work wykonujemy w tym samym wątku, żeby nie mnożyć Worków i nie tracić dostępu do lokalnego folderu.
- Work działa w trybie `Na Twoim komputerze` i ma potwierdzony zapis do `E:\Rejsy-morskie`.
- GitHub nie jest synchronizowany automatycznie.
- Commit i push wykonuje użytkownik ręcznie w GitHub Desktop.

## Generowanie i pełna kontrola lokalna

Uruchom `Uruchom-Rejsy.cmd`. Skrypt:

1. uruchamia sea-router, jeżeli ten jeszcze nie działa;
2. oblicza trasy i aktualizuje `routes/rejsy.xlsx` w miejscu, zachowując `routes/rejsy.bak.xlsx`;
3. czyta `routes/media.xlsx`;
4. buduje kompletną stronę w `outputs/podglad-leaflet`;
5. uruchamia lokalny serwer WWW i otwiera mapę w przeglądarce.

Ten etap nie wymaga commita ani połączenia z GitHubem. Lokalna mapa jest pełnym wynikiem Leaflet: zawiera porty, rzeczywiste trasy GeoJSON, media i punkty `Na morzu`.

Aktualizacja skoroszytu dotyczy danych wyliczanych (`Porty.Lat/Lon`, `Etapy`). Brakujące współrzędne są rozwiązywane w kolejności `Porty.Lat/Lon → Lokalizacje → geokoder zwykłego portu → błąd`. Arkusz `Lokalizacje` jest ręczną bazą referencyjną i program nigdy nie zmienia jego danych. Kolumny `Porty.Kiedy` i `Porty.Postoj_dni` pozostają po przebiegu dokładnie w pierwotnej postaci. Dla `+N` obowiązuje `data_bieżącego = data_poprzedniego + N + max(Postoj_dni - 1, 0)`. Data `RRRR-MM-DD` lub `N` bez znaku jest niezależną kotwicą i wymaga tylko zachowania chronologii względem poprzedniego postoju. Dni wpływu oraz `Dzien_od` i `Dzien_do` są przy każdym przebiegu liczone ponownie z `Porty`; stare wartości `Etapy` są zastępowane.

Ręczne `Porty.Lat/Lon` punktów trasy są nienaruszalne. Gdy są puste, punkt może użyć wpisu `Lokalizacje` o tej samej znormalizowanej nazwie; program może skopiować te współrzędne do `Porty`, lecz nigdy nie uruchamia geokodera dla punktu trasy. Zmiana `Typ` pomiędzy `Punkt_trasy` i `Punkt_trasy_ukryty` zmienia wyłącznie widoczność technicznego znacznika, nie przebieg geometrii.

## Przygotowanie publikacji

Po zaakceptowaniu podglądu uruchom `Publikuj-Rejsy.cmd`. Skrypt sprawdza sumy plików lokalnego wyniku i kopiuje dokładnie te same pliki prezentacji oraz danych do `docs`. Nie przelicza trasy, nie tworzy innej wersji mapy i nie wykonuje żadnej operacji Git ani GitHub.

Następnie użytkownik sam wykonuje commit i push w GitHub Desktop.

## GitHub Pages

Repozytorium `Nosor-ozec/Rejsy-morskie` powinno publikować katalog `/docs` z gałęzi `main`. Po wypchnięciu zmian GitHub Pages udostępnia stronę zwykle pod adresem:

`https://nosor-ozec.github.io/Rejsy-morskie/`

KML pozostaje pomocniczym wynikiem kontroli. Docelową prezentacją lokalną i publiczną jest Leaflet.

## Zakres repozytorium

W repozytorium przechowujemy kod, testy, oba źródłowe XLSX, dokumentację i przygotowane pliki statycznej strony. Lokalne dane sea-routera, cache geokodowania, `outputs/` i `routes/rejsy.bak.xlsx` pozostają lokalne.
