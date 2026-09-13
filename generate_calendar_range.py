#!/usr/bin/env python3
"""Generate only the requested weekly calendar pages using the existing publisher."""
from __future__ import annotations

import argparse
from pathlib import Path

import publish_weekly_pages as publisher
from generator_week_range import resolve


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("start_year", type=int)
    parser.add_argument("start_week", type=int)
    parser.add_argument("end_year", nargs="?", default="")
    parser.add_argument("end_week", nargs="?", default="")
    args = parser.parse_args()

    requested = resolve(args.start_year, args.start_week, args.end_year, args.end_week)
    if any(year != 2026 for year, _ in requested):
        raise SystemExit("Calendar source currently contains ISO year 2026 only")

    text = publisher.SOURCE.read_text(encoding="utf-8")
    matches = list(publisher.WEEK_RE.finditer(text))
    by_week = {int(match.group(2)): (idx, match) for idx, match in enumerate(matches)}
    if len(matches) != 53:
        raise SystemExit(f"Expected 53 ISO 2026 week sections, found {len(matches)}")

    publisher.OUT.mkdir(parents=True, exist_ok=True)
    generated = []
    for _, week in requested:
        idx, match = by_week[week]
        start = match.start()
        if idx + 1 < len(matches):
            end = matches[idx + 1].start()
        else:
            next_h2 = publisher.H2_RE.search(text, match.end())
            end = next_h2.start() if next_h2 else len(text)
        section = text[start:end].strip()
        fragment = publisher.markdown_fragment(section)
        target = publisher.OUT / f"W{week:02d}"
        target.mkdir(parents=True, exist_ok=True)
        (target / "index.html").write_text(
            publisher.page_shell(f"ISO 2026-W{week:02d}", fragment, publisher.week_nav(week)),
            encoding="utf-8",
        )
        generated.append(f"2026-W{week:02d}")

    print("Generated calendar pages:", ", ".join(generated))


if __name__ == "__main__":
    main()
