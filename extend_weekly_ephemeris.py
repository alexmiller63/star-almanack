#!/usr/bin/env python3
"""Extend the 2026 weekly ephemeris with Uranus, Neptune, and Ceres.

The existing Sun-through-Saturn columns remain untouched.  The 3 added
observer-oriented bodies are obtained from NASA/JPL Horizons as apparent,
geocentric, ecliptic-of-date longitudes (Horizons observer quantity 31),
sampled at the Almanack standard epoch: Monday 00:00 UTC.

Targets:
    799  Uranus
    899  Neptune
    1;   Ceres (small-body syntax; the semicolon is significant)

The generated values are rounded to the nearest arcminute and rendered in
the same zodiac-sign notation as the existing weekly ephemeris.
"""
from __future__ import annotations

import csv
import io
import json
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).parent
CSV_PATH = ROOT / "weekly-ephemeris-2026.csv"
HORIZONS_API = "https://ssd.jpl.nasa.gov/api/horizons.api"
TARGETS = {
    "uranus": "799",
    "neptune": "899",
    "ceres": "1;",
}
SIGNS = "♈♉♊♋♌♍♎♏♐♑♒♓"


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
    header = next(csv.reader([header_line]))
    header = [h.strip() for h in header]
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


def zodiac(longitude_deg: float) -> str:
    total_minutes = int(round((longitude_deg % 360.0) * 60.0)) % (360 * 60)
    sign_index, within = divmod(total_minutes, 30 * 60)
    degrees, minutes = divmod(within, 60)
    return f"{SIGNS[sign_index]} {degrees}°{minutes:02d}′"


def main() -> None:
    with CSV_PATH.open(encoding="utf-8", newline="") as f:
        rows = list(csv.DictReader(f))
        original_fields = list(rows[0].keys()) if rows else []
    if len(rows) != 53:
        raise SystemExit(f"Expected 53 weekly rows, found {len(rows)}")

    expected_prefix = ["iso_week", "monday_utc", "sun", "moon", "mercury", "venus", "mars", "jupiter", "saturn"]
    if original_fields[:9] != expected_prefix:
        raise SystemExit(f"Unexpected weekly ephemeris columns: {original_fields}")

    generated = {name: horizons_longitudes(command) for name, command in TARGETS.items()}
    for i, row in enumerate(rows):
        for name in TARGETS:
            row[name] = zodiac(generated[name][i])

    fields = expected_prefix + ["uranus", "neptune", "ceres"]
    with CSV_PATH.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)

    print("Extended weekly-ephemeris-2026.csv: 53 weeks × Uranus, Neptune, Ceres from JPL Horizons")


if __name__ == "__main__":
    main()
