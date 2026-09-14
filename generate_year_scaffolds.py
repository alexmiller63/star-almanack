#!/usr/bin/env python3
"""Create clean ISO-year Star Almanack scaffolds from calendar rules."""
from __future__ import annotations

import argparse
import calendar
import datetime as dt
from pathlib import Path

ROOT = Path(__file__).resolve().parent
OWNED_SECTIONS = (
    ("calendar", "Calendar"),
    ("solar-system-ephemeris", "Weekly Solar-System Ephemeris"),
    ("sky-note", "Sky Note"),
    ("observing-descriptors", "Observer Descriptors"),
    ("chart", "Chart"),
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


def render_year(year: int) -> str:
    week_count = iso_week_count(year)
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
        f"**ISO weeks:** {week_count}",
    ]
    for week in range(1, week_count + 1):
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


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("start_year", type=int)
    parser.add_argument("end_year", type=int, nargs="?")
    parser.add_argument("--output-dir", type=Path, default=ROOT / "year-scaffolds")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    generate(args.start_year, args.end_year, args.output_dir)


if __name__ == "__main__":
    main()
