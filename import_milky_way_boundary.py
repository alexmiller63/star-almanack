#!/usr/bin/env python3
"""Download and freeze the Star Almanack Milky Way boundary.

The Star Almanack operational definition of "in the Milky Way" is the
outermost visible contour (feature id ``ol1``) from d3-celestial's ``mw.json``,
which is based on José R. Vieira's Milky Way outline catalog.

This importer is intended to be run only when intentionally refreshing the
frozen local boundary. Normal classification is entirely offline.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from urllib.request import urlopen

SOURCE_COMMIT = "7e720a3de062059d4c5400a379146a601d9010e0"
SOURCE_URL = (
    "https://raw.githubusercontent.com/ofrohn/d3-celestial/"
    f"{SOURCE_COMMIT}/data/mw.json"
)
FEATURE_ID = "ol1"
DEFAULT_OUTPUT = Path(__file__).resolve().parent / "data" / "milky-way" / "vieira-outer.json"


def main() -> int:
    parser = argparse.ArgumentParser(description="Freeze the selected Milky Way boundary locally.")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()

    with urlopen(SOURCE_URL, timeout=60) as response:
        raw = response.read()

    source = json.loads(raw)
    feature = next((f for f in source.get("features", []) if f.get("id") == FEATURE_ID), None)
    if feature is None:
        raise SystemExit(f"Feature {FEATURE_ID!r} not found in source data")

    geometry = feature.get("geometry")
    if not geometry or geometry.get("type") not in {"Polygon", "MultiPolygon"}:
        raise SystemExit(f"Unexpected geometry for {FEATURE_ID!r}: {geometry!r}")

    frozen = {
        "definition": "Star Almanack Milky Way bounded region",
        "rule": "inside the d3-celestial/Vieira outermost visible contour (feature ol1)",
        "boundary_inclusive": True,
        "coordinate_system": "equatorial longitude/declination in degrees; longitude = RA * 15",
        "source": {
            "project": "d3-celestial",
            "repository": "ofrohn/d3-celestial",
            "commit": SOURCE_COMMIT,
            "path": "data/mw.json",
            "feature_id": FEATURE_ID,
            "url": SOURCE_URL,
            "sha256": hashlib.sha256(raw).hexdigest(),
            "catalog_credit": "José R. Vieira Milky Way Outline Catalog",
        },
        "geometry": geometry,
    }

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(frozen, separators=(",", ":")) + "\n", encoding="utf-8")
    print(args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
