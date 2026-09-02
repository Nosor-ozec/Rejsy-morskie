from __future__ import annotations

import re
from datetime import date, datetime, timedelta

from .models import Leg, PortCall, Voyage

DATE_TOKEN = re.compile(r"^(\d{4}-\d{2}-\d{2})$")
START_OFFSET_TOKEN = re.compile(r"^(\d+)$")
PREVIOUS_OFFSET_TOKEN = re.compile(r"^\+(\d+)$")
WHEN_FORMAT_ERROR = (
    "Kiedy musi mieć jedną z form tekstowych: RRRR-MM-DD, N albo +N "
    "(N jest liczbą całkowitą >= 0)"
)
EXCEL_DATE_EPOCH = date(1899, 12, 30)
LEGACY_EXCEL_DATE_SERIAL_MIN = 10_000


def parse_excel_date(value: object) -> date:
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    if isinstance(value, str):
        return date.fromisoformat(value.strip())
    raise ValueError(f"Niepoprawna data: {value!r}")


def _parse_numeric_offset(value: object) -> int | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, int):
        return value
    if isinstance(value, float):
        if not value.is_integer():
            raise ValueError("Liczba w Kiedy musi być całkowita")
        return int(value)
    return None


def _stay_schedule_offset(stay_days: int) -> int:
    """Zwróć liczbę dodatkowych dni harmonogramu wynikających z postoju."""

    return max(stay_days - 1, 0)


def parse_when(value: object) -> tuple[str, date | int]:
    """Rozróżnij datę, kotwicę od startu i przesunięcie od poprzedniego portu."""

    if isinstance(value, str):
        date_match = DATE_TOKEN.fullmatch(value)
        if date_match:
            try:
                return "date", date.fromisoformat(date_match.group(1))
            except ValueError as error:
                raise ValueError(
                    f"Niepoprawna data w Kiedy: {value!r}; dozwolony format to RRRR-MM-DD"
                ) from error

        start_match = START_OFFSET_TOKEN.fullmatch(value)
        if start_match:
            return "start_offset", int(start_match.group(1))

        previous_match = PREVIOUS_OFFSET_TOKEN.fullmatch(value)
        if previous_match:
            return "previous_offset", int(previous_match.group(1))

        raise ValueError(WHEN_FORMAT_ERROR)

    # Zgodność z istniejącymi skoroszytami, w których Excel zdążył już zapisać
    # wcześniejsze wartości jako natywną liczbę lub datę. Zapis wyników nigdy
    # nie zmienia tych komórek; wszystkie nowe wpisy mają być tekstem.
    numeric_offset = _parse_numeric_offset(value)
    if numeric_offset is not None:
        if numeric_offset < 0:
            raise ValueError(WHEN_FORMAT_ERROR)
        if numeric_offset >= LEGACY_EXCEL_DATE_SERIAL_MIN:
            return "date", EXCEL_DATE_EPOCH + timedelta(days=numeric_offset)
        return "start_offset", numeric_offset

    if isinstance(value, datetime):
        return "date", value.date()
    if isinstance(value, date):
        return "date", value
    raise ValueError(WHEN_FORMAT_ERROR)


def resolve_when(
    value: object,
    start_date: date,
    previous_arrival_date: date | None = None,
    previous_stay_days: int = 0,
) -> tuple[int, date]:
    """Zwróć numer dnia rejsu (od 1) oraz datę wpływu.

    Tekst N oznacza N dni po dacie startu. Tekst +N oznacza N dni podróży
    od poprzedniego portu oraz dodatkowe dni postoju ponad dzień wpływu:
    N + max(Postoj_dni - 1, 0). Dzień startu ma numer 1.
    """
    kind, parsed_value = parse_when(value)
    if kind == "start_offset":
        assert isinstance(parsed_value, int)
        arrival_date = start_date + timedelta(days=parsed_value)
    elif kind == "previous_offset":
        assert isinstance(parsed_value, int)
        if previous_arrival_date is None:
            raise ValueError("+N w Kiedy nie może wystąpić dla pierwszego portu")
        arrival_date = previous_arrival_date + timedelta(
            days=parsed_value + _stay_schedule_offset(previous_stay_days)
        )
    else:
        assert isinstance(parsed_value, date)
        arrival_date = parsed_value

    offset = (arrival_date - start_date).days
    if offset < 0:
        raise ValueError("Data wpływu nie może być wcześniejsza niż Data_startu")
    return offset + 1, arrival_date


def calculate_schedule(voyage: Voyage, calls: list[PortCall]) -> list[Leg]:
    ordered = sorted(calls, key=lambda call: call.order)
    if [call.order for call in ordered] != list(range(1, len(ordered) + 1)):
        raise ValueError("Kolejnosc musi być unikalna i ciągła od 1")

    for index, call in enumerate(ordered):
        if call.stay_days < 0:
            raise ValueError(f"Ujemny Postoj_dni dla portu {call.port}")
        previous = ordered[index - 1] if index else None
        previous_arrival = previous.arrival_date if previous else None
        kind, _ = parse_when(call.when)
        call.arrival_day, call.arrival_date = resolve_when(
            call.when,
            voyage.start_date,
            previous_arrival,
            previous.stay_days if previous else 0,
        )
        if previous is not None and kind != "previous_offset":
            assert previous.arrival_date is not None
            earliest = previous.arrival_date + timedelta(days=previous.stay_days)
            if call.arrival_date < earliest:
                raise ValueError(
                    f"Niespójny harmonogram przy porcie {call.port}: "
                    f"wpływ {call.arrival_date.isoformat()}, najwcześniej "
                    f"{earliest.isoformat()} po postoju w {previous.port}"
                )

    real_ports = [call for call in ordered if call.is_real_port]
    if len(real_ports) < 2:
        raise ValueError("Rejs musi zawierać co najmniej dwa zwykłe porty")
    if ordered[0].is_route_point or ordered[-1].is_route_point:
        raise ValueError("Punkty trasy muszą znajdować się pomiędzy zwykłymi portami")

    legs: list[Leg] = []
    for number, (start, end) in enumerate(zip(real_ports, real_ports[1:]), start=1):
        assert start.arrival_day is not None and start.arrival_date is not None
        assert end.arrival_day is not None and end.arrival_date is not None
        day_from = start.arrival_day + start.stay_days
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
                route_points=[
                    call
                    for call in ordered
                    if start.order < call.order < end.order and call.is_route_point
                ],
            )
        )
    return legs

