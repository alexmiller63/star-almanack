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
ANGLE_EPS = 1e-8

Vector = tuple[float, float, float]
Ring = Sequence[Sequence[float]]


def _dot(a: Vector, b: Vector) -> float:
    return a[0] * b[0] + a[1] * b[1] + a[2] * b[2]


def _cross(a: Vector, b: Vector) -> Vector:
    return (
        a[1] * b[2] - a[2] * b[1],
        a[2] * b[0] - a[0] * b[2],
        a[0] * b[1] - a[1] * b[0],
    )


def _norm(v: Vector) -> float:
    return math.sqrt(_dot(v, v))


def _unit(v: Vector) -> Vector:
    n = _norm(v)
    if n == 0.0:
        raise ValueError("zero-length vector")
    return (v[0] / n, v[1] / n, v[2] / n)


def _radec_vector(lon_deg: float, dec_deg: float) -> Vector:
    lon = math.radians(lon_deg)
    dec = math.radians(dec_deg)
    c = math.cos(dec)
    return (c * math.cos(lon), c * math.sin(lon), math.sin(dec))


def _angle(a: Vector, b: Vector) -> float:
    return math.atan2(_norm(_cross(a, b)), max(-1.0, min(1.0, _dot(a, b))))


def _point_on_arc(q: Vector, a: Vector, b: Vector) -> bool:
    ab = _angle(a, b)
    aq = _angle(a, q)
    qb = _angle(q, b)
    return abs((aq + qb) - ab) <= ANGLE_EPS


def _ring_contains(ring: Ring, query_lon_deg: float, query_dec_deg: float) -> bool:
    """Boundary-inclusive spherical winding test for one GeoJSON ring."""
    if len(ring) < 3:
        return False

    q = _radec_vector(query_lon_deg, query_dec_deg)
    vertices = [_radec_vector(float(lon), float(dec)) for lon, dec in ring]

    winding = 0.0
    for i, a in enumerate(vertices):
        b = vertices[(i + 1) % len(vertices)]
        if _point_on_arc(q, a, b):
            return True

        da = _dot(q, a)
        db = _dot(q, b)
        ta = (a[0] - da * q[0], a[1] - da * q[1], a[2] - da * q[2])
        tb = (b[0] - db * q[0], b[1] - db * q[1], b[2] - db * q[2])
        if _norm(ta) < 1e-15 or _norm(tb) < 1e-15:
            return True
        ta = _unit(ta)
        tb = _unit(tb)
        winding += math.atan2(_dot(q, _cross(ta, tb)), _dot(ta, tb))

    return abs(winding) > math.pi


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
