#!/usr/bin/env python3
"""Extend the 2026 weekly ephemeris with Uranus, Neptune, and Ceres.

The existing Sun-through-Saturn values are preserved. If the CSV contains
only a partial ISO-year extract, the complete 53-week base is recovered from
the already-published Almanack source before the new columns are added.

The 3 added observer-oriented bodies are obtained from NASA/JPL Horizons as
apparent, geocentric, ecliptic-of-date longitudes (Horizons observer quantity
31), sampled at the Almanack standard epoch: Monday 00:00 UTC.

Targets:
    799  Uranus
    899  Neptune
    1;   Ceres (small-body syntax; the semicolon is significant)

The generated values are rounded to the nearest arcminute and rendered in
the same zodiac-sign notation as the existing weekly ephemeris.
"""
from __future__ import annotations

import csv
import json
import re
import urllib.parse
import urllib.request
from datetime import date
from pathlib import Path

ROOT = Path(__file__).parent
CSV_PATH = ROOT / "weekly-ephemeris-2026.csv"
ALMANACK_PATH = ROOT / "almanack.md"
HORIZONS_API = "https://ssd.jpl.nasa.gov/api/horizons.api"
TARGETS = {
    "uranus": "799",
    "neptune": "899",
    "ceres": "1;",
}
SIGNS = "♈♉♊♋♌♍♎♏♐♑♒♓"
BASE_FIELDS = ["iso_week", "monday_utc", "sun", "moon", "mercury", "venus", "mars", "jupiter", "saturn"]


def horizons_longitudes(command: str) -> list[float]:
    params = {
        "format": "json",
        "COMMAND": f"'{command}'",
        "OBJ_DATA": "'NO'",
        "MAKE_EPHEM": "'YES'",
        "EPHEM_TYPE": "'OBSERVER'",
        "CENTER": "'500@399'",
        "START_TIME": "'2025-12-29 00:00'",
        "STOP_TIME": "'2026-12-29 00:00'",
        "STEP_SIZE": "'7 d'",
        "QUANTITIES": "'31'",
        "CSV_FORMAT": "'YES'",
        "ANG_FORMAT": "'DEG'",
        "CAL_FORMAT": "'CAL'",
        "TIME_DIGITS": "'SECONDS'",
    }
    url = HORIZONS_API + "?" + urllib.parse.urlencode(params)
    request = urllib.request.Request(url, headers={"User-Agent": "Star-Almanack/2026"})
    with urllib.request.urlopen(request, timeout=60) as response:
        payload = json.load(response)
    text = payload.get("result", "")
    if "$$SOE" not in text or "$$EOE" not in text:
        raise RuntimeError(f"Horizons returned no ephemeris for {command}: {text[:500]}")

    lines = text.splitlines()
    header_line = next((line for line in lines if "ObsEcLon" in line), None)
    if not header_line:
        raise RuntimeError(f"Could not find ObsEcLon header for {command}")
    header = [h.strip() for h in next(csv.reader([header_line]))]
    try:
        lon_index = header.index("ObsEcLon")
    except ValueError as exc:
        raise RuntimeError(f"Unexpected Horizons header for {command}: {header}") from exc

    start = lines.index("$$SOE") + 1
    stop = lines.index("$$EOE")
    values = []
    for line in lines[start:stop]:
        if not line.strip():
            continue
        row = next(csv.reader([line]))
        values.append(float(row[lon_index].strip()))
    if len(values) != 53:
        raise RuntimeError(f"Expected 53 weekly Horizons rows for {command}, found {len(values)}")
    return values


def recover_base_rows() -> list[dict[str, str]]:
    """Recover the complete existing 7-body weekly table from almanack.md."""
    text = ALMANACK_PATH.read_text(encoding="utf-8")
    week_matches = list(re.finditer(r"(?m)^## ISO 2026-W(\d{2})\s*$", text))
    if len(week_matches) != 53:
        raise RuntimeError(f"Expected 53 Almanack week sections, found {len(week_matches)}")

    rows = []
    for i, match in enumerate(week_matches):
        week = int(match.group(1))
        end = week_matches[i + 1].start() if i + 1 < len(week_matches) else len(text)
        section = text[match.start():end]
        table = re.search(
            r"(?ms)\|\s*☉ Sun\s*\|\s*☽ Moon\s*\|\s*☿ Mercury\s*\|\s*♀ Venus\s*\|\s*♂ Mars\s*\|\s*♃ Jupiter\s*\|\s*♄ Saturn\s*\|"
            r"\s*\n\s*\|[^\n]+\|\s*\n\s*\|\s*([^\n]+?)\s*\|",
            section,
        )
        if not table:
            raise RuntimeError(f"Could not recover the 7-body ephemeris table for 2026-W{week:02d}")
        values = [cell.strip() for cell in table.group(1).split("|")]
        if len(values) != 7:
            raise RuntimeError(f"Expected 7 base values for 2026-W{week:02d}, found {len(values)}")
        monday = date.fromisocalendar(2026, week, 1)
        row = {
            "iso_week": f"2026-W{week:02d}",
            "monday_utc": monday.isoformat(),
        }
        for field, value in zip(BASE_FIELDS[2:], values):
            row[field] = value
        rows.append(row)
    return rows


def zodiac(longitude_deg: float) -> str:
    total_minutes = int(round((longitude_deg % 360.0) * 60.0)) % (360 * 60)
    sign_index, within = divmod(total_minutes, 30 * 60)
    degrees, minutes = divmod(within, 60)
    return f"{SIGNS[sign_index]} {degrees}°{minutes:02d}′"


def main() -> None:
    with CSV_PATH.open(encoding="utf-8", newline="") as f:
        current_rows = list(csv.DictReader(f))
        current_fields = list(current_rows[0].keys()) if current_rows else []
    if current_fields[:9] != BASE_FIELDS:
        raise SystemExit(f"Unexpected weekly ephemeris columns: {current_fields}")

    rows = current_rows if len(current_rows) == 53 else recover_base_rows()
    if len(current_rows) != 53:
        print(f"Recovered full 53-week base ephemeris from almanack.md (CSV had {len(current_rows)} rows)")

    generated = {name: horizons_longitudes(command) for name, command in TARGETS.items()}
    for i, row in enumerate(rows):
        for name in TARGETS:
            row[name] = zodiac(generated[name][i])

    fields = BASE_FIELDS + ["uranus", "neptune", "ceres"]
    with CSV_PATH.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)

    print("Extended weekly-ephemeris-2026.csv: 53 weeks × Uranus, Neptune, Ceres from JPL Horizons")


if __name__ == "__main__":
    main()
