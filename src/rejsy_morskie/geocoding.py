from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Protocol


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
    pass


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
            raise AmbiguousPortError(
                f"{port}, {country or ''}: znaleziono {len(candidates)} kandydatów"
            )
        result = candidates[0]
        self.cache[key] = asdict(result)
        self.cache_path.parent.mkdir(parents=True, exist_ok=True)
        self.cache_path.write_text(
            json.dumps(self.cache, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        return result
