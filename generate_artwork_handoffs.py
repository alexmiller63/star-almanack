#!/usr/bin/env python3
"""Derive authoritative yearly artwork handoffs from observing descriptors."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from iso_week_range import IsoWeekRange

ROOT = Path(__file__).resolve().parent


def generate(week_range: IsoWeekRange, root: Path) -> list[Path]:
    figures = json.loads((root / "constellation-figures.json").read_text(encoding="utf-8"))
    figure_by_abbr = {value["constellation"]: (name, value) for name, value in figures.items()}
    written = []
    for year, weeks in week_range.by_year().items():
        descriptor_root = root / f"observing-descriptors-{year}"
        descriptors = []
        for week in weeks:
            week_id = f"W{week:02d}"
            week_payload = json.loads((descriptor_root / f"{week_id}.json").read_text(encoding="utf-8"))
            selected: dict[str, list[str]] = {}
            for record in week_payload.get("linked_descriptors", []):
                obj = json.loads((descriptor_root / record["href"]).read_text(encoding="utf-8"))
                abbr = obj.get("identity", {}).get("constellation")
                if abbr in figure_by_abbr:
                    selected.setdefault(abbr, []).append(obj["identity"].get("display_name", ""))
            for abbr, names in sorted(selected.items()):
                constellation, figure = figure_by_abbr[abbr]
                haystack = " ".join(names).casefold()
                featured = [
                    item["name"] for item in figure.get("asterisms", [])
                    if item["name"].casefold() in haystack
                    or (constellation == "Pegasus" and item["name"] == "Great Square of Pegasus")
                ]
                targets = []
                for name in [figure.get("target_name"), *(item.get("name") for item in figure.get("deep_sky_objects", []))]:
                    if name and name.casefold() in haystack:
                        targets.append(name)
                descriptors.append({
                    "week": week_id,
                    "constellation": constellation,
                    "figure_source": "constellation-figures.json",
                    "figure_standard": "accepted Martz/MacRobert stick figure",
                    "constellation_line_color": "blue",
                    "featured_asterism_color": "green",
                    "featured_asterisms": featured,
                    "circle_targets": targets,
                    "instructions": "Use the accepted figure paths exactly; do not invent a replacement stick figure. Draw the constellation in blue, emphasize the featured asterism in green, and circle named observing targets when present.",
                })
        payload = {"year": year, "purpose": "Sky Notes artwork-generator handoff", "descriptors": descriptors}
        target = root / f"sky-note-artwork-descriptors-{year}.json"
        temporary = target.with_suffix(".json.tmp")
        temporary.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        temporary.replace(target)
        written.append(target)
        print(f"Recreated {target.name} with {len(descriptors)} artwork handoffs")
    return written


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("first_iso_week")
    parser.add_argument("last_iso_week")
    parser.add_argument("--root", type=Path, default=ROOT)
    args = parser.parse_args()
    generate(IsoWeekRange.parse(args.first_iso_week, args.last_iso_week), args.root)


if __name__ == "__main__":
    main()
