from __future__ import annotations

import json
import time
import urllib.parse
import urllib.request
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Callable, Protocol


@dataclass(slots=True)
class GeocodingCandidate:
    label: str
    lat: float
    lon: float
    source: str
    fetched_at: str = ""

    def __post_init__(self) -> None:
        if not self.fetched_at:
            self.fetched_at = datetime.now(UTC).isoformat()


class Geocoder(Protocol):
    def search(self, port: str, country: str | None) -> list[GeocodingCandidate]: ...


class AmbiguousPortError(ValueError):
    def __init__(
        self,
        port: str,
        country: str | None,
        candidates: list[GeocodingCandidate],
    ) -> None:
        self.port = port
        self.country = country
        self.candidates = candidates
        if candidates:
            details = "\n".join(
                f"  {number}. {item.label} ({item.lat:.6f}, {item.lon:.6f})"
                for number, item in enumerate(candidates, start=1)
            )
            message = (
                f"Port {port}, {country or 'bez kraju'} jest niejednoznaczny. "
                f"Znaleziono {len(candidates)} kandydatów:\n{details}\n"
                "Uzupełnij Kraj albo wpisz zatwierdzone Lat/Lon w arkuszu Porty."
            )
        else:
            message = (
                f"Nie znaleziono portu {port}, {country or 'bez kraju'}. "
                "Uzupełnij Kraj lub wpisz Lat/Lon w arkuszu Porty."
            )
        super().__init__(message)


class NominatimGeocoder:
    """Mały klient publicznego API Nominatim z wymaganym limitem zapytań."""

    def __init__(
        self,
        *,
        base_url: str = "https://nominatim.openstreetmap.org",
        user_agent: str = (
            "Rejsy-morskie/0.1 "
            "(https://github.com/Nosor-ozec/Rejsy-morskie)"
        ),
        min_interval_seconds: float = 1.0,
        timeout_seconds: float = 20.0,
        fetch_json: Callable[[str, dict[str, str], float], object] | None = None,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.user_agent = user_agent
        self.min_interval_seconds = min_interval_seconds
        self.timeout_seconds = timeout_seconds
        self.fetch_json = fetch_json or _fetch_json
        self._last_request_at = 0.0

    def search(self, port: str, country: str | None) -> list[GeocodingCandidate]:
        elapsed = time.monotonic() - self._last_request_at
        if elapsed < self.min_interval_seconds:
            time.sleep(self.min_interval_seconds - elapsed)

        query = ", ".join(part for part in (port.strip(), (country or "").strip()) if part)
        params = urllib.parse.urlencode(
            {
                "q": query,
                "format": "jsonv2",
                "limit": 5,
                "addressdetails": 1,
                "accept-language": "pl,en",
                "featureType": "city",
            }
        )
        url = f"{self.base_url}/search?{params}"
        headers = {"User-Agent": self.user_agent, "Accept": "application/json"}
        try:
            payload = self.fetch_json(url, headers, self.timeout_seconds)
        finally:
            self._last_request_at = time.monotonic()

        if not isinstance(payload, list):
            raise RuntimeError("Geokoder zwrócił niepoprawną odpowiedź")

        candidates: list[GeocodingCandidate] = []
        seen_places: list[tuple[str, str, float, float]] = []
        for item in payload:
            if not isinstance(item, dict):
                continue
            try:
                label = str(item["display_name"])
                lat = float(item["lat"])
                lon = float(item["lon"])
                address = item.get("address")
                country_code = (
                    str(address.get("country_code", "")).casefold()
                    if isinstance(address, dict)
                    else ""
                )
                short_name = label.split(",", 1)[0].strip().casefold()
                duplicate = any(
                    short_name == previous_name
                    and country_code == previous_country
                    and abs(lat - previous_lat) <= 0.2
                    and abs(lon - previous_lon) <= 0.3
                    for previous_name, previous_country, previous_lat, previous_lon
                    in seen_places
                )
                if duplicate:
                    continue
                seen_places.append((short_name, country_code, lat, lon))
                candidates.append(
                    GeocodingCandidate(
                        label=label,
                        lat=lat,
                        lon=lon,
                        source="Nominatim / OpenStreetMap",
                    )
                )
            except (KeyError, TypeError, ValueError):
                continue
        return candidates


def _fetch_json(url: str, headers: dict[str, str], timeout: float) -> object:
    request = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return json.load(response)


class CachedGeocoder:
    def __init__(self, provider: Geocoder, cache_path: Path) -> None:
        self.provider = provider
        self.cache_path = cache_path
        self.cache = json.loads(cache_path.read_text("utf-8")) if cache_path.exists() else {}

    @staticmethod
    def _key(port: str, country: str | None) -> str:
        return f"{port.strip().casefold()}|{(country or '').strip().casefold()}"

    def resolve(self, port: str, country: str | None) -> GeocodingCandidate:
        key = self._key(port, country)
        if key in self.cache:
            return GeocodingCandidate(**self.cache[key])

        candidates = self.provider.search(port, country)
        if len(candidates) != 1:
            raise AmbiguousPortError(port, country, candidates)
        result = candidates[0]
        self.cache[key] = asdict(result)
        self.cache_path.parent.mkdir(parents=True, exist_ok=True)
        self.cache_path.write_text(
            json.dumps(self.cache, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        return result

