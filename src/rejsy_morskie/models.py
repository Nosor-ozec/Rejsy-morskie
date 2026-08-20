from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from pathlib import Path


@dataclass(slots=True)
class Voyage:
    voyage_id: str
    name: str
    start_date: date
    route_color: str = "#0057B8"
    ca: str | None = None
    notes: str | None = None


@dataclass(slots=True)
class PortCall:
    voyage_id: str
    order: int
    port: str
    country: str | None
    when: date | str
    stay_days: int = 1
    lat: float | None = None
    lon: float | None = None
    notes: str | None = None
    arrival_day: int | None = None
    arrival_date: date | None = None


@dataclass(slots=True)
class Leg:
    voyage_id: str
    number: int
    start_port: str
    end_port: str
    day_from: int
    day_to: int
    date_from: date
    date_to: date
    distance_nm: float | None = None
    geojson_path: Path | None = None
    status: str = "oczekuje"
    notes: str | None = None

    @property
    def name(self) -> str:
        return f"{self.start_port} → {self.end_port}"

    @property
    def day_range(self) -> str:
        return f"Dni {self.day_from}–{self.day_to}"
