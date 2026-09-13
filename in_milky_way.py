#!/usr/bin/env python3
"""Return YES or NO for whether an equatorial coordinate is in the Milky Way.

Usage:
    python in_milky_way.py RA_HOURS DEC_DEGREES

The classification uses the frozen Star Almanack Milky Way boundary in
``data/milky-way/vieira-outer.json``. Boundary points count as inside.
"""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from typing import Sequence

BOUNDARY_PATH = Path(__file__).resolve().parent / "data" / "milky-way" / "vieira-outer.json"
EPS = 1e-9

Ring = Sequence[Sequence[float]]


def _point_on_segment(px: float, py: float, ax: float, ay: float, bx: float, by: float) -> bool:
    cross = (px - ax) * (by - ay) - (py - ay) * (bx - ax)
    scale = max(1.0, abs(px), abs(py), abs(ax), abs(ay), abs(bx), abs(by))
    if abs(cross) > EPS * scale:
        return False
    return (
        min(ax, bx) - EPS <= px <= max(ax, bx) + EPS
        and min(ay, by) - EPS <= py <= max(ay, by) + EPS
    )


def _ring_contains(ring: Ring, lon_deg: float, dec_deg: float) -> bool:
    """Boundary-inclusive point-in-ring in the source GeoJSON plane."""
    if len(ring) < 3:
        return False

    inside = False
    for i, (ax_raw, ay_raw) in enumerate(ring):
        bx_raw, by_raw = ring[(i + 1) % len(ring)]
        ax, ay = float(ax_raw), float(ay_raw)
        bx, by = float(bx_raw), float(by_raw)

        if _point_on_segment(lon_deg, dec_deg, ax, ay, bx, by):
            return True

        if (ay > dec_deg) != (by > dec_deg):
            x_cross = ax + (dec_deg - ay) * (bx - ax) / (by - ay)
            if abs(x_cross - lon_deg) <= EPS:
                return True
            if x_cross > lon_deg:
                inside = not inside

    return inside


def _polygon_contains(rings: Sequence[Ring], lon_deg: float, dec_deg: float) -> bool:
    if not rings or not _ring_contains(rings[0], lon_deg, dec_deg):
        return False
    return not any(_ring_contains(hole, lon_deg, dec_deg) for hole in rings[1:])


def _geometry_contains(geometry: dict, lon_deg: float, dec_deg: float) -> bool:
    kind = geometry.get("type")
    coordinates = geometry.get("coordinates", [])
    if kind == "Polygon":
        return _polygon_contains(coordinates, lon_deg, dec_deg)
    if kind == "MultiPolygon":
        return any(_polygon_contains(polygon, lon_deg, dec_deg) for polygon in coordinates)
    raise ValueError(f"Unsupported geometry type: {kind!r}")


def _ra_to_geojson_lon(ra_hours: float) -> float:
    """Map RA hours to d3-celestial's [-180, 180] GeoJSON longitude."""
    ra_deg = (ra_hours % 24.0) * 15.0
    return ra_deg if ra_deg <= 180.0 else ra_deg - 360.0


def in_milky_way(ra_hours: float, dec_degrees: float, boundary_path: Path = BOUNDARY_PATH) -> bool:
    """Return True when the coordinate lies in the frozen Milky Way region."""
    if not math.isfinite(ra_hours) or not math.isfinite(dec_degrees):
        raise ValueError("RA and declination must be finite numbers")
    if not -90.0 <= dec_degrees <= 90.0:
        raise ValueError("Declination must be between -90 and +90 degrees")

    lon_deg = _ra_to_geojson_lon(ra_hours)
    data = json.loads(boundary_path.read_text(encoding="utf-8"))
    return _geometry_contains(data["geometry"], lon_deg, dec_degrees)


def main() -> int:
    parser = argparse.ArgumentParser(description="Answer whether an RA/Dec coordinate is in the Milky Way.")
    parser.add_argument("ra_hours", type=float, help="right ascension in decimal hours")
    parser.add_argument("dec_degrees", type=float, help="declination in decimal degrees")
    args = parser.parse_args()

    try:
        result = in_milky_way(args.ra_hours, args.dec_degrees)
    except (OSError, KeyError, ValueError, json.JSONDecodeError) as exc:
        parser.error(str(exc))

    print("YES" if result else "NO")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
