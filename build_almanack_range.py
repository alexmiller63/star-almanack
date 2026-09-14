#!/usr/bin/env python3
"""Build the complete Star Almanack for an inclusive ISO-week range."""
from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

from iso_week_range import IsoWeekRange

ROOT = Path(__file__).resolve().parent


def run(*args: str) -> None:
    print("+", " ".join(args), flush=True)
    subprocess.run([sys.executable, *args], cwd=ROOT, check=True)


def build(first: str, last: str) -> None:
    requested = IsoWeekRange.parse(first, last)
    # Structure and every independent source are regenerated before population.
    run("generate_year_scaffolds.py", first, last)
    run("generate_fixed_object_sky_notes.py", "--start-year", str(requested.first.year),
        "--end-year", str(requested.last.year))
    run("generate_calendar_event_range.py", first, last)
    run("generate_weekly_ephemeris.py", first, last)

    for year in requested.by_year():
        run("populate_scaffold_calendar.py", str(year))
        run("populate_scaffold_ephemeris.py", str(year))
        run("populate_scaffold_sky_notes.py", str(year))
        run("populate_scaffold_planet_finders.py", str(year))

    run("generate_artwork_handoffs.py", first, last)
    for year in requested.by_year():
        run("populate_scaffold_artwork.py", str(year))

    run("publish_weekly_pages.py", first, last)
    run("add_greek_latin_toggle.py", first, last)
    run("add_observing_aid_notation.py", first, last)
    print(f"Built everything for {requested.first} through {requested.last}: {len(requested)} weekly pages")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("first_iso_week")
    parser.add_argument("last_iso_week")
    args = parser.parse_args()
    build(args.first_iso_week, args.last_iso_week)


if __name__ == "__main__":
    main()
