import unittest

from rejsy_morskie.sea_router import HttpSeaRouter


class SeaRouterTests(unittest.TestCase):
    def test_http_adapter_selects_final_path_and_converts_distance(self) -> None:
        requested = {}

        def fetch(url, timeout):
            requested.update(url=url, timeout=timeout)
            return {
                "type": "FeatureCollection",
                "features": [
                    {
                        "type": "Feature",
                        "geometry": {
                            "type": "LineString",
                            "coordinates": [[18.09, 42.64], [15.09, 37.50]],
                        },
                        "properties": {"name": "raw", "distanceKm": 1852},
                    },
                    {
                        "type": "Feature",
                        "geometry": {
                            "type": "LineString",
                            "coordinates": [[0, 0], [1, 0], [2, 0]],
                        },
                        "properties": {"name": "final"},
                    },
                ],
            }

        router = HttpSeaRouter(fetch_json=fetch)
        result = router.route(42.64, 18.09, 37.50, 15.09, penalty=8)

        self.assertEqual(len(result.geometry["coordinates"]), 3)
        self.assertAlmostEqual(result.distance_nm, 120.1, places=1)
        self.assertIn("from=18.09%2C42.64", requested["url"])
        self.assertIn("penalty=8", requested["url"])


if __name__ == "__main__":
    unittest.main()
