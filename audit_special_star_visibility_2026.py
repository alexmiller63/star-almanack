#!/usr/bin/env python3
"""Audit Special Star dates against the Star Almanack 2026 visibility rule.

The long-form editorial source remains special-stars.md. This script extracts each
Special Star heading and its printed RA, recomputes the natural 2026 placement
using the same solar-RA solver as the Bayer and bright-star layers, and writes a
machine-readable audit without changing the editorial source.
"""

from __future__ import annotations

import argparse
import csv
import datetime as dt
import re
from pathlib import Path

from compute_bayer_visibility_2026 import best_visibility, iso_date
from compute_bright_star_visibility_2026 import normalize_to_iso_2026

MONTHS = {
    name: number
    for number, name in enumerate(
        [
            "January", "February", "March", "April", "May", "June",
            "July", "August", "September", "October", "November", "December",
        ],
        1,
    )
}

HEADING_RE = re.compile(
    r"(?m)^### (?P<title>.+?) · (?P<season>.+?) · "
    r"(?P<month>January|February|March|April|May|June|July|August|September|October|November|December) "
    r"(?P<day>\d{1,2})\s*$"
)
COORD_RE = re.compile(
    r"\*\*RA (?P<h>\d+)h (?P<m>\d+)m · Dec (?P<dec>[+−\-]?\d+(?:\.\d+)?)° · mag (?P<mag>.+?)\*\*"
)
OBS_RE = re.compile(r"\*\*Observing:\s*(?P<obs>.*?)\*\*", re.S)


def normalize_minus(value: str) -> str:
    return value.replace("−", "-")


def compact(text: str) -> str:
    return " ".join(text.split())


def parse_special_stars(text: str) -> list[dict[str, str]]:
    matches = list(HEADING_RE.finditer(text))
    rows: list[dict[str, str]] = []

    for i, match in enumerate(matches):
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        block = text[match.end():end]
        coord = COORD_RE.search(block)
        if coord is None:
            raise SystemExit(f"Missing RA/Dec line for Special Star heading: {match.group('title')}")
        obs = OBS_RE.search(block)
        if obs is None:
            raise SystemExit(f"Missing observing line for Special Star heading: {match.group('title')}")

        stated_date = dt.date(
            2026,
            MONTHS[match.group("month")],
            int(match.group("day")),
        )
        ra_h = int(coord.group("h")) + int(coord.group("m")) / 60.0
        instant, computed_date = best_visibility(ra_h)
        instant, computed_date = normalize_to_iso_2026(ra_h, instant, computed_date)

        rows.append(
            {
                "title": match.group("title").strip(),
                "season": match.group("season").strip(),
                "stated_date": stated_date.isoformat(),
                "ra_h": f"{ra_h:.6f}",
                "dec_deg": normalize_minus(coord.group("dec")),
                "magnitude_text": compact(coord.group("mag")),
                "observing_text": compact(obs.group("obs")),
                "best_instant_utc": instant.strftime("%Y-%m-%d %H:%M"),
                "computed_date": computed_date.isoformat(),
                "iso": iso_date(computed_date),
                "status": "PASS" if computed_date == stated_date else "STALE_DATE",
            }
        )

    if not rows:
        raise SystemExit("No Special Star headings found in editorial source")
    return rows


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("input", type=Path, nargs="?", default=Path("special-stars.md"))
    parser.add_argument(
        "output",
        type=Path,
        nargs="?",
        default=Path("special-star-visibility-audit-2026.csv"),
    )
    args = parser.parse_args()

    rows = parse_special_stars(args.input.read_text(encoding="utf-8"))
    fieldnames = [
        "title", "season", "stated_date", "ra_h", "dec_deg", "magnitude_text",
        "observing_text", "best_instant_utc", "computed_date", "iso", "status",
    ]
    with args.output.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    stale = [r for r in rows if r["status"] != "PASS"]
    print(f"Special Stars audited: {len(rows)}")
    print(f"Dates matching current visibility rule: {len(rows) - len(stale)}")
    print(f"Dates requiring reconciliation: {len(stale)}")
    for row in stale:
        print(f"STALE {row['title']}: stated {row['stated_date']} -> computed {row['computed_date']}")
    print(f"Wrote {args.output}")


if __name__ == "__main__":
    main()
