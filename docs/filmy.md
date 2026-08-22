# Filmy na mapie — założenia i plan implementacji

## Cel

Filmy związane z portami mają być widoczne z poziomu mapy Google Earth, ale ich dodawanie i usuwanie nie może wymagać ponownego uruchamiania generatora tras ani ponownego liczenia `sea-routerem`.

Trasa i porty są warstwą względnie stałą. Filmy mają stanowić osobną, dynamiczną warstwę mediów.

## Powiązanie portu z grupą filmów

W arkuszu `Porty` zostanie dodana kolumna `Filmy_grupa`.

Przykład:

```text
Filmy_grupa = 51
```

Oznacza to, że do danego portu należą wszystkie filmy, których nazwa zaczyna się od `51_`.

## Nazewnictwo filmów

Format nazwy:

```text
<grupa>_<kolejność>-<opis>.mp4
```

Przykłady:

```text
51_1-film1.mp4
51_2-film2.mp4
51_3-film3.mp4
```

Przykłady z dotychczasowych danych:

```text
2_1-Dubrownik.mp4
4_1-Katania.mp4
11_1-Casablanca.mp4
11_2-Casablanca meczet.mp4
```

W Excelu przy Casablance wpisuje się tylko:

```text
Filmy_grupa = 11
```

Numery grupy i kolejności są techniczne i nie powinny być pokazywane użytkownikowi na mapie. Opis filmu może być wyprowadzany z części nazwy po myślniku.

## Dynamiczne aktualizowanie

Lista filmów nie jest zapisywana na stałe w KML trasy. Ma być ustalana dynamicznie na podstawie aktualnej zawartości internetowego katalogu filmów.

W konsekwencji:

- dodanie nowego pliku, np. `51_3-...mp4`, nie wymaga zmiany Excela;
- usunięcie istniejącego filmu nie wymaga zmiany Excela;
- nie trzeba ponownie uruchamiać generatora Pythona;
- nie trzeba ponownie uruchamiać `sea-routera`;
- nie trzeba ponownie generować całej mapy;
- po odświeżeniu albo ponownym otwarciu mapy Google Earth użytkownik ma zobaczyć aktualny zestaw filmów.

To wymaganie jest kluczowe dla architektury rozwiązania.

## Architektura docelowa do sprawdzenia

Planowany podział:

```text
stała warstwa: trasa + porty
        ↓
Google Earth
        ↓
dynamiczna warstwa mediów przez KML NetworkLink
        ↓
internetowy katalog filmów
```

Google Earth ma pobierać dynamiczną warstwę mediów przez `NetworkLink` lub równoważny mechanizm pozwalający odświeżyć dane bez ponownego generowania trasy.

Przed przyjęciem rozwiązania jako ostatecznego trzeba wykonać praktyczny test na jednym porcie i jednym filmie, a następnie sprawdzić dodanie drugiego filmu oraz usunięcie pierwszego.

## Miejsce publikacji mapy

Docelowa mapa/projekt Google Earth ma być publikowana i udostępniana z konta Google właściciela projektu.

Mapa i magazyn filmów są oddzielnymi elementami: odbiorca mapy nie powinien potrzebować dostępu administracyjnego do miejsca przechowywania filmów.

## Miejsce przechowywania filmów

### Wariant preferowany: Google Drive

Pierwszy test należy wykonać z filmami przechowywanymi na Google Drive, ponieważ:

- mapa Google Earth i filmy mogą być utrzymywane w ekosystemie tego samego konta Google;
- zarządzanie plikami jest proste;
- można dodawać i usuwać pliki bez ingerencji w dane trasy;
- nie trzeba utrzymywać dodatkowej usługi, jeśli Drive spełni wymagania techniczne.

Do sprawdzenia w teście:

- czy link do filmu działa poprawnie dla osoby oglądającej udostępnioną mapę;
- czy film otwiera się w wygodny sposób z opisu portu;
- czy warstwa dynamiczna może wykrywać aktualny zestaw plików;
- czy dodanie/usunięcie filmu jest widoczne po odświeżeniu Google Earth bez uruchamiania generatora;
- czy wymagane ustawienia udostępniania są akceptowalne.

### Wariant zapasowy: Cloudflare R2

Jeżeli Google Drive okaże się niewygodny z powodu sposobu tworzenia linków, automatycznego katalogowania albo odświeżania danych, wariantem zapasowym jest Cloudflare R2 z publicznymi adresami HTTPS.

YouTube nie jest planowany jako magazyn filmów dla tego projektu.

## Test akceptacyjny

Przed pełną implementacją należy wykonać minimalny test:

1. Jeden port otrzymuje `Filmy_grupa`, np. `51`.
2. W internetowym magazynie istnieje `51_1-test.mp4`.
3. Film pojawia się przy porcie w Google Earth.
4. Bez zmiany Excela i bez uruchamiania generatora dodajemy `51_2-test2.mp4`.
5. Po odświeżeniu lub ponownym otwarciu mapy widoczne są oba filmy.
6. Usuwamy `51_1-test.mp4`.
7. Po odświeżeniu mapy pozostaje tylko drugi film.

Dopiero po przejściu tego testu należy rozszerzać rozwiązanie na wszystkie porty.

## Stan

Ta funkcja nie jest jeszcze zaimplementowana. Dokument opisuje uzgodniony kierunek i wymagania do kolejnego etapu rozwoju.
