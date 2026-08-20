import unittest
from datetime import date

from rejsy_morskie.models import PortCall, Voyage
from rejsy_morskie.schedule import calculate_schedule, resolve_when


class ScheduleTests(unittest.TestCase):
    def test_number_is_offset_from_start(self) -> None:
        self.assertEqual(resolve_when(4, date(2024, 12, 7)), (5, date(2024, 12, 11)))
        self.assertEqual(resolve_when("+4", date(2024, 12, 7)), (5, date(2024, 12, 11)))

    def test_hard_date_is_checkpoint(self) -> None:
        self.assertEqual(
            resolve_when("2024-12-10", date(2024, 12, 7)),
            (4, date(2024, 12, 10)),
        )

    def test_mixed_offsets_and_dates_are_consistent(self) -> None:
        voyage = Voyage("Rejs 3", "Test", date(2024, 12, 7))
        calls = [
            PortCall("Rejs 3", 1, "Triest", None, date(2024, 12, 7), stay_days=0),
            PortCall("Rejs 3", 2, "Dubrownik", None, 1, stay_days=1),
            PortCall("Rejs 3", 3, "Catania", None, date(2024, 12, 10), stay_days=1),
            PortCall("Rejs 3", 4, "Civitavecchia", None, 4, stay_days=1),
        ]
        legs = calculate_schedule(voyage, calls)
        self.assertEqual((legs[1].day_from, legs[1].day_to), (3, 4))
        self.assertEqual(legs[2].date_to, date(2024, 12, 11))

    def test_inconsistent_checkpoint_is_reported(self) -> None:
        voyage = Voyage("R1", "Test", date(2024, 12, 7))
        calls = [
            PortCall("R1", 1, "A", None, date(2024, 12, 10), stay_days=1),
            PortCall("R1", 2, "B", None, 2, stay_days=1),
        ]
        with self.assertRaisesRegex(ValueError, "Niespójny harmonogram"):
            calculate_schedule(voyage, calls)


if __name__ == "__main__":
    unittest.main()
