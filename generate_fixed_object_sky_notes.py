#!/usr/bin/env python3
"""Generate deterministic fixed-object Sky Notes for one or more ISO years.

The output is observer-first prose for naked-eye, binocular, and telescope
observing. Best-visibility dates are recalculated independently for every
requested ISO year from each object's right ascension and the Star Almanack
observer-first rule. No generated year's output is reused as source.
"""

from __future__ import annotations

import argparse
import csv
import datetime as dt
from pathlib import Path
from typing import Any

import yaml

from in_milky_way import in_milky_way
from compute_bayer_visibility_2026 import apparent_sun_ra_hours, wrapped_hour_distance

GALAXY_TYPES = {"SG", "BG", "LG", "EG", "IG"}


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


def iso_week_date(value: dt.date) -> str:
    iso = value.isocalendar()
    return f"{iso.year}-W{iso.week:02d}-{iso.weekday}"


def best_visibility_for_iso_year(ra_object_h: float, iso_year: int) -> tuple[dt.datetime, dt.date]:
    """Solve α☉ = αobject − 9h inside the requested ISO week-year."""
    target = (ra_object_h - 9.0) % 24.0
    first_day = dt.date.fromisocalendar(iso_year, 1, 1)
    last_week = dt.date(iso_year, 12, 28).isocalendar().week
    last_day = dt.date.fromisocalendar(iso_year, last_week, 7)
    start = dt.datetime.combine(first_day, dt.time.min) - dt.timedelta(hours=12)
    end = dt.datetime.combine(last_day, dt.time.max) + dt.timedelta(hours=12)

    candidates: list[tuple[float, dt.datetime]] = []
    current = start
    while current <= end:
        rounded = (current + dt.timedelta(hours=12)).date()
        if rounded.isocalendar().year == iso_year:
            candidates.append((
                wrapped_hour_distance(apparent_sun_ra_hours(current), target),
                current,
            ))
        current += dt.timedelta(hours=6)
    if not candidates:
        raise RuntimeError(f"No visibility candidates for ISO {iso_year}")

    _, coarse = min(candidates)
    best_distance = float("inf")
    best_time: dt.datetime | None = None
    current = max(start, coarse - dt.timedelta(hours=8))
    refine_end = min(end, coarse + dt.timedelta(hours=8))
    while current <= refine_end:
        rounded = (current + dt.timedelta(hours=12)).date()
        if rounded.isocalendar().year == iso_year:
            distance = wrapped_hour_distance(apparent_sun_ra_hours(current), target)
            if distance < best_distance:
                best_distance = distance
                best_time = current
        current += dt.timedelta(minutes=1)
    if best_time is None:
        raise RuntimeError(f"Could not refine visibility solution for ISO {iso_year}")

    rounded_date = (best_time + dt.timedelta(hours=12)).date()
    return best_time, rounded_date

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


def generate_year(data: dict[str, Any], output: Path, iso_year: int) -> tuple[int, int]:
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
            # Presence in the dated source catalog determines eligibility; the
            # stored 2026 date does not determine another year's placement.
            if not r.get("best") or not r.get("iso"):
                continue

            ra = float(r["ra_h"])
            dec = float(r["dec_deg"])
            _, best_date = best_visibility_for_iso_year(ra, iso_year)
            iso = iso_week_date(best_date)
            if not iso.startswith(f"{iso_year}-W"):
                raise RuntimeError(f"Visibility date escaped ISO {iso_year}: {best_date}")

            inside = in_milky_way(ra, dec)
            naked, binocular, telescope = notes_for(category, r, inside)
            mw_count += int(inside)
            rows_out.append(
                {
                    "category": category,
                    "object": identity(category, r),
                    "name": display_name(category, r),
                    "constellation": str(r.get("con") or ""),
                    "best": best_date.isoformat(),
                    "iso": iso,
                    "in_milky_way": "yes" if inside else "no",
                    "naked_eye": naked,
                    "binoculars": binocular,
                    "telescope": telescope,
                }
            )

    rows_out.sort(key=lambda r: (r["iso"], r["category"], r["object"], r["constellation"]))
    output.parent.mkdir(parents=True, exist_ok=True)
    # Regenerative ownership: truncate and recreate the complete yearly file.
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


def generate(source: Path, output_dir: Path, start_year: int, end_year: int) -> dict[int, tuple[int, int]]:
    if end_year < start_year:
        raise ValueError("end year must not precede start year")
    data = yaml.safe_load(source.read_text(encoding="utf-8"))
    results: dict[int, tuple[int, int]] = {}
    for iso_year in range(start_year, end_year + 1):
        output = output_dir / f"fixed-object-sky-notes-{iso_year}.csv"
        results[iso_year] = generate_year(data, output, iso_year)
    return results

def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=Path, default=Path("fixed-objects.yaml"))
    parser.add_argument("--output-dir", type=Path, default=Path("."))
    parser.add_argument("--start-year", type=int, default=2026)
    parser.add_argument("--end-year", type=int)
    args = parser.parse_args()
    end_year = args.start_year if args.end_year is None else args.end_year
    results = generate(args.source, args.output_dir, args.start_year, end_year)
    for year, (total, mw_count) in results.items():
        print(f"year={year} notes={total} in_milky_way={mw_count}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
