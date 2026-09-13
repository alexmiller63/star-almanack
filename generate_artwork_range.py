#!/usr/bin/env python3
"""Render accepted constellation artwork for the requested ISO weeks."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from generator_week_range import resolve
from render_stellar_finders import load_hyg, render_figure

ROOT = Path(__file__).parent
DESCRIPTORS = ROOT / "sky-note-artwork-descriptors-2026.json"
FIGURES = ROOT / "constellation-figures.json"
OUT_ROOT = ROOT / "observer-views"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("hyg_catalog", type=Path)
    parser.add_argument("start_year", type=int)
    parser.add_argument("start_week", type=int)
    parser.add_argument("end_year", nargs="?", default="")
    parser.add_argument("end_week", nargs="?", default="")
    args = parser.parse_args()

    requested = resolve(args.start_year, args.start_week, args.end_year, args.end_week)
    if any(year != 2026 for year, _ in requested):
        raise SystemExit("Artwork descriptors currently exist for ISO year 2026 only")

    descriptor_data = json.loads(DESCRIPTORS.read_text(encoding="utf-8"))
    figures = json.loads(FIGURES.read_text(encoding="utf-8"))
    stars = load_hyg(args.hyg_catalog)
    by_week: dict[str, list[dict]] = {}
    for descriptor in descriptor_data.get("descriptors", []):
        by_week.setdefault(descriptor["week"], []).append(descriptor)

    rendered = []
    for year, week_number in requested:
        week = f"W{week_number:02d}"
        descriptors = by_week.get(week, [])
        if not descriptors:
            print(f"{year}-{week}: no accepted-figure artwork descriptor; nothing to render")
            continue
        out_dir = OUT_ROOT / str(year) / week
        seen = set()
        for descriptor in descriptors:
            figure_name = descriptor["constellation"]
            if figure_name in seen:
                continue
            if figure_name not in figures:
                raise SystemExit(f"Descriptor references unknown accepted figure: {figure_name}")
            seen.add(figure_name)
            for path in render_figure(figure_name, figures[figure_name], stars, out_dir):
                rendered.append(str(path))
                print(f"wrote {path}")

    print(f"Rendered {len(rendered)} artwork file(s)")


if __name__ == "__main__":
    main()
