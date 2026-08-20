import json
import unittest
from contextlib import contextmanager
from pathlib import Path
from uuid import uuid4

from rejsy_morskie.geocoding import (
    AmbiguousPortError,
    CachedGeocoder,
    GeocodingCandidate,
    NominatimGeocoder,
)


class StubProvider:
    def __init__(self, candidates):
        self.candidates = candidates
        self.calls = 0

    def search(self, port, country):
        self.calls += 1
        return self.candidates


@contextmanager
def test_directory():
    path = Path(__file__).parent / "_work" / uuid4().hex
    path.mkdir(parents=True)
    yield path


class GeocodingTests(unittest.TestCase):
    def test_nominatim_parses_candidates(self) -> None:
        requested = {}

        def fetch(url, headers, timeout):
            requested.update(url=url, headers=headers, timeout=timeout)
            return [
                {
                    "display_name": "Dubrovnik, Croatia",
                    "lat": "42.65",
                    "lon": "18.09",
                }
            ]

        provider = NominatimGeocoder(
            min_interval_seconds=0, fetch_json=fetch
        )
        result = provider.search("Dubrownik", "Chorwacja")

        self.assertEqual(len(result), 1)
        self.assertEqual((result[0].lat, result[0].lon), (42.65, 18.09))
        self.assertIn("Dubrownik%2C+Chorwacja", requested["url"])
        self.assertIn("featureType=city", requested["url"])
        self.assertIn("Rejsy-morskie", requested["headers"]["User-Agent"])

    def test_nominatim_collapses_nearby_duplicates_of_same_city(self) -> None:
        def fetch(url, headers, timeout):
            return [
                {
                    "display_name": "Dubrownik, Chorwacja",
                    "lat": "42.6491",
                    "lon": "18.0939",
                    "address": {"country_code": "hr"},
                },
                {
                    "display_name": "Dubrownik, żupania, Chorwacja",
                    "lat": "42.6487",
                    "lon": "18.0947",
                    "address": {"country_code": "hr"},
                },
            ]

        provider = NominatimGeocoder(min_interval_seconds=0, fetch_json=fetch)
        self.assertEqual(len(provider.search("Dubrownik", "Chorwacja")), 1)

    def test_cache_avoids_second_provider_call(self) -> None:
        provider = StubProvider(
            [GeocodingCandidate("Catania, Italy", 37.5, 15.09, "test")]
        )
        with test_directory() as directory:
            path = directory / "cache.json"
            geocoder = CachedGeocoder(provider, path)
            first = geocoder.resolve("Catania", "Włochy")
            second = geocoder.resolve("Catania", "Włochy")
            saved = json.loads(path.read_text("utf-8"))

        self.assertEqual(first, second)
        self.assertEqual(provider.calls, 1)
        self.assertEqual(len(saved), 1)

    def test_ambiguous_error_lists_candidates(self) -> None:
        provider = StubProvider(
            [
                GeocodingCandidate("Port A", 1, 2, "test"),
                GeocodingCandidate("Port B", 3, 4, "test"),
            ]
        )
        with test_directory() as directory:
            geocoder = CachedGeocoder(provider, directory / "cache.json")
            with self.assertRaisesRegex(AmbiguousPortError, "Port A"):
                geocoder.resolve("Test", None)


if __name__ == "__main__":
    unittest.main()

