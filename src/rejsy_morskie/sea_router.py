from __future__ import annotations

import json
import math
import urllib.parse
import urllib.request
from dataclasses import dataclass
from typing import Any, Callable, Protocol


@dataclass(slots=True)
class RouteResult:
    geometry: dict[str, Any]
    distance_nm: float | None = None


class SeaRouter(Protocol):
    def route(
        self,
        start_lat: float,
        start_lon: float,
        end_lat: float,
        end_lon: float,
        *,
        penalty: float | None = None,
    ) -> RouteResult: ...


class NotConfiguredSeaRouter:
    """Jawny placeholder do czasu wyboru lokalnego sea-routera i jego CLI/API."""

    def route(
        self,
        start_lat: float,
        start_lon: float,
        end_lat: float,
        end_lon: float,
        *,
        penalty: float | None = None,
    ) -> RouteResult:
        raise RuntimeError(
            "Sea-router nie jest skonfigurowany. Dodaj adapter lokalnego CLI/API."
        )


class HttpSeaRouter:
    """Adapter do lokalnego serwera `sea-router-rs serve`."""

    def __init__(
        self,
        base_url: str = "http://127.0.0.1:3001",
        *,
        penalty: float = 5.0,
        timeout_seconds: float = 60.0,
        fetch_json: Callable[[str, float], object] | None = None,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.penalty = penalty
        self.timeout_seconds = timeout_seconds
        self.fetch_json = fetch_json or _fetch_json

    def route(
        self,
        start_lat: float,
        start_lon: float,
        end_lat: float,
        end_lon: float,
        *,
        penalty: float | None = None,
    ) -> RouteResult:
        params = urllib.parse.urlencode(
            {
                "from": f"{start_lon},{start_lat}",
                "to": f"{end_lon},{end_lat}",
                "penalty": self.penalty if penalty is None else penalty,
            }
        )
        payload = self.fetch_json(
            f"{self.base_url}/route?{params}", self.timeout_seconds
        )
        if not isinstance(payload, dict):
            raise RuntimeError("Sea-router zwrócił niepoprawną odpowiedź")
        if payload.get("error"):
            raise RuntimeError(f"Sea-router: {payload['error']}")

        features = payload.get("features")
        if not isinstance(features, list) or not features:
            raise RuntimeError("Sea-router nie zwrócił geometrii trasy")

        final_feature = next(
            (
                feature
                for feature in features
                if isinstance(feature, dict)
                and isinstance(feature.get("properties"), dict)
                and feature["properties"].get("name") == "final"
            ),
            None,
        )
        if final_feature is None:
            final_feature = features[-1]
        if not isinstance(final_feature, dict) or not isinstance(
            final_feature.get("geometry"), dict
        ):
            raise RuntimeError("Sea-router zwrócił niepoprawną geometrię")

        return RouteResult(
            geometry=final_feature["geometry"],
            distance_nm=_line_distance_nm(final_feature["geometry"]),
        )


def _fetch_json(url: str, timeout: float) -> object:
    with urllib.request.urlopen(url, timeout=timeout) as response:
        return json.load(response)


def _line_distance_nm(geometry: dict[str, Any]) -> float | None:
    coordinates = geometry.get("coordinates")
    if geometry.get("type") != "LineString" or not isinstance(coordinates, list):
        return None

    distance_km = 0.0
    valid_points = 0
    previous: tuple[float, float] | None = None
    for point in coordinates:
        if not isinstance(point, (list, tuple)) or len(point) < 2:
            return None
        current = (float(point[0]), float(point[1]))
        if previous is not None:
            distance_km += _haversine_km(previous, current)
        previous = current
        valid_points += 1
    return distance_km / 1.852 if valid_points >= 2 else None


def _haversine_km(start: tuple[float, float], end: tuple[float, float]) -> float:
    lon1, lat1 = map(math.radians, start)
    lon2, lat2 = map(math.radians, end)
    delta_lat = lat2 - lat1
    delta_lon = (lon2 - lon1 + math.pi) % (2 * math.pi) - math.pi
    value = (
        math.sin(delta_lat / 2) ** 2
        + math.cos(lat1) * math.cos(lat2) * math.sin(delta_lon / 2) ** 2
    )
    return 2 * 6371.0088 * math.asin(math.sqrt(value))
