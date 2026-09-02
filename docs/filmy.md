# Media na mapie

Media są oddzielną warstwą danych z `routes/media.xlsx`. Aktualizacja tej warstwy nie przelicza trasy.

Program nie odczytuje katalogu Google Drive, nie wyszukuje plików po nazwie i nie wymaga żadnego wzorca nazewnictwa. Każdy aktywny wiersz zawiera gotowy publiczny URL. `Film_ID` służy wyłącznie do przypisania wpisu do portu albo punktu trasy przez część przed końcowym `_numer`, np. `Katania_1`, `Horn1_1` lub `Horn2_1`.

Nazwa `Porty.Port` nie musi być unikalna. Media są przypisane do nazwy lokalizacji, a nie do konkretnej wizyty. Jeśli `Barcelona` występuje w `Porty` dwa razy, przy obu wizytach dostępne są wszystkie aktywne `Barcelona_1`, `Barcelona_2` itd. Końcowy numer jest wyłącznie lokalną kolejnością mediów dla nazwy.

Opcjonalna historyczna kolumna `Kolejnosc_wizyty` nie jest już używana funkcjonalnie. Może pozostać w istniejącym `media.xlsx`, ale jej wartość jest ignorowana. Przenumerowanie `Porty.Kolejnosc` nie wymaga zmiany mediów. Reguła po nazwie działa identycznie dla zwykłych portów, `Punkt_trasy` i `Punkt_trasy_ukryty`.

`Dzien_od_portu` jest czasem w dniach, nie procentem długości. `0.25` oznacza 6 godzin, a `0.7` oznacza 0,7 dnia. Wartość pusta lub `0` umieszcza medium dokładnie w bazowym porcie/punkcie. Wartość dodatnia oznacza odpowiednią liczbę dni po jego osiągnięciu.

Dla punktu trasy na logicznym etapie port–port program najpierw wyznacza czas jego osiągnięcia przy stałym średnim tempie na całej połączonej geometrii: `czas_punktu = T * L1/L`. Następnie oblicza `czas_medium = czas_punktu + Dzien_od_portu` i z tego czasu wyznacza pozycję na całej geometrii. Dodanie punktów technicznych nie zmienia znaczenia mediów liczonych od portu początkowego.

W Leaflet kliknięcie znacznika otwiera dymek z nazwą bazy i opisowymi linkami. Medium z `0` pozostaje w popupie zwykłego portu albo widocznego punktu trasy. Ukryty punkt nie otrzymuje technicznego znacznika, dlatego jego medium jest pokazane znacznikiem `Na morzu`. Każde medium z wartością dodatnią także używa znacznika `Na morzu`. MP4, MOV i zdjęcia otwierają się jak zwykłe linki w nowej karcie.
