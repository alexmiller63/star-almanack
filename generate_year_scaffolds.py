#!/usr/bin/env python3
"""Create clean ISO-year Star Almanack scaffolds from calendar rules."""
from __future__ import annotations

import argparse
import datetime as dt
from pathlib import Path

from iso_week_range import IsoWeekRange, range_from_legacy_years

ROOT = Path(__file__).resolve().parent
OWNED_SECTIONS = (
    ("calendar", "Calendar"),
    ("ephemeris", "Weekly Solar-System Ephemeris"),
    ("sky-note", "Sky Note"),
    ("planet-finder", "Planet Finder"),
    ("artwork", "Artwork"),
)


def iso_week_count(year: int) -> int:
    return dt.date(year, 12, 28).isocalendar().week


def civil_label(day: dt.date) -> str:
    return f"{day.strftime('%b')} {day.day:02d}, {day.year}"


def section(owner: str, title: str) -> str:
    return (
        f"### {title}\n\n"
        f"<!-- BEGIN GENERATED: {owner} -->\n"
        f"<!-- owner: {owner}; generator must replace this entire block -->\n"
        f"<!-- END GENERATED: {owner} -->"
    )


def render_year(year: int, weeks: tuple[int, ...] | None = None) -> str:
    selected = weeks or tuple(range(1, iso_week_count(year) + 1))
    parts = [
        f"# Star Almanack — ISO {year}",
        "",
        "## Working Integrated Almanack",
        "",
        (
            "This file is a generated year scaffold. It contains only structure derived "
            "from ISO 8601 calendar rules; content generators own and recreate their "
            "marked sections."
        ),
        "",
        f"**ISO weeks:** {len(selected)}",
    ]
    for week in selected:
        monday = dt.date.fromisocalendar(year, week, 1)
        sunday = dt.date.fromisocalendar(year, week, 7)
        parts.extend(
            [
                "",
                f"## ISO {year}-W{week:02d}",
                "",
                f"**ISO dates:** {year}-W{week:02d}-1 through {year}-W{week:02d}-7  ",
                "",
                f"**Civil dates:** {civil_label(monday)} – {civil_label(sunday)}",
            ]
        )
        for owner, title in OWNED_SECTIONS:
            parts.extend(["", section(owner, title)])
    return "\n".join(parts) + "\n"


def generate(start_year: int, end_year: int | None, output_dir: Path) -> list[Path]:
    final_year = start_year if end_year is None else end_year
    if not 1 <= start_year <= 9999 or not 1 <= final_year <= 9999:
        raise ValueError("Years must be between 1 and 9999")
    if final_year < start_year:
        raise ValueError("End year cannot be earlier than start year")

    output_dir.mkdir(parents=True, exist_ok=True)
    written = []
    for year in range(start_year, final_year + 1):
        target = output_dir / f"almanack-{year}.md"
        content = render_year(year)
        temporary = target.with_suffix(".md.tmp")
        temporary.write_text(content, encoding="utf-8")
        temporary.replace(target)
        written.append(target)
        print(f"Recreated {target.relative_to(ROOT)} with {iso_week_count(year)} ISO weeks")
    return written


def generate_range(week_range: IsoWeekRange, output_dir: Path) -> list[Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    written = []
    for year, weeks in week_range.by_year().items():
        target = output_dir / f"almanack-{year}.md"
        temporary = target.with_suffix(".md.tmp")
        temporary.write_text(render_year(year, weeks), encoding="utf-8")
        temporary.replace(target)
        written.append(target)
        print(f"Recreated {target.relative_to(ROOT)} for {year}-W{weeks[0]:02d} through {year}-W{weeks[-1]:02d}")
    return written


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("first", help="First ISO week (YYYY-Www), or legacy start year")
    parser.add_argument("last", nargs="?", help="Last ISO week (YYYY-Www), or legacy end year")
    parser.add_argument("--output-dir", type=Path, default=ROOT / "year-scaffolds")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if "-W" in args.first:
        generate_range(IsoWeekRange.parse(args.first, args.last), args.output_dir)
    else:
        legacy = range_from_legacy_years(int(args.first), int(args.last) if args.last else None)
        generate_range(legacy, args.output_dir)


if __name__ == "__main__":
    main()
