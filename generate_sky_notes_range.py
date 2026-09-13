#!/usr/bin/env python3
"""Apply Sky Notes only to the requested ISO weeks and refresh their artwork descriptors."""
from __future__ import annotations

import argparse
import json
import re

import apply_sky_notes as sky
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
        raise SystemExit("Sky Notes source currently contains ISO year 2026 only")
    selected = {f"W{week:02d}" for _, week in requested}

    text = sky.ALMANACK.read_text(encoding="utf-8")
    weeks = sky.load_notes()
    messier_catalog = sky.load_messier_catalog()
    planetary = sky.load_planetary_context()

    enriched_notes: dict[str, str] = {}
    for week in sorted(selected):
        payload = weeks[week]
        note = payload.get("note", "").strip()
        if not re.fullmatch(r"W(?:0[1-9]|[1-4]\d|5[0-3])", week):
            raise SystemExit(f"Invalid week key: {week}")
        if not note:
            raise SystemExit(f"Empty note for {week}")
        if note == sky.PLACEHOLDER_NOTE:
            raise SystemExit(f"Placeholder Sky Note survived for {week}")
        note = sky.enrich_observer_note(week, note, planetary)
        note = sky.expand_messier_mentions(note, messier_catalog)
        enriched_notes[week] = note
        text = sky.replace_week_note(text, week, note)

    sky.ALMANACK.write_text(text, encoding="utf-8")

    figures = json.loads(sky.CONSTELLATION_FIGURES.read_text(encoding="utf-8"))
    if sky.ARTWORK_DESCRIPTORS.exists():
        output = json.loads(sky.ARTWORK_DESCRIPTORS.read_text(encoding="utf-8"))
    else:
        output = {"year": 2026, "purpose": "Sky Notes artwork-generator handoff", "descriptors": []}
    retained = [d for d in output.get("descriptors", []) if d.get("week") not in selected]
    refreshed = []
    for week in sorted(selected):
        descriptor = sky.artwork_descriptor_for(week, weeks[week].get("note", ""), figures)
        if descriptor:
            refreshed.append(descriptor)
    output["year"] = 2026
    output["purpose"] = "Sky Notes artwork-generator handoff"
    output["descriptors"] = sorted(retained + refreshed, key=lambda d: (d.get("week", ""), d.get("constellation", "")))
    sky.ARTWORK_DESCRIPTORS.write_text(json.dumps(output, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    labels = [f"{year}-W{week:02d}" for year, week in requested]
    print("Applied Sky Notes:", ", ".join(labels))
    print(f"Refreshed {len(refreshed)} artwork descriptor(s) in the selected range")


if __name__ == "__main__":
    main()
