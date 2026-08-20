from __future__ import annotations

import argparse
from pathlib import Path

from .excel_io import load_input
from .pipeline import build_schedule


def parser() -> argparse.ArgumentParser:
    root = argparse.ArgumentParser(prog="rejsy-morskie")
    commands = root.add_subparsers(dest="command", required=True)

    validate = commands.add_parser("validate", help="Sprawdź strukturę skoroszytu")
    validate.add_argument("input", type=Path)

    schedule = commands.add_parser("schedule", help="Wylicz i zapisz arkusz Etapy")
    schedule.add_argument("input", type=Path)
    schedule.add_argument("output", type=Path)

    return root


def main() -> None:
    args = parser().parse_args()
    if args.command == "validate":
        voyages, calls = load_input(args.input)
        print(f"OK: {len(voyages)} rejsów, {len(calls)} portów")
    elif args.command == "schedule":
        legs = build_schedule(args.input, args.output)
        print(f"Zapisano {len(legs)} etapów: {args.output}")
