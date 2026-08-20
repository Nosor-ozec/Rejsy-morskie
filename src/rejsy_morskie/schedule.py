from __future__ import annotations

import re
from datetime import date, datetime, timedelta

from .models import Leg, PortCall, Voyage

DAY_TOKEN = re.compile(r"^\+(\d+)$")


def parse_excel_date(value: object) -> date:
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    if isinstance(value, str):
        return date.fromisoformat(value.strip())
    raise ValueError(f"Niepoprawna data: {value!r}")


def resolve_when(value: object, start_date: date) -> tuple[int, date]:
    if isinstance(value, str):
        match = DAY_TOKEN.fullmatch(value.strip())
        if match:
            day = int(match.group(1))
            if day < 1:
                raise ValueError("Numer dnia w Kiedy musi być >= 1")
            return day, start_date + timedelta(days=day - 1)

    arrival_date = parse_excel_date(value)
    day = (arrival_date - start_date).days + 1
    if day < 1:
        raise ValueError("Data wpływu nie może być wcześniejsza niż Data_startu")
    return day, arrival_date


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
            raise ValueError(
                f"Port {end.port} przypada przed możliwym wyjściem z {start.port}"
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
