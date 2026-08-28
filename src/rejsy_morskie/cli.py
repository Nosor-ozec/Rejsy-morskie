from __future__ import annotations

import argparse
from pathlib import Path

from .excel_io import load_input
from .geocoding import CachedGeocoder, NominatimGeocoder
from .pipeline import build_schedule, generate_routes
from .sea_router import HttpSeaRouter
from .web import build_local_site, publish_site


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
    generate.add_argument("--media", type=Path)
    generate.add_argument("--site-dir", type=Path)
    generate.add_argument("--web-assets", type=Path)

    publish = commands.add_parser(
        "publish", help="Skopiuj sprawdzony podgląd lokalny do docs"
    )
    publish.add_argument("site_dir", type=Path)
    publish.add_argument("docs_dir", type=Path)

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
            site_arguments = (args.media, args.site_dir, args.web_assets)
            if any(site_arguments) and not all(site_arguments):
                raise ValueError(
                    "Opcje --media, --site-dir i --web-assets muszą wystąpić razem"
                )
            if all(site_arguments):
                site_outputs = build_local_site(
                    args.input, args.media, args.output_dir, args.site_dir,
                    args.web_assets,
                )
                print("Gotowy pełny podgląd Leaflet:")
                for output in site_outputs:
                    print(f"- {output}")
        elif args.command == "publish":
            outputs = publish_site(args.site_dir, args.docs_dir)
            print(f"Przygotowano {len(outputs)} plików publicznych w {args.docs_dir}")
    except (OSError, RuntimeError, ValueError) as error:
        raise SystemExit(f"Błąd: {error}") from None


if __name__ == "__main__":
    main()
