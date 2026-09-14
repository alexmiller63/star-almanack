#!/usr/bin/env python3
"""Recreate Planet Finder blocks and their machine-readable descriptors."""
from __future__ import annotations

import argparse
import json
import re
import shutil
from pathlib import Path

from populate_scaffold_ephemeris import load_rows
from scaffold_sections import replace_owner_blocks, write_atomic

ROOT = Path(__file__).resolve().parent
PLANETS = (
    ("Mercury", "mercury"), ("Venus", "venus"), ("Mars", "mars"),
    ("Jupiter", "jupiter"), ("Saturn", "saturn"), ("Uranus", "uranus"),
    ("Neptune", "neptune"),
)
POSITION = re.compile(r"^([♈♉♊♋♌♍♎♏♐♑♒♓])\s*(\d{1,2})°(\d{2})′$")


def parse_position(value: str) -> dict[str, int | str]:
    match = POSITION.fullmatch(value.strip())
    if not match:
        raise ValueError(f"Invalid zodiac position: {value!r}")
    return {"sign": match.group(1), "degrees": int(match.group(2)), "minutes": int(match.group(3))}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("year", type=int)
    parser.add_argument("--root", type=Path, default=ROOT)
    args = parser.parse_args()
    scaffold = args.root / "year-scaffolds" / f"almanack-{args.year}.md"
    source = args.root / f"weekly-ephemeris-{args.year}.csv"
    if not scaffold.exists() or not source.exists():
        raise SystemExit(f"Missing scaffold or weekly ephemeris for {args.year}")
    rows = load_rows(source, args.year)
    output = args.root / f"planet-finder-descriptors-{args.year}"
    if output.exists():
        shutil.rmtree(output)
    output.mkdir(parents=True)
    blocks: dict[int, str] = {}
    for week, row in rows.items():
        week_id = f"W{week:02d}"
        positions = [
            {"name": name, "notation": row[key], **parse_position(row[key])}
            for name, key in PLANETS
        ]
        payload = {
            "schema": "star-almanack.planet-finder.v1",
            "iso_week": f"{args.year}-{week_id}",
            "snapshot_utc": f"{row['monday_utc']}T00:00:00Z",
            "coordinate_system": "geocentric tropical ecliptic longitude of date",
            "planets": positions,
            "generated_from": source.name,
        }
        descriptor = output / f"{week_id}.json"
        descriptor.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        blocks[week] = (
            "The planet-finder positions use this week's Monday 00:00 UTC snapshot.\n\n"
            f"**Machine-readable planet finder:** [Open {week_id} descriptor]"
            f"(../planet-finder-descriptors-{args.year}/{week_id}.json)"
        )
    updated = replace_owner_blocks(
        scaffold.read_text(encoding="utf-8"), args.year, "planet-finder", blocks.__getitem__
    )
    write_atomic(scaffold, updated)
    print(f"Recreated {len(blocks)} Planet Finder blocks and descriptors for {args.year}")


if __name__ == "__main__":
    main()
