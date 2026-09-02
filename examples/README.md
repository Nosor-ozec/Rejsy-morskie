# Przykładowy skoroszyt

## Rejsy

| Rejs_ID | Nazwa_rejsu | Data_startu | Kolor_trasy | CA | Uwagi |
|---|---|---|---|---|---|
| MED-2026-01 | Adriatyk i Italia | 2026-05-10 | #0057B8 |  | Przykład |

## Porty

| Rejs_ID | Kolejnosc | Port | Kraj | Kiedy | Postoj_dni | Lat | Lon | Uwagi | Typ |
|---|---:|---|---|---|---:|---:|---:|---|---|
| MED-2026-01 | 1 | Split | Chorwacja | 2026-05-10 | 0 | 43.5081 | 16.4402 | Start | |
|  | 2 | Dubrovnik | Chorwacja | 1 | 1 |  |  | Do geokodowania | |
|  | 3 | Catania | Włochy | 3 | 1 |  |  |  | |
|  | 4 | Civitavecchia | Włochy | 2026-05-14 | 1 |  |  | Kotwica datowa | |

Puste `Rejs_ID` dziedziczy wartość z poprzedniego niepustego wiersza. Liczba w `Kiedy` oznacza liczbę dni po `Data_startu`, więc `1` oznacza 2026-05-11, a `3` oznacza 2026-05-13.

Arkusz `Etapy` może być pusty; program zastąpi jego zawartość. W powyższym przykładzie etap Dubrovnik → Catania ma zakres `Dni 3–4`.

Punkt techniczny wpisuje się w tej samej kolejności, ustawiając `Typ` na `Punkt_trasy` albo `Punkt_trasy_ukryty`, `Postoj_dni` na `0` oraz ręczne `Lat` i `Lon`. Używa on tego samego języka `Kiedy`, np. `+0`, ale nie tworzy osobnego wiersza `Etapy`.

