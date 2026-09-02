import unittest
from datetime import date

from rejsy_morskie.models import PortCall, Voyage
from rejsy_morskie.schedule import calculate_schedule, parse_when, resolve_when


class ScheduleTests(unittest.TestCase):
    def test_unsigned_number_is_offset_from_start(self) -> None:
        self.assertEqual(resolve_when("4", date(2024, 12, 7)), (5, date(2024, 12, 11)))

    def test_zero_is_start_date_even_with_previous_row_context(self) -> None:
        self.assertEqual(
            resolve_when("0", date(2024, 12, 7), date(2025, 1, 9), 0),
            (1, date(2024, 12, 7)),
        )

    def test_zero_and_plus_zero_are_distinct_tokens(self) -> None:
        self.assertEqual(parse_when("0"), ("start_offset", 0))
        self.assertEqual(parse_when("+0"), ("previous_offset", 0))
        self.assertNotEqual(parse_when("0"), parse_when("+0"))

    def test_absolute_date(self) -> None:
        self.assertEqual(
            resolve_when("2024-12-10", date(2024, 12, 7)),
            (4, date(2024, 12, 10)),
        )

    def test_plus_one_after_zero_day_stay(self) -> None:
        self.assertEqual(
            resolve_when("+1", date(2024, 12, 7), date(2024, 12, 10), 0),
            (5, date(2024, 12, 11)),
        )

    def test_plus_one_after_one_day_stay(self) -> None:
        self.assertEqual(
            resolve_when("+1", date(2024, 12, 7), date(2024, 12, 10), 1),
            (5, date(2024, 12, 11)),
        )

    def test_plus_one_after_two_day_stay(self) -> None:
        self.assertEqual(
            resolve_when("+1", date(2024, 12, 7), date(2024, 12, 10), 2),
            (6, date(2024, 12, 12)),
        )

    def test_plus_two_after_one_day_stay(self) -> None:
        self.assertEqual(
            resolve_when("+2", date(2024, 12, 7), date(2024, 12, 10), 1),
            (6, date(2024, 12, 12)),
        )

    def test_chain_of_plus_offsets_with_different_stays(self) -> None:
        calls = self._calls(["0", "+1", "+2", "+1", "+2"])
        stays = [0, 1, 2, 3, 0]
        for call, stay in zip(calls, stays):
            call.stay_days = stay
        calculate_schedule(self._voyage(), calls)
        self.assertEqual(
            [call.arrival_date for call in calls],
            [
                date(2024, 12, 7), date(2024, 12, 8),
                date(2024, 12, 10), date(2024, 12, 12),
                date(2024, 12, 16),
            ],
        )

    def test_reference_ports_have_expected_arrival_days_and_leg_ranges(self) -> None:
        definitions = [
            ("Triest", "2024-12-07", 0),
            ("Dubrownik", "+1", 1),
            ("Katania", "2024-12-10", 1),
            ("Civitavecchia", "+1", 1),
            ("Savona", "+1", 1),
        ]
        calls = [
            PortCall("R1", index, port, None, when, stay_days=stay)
            for index, (port, when, stay) in enumerate(definitions, start=1)
        ]

        legs = calculate_schedule(self._voyage(), calls)

        self.assertEqual([call.arrival_day for call in calls], [1, 2, 4, 5, 6])
        self.assertEqual(
            [(leg.day_from, leg.day_to) for leg in legs],
            [(1, 2), (3, 4), (5, 5), (6, 6)],
        )
        self.assertEqual(
            [leg.day_range for leg in legs],
            ["Dni 1–2", "Dni 3–4", "Dni 5–5", "Dni 6–6"],
        )

    def test_absolute_date_anchor_after_plus_offset_may_include_travel_time(self) -> None:
        calls = self._calls(["0", "+1", "2024-12-10"])
        calls[0].stay_days = 0
        calls[1].stay_days = 1
        calculate_schedule(self._voyage(), calls)
        self.assertEqual(calls[2].arrival_date, date(2024, 12, 10))

    def test_absolute_date_anchor_cannot_overlap_previous_stay(self) -> None:
        calls = self._calls(["0", "+1", "2024-12-08"])
        calls[0].stay_days = 0
        calls[1].stay_days = 1
        with self.assertRaisesRegex(
            ValueError, "wpływ 2024-12-08, najwcześniej 2024-12-09"
        ):
            calculate_schedule(self._voyage(), calls)

    def test_unsigned_number_is_independent_anchor(self) -> None:
        calls = self._calls(["0", "+1", "5"])
        calls[0].stay_days = 0
        calls[1].stay_days = 1
        calculate_schedule(self._voyage(), calls)
        self.assertEqual(calls[2].arrival_date, date(2024, 12, 12))

    def test_unsigned_number_anchor_cannot_overlap_previous_stay(self) -> None:
        calls = self._calls(["0", "+1", "1"])
        calls[0].stay_days = 0
        calls[1].stay_days = 1
        with self.assertRaisesRegex(
            ValueError, "wpływ 2024-12-08, najwcześniej 2024-12-09"
        ):
            calculate_schedule(self._voyage(), calls)

    def test_plus_offset_for_first_port_is_error(self) -> None:
        with self.assertRaisesRegex(ValueError, "pierwszego portu"):
            calculate_schedule(self._voyage(), self._calls(["+1", "+2"]))

    def test_plus_zero_keeps_same_day_after_one_day_stay(self) -> None:
        calls = self._calls(["0", "+0"])
        calls[0].stay_days = 1
        calculate_schedule(self._voyage(), calls)
        self.assertEqual(calls[1].arrival_date, calls[0].arrival_date)

    def test_plus_zero_keeps_previous_date_without_stay_offset(self) -> None:
        self.assertEqual(
            resolve_when("+0", date(2024, 12, 7), date(2024, 12, 20), 0),
            (14, date(2024, 12, 20)),
        )

    def test_route_points_participate_in_chronology_but_form_one_leg(self) -> None:
        calls = [
            PortCall("R1", 1, "Ushuaia", None, "0", stay_days=0),
            PortCall(
                "R1", 2, "Horn1", None, "+0", stay_days=0,
                lat=-55.5, lon=-67.0, call_type="Punkt_trasy",
            ),
            PortCall(
                "R1", 3, "Horn2", None, "+0", stay_days=0,
                lat=-56.0, lon=-68.0, call_type="Punkt_trasy_ukryty",
            ),
            PortCall("R1", 4, "Puerto Montt", None, "5", stay_days=1),
        ]

        legs = calculate_schedule(self._voyage(), calls)

        self.assertEqual([call.arrival_day for call in calls], [1, 1, 1, 6])
        self.assertEqual([call.when for call in calls], ["0", "+0", "+0", "5"])
        self.assertEqual(len(legs), 1)
        self.assertEqual(legs[0].name, "Ushuaia → Puerto Montt")
        self.assertEqual([point.port for point in legs[0].route_points], ["Horn1", "Horn2"])

    def test_calculation_does_not_modify_when_or_stay_days(self) -> None:
        calls = self._calls(["0", "+1", "+2", "2024-12-14"])
        stays = [2, 2, 2, 3]
        for call, stay in zip(calls, stays):
            call.stay_days = stay
        when_before = [call.when for call in calls]
        stays_before = [call.stay_days for call in calls]

        calculate_schedule(self._voyage(), calls)

        self.assertEqual([call.when for call in calls], when_before)
        self.assertEqual([call.stay_days for call in calls], stays_before)

    def test_required_text_forms_are_recognized(self) -> None:
        expected = {
            "2024-12-10": ("date", date(2024, 12, 10)),
            "0": ("start_offset", 0),
            "10": ("start_offset", 10),
            "+1": ("previous_offset", 1),
            "+12": ("previous_offset", 12),
        }
        for value, parsed in expected.items():
            with self.subTest(value=value):
                self.assertEqual(parse_when(value), parsed)

    def test_non_specification_text_is_rejected(self) -> None:
        invalid_values = (
            "10.12.2024", "12/10/2024", "2024/12/10", "2024-12-10 00:00",
            "2024-2-10", " 10", "10 ", "-1", "+1.5", "+-1", "1.0", "",
        )
        for value in invalid_values:
            with self.subTest(value=value), self.assertRaisesRegex(
                ValueError, "RRRR-MM-DD, N albo \\+N"
            ):
                parse_when(value)

    def test_invalid_calendar_date_is_rejected(self) -> None:
        with self.assertRaisesRegex(ValueError, "Niepoprawna data"):
            parse_when("2024-02-30")

    def test_legacy_excel_date_serial_remains_readable(self) -> None:
        self.assertEqual(parse_when(45633), ("date", date(2024, 12, 7)))

    @staticmethod
    def _voyage() -> Voyage:
        return Voyage("R1", "Test", date(2024, 12, 7))

    @staticmethod
    def _calls(values) -> list[PortCall]:
        return [
            PortCall("R1", index, f"P{index}", None, value, stay_days=0)
            for index, value in enumerate(values, start=1)
        ]


if __name__ == "__main__":
    unittest.main()
