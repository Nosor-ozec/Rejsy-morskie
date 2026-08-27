# Media na mapie

Media są oddzielną warstwą danych z `routes/media.xlsx`. Aktualizacja tej warstwy nie przelicza trasy.

Program nie odczytuje katalogu Google Drive, nie wyszukuje plików po nazwie i nie wymaga żadnego wzorca nazewnictwa. Każdy aktywny wiersz zawiera gotowy publiczny URL. `Film_ID` służy wyłącznie do przypisania wpisu do portu przez część przed końcowym `_numer`.

Wartość pusta lub `0` w `Dzien_od_portu` przypina medium do portu. Wartość dodatnia umieszcza punkt proporcjonalnie wzdłuż GeoJSON etapu do następnego portu. Liczby dziesiętne są obsługiwane; wartości przekraczające czas etapu są odrzucane.

W Leaflet kliknięcie znacznika otwiera dymek z nazwą portu i opisowymi linkami. Nie jest używane słowo „Filmy”, a nazwa portu nie jest powtarzana przy każdym linku. MP4, MOV i zdjęcia otwierają się jak zwykłe linki w nowej karcie.
