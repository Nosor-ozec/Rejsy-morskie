from __future__ import annotations

from collections import defaultdict
from pathlib import Path

from .excel_io import load_input, write_legs
from .models import Leg, PortCall
from .schedule import calculate_schedule


def build_schedule(input_path: Path, output_path: Path) -> list[Leg]:
    voyages, calls = load_input(input_path)
    calls_by_voyage: dict[str, list[PortCall]] = defaultdict(list)
    for call in calls:
        calls_by_voyage[call.voyage_id].append(call)

    legs: list[Leg] = []
    for voyage_id, voyage in voyages.items():
        legs.extend(calculate_schedule(voyage, calls_by_voyage[voyage_id]))

    write_legs(input_path, output_path, legs)
    return legs


# Kolejne kroki integracji:
# 1. uzupełnij brakujące Lat/Lon przez CachedGeocoder;
# 2. zapisz współrzędne do skoroszytu wynikowego;
# 3. wywołaj SeaRouter dla każdej pary portów;
# 4. zapisz GeoJSON i przekaż linie do export_kml.
