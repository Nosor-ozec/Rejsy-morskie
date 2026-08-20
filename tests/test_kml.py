import unittest

from rejsy_morskie.kml import kml_color


class KmlTests(unittest.TestCase):
    def test_named_polish_color(self) -> None:
        self.assertEqual(kml_color("Niebieski"), "ffB85700")

    def test_hex_color(self) -> None:
        self.assertEqual(kml_color("#112233"), "ff332211")

    def test_invalid_color(self) -> None:
        with self.assertRaisesRegex(ValueError, "format"):
            kml_color("nieznany")


if __name__ == "__main__":
    unittest.main()

