#!/usr/bin/env python3
"""Generate deterministic 2026 observing notes for fixed Almanack objects.

The output is observer-first prose for three equipment levels: naked eye,
binoculars, and telescope. It is generated from the authoritative fixed-object
catalog plus the frozen Milky Way boundary; no network access is required.

This is an ISO-year publication layer. Some legacy catalog rows store a full
ISO week date (``2026-W08-7``), while Bayer rows store the compact form
(``W08-7``). Compact values are given their ISO week-numbering year from the
stored best-visibility civil date, so year-boundary behavior is not guessed.
"""

from __future__ import annotations

import argparse
import csv
from datetime import date
from pathlib import Path
from typing import Any

import yaml

from in_milky_way import in_milky_way

GALAXY_TYPES = {"SG", "BG", "LG", "EG", "IG"}
TARGET_ISO_YEAR = 2026


def record_from_row(fields: list[str], row: list[Any]) -> dict[str, Any]:
    return dict(zip(fields, row))


def identity(category: str, r: dict[str, Any]) -> str:
    if category == "messier":
        return str(r.get("id") or "")
    if category == "bayer":
        return f"{r.get('bayer', '')} {r.get('con', '')}".strip()
    value = r.get("id") or r.get("catalog") or r.get("name") or ""
    return str(value)


def display_name(category: str, r: dict[str, Any]) -> str:
    ident = identity(category, r)
    name = r.get("name")
    if name and str(name) != ident:
        return f"{ident} — {name}" if ident else str(name)
    return ident


def magnitude(r: dict[str, Any]) -> float | None:
    try:
        value = r.get("mag")
        return None if value in (None, "") else float(value)
    except (TypeError, ValueError):
        return None


def canonical_iso(r: dict[str, Any]) -> str:
    """Return YYYY-Www-d, deriving ISO year for legacy compact values."""
    raw = str(r.get("iso") or "")
    if not raw:
        return ""
    if raw[:4].isdigit() and len(raw) >= 10 and raw[4:6] == "-W":
        return raw
    if not raw.startswith("W"):
        raise ValueError(f"unrecognized ISO week date: {raw!r}")

    best = r.get("best")
    if isinstance(best, date):
        civil = best
    else:
        civil = date.fromisoformat(str(best))
    iso_year = civil.isocalendar().year
    return f"{iso_year}-{raw}"


def milky_way_clause(inside: bool) -> str:
    if inside:
        return " The field lies within the Almanack's visible Milky Way boundary, so the background is especially star-rich."
    return ""


def star_notes(r: dict[str, Any], inside: bool) -> tuple[str, str, str]:
    mag = magnitude(r)
    name = str(r.get("name") or r.get("bayer") or "This star")
    if mag is None:
        naked = f"Use {name} as a naked-eye landmark in its constellation pattern."
    elif mag <= 2.0:
        naked = f"Bright and easy to see unaided; use {name} as a primary landmark for the surrounding constellation."
    elif mag <= 4.0:
        naked = "Readily visible unaided under ordinary dark-sky conditions; identify it from the surrounding constellation pattern."
    elif mag <= 5.5:
        naked = "Visible unaided from a reasonably dark site, but easier after full dark adaptation."
    else:
        naked = "Near or beyond the practical unaided-eye limit for many observers; use optical aid for a reliable identification."

    binocular = (
        "Binoculars isolate the star from the surrounding pattern and make star-hopping easier."
        + milky_way_clause(inside)
    )
    telescope = "A telescope sharpens the local field and helps inspect nearby companions; the star itself remains an unresolved point of light."
    return naked, binocular, telescope


def messier_notes(r: dict[str, Any], inside: bool) -> tuple[str, str, str]:
    obj = str(r.get("id") or "Object")
    code = str(r.get("type") or "")
    mag = magnitude(r)
    mw = milky_way_clause(inside)

    if obj == "M31":
        naked = "Visible as an elongated misty patch from a dark site; use averted vision when skyglow is present."
    elif obj == "M33":
        naked = "A demanding naked-eye target: exceptionally dark, transparent skies and averted vision are usually required."
    elif obj == "M42":
        naked = "Visible unaided as the hazy middle 'star' of Orion's Sword beneath the Belt."
    elif obj == "M45":
        naked = "An obvious compact star group to the unaided eye; count how many Pleiads you can distinguish."
    elif obj == "M44":
        naked = "Visible to the unaided eye as a soft patch in Cancer under a dark sky."
    elif obj == "M24":
        naked = "A conspicuous bright star cloud in a dark summer Milky Way; scan for the dense glow rather than a compact object."
    elif code == "OC":
        if mag is not None and mag <= 4.5:
            naked = "Visible unaided as a small stellar haze or loose knot under a dark sky."
        elif mag is not None and mag <= 5.5:
            naked = "Possible unaided from a dark site as a faint unresolved patch; binoculars make identification much easier."
        else:
            naked = "Not normally a distinct naked-eye object; locate the surrounding constellation first."
    elif code == "GC":
        if mag is not None and mag <= 5.8:
            naked = "At a dark site it can be glimpsed unaided as a tiny diffuse point, especially with averted vision."
        else:
            naked = "Not normally a naked-eye target; use the surrounding star pattern to reach its position."
    elif code in {"DN", "SN"}:
        if mag is not None and mag <= 5.0:
            naked = "A faint diffuse glow can be detected unaided from a genuinely dark site."
        else:
            naked = "Not normally visible as a distinct nebula to the unaided eye."
    elif code == "MW":
        naked = "Best appreciated unaided as a concentrated brightening of the Milky Way rather than as a sharply bounded object."
    elif code in GALAXY_TYPES:
        naked = "Not normally visible to the unaided eye; begin with a star-hop from nearby bright stars."
    elif code in {"PN", "DS", "AS"}:
        naked = "Not normally identifiable as a distinct object to the unaided eye."
    else:
        naked = "Use the surrounding constellation as the naked-eye framework for locating this object."

    if code == "OC":
        binocular = "An excellent binocular target: the cluster separates from the field and its brightest members begin to stand out." + mw
        telescope = "Low to moderate power resolves many more members; use a wide field first so the cluster remains visually coherent."
    elif code == "GC":
        binocular = "Appears as a compact, round glow with a brighter center; steady binocular support improves detection." + mw
        telescope = "Moderate to high power concentrates the core and, with sufficient aperture and good seeing, begins to resolve stars around the outskirts."
    elif code in {"DN", "SN"}:
        binocular = "Look for a low-contrast patch against the surrounding field; dark adaptation matters more than high magnification." + mw
        telescope = "Use low to moderate power to trace the nebular form; a suitable narrowband nebula filter can improve contrast on emission-rich regions."
    elif code == "PN":
        binocular = "Usually stellar or nearly stellar in binoculars; careful comparison with nearby stars is the key." + mw
        telescope = "Moderate to high power reveals the small nebular disk or ring-like structure; a nebula filter can help separate it from the stellar field."
    elif code in GALAXY_TYPES:
        binocular = "Under a dark sky, look for a faint diffuse glow with a brighter central concentration; sky transparency is crucial."
        telescope = "Begin at low power to secure the galaxy, then increase magnification moderately to examine the core, elongation, and any visible structure."
    elif code == "DS":
        binocular = "Binoculars may show the pair as elongated or separated if the components are wide enough." + mw
        telescope = "Use moderate power to separate the components cleanly and compare their relative brightness."
    elif code == "AS":
        binocular = "Binoculars make the small stellar pattern easier to recognize in context." + mw
        telescope = "Low power shows the component stars clearly; keep enough field around them to preserve the pattern."
    elif code == "MW":
        binocular = "Sweep slowly across the star cloud: binoculars break the glow into innumerable stars, knots, and dark lanes." + mw
        telescope = "Use a rich-field, low-power view for selected knots and clusters; high power loses the large-scale star-cloud context."
    else:
        binocular = "Binoculars provide the most useful first optical view and help confirm the surrounding star field." + mw
        telescope = "Start at low power, center the target, and increase magnification only when the object benefits from it."

    return naked, binocular, telescope


def notes_for(category: str, r: dict[str, Any], inside: bool) -> tuple[str, str, str]:
    if category == "messier":
        return messier_notes(r, inside)
    return star_notes(r, inside)


def generate(source: Path, output: Path) -> tuple[int, int]:
    data = yaml.safe_load(source.read_text(encoding="utf-8"))
    schemas = data.get("schema", {})
    rows_out: list[dict[str, str]] = []
    mw_count = 0

    for category, rows in data.items():
        if category in {"edition", "schema"} or not isinstance(rows, list):
            continue
        fields = schemas.get(category)
        if not isinstance(fields, list):
            continue
        if not {"ra_h", "dec_deg", "best", "iso"}.issubset(fields):
            continue

        for row in rows:
            if not isinstance(row, list):
                continue
            r = record_from_row(fields, row)
            if not r.get("best") or not r.get("iso"):
                continue
            iso = canonical_iso(r)
            if not iso.startswith(f"{TARGET_ISO_YEAR}-W"):
                continue

            ra = float(r["ra_h"])
            dec = float(r["dec_deg"])
            inside = in_milky_way(ra, dec)
            naked, binocular, telescope = notes_for(category, r, inside)
            mw_count += int(inside)
            rows_out.append(
                {
                    "category": category,
                    "object": identity(category, r),
                    "name": display_name(category, r),
                    "constellation": str(r.get("con") or ""),
                    "best": str(r.get("best") or ""),
                    "iso": iso,
                    "in_milky_way": "yes" if inside else "no",
                    "naked_eye": naked,
                    "binoculars": binocular,
                    "telescope": telescope,
                }
            )

    rows_out.sort(key=lambda r: (r["iso"], r["category"], r["object"], r["constellation"]))
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=[
                "category", "object", "name", "constellation", "best", "iso",
                "in_milky_way", "naked_eye", "binoculars", "telescope",
            ],
        )
        writer.writeheader()
        writer.writerows(rows_out)

    return len(rows_out), mw_count


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=Path, default=Path("fixed-objects.yaml"))
    parser.add_argument("--output", type=Path, default=Path("fixed-object-sky-notes-2026.csv"))
    args = parser.parse_args()
    total, mw_count = generate(args.source, args.output)
    print(f"notes={total} in_milky_way={mw_count}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
