#!/usr/bin/env python3
"""Classify every fixed object with RA/Dec as inside/outside the Milky Way.

Reads fixed-objects.yaml and the frozen local Milky Way boundary used by
in_milky_way.py, then writes a compact sidecar CSV.  The source catalog is not
rewritten; this keeps fixed-objects.yaml authoritative and preserves its
formatting.
"""

from __future__ import annotations

import argparse
import csv
from pathlib import Path
from typing import Any

import yaml

from in_milky_way import in_milky_way


def object_label(fields: list[str], row: list[Any]) -> str:
    record = dict(zip(fields, row))
    for key in ("id", "bayer", "name", "catalog", "component"):
        value = record.get(key)
        if value not in (None, ""):
            return str(value)
    return ""


def classify(source: Path, output: Path) -> tuple[int, int, int]:
    data = yaml.safe_load(source.read_text(encoding="utf-8"))
    schemas = data.get("schema", {})

    results: list[dict[str, str]] = []
    yes_count = 0
    no_count = 0

    for category, rows in data.items():
        if category in {"edition", "schema"} or not isinstance(rows, list):
            continue

        fields = schemas.get(category)
        if not isinstance(fields, list):
            continue
        if "ra_h" not in fields or "dec_deg" not in fields:
            continue

        ra_i = fields.index("ra_h")
        dec_i = fields.index("dec_deg")

        for row in rows:
            if not isinstance(row, list):
                continue
            ra = float(row[ra_i])
            dec = float(row[dec_i])
            inside = in_milky_way(ra, dec)
            yes_count += int(inside)
            no_count += int(not inside)
            results.append(
                {
                    "category": category,
                    "object": object_label(fields, row),
                    "ra_h": f"{ra:.9f}".rstrip("0").rstrip("."),
                    "dec_deg": f"{dec:.9f}".rstrip("0").rstrip("."),
                    "in_milky_way": "yes" if inside else "no",
                }
            )

    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=["category", "object", "ra_h", "dec_deg", "in_milky_way"],
        )
        writer.writeheader()
        writer.writerows(results)

    return len(results), yes_count, no_count


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=Path, default=Path("fixed-objects.yaml"))
    parser.add_argument(
        "--output", type=Path, default=Path("fixed-object-milky-way.csv")
    )
    args = parser.parse_args()

    total, yes_count, no_count = classify(args.source, args.output)
    print(f"classified={total} yes={yes_count} no={no_count}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
