# Założenia projektu Rejsy-morskie

## Cel

Celem projektu jest przygotowanie kompletnej, odtwarzalnej prezentacji rejsu na mapie na podstawie jednego źródła danych: skoroszytu `routes/rejsy.xlsx`.

Program ma przetwarzać dane rejsu do postaci możliwej do wykorzystania w Google My Maps / Google Earth, bez ręcznego rysowania całej trasy po każdej zmianie danych.

## Docelowy rezultat

Dla każdego rejsu mają powstawać co najmniej:

- punkty portów w kolejności odwiedzin;
- rzeczywista trasa morska pomiędzy portami, prowadzona przez wodę i unikająca wejścia na ląd;
- daty i numery dni rejsu;
- informacje o postoju w portach;
- dystanse poszczególnych etapów;
- KML gotowy do importu do Google My Maps / Google Earth;
- pomocnicze pliki GeoJSON i wynikowy Excel z danymi uzupełnionymi przez program.

W trudnych miejscach, takich jak cieśniny i kanały, dopuszcza się korekty parametrów routingu lub pojedynczych punktów trasy. Parametr `CA` służy do sterowania odsunięciem trasy od wybrzeża.

## Źródło danych

Głównym źródłem danych użytkownika jest:

`routes/rejsy.xlsx`

Skoroszyt opisuje rejs, porty, daty, postoje i pozostałe dane wejściowe. Szczegółowa definicja arkuszy i kolumn znajduje się w `docs/specyfikacja-excel.md`.

Program nie powinien nadpisywać wejściowego skoroszytu podczas generowania wyników. Dane wyliczone są zapisywane do plików wynikowych.

## Zasada odtwarzalności

Repozytorium GitHub ma zawierać wszystko, co jest niezbędne do zrozumienia i odtworzenia projektu, z wyjątkiem dużych danych technicznych oraz plików wynikowych, które można ponownie wygenerować.

W GitHubie przechowujemy:

- kod programu;
- dokumentację i specyfikacje;
- `routes/rejsy.xlsx` jako właściwe dane wejściowe projektu;
- testy i małe pliki pomocnicze potrzebne do rozwoju programu.

Lokalnie pozostają przede wszystkim:

- duże grafy i dane OSM używane przez `sea-router`;
- cache geokodowania;
- wygenerowane KML, GeoJSON i wynikowe skoroszyty w `outputs/`.

Utrata plików wynikowych nie powinna oznaczać utraty projektu: powinny dać się odtworzyć z kodu, `routes/rejsy.xlsx` i lokalnych danych routingu.

## Planowane rozszerzenie: filmy

Do punktów portów mają być przypisywane filmy związane z danym portem.

Uzgodniona koncepcja jest następująca:

- w arkuszu `Porty` zostanie dodana kolumna `Filmy_grupa`;
- dla portu wpisuje się identyfikator grupy, np. `51`;
- pliki filmowe mają nazwy w formacie `<grupa>_<kolejność>-<opis>.mp4`, np. `51_1-film1.mp4`, `51_2-film2.mp4`;
- system ma odnajdywać wszystkie filmy zaczynające się od identyfikatora grupy, np. `51_`;
- dodanie lub usunięcie filmu z tej samej grupy nie wymaga zmiany Excela;
- techniczne numery grupy i kolejności nie powinny być eksponowane użytkownikowi na mapie;
- lista filmów ma być dynamiczna: po zmianie zawartości internetowego katalogu aktualny zestaw ma pojawić się po odświeżeniu albo ponownym otwarciu Google Earth;
- aktualizacja filmów nie może wymagać ponownego uruchamiania generatora Pythona, `sea-routera` ani ponownego generowania całej trasy;
- planowana architektura rozdziela stałą warstwę trasy i portów od dynamicznej warstwy mediów, prawdopodobnie z użyciem KML `NetworkLink`;
- preferowanym miejscem pierwszego testu przechowywania filmów jest Google Drive; Cloudflare R2 pozostaje wariantem zapasowym;
- YouTube nie jest planowany jako magazyn filmów.

Szczegółowe wymagania i test akceptacyjny opisuje `docs/filmy.md`.

Ta funkcja jest założeniem do kolejnego etapu rozwoju i nie jest jeszcze zaimplementowana w bieżącej wersji programu.

## Zasada rozwoju

Każda zmiana struktury danych wejściowych musi być wykonywana jako jedna spójna zmiana projektu:

1. aktualizacja `docs/specyfikacja-excel.md`;
2. aktualizacja kodu czytającego/generującego dane;
3. aktualizacja lub migracja `routes/rejsy.xlsx`;
4. aktualizacja testów i dokumentacji;
5. commit zmian do GitHuba.

Dzięki temu dokumentacja, dane i program nie powinny się rozjeżdżać.
