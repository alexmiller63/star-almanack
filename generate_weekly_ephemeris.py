#!/usr/bin/env python3
"""Recreate canonical weekly ephemerides for an inclusive ISO-week range.

All bodies use the same NASA/JPL Horizons observer solution: apparent,
geocentric, ecliptic-of-date longitude at Monday 00:00 UTC.
"""
from __future__ import annotations

import argparse
import csv
import json
import urllib.parse
import urllib.request
from pathlib import Path

from iso_week_range import IsoWeekRange

ROOT = Path(__file__).resolve().parent
HORIZONS_API = "https://ssd.jpl.nasa.gov/api/horizons.api"
BODIES = (
    ("sun", "10"), ("moon", "301"), ("mercury", "199"),
    ("venus", "299"), ("mars", "499"), ("jupiter", "599"),
    ("saturn", "699"), ("uranus", "799"), ("neptune", "899"),
    ("ceres", "1;"),
)
SIGNS = "♈♉♊♋♌♍♎♏♐♑♒♓"


def zodiac(longitude_deg: float) -> str:
    minutes_total = int(round((longitude_deg % 360.0) * 60.0)) % (360 * 60)
    sign, within = divmod(minutes_total, 30 * 60)
    degrees, minutes = divmod(within, 60)
    return f"{SIGNS[sign]} {degrees}°{minutes:02d}′"


def parse_horizons_result(text: str, expected: int) -> list[float]:
    lines = text.splitlines()
    header_line = next((line for line in lines if "ObsEcLon" in line), None)
    if not header_line or "$$SOE" not in lines or "$$EOE" not in lines:
        raise RuntimeError("Horizons response does not contain a complete ObsEcLon ephemeris")
    header = [value.strip() for value in next(csv.reader([header_line]))]
    try:
        longitude_index = header.index("ObsEcLon")
    except ValueError as exc:
        raise RuntimeError(f"Unexpected Horizons columns: {header}") from exc
    start, stop = lines.index("$$SOE") + 1, lines.index("$$EOE")
    values = [
        float(next(csv.reader([line]))[longitude_index].strip())
        for line in lines[start:stop] if line.strip()
    ]
    if len(values) != expected:
        raise RuntimeError(f"Expected {expected} Horizons rows, found {len(values)}")
    return values


def fetch_longitudes(command: str, week_range: IsoWeekRange) -> list[float]:
    params = {
        "format": "json", "COMMAND": f"'{command}'", "OBJ_DATA": "'NO'",
        "MAKE_EPHEM": "'YES'", "EPHEM_TYPE": "'OBSERVER'", "CENTER": "'500@399'",
        "START_TIME": f"'{week_range.first.monday.isoformat()} 00:00'",
        "STOP_TIME": f"'{week_range.last.monday.isoformat()} 00:01'",
        "STEP_SIZE": "'7 d'", "QUANTITIES": "'31'", "CSV_FORMAT": "'YES'",
        "ANG_FORMAT": "'DEG'", "CAL_FORMAT": "'CAL'", "TIME_DIGITS": "'SECONDS'",
    }
    request = urllib.request.Request(
        HORIZONS_API + "?" + urllib.parse.urlencode(params),
        headers={"User-Agent": "Star-Almanack/week-range-generator"},
    )
    with urllib.request.urlopen(request, timeout=120) as response:
        result = json.load(response).get("result", "")
    return parse_horizons_result(result, len(week_range))


def generate(week_range: IsoWeekRange, output_dir: Path) -> list[Path]:
    weeks = week_range.weeks()
    positions = {name: fetch_longitudes(command, week_range) for name, command in BODIES}
    fields = ["iso_week", "monday_utc", *(name for name, _ in BODIES)]
    rows_by_year: dict[int, list[dict[str, str]]] = {}
    for index, week in enumerate(weeks):
        row = {"iso_week": str(week), "monday_utc": week.monday.isoformat()}
        row.update({name: zodiac(values[index]) for name, values in positions.items()})
        rows_by_year.setdefault(week.year, []).append(row)
    written = []
    for year, rows in rows_by_year.items():
        target = output_dir / f"weekly-ephemeris-{year}.csv"
        temporary = target.with_suffix(".csv.tmp")
        with temporary.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
            writer.writeheader()
            writer.writerows(rows)
        temporary.replace(target)
        written.append(target)
        print(f"Recreated {target.name} with {len(rows)} weekly snapshots")
    return written


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("first_iso_week")
    parser.add_argument("last_iso_week")
    parser.add_argument("--output-dir", type=Path, default=ROOT)
    args = parser.parse_args()
    generate(IsoWeekRange.parse(args.first_iso_week, args.last_iso_week), args.output_dir)


if __name__ == "__main__":
    main()
