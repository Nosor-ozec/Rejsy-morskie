import unittest
from contextlib import contextmanager
from pathlib import Path
from uuid import uuid4
from xml.etree import ElementTree

from openpyxl import Workbook, load_workbook
from openpyxl.worksheet.table import Table, TableStyleInfo

from rejsy_morskie.geocoding import CachedGeocoder, GeocodingCandidate
from rejsy_morskie.pipeline import generate_routes
from rejsy_morskie.sea_router import RouteResult


class FakeProvider:
    def search(self, port, country):
        coordinates = {"A": (42.0, 18.0), "B": (40.0, 16.0)}
        lat, lon = coordinates[port]
        return [GeocodingCandidate(port, lat, lon, "test")]


class FakeRouter:
    def __init__(self):
        self.penalties = []

    def route(self, start_lat, start_lon, end_lat, end_lon, *, penalty=None):
        self.penalties.append(penalty)
        return RouteResult(
            geometry={
                "type": "LineString",
                "coordinates": [[start_lon, start_lat], [end_lon, end_lat]],
            },
            distance_nm=123.45,
        )


@contextmanager
def test_directory():
    path = Path(__file__).parent / "_work" / uuid4().hex
    path.mkdir(parents=True)
    yield path


class PipelineTests(unittest.TestCase):
    def test_generate_routes_writes_all_outputs(self) -> None:
        with test_directory() as root:
            input_path = root / "input.xlsx"
            output_dir = root / "outputs"
            self._make_workbook(input_path)
            geocoder = CachedGeocoder(FakeProvider(), root / "cache.json")
            router = FakeRouter()

            outputs = generate_routes(input_path, output_dir, geocoder, router)

            workbook_path = output_dir / "rejs-uzupelniony.xlsx"
            workbook = load_workbook(workbook_path, data_only=True)
            porty = workbook["Porty"]
            etapy = workbook["Etapy"]

            self.assertEqual(porty["G2"].value, 42)
            self.assertEqual(porty["H3"].value, 16)
            self.assertEqual(etapy["N2"].value, "gotowy")
            self.assertEqual(etapy["L2"].value, 123.5)
            self.assertEqual(
                etapy["M2"].value, str(Path("R1") / "geojson" / "01-A-B.geojson")
            )
            self.assertEqual(etapy.tables["EtapyTable"].ref, "A1:O2")
            self.assertTrue((output_dir / "R1" / "trasa.kml").exists())
            self.assertTrue((output_dir / "R1" / "geojson" / "01-A-B.geojson").exists())
            self.assertEqual(outputs[0], workbook_path)
            self.assertEqual(router.penalties, [8.0])

            kml = ElementTree.parse(output_dir / "R1" / "trasa.kml")
            namespace = {"kml": "http://www.opengis.net/kml/2.2"}
            line_coordinates = kml.find(
                ".//kml:Folder[kml:name='Etapy']//kml:LineString/kml:coordinates",
                namespace,
            )
            self.assertIsNotNone(line_coordinates)
            self.assertEqual(line_coordinates.text, "18.0,42.0,0 16.0,40.0,0")

    @staticmethod
    def _make_workbook(path: Path) -> None:
        workbook = Workbook()
        rejsy = workbook.active
        rejsy.title = "Rejsy"
        rejsy.append(
            ["Rejs_ID", "Nazwa_rejsu", "Data_startu", "Kolor_trasy", "CA", "Uwagi"]
        )
        rejsy.append(["R1", "Test", "2024-12-07", "#0057B8", 8, None])

        porty = workbook.create_sheet("Porty")
        porty.append(
            [
                "Rejs_ID", "Kolejnosc", "Port", "Kraj", "Kiedy",
                "Postoj_dni", "Lat", "Lon", "Uwagi",
            ]
        )
        porty.append(["R1", 1, "A", None, 0, 0, None, None, None])
        porty.append([None, 2, "B", None, 1, 1, None, None, None])

        etapy = workbook.create_sheet("Etapy")
        etapy.append(
            [
                "Rejs_ID", "Etap_nr", "Port_start", "Port_koniec", "Nazwa_etapu",
                "Dzien_od", "Dzien_do", "Data_od", "Data_do", "Zakres_dni",
                "Zakres_dat", "Dystans_nm", "GeoJSON_path", "Status", "Uwagi",
            ]
        )
        etapy.append([None] * 15)
        table = Table(displayName="EtapyTable", ref="A1:O2")
        table.tableStyleInfo = TableStyleInfo(name="TableStyleMedium2", showRowStripes=True)
        etapy.add_table(table)
        workbook.save(path)


if __name__ == "__main__":
    unittest.main()
