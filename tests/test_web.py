import json
import unittest
from pathlib import Path
from uuid import uuid4

from openpyxl import Workbook

from rejsy_morskie.web import build_local_site, publish_site


class WebTests(unittest.TestCase):
    def test_local_site_and_publication_use_the_same_files(self) -> None:
        root = Path(__file__).parent / "_work" / uuid4().hex
        root.mkdir(parents=True)
        rejsy_path = root / "rejsy.xlsx"
        media_path = root / "media.xlsx"
        outputs = root / "outputs"
        assets = root / "assets"
        site = root / "site"
        docs = root / "docs"
        self._make_rejsy(rejsy_path)
        self._make_media(media_path)
        self._make_geojson(outputs)
        self._make_assets(assets)

        build_local_site(rejsy_path, media_path, outputs, site, assets)
        route = json.loads((site / "data" / "route.json").read_text(encoding="utf-8"))
        media = json.loads((site / "data" / "media.json").read_text(encoding="utf-8"))

        self.assertEqual(route["ports"][0]["name"], "A")
        self.assertEqual(route["legs"][0]["coordinates"], [[0.0, 0.0], [1.0, 0.0], [3.0, 0.0]])
        self.assertEqual(len(media["media"]), 2)
        self.assertFalse(media["media"][0]["atSea"])
        self.assertTrue(media["media"][1]["atSea"])
        self.assertAlmostEqual(media["media"][1]["position"][0], 1.5, places=2)
        self.assertEqual(media["media"][1]["description"], "Opis na morzu")

        docs.mkdir()
        (docs / "README.md").write_text("zachowaj", encoding="utf-8")
        publish_site(site, docs)
        self.assertEqual((docs / "README.md").read_text(encoding="utf-8"), "zachowaj")
        for relative in ("index.html", "app.js", "style.css", "data/route.json", "data/media.json"):
            self.assertEqual((site / relative).read_bytes(), (docs / relative).read_bytes())

    @staticmethod
    def _make_rejsy(path: Path) -> None:
        workbook = Workbook()
        rejsy = workbook.active
        rejsy.title = "Rejsy"
        rejsy.append(["Rejs_ID", "Nazwa_rejsu", "Data_startu", "Kolor_trasy", "CA", "Uwagi"])
        rejsy.append(["R1", "Test", "2024-01-01", "Niebieski", 4, None])
        porty = workbook.create_sheet("Porty")
        porty.append(["Rejs_ID", "Kolejnosc", "Port", "Kraj", "Kiedy", "Postoj_dni", "Lat", "Lon", "Uwagi"])
        porty.append(["R1", 1, "A", None, 0, 0, 0, 0, None])
        porty.append([None, 2, "B", None, 3, 0, 3, 0, None])
        etapy = workbook.create_sheet("Etapy")
        etapy.append(["Rejs_ID", "Etap_nr", "Port_start", "Port_koniec", "Nazwa_etapu", "Dzien_od", "Dzien_do", "Data_od", "Data_do", "Zakres_dni", "Zakres_dat", "Dystans_nm", "GeoJSON_path", "Status", "Uwagi"])
        etapy.append(["R1", 1, "A", "B", "A → B", 1, 3, "2024-01-01", "2024-01-03", "Dni 1–3", "2024-01-01 – 2024-01-03", 180, str(Path("R1") / "geojson" / "01-A-B.geojson"), "gotowy", None])
        workbook.save(path)

    @staticmethod
    def _make_media(path: Path) -> None:
        workbook = Workbook()
        sheet = workbook.active
        sheet.title = "Filmy"
        sheet.append(["Film_ID", "Typ", "Powiazanie", "Dzien_od_portu", "Opis", "URL_Google_Drive", "Aktywny"])
        sheet.append(["A_1", None, None, 0, "Opis portu", "https://example.com/port", "TAK"])
        sheet.append(["A_2", None, None, 1.5, "Opis na morzu", "https://example.com/morze", "TAK"])
        sheet.append(["B_1", None, None, 0, "Nieaktywne", "https://example.com/off", "NIE"])
        workbook.save(path)

    @staticmethod
    def _make_geojson(outputs: Path) -> None:
        path = outputs / "R1" / "geojson" / "01-A-B.geojson"
        path.parent.mkdir(parents=True)
        path.write_text(json.dumps({"type": "Feature", "geometry": {"type": "LineString", "coordinates": [[0, 0], [0, 1], [0, 3]]}, "properties": {}}), encoding="utf-8")

    @staticmethod
    def _make_assets(assets: Path) -> None:
        assets.mkdir()
        for name in ("index.html", "app.js", "style.css"):
            (assets / name).write_text(name, encoding="utf-8")
        vendor = assets / "vendor"
        vendor.mkdir()
        (vendor / "leaflet.js").write_text("leaflet", encoding="utf-8")


if __name__ == "__main__":
    unittest.main()
