#!/usr/bin/env python3
"""Recreate ephemeris owner blocks from a canonical weekly CSV."""
from __future__ import annotations

import argparse
import csv
import datetime as dt
from pathlib import Path

from scaffold_sections import iso_week_count, replace_owner_blocks, write_atomic

ROOT = Path(__file__).resolve().parent
PRIMARY = (("☉ Sun", "sun"), ("☽ Moon", "moon"), ("☿ Mercury", "mercury"),
           ("♀ Venus", "venus"), ("♂ Mars", "mars"), ("♃ Jupiter", "jupiter"),
           ("♄ Saturn", "saturn"))
EXTENDED = (("♅ Uranus", "uranus"), ("♆ Neptune", "neptune"), ("⚳ Ceres", "ceres"))


def table(columns: tuple[tuple[str, str], ...], row: dict[str, str]) -> str:
    return (
        "| " + " | ".join(label for label, _ in columns) + " |\n"
        + "|" + "|".join("---:" for _ in columns) + "|\n"
        + "| " + " | ".join(row[key] for _, key in columns) + " |"
    )


def load_rows(path: Path, year: int) -> dict[int, dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    required_fields = {key for _, key in PRIMARY + EXTENDED} | {"iso_week", "monday_utc"}
    if not rows or not required_fields.issubset(rows[0]):
        raise ValueError(f"Missing required ephemeris columns in {path}")
    result: dict[int, dict[str, str]] = {}
    for week, row in enumerate(rows, 1):
        expected_key = f"{year}-W{week:02d}"
        expected_date = dt.date.fromisocalendar(year, week, 1).isoformat()
        if row["iso_week"] != expected_key or row["monday_utc"] != expected_date:
            raise ValueError(f"Unexpected ephemeris row {week}: {row['iso_week']}, {row['monday_utc']}")
        result[week] = row
    if len(result) != iso_week_count(year):
        raise ValueError(f"Expected {iso_week_count(year)} ephemeris rows for {year}, found {len(result)}")
    return result


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

    def render(week: int) -> str:
        row = rows[week]
        monday = dt.date.fromisoformat(row["monday_utc"])
        return (
            f"**Snapshot:** {monday:%B} {monday.day}, {monday.year} · 00:00 UTC\n\n"
            + table(PRIMARY, row)
            + "\n\n**Extended targets:**\n\n"
            + table(EXTENDED, row)
        )

    updated = replace_owner_blocks(
        scaffold.read_text(encoding="utf-8"), args.year, "ephemeris", render
    )
    write_atomic(scaffold, updated)
    print(f"Recreated {len(rows)} ephemeris blocks for {args.year}")


if __name__ == "__main__":
    main()
