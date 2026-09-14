#!/usr/bin/env python3
"""Recreate Calendar owner blocks from calculated calendar-event JSON."""
from __future__ import annotations

import argparse
import datetime as dt
import json
from pathlib import Path

from scaffold_sections import iso_week_count, replace_owner_blocks, scaffold_weeks, write_atomic

ROOT = Path(__file__).resolve().parent
SIGN_NAMES = {
    "♈": "Aries", "♉": "Taurus", "♊": "Gemini", "♋": "Cancer",
    "♌": "Leo", "♍": "Virgo", "♎": "Libra", "♏": "Scorpio",
    "♐": "Sagittarius", "♑": "Capricorn", "♒": "Aquarius", "♓": "Pisces",
}


def parse_moment(value: str) -> dt.datetime:
    return dt.datetime.fromisoformat(value.replace("Z", "+00:00"))


def load_events(source_dir: Path, days: list[dt.date]) -> tuple[list[dict], list[dict]]:
    ingresses: list[dict] = []
    phases: list[dict] = []
    required = {day.year for day in days}

    def add_year(year: int) -> None:
        path = source_dir / f"calendar-events-{year}.json"
        if not path.exists():
            raise FileNotFoundError(f"Missing authoritative calendar-event input: {path}")
        payload = json.loads(path.read_text(encoding="utf-8"))
        if payload.get("year") != year or payload.get("schema") != "star-almanack.calendar-events.v1":
            raise ValueError(f"Invalid calendar-event input: {path}")
        ingresses.extend(payload["zodiac_ingresses"])
        phases.extend(payload["lunar_phases"])

    for year in sorted(required):
        add_year(year)
    if not any(parse_moment(item["utc"]).date() <= min(days) for item in ingresses):
        add_year(min(required) - 1)
    ingresses.sort(key=lambda item: item["utc"])
    phases.sort(key=lambda item: item["utc"])
    return ingresses, phases


def render_calendar(year: int, source_dir: Path, weeks: tuple[int, ...] | None = None) -> dict[int, str]:
    selected = weeks or tuple(range(1, iso_week_count(year) + 1))
    days = [
        dt.date.fromisocalendar(year, week, weekday)
        for week in selected
        for weekday in range(1, 8)
    ]
    ingresses, phases = load_events(source_dir, days)
    boundaries = [(parse_moment(item["utc"]).date(), item) for item in ingresses]
    events: dict[dt.date, list[str]] = {}
    for item in ingresses:
        moment = parse_moment(item["utc"])
        events.setdefault(moment.date(), []).append(
            f"☉ enters {item['symbol']} ({item['name']}) — {moment:%H:%M:%S} UTC"
        )
    for item in phases:
        moment = parse_moment(item["utc"])
        events.setdefault(moment.date(), []).append(
            f"{item['symbol']} {item['name']} — {moment:%H:%M:%S} UTC"
        )

    rendered: dict[int, str] = {}
    for week in selected:
        rows = []
        for weekday in range(1, 8):
            day = dt.date.fromisocalendar(year, week, weekday)
            prior = [boundary for boundary in boundaries if boundary[0] <= day]
            if not prior:
                raise RuntimeError(f"No zodiac ingress available on or before {day}")
            ingress_day, ingress = prior[-1]
            zodiac_day = (day - ingress_day).days + 1
            zodiac = f"{ingress['symbol']} ({SIGN_NAMES[ingress['symbol']]}) {zodiac_day}" if zodiac_day == 1 else f"{ingress['symbol']} {zodiac_day}"
            event_text = "<br>".join(events.get(day, ["—"]))
            rows.append(f"| {day:%a, %b %d, %Y} | {zodiac} | {event_text} |")
        rendered[week] = "| Date | Zodiac day | Events |\n|---|---|---|\n" + "\n".join(rows)
    return rendered


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("year", type=int)
    parser.add_argument("--root", type=Path, default=ROOT)
    args = parser.parse_args()
    scaffold = args.root / "year-scaffolds" / f"almanack-{args.year}.md"
    if not scaffold.exists():
        raise SystemExit(f"Missing scaffold: {scaffold}")
    text = scaffold.read_text(encoding="utf-8")
    selected = scaffold_weeks(text, args.year)
    blocks = render_calendar(args.year, args.root, selected)
    updated = replace_owner_blocks(
        text, args.year, "calendar", blocks.__getitem__
    )
    write_atomic(scaffold, updated)
    print(f"Recreated {len(blocks)} Calendar blocks for {args.year}")


if __name__ == "__main__":
    main()
