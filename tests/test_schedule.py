from datetime import date

import pytest

from rejsy_morskie.models import PortCall, Voyage
from rejsy_morskie.schedule import calculate_schedule, resolve_when


def test_plus_day_is_counted_from_one() -> None:
    assert resolve_when("+4", date(2026, 5, 10)) == (4, date(2026, 5, 13))


def test_hard_date_is_converted_to_day() -> None:
    assert resolve_when("2026-05-14", date(2026, 5, 10)) == (
        5, date(2026, 5, 14)
    )


def test_stay_moves_start_of_leg() -> None:
    voyage = Voyage("R1", "Test", date(2026, 5, 10))
    calls = [
        PortCall("R1", 1, "Start", None, "+1", stay_days=0),
        PortCall("R1", 2, "Dubrovnik", "Chorwacja", "+2", stay_days=1),
        PortCall("R1", 3, "Catania", "Włochy", "+4", stay_days=1),
    ]
    legs = calculate_schedule(voyage, calls)
    assert (legs[1].day_from, legs[1].day_to) == (3, 4)


def test_rejects_impossible_timing() -> None:
    voyage = Voyage("R1", "Test", date(2026, 5, 10))
    calls = [
        PortCall("R1", 1, "A", None, "+1", stay_days=2),
        PortCall("R1", 2, "B", None, "+2", stay_days=1),
    ]
    with pytest.raises(ValueError, match="przed możliwym wyjściem"):
        calculate_schedule(voyage, calls)
