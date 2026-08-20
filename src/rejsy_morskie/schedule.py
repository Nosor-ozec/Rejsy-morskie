from __future__ import annotations

import re
from datetime import date, datetime, timedelta

from .models import Leg, PortCall, Voyage

OFFSET_TOKEN = re.compile(r"^\+?(\d+)$")


def parse_excel_date(value: object) -> date:
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    if isinstance(value, str):
        return date.fromisoformat(value.strip())
    raise ValueError(f"Niepoprawna data: {value!r}")


def _parse_offset(value: object) -> int | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, int):
        return value
    if isinstance(value, float):
        if not value.is_integer():
            raise ValueError("Liczba w Kiedy musi być całkowita")
        return int(value)
    if isinstance(value, str):
        match = OFFSET_TOKEN.fullmatch(value.strip())
        if match:
            return int(match.group(1))
    return None


def resolve_when(value: object, start_date: date) -> tuple[int, date]:
    """Zwróć numer dnia rejsu (od 1) oraz datę wpływu.

    Liczba N w wejściu oznacza N dni po dacie startu. Dzień startu ma
    w wynikach numer 1, więc przesunięcie 0 daje dzień 1.
    """
    offset = _parse_offset(value)
    if offset is not None:
        if offset < 0:
            raise ValueError("Przesunięcie w Kiedy musi być >= 0")
        return offset + 1, start_date + timedelta(days=offset)

    arrival_date = parse_excel_date(value)
    offset = (arrival_date - start_date).days
    if offset < 0:
        raise ValueError("Data wpływu nie może być wcześniejsza niż Data_startu")
    return offset + 1, arrival_date


def calculate_schedule(voyage: Voyage, calls: list[PortCall]) -> list[Leg]:
    ordered = sorted(calls, key=lambda call: call.order)
    if [call.order for call in ordered] != list(range(1, len(ordered) + 1)):
        raise ValueError("Kolejnosc musi być unikalna i ciągła od 1")

    for call in ordered:
        if call.stay_days < 0:
            raise ValueError(f"Ujemny Postoj_dni dla portu {call.port}")
        call.arrival_day, call.arrival_date = resolve_when(call.when, voyage.start_date)

    legs: list[Leg] = []
    for number, (start, end) in enumerate(zip(ordered, ordered[1:]), start=1):
        assert start.arrival_day is not None and start.arrival_date is not None
        assert end.arrival_day is not None and end.arrival_date is not None
        day_from = start.arrival_day + start.stay_days
        if end.arrival_day < day_from:
            earliest = voyage.start_date + timedelta(days=day_from - 1)
            raise ValueError(
                f"Niespójny harmonogram przy porcie {end.port}: "
                f"wpływ {end.arrival_date.isoformat()}, najwcześniej {earliest.isoformat()} "
                f"po postoju w {start.port}"
            )
        legs.append(
            Leg(
                voyage_id=voyage.voyage_id,
                number=number,
                start_port=start.port,
                end_port=end.port,
                day_from=day_from,
                day_to=end.arrival_day,
                date_from=voyage.start_date + timedelta(days=day_from - 1),
                date_to=end.arrival_date,
            )
        )
    return legs

