from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Protocol


@dataclass(slots=True)
class RouteResult:
    geometry: dict[str, Any]
    distance_nm: float | None = None


class SeaRouter(Protocol):
    def route(
        self, start_lat: float, start_lon: float, end_lat: float, end_lon: float
    ) -> RouteResult: ...


class NotConfiguredSeaRouter:
    """Jawny placeholder do czasu wyboru lokalnego sea-routera i jego CLI/API."""

    def route(
        self, start_lat: float, start_lon: float, end_lat: float, end_lon: float
    ) -> RouteResult:
        raise RuntimeError(
            "Sea-router nie jest skonfigurowany. Dodaj adapter lokalnego CLI/API."
        )
