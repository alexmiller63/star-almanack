#!/usr/bin/env python3
"""Resolve the common generator week-range interface.

Start year/week are required. End year/week are optional as a pair. If both
end fields are blank, the range is exactly the starting ISO week.
"""
from __future__ import annotations

import argparse
import json
from datetime import date, timedelta


def iso_monday(year: int, week: int) -> date:
    try:
        return date.fromisocalendar(year, week, 1)
    except ValueError as exc:
        raise SystemExit(f"Invalid ISO week {year}-W{week:02d}: {exc}") from exc


def resolve(start_year: int, start_week: int, end_year: str = "", end_week: str = "") -> list[tuple[int, int]]:
    end_year = str(end_year or "").strip()
    end_week = str(end_week or "").strip()
    if bool(end_year) != bool(end_week):
        raise SystemExit("End year and End week must either both be blank or both be supplied")

    start = iso_monday(int(start_year), int(start_week))
    if not end_year:
        end = start
    else:
        end = iso_monday(int(end_year), int(end_week))
    if end < start:
        raise SystemExit("End week must not be before Start week")

    weeks: list[tuple[int, int]] = []
    current = start
    while current <= end:
        iso = current.isocalendar()
        weeks.append((iso.year, iso.week))
        current += timedelta(days=7)
    return weeks


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("start_year", type=int)
    parser.add_argument("start_week", type=int)
    parser.add_argument("end_year", nargs="?", default="")
    parser.add_argument("end_week", nargs="?", default="")
    parser.add_argument("--format", choices=("lines", "json", "csv"), default="lines")
    args = parser.parse_args()

    weeks = resolve(args.start_year, args.start_week, args.end_year, args.end_week)
    labels = [f"{year}-W{week:02d}" for year, week in weeks]
    if args.format == "json":
        print(json.dumps(labels))
    elif args.format == "csv":
        print(",".join(labels))
    else:
        print("\n".join(labels))


if __name__ == "__main__":
    main()
