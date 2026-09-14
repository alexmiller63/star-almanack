#!/usr/bin/env python3
"""Recreate every civil-year calendar-event file needed by an ISO-week range."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import generate_calendar_events
from iso_week_range import IsoWeekRange

ROOT = Path(__file__).resolve().parent


def generate(week_range: IsoWeekRange, manifest: Path, output_dir: Path) -> list[Path]:
    normalized = generate_calendar_events.lunar_elp.load_normalized(manifest)
    years = range(week_range.first.monday.year, week_range.last.sunday.year + 1)
    written = []
    for year in years:
        payload = generate_calendar_events.calculate(year, normalized)
        target = output_dir / f"calendar-events-{year}.json"
        temporary = target.with_suffix(".json.tmp")
        temporary.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        temporary.replace(target)
        written.append(target)
        print(f"Recreated {target.name}")
    return written


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("first_iso_week")
    parser.add_argument("last_iso_week")
    parser.add_argument("--manifest", type=Path,
                        default=ROOT / "star-almanack-elp82b" / "elp82b-manifest.json")
    parser.add_argument("--output-dir", type=Path, default=ROOT)
    args = parser.parse_args()
    generate(IsoWeekRange.parse(args.first_iso_week, args.last_iso_week), args.manifest, args.output_dir)


if __name__ == "__main__":
    main()
