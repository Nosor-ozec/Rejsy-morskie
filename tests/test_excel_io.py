import unittest
from rejsy_morskie.excel_io import _inherit_voyage_id


class ExcelIoTests(unittest.TestCase):
    def test_blank_voyage_id_inherits_previous_row(self) -> None:
        self.assertEqual(_inherit_voyage_id(None, "R1", 3), "R1")
        self.assertEqual(_inherit_voyage_id("", "R1", 4), "R1")
        self.assertEqual(_inherit_voyage_id("R2", "R1", 5), "R2")

    def test_first_port_requires_voyage_id(self) -> None:
        with self.assertRaisesRegex(ValueError, "pierwszy Rejs_ID nie może być pusty"):
            _inherit_voyage_id(None, None, 2)


if __name__ == "__main__":
    unittest.main()
