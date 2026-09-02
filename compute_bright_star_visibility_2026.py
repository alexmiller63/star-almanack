#!/usr/bin/env python3
"""Compute 2026 best-visibility dates for the reconciled bright-star layer.

Uses the same observer-first rule and solar-RA implementation as the audited
alpha/beta Bayer visibility computation. The output includes all reconciled
bright-star systems; `new_non_alpha_beta=yes` identifies the systems that add
new stellar content to the expanded Almanack.
"""

from __future__ import annotations

import argparse
import csv
import math
from pathlib import Path

from compute_bayer_visibility_2026 import REGRESSION, REGRESSION_BAYER, best_visibility, iso_date


def magnitude_class(value: str) -> str:
    """Whole-number Almanack display class; decimal V remains in source fields."""
    if not value:
        return ""
    mag = float(value)
    return str(max(1, min(6, int(math.floor(mag + 0.5)))))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("input", type=Path, nargs="?", default=Path("bright-stars-2mag.csv"))
    parser.add_argument("output", type=Path, nargs="?", default=Path("bright-star-visibility-2026.csv"))
    args = parser.parse_args()

    with args.input.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    if not rows:
        raise SystemExit("Bright-star catalog is empty")

    output = []
    proper_to_date: dict[str, str] = {}
    bayer_to_date: dict[tuple[str, str], str] = {}

    for row in rows:
        instant, date = best_visibility(float(row["ra_h"]))
        enriched = dict(row)
        enriched["best_instant_utc"] = instant.strftime("%Y-%m-%d %H:%M")
        enriched["best_date"] = date.isoformat()
        enriched["iso"] = iso_date(date)
        enriched["mag_class"] = magnitude_class(row.get("representative_vmax", ""))
        enriched["new_non_alpha_beta"] = "yes" if row.get("in_alpha_beta_layer") == "no" else "no"
        output.append(enriched)

        proper = (row.get("proper") or "").strip()
        if proper:
            proper_to_date.setdefault(proper, date.isoformat())
        bayer = (row.get("bayer") or "").strip()
        con = (row.get("con") or "").strip()
        if bayer and con:
            # Normalize HYG spelling such as Bet-1 to the Bayer regression key Bet1.
            bayer_to_date.setdefault((bayer.replace("-", ""), con), date.isoformat())

    # Run every historical regression object that exists in this bright-star layer.
    failures = []
    checked = 0
    for name, expected in REGRESSION.items():
        if name in REGRESSION_BAYER:
            actual = bayer_to_date.get(REGRESSION_BAYER[name])
        else:
            actual = proper_to_date.get(name)
        if actual is None:
            continue
        checked += 1
        if actual != expected:
            failures.append((name, expected, actual))
    if failures:
        for name, expected, actual in failures:
            print(f"FAIL {name}: expected {expected}, got {actual}")
        raise SystemExit(f"Bright-star best-visibility regression failed: {len(failures)}/{checked}")

    fieldnames = list(rows[0].keys()) + [
        "best_instant_utc", "best_date", "iso", "mag_class", "new_non_alpha_beta"
    ]
    with args.output.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(output)

    new_rows = sum(r["new_non_alpha_beta"] == "yes" for r in output)
    print(f"Bright-star visibility regression: {checked}/{checked} PASS")
    print(f"Dated bright-star systems: {len(output)}")
    print(f"New non-alpha/beta systems: {new_rows}")
    print(f"Wrote {args.output}")


if __name__ == "__main__":
    main()
