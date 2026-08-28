from __future__ import annotations

import json
import re
from collections import defaultdict
from pathlib import Path

from .excel_io import load_input, write_legs, write_results
from .geocoding import CachedGeocoder
from .kml import export_kml
from .models import Leg, PortCall
from .schedule import calculate_schedule
from .sea_router import SeaRouter


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


def generate_routes(
    input_path: Path,
    output_dir: Path,
    geocoder: CachedGeocoder,
    sea_router: SeaRouter,
) -> list[Path]:
    voyages, calls = load_input(input_path)
    calls_by_voyage: dict[str, list[PortCall]] = defaultdict(list)
    for call in calls:
        if call.lat is None or call.lon is None:
            candidate = geocoder.resolve(call.port, call.country)
            call.lat = candidate.lat
            call.lon = candidate.lon
        calls_by_voyage[call.voyage_id].append(call)

    all_legs: list[Leg] = []
    output_paths: list[Path] = []
    for voyage_id, voyage in voyages.items():
        voyage_calls = sorted(calls_by_voyage[voyage_id], key=lambda item: item.order)
        legs = calculate_schedule(voyage, voyage_calls)
        coastal_penalty = _coastal_penalty(voyage.ca)
        voyage_dir = output_dir / _safe_name(voyage_id)
        geojson_dir = voyage_dir / "geojson"
        kml_legs: list[tuple[Leg, list[tuple[float, float]]]] = []

        for leg, start, end in zip(legs, voyage_calls, voyage_calls[1:]):
            if start.lat is None or start.lon is None or end.lat is None or end.lon is None:
                leg.status = "brak_wspolrzednych"
                continue
            try:
                result = sea_router.route(
                    start.lat,
                    start.lon,
                    end.lat,
                    end.lon,
                    penalty=coastal_penalty,
                )
                coordinates = _coordinates_lon_lat(result.geometry)
                geojson_path = geojson_dir / f"{leg.number:02d}-{_safe_name(leg.name)}.geojson"
                _write_geojson(geojson_path, leg, result.geometry, result.distance_nm)
                leg.distance_nm = (
                    round(result.distance_nm, 1)
                    if result.distance_nm is not None
                    else None
                )
                leg.geojson_path = geojson_path.relative_to(output_dir)
                leg.status = "gotowy"
                kml_legs.append((leg, coordinates))
            except (OSError, RuntimeError, ValueError) as error:
                leg.status = "brak_trasy"
                leg.notes = str(error)

        kml_path = voyage_dir / "trasa.kml"
        export_kml(voyage, voyage_calls, kml_legs, kml_path)
        output_paths.append(kml_path)
        all_legs.extend(legs)

    workbook_path = input_path
    write_results(input_path, workbook_path, calls, all_legs)
    return [workbook_path, *output_paths]


def _coordinates_lon_lat(geometry: dict[str, object]) -> list[tuple[float, float]]:
    if geometry.get("type") != "LineString" or not isinstance(
        geometry.get("coordinates"), list
    ):
        raise ValueError("Sea-router nie zwrócił linii GeoJSON")
    result: list[tuple[float, float]] = []
    for point in geometry["coordinates"]:
        if not isinstance(point, (list, tuple)) or len(point) < 2:
            raise ValueError("Sea-router zwrócił niepoprawny punkt GeoJSON")
        result.append((float(point[0]), float(point[1])))
    if len(result) < 2:
        raise ValueError("Trasa musi zawierać co najmniej dwa punkty")
    return result


def _write_geojson(
    path: Path,
    leg: Leg,
    geometry: dict[str, object],
    distance_nm: float | None,
) -> None:
    feature = {
        "type": "Feature",
        "geometry": geometry,
        "properties": {
            "name": leg.name,
            "rejs_id": leg.voyage_id,
            "etap_nr": leg.number,
            "zakres_dni": leg.day_range,
            "distance_nm": distance_nm,
        },
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(feature, ensure_ascii=False, indent=2), encoding="utf-8"
    )


def _safe_name(value: str) -> str:
    normalized = re.sub(r"[^0-9A-Za-zÀ-ž._-]+", "-", value.strip())
    return normalized.strip("-._") or "rejs"


def _coastal_penalty(value: str | None) -> float | None:
    if value is None or not value.strip():
        return None
    try:
        penalty = float(value.replace(",", "."))
    except ValueError as error:
        raise ValueError("CA musi być dodatnią liczbą, np. 5 albo 8") from error
    if penalty <= 0:
        raise ValueError("CA musi być dodatnią liczbą, np. 5 albo 8")
    return penalty
