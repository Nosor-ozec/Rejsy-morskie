from __future__ import annotations

import argparse
from pathlib import Path

from .excel_io import load_input
from .geocoding import CachedGeocoder, NominatimGeocoder
from .pipeline import build_schedule, generate_routes
from .sea_router import HttpSeaRouter


def parser() -> argparse.ArgumentParser:
    root = argparse.ArgumentParser(prog="rejsy-morskie")
    commands = root.add_subparsers(dest="command", required=True)

    validate = commands.add_parser("validate", help="Sprawdź strukturę skoroszytu")
    validate.add_argument("input", type=Path)

    schedule = commands.add_parser("schedule", help="Wylicz i zapisz arkusz Etapy")
    schedule.add_argument("input", type=Path)
    schedule.add_argument("output", type=Path)

    generate = commands.add_parser(
        "generate", help="Uzupełnij porty, wyznacz trasy i zapisz Excel/GeoJSON/KML"
    )
    generate.add_argument("input", type=Path)
    generate.add_argument("output_dir", type=Path)
    generate.add_argument(
        "--sea-router-url", default="http://127.0.0.1:3001"
    )
    generate.add_argument(
        "--nominatim-url", default="https://nominatim.openstreetmap.org"
    )

    return root


def main() -> None:
    args = parser().parse_args()
    try:
        if args.command == "validate":
            voyages, calls = load_input(args.input)
            print(f"OK: {len(voyages)} rejsów, {len(calls)} portów")
        elif args.command == "schedule":
            legs = build_schedule(args.input, args.output)
            print(f"Zapisano {len(legs)} etapów: {args.output}")
        elif args.command == "generate":
            cache_path = args.output_dir / "geocoding-cache.json"
            geocoder = CachedGeocoder(
                NominatimGeocoder(base_url=args.nominatim_url), cache_path
            )
            outputs = generate_routes(
                args.input,
                args.output_dir,
                geocoder,
                HttpSeaRouter(args.sea_router_url),
            )
            print("Gotowe pliki:")
            for output in outputs:
                print(f"- {output}")
    except (OSError, RuntimeError, ValueError) as error:
        raise SystemExit(f"Błąd: {error}") from None


if __name__ == "__main__":
    main()

