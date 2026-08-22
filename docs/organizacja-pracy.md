# Organizacja pracy z projektem

## Podział odpowiedzialności

### Zmiana struktury danych lub programu

Zmiany takie jak dodanie kolumny do Excela, zmiana znaczenia pola, dodanie arkusza albo nowej funkcji generatora są zmianami programu.

Powinny być wykonywane razem z odpowiednimi zmianami kodu, dokumentacji i testów, a następnie zapisane w GitHubie. Do takich prac może być używany Codex/Work.

### Wprowadzanie danych konkretnego rejsu

Gdy struktura skoroszytu jest już ustalona, użytkownik normalnie edytuje lokalną kopię:

`E:\Rejsy-morskie\routes\rejsy.xlsx`

Wpisuje lub poprawia porty, daty, postoje i inne dane rejsu. Nie wymaga to zmiany programu.

Po istotnych zmianach danych `routes/rejsy.xlsx` powinien zostać zapisany również w repozytorium GitHub, aby kod, dokumentacja i dane wejściowe miały wspólną historię wersji.

## Co jest na GitHubie

Repozytorium jest trwałym źródłem projektu i powinno zawierać:

- `README.md`;
- katalog `docs/`;
- kod w `src/`;
- testy;
- `routes/rejsy.xlsx` — właściwy skoroszyt wejściowy z danymi rejsów.

Plik XLSX jest binarny, więc GitHub nie pokazuje wygodnego porównania zmian komórek, ale kolejne commity przechowują kolejne wersje całego pliku.

## Co pozostaje lokalnie

Nie wersjonujemy plików, które są duże albo można je ponownie wygenerować:

- `outputs/`;
- wygenerowanych GeoJSON;
- wygenerowanych KML;
- wynikowych skoroszytów;
- dużych danych OSM i grafów `sea-router`;
- lokalnego cache geokodowania.

## Uruchamianie generatora

Generator działa na komputerze, na którym dostępne są lokalny `sea-router`, jego dane oraz lokalna kopia repozytorium.

Najpierw uruchamia się router w osobnym oknie:

```powershell
E:\sea-router\rust\target\release\sea-router-rs.exe serve E:\sea-router\data
```

Następnie generator:

```powershell
rejsy-morskie generate E:\Rejsy-morskie\routes\rejsy.xlsx E:\Rejsy-morskie\outputs
```

Program czyta dane z `routes/rejsy.xlsx`, wylicza harmonogram i etapy, korzysta z geokodowania oraz `sea-routera`, a następnie zapisuje wyniki w `outputs/`.

Codex/Work może uruchamiać i testować te polecenia podczas prac rozwojowych. Po skonfigurowaniu środowiska generator nie wymaga Codexa do zwykłego użycia — może być uruchamiany lokalnie przez użytkownika. W przyszłości można przygotować prosty skrypt `.bat`/PowerShell uruchamiający cały proces.

## Typowy cykl pracy

1. Zaktualizować lokalne repozytorium z GitHuba, jeśli były zmiany programu.
2. Otworzyć `routes/rejsy.xlsx` i wprowadzić dane rejsu.
3. Zapisać skoroszyt.
4. Uruchomić lokalny `sea-router`.
5. Uruchomić generator.
6. Sprawdzić wygenerowany KML w Google My Maps / Google Earth.
7. Jeśli trzeba, poprawić dane lub parametry i wygenerować ponownie.
8. Po istotnej zmianie danych zapisać aktualny `routes/rejsy.xlsx` w GitHubie.

## Ważna zasada bezpieczeństwa

GitHub jest podstawowym trwałym zapisem projektu. Rozmowa z ChatGPT, sesja Work ani katalog roboczy Codexa nie powinny być jedynym miejscem przechowywania ustaleń lub ukończonego kodu.

Istotne decyzje projektowe należy dopisywać do dokumentacji, a ukończone zmiany programu i danych wejściowych commitować do repozytorium.
