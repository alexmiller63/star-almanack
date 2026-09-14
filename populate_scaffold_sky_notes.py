#!/usr/bin/env python3
"""Recreate the Sky Note owner blocks in an ISO-year scaffold."""
from __future__ import annotations

import argparse
import csv
import datetime as dt
import hashlib
import json
import re
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parent
BEGIN = "<!-- BEGIN GENERATED: sky-note -->"
END = "<!-- END GENERATED: sky-note -->"


def week_count(year: int) -> int:
    return dt.date(year, 12, 28).isocalendar().week


def row_week(row: dict[str, str], year: int) -> int:
    match = re.fullmatch(r"(\d{4})-W(\d{2})-[1-7]", row["iso"])
    if not match or int(match.group(1)) != year:
        raise ValueError(f"Invalid ISO date for {year}: {row['iso']!r}")
    return int(match.group(2))


def label(row: dict[str, str]) -> str:
    return row["name"] or row["object"]


def slug(row: dict[str, str]) -> str:
    identity = "|".join((row["category"], row["object"], row["constellation"], row["best"]))
    stem = re.sub(r"[^a-z0-9]+", "-", label(row).casefold()).strip("-") or "object"
    return f"{stem[:55]}-{hashlib.sha1(identity.encode()).hexdigest()[:8]}.json"


def selected(rows: list[dict[str, str]], year: int, week: int, count: int = 6) -> list[dict[str, str]]:
    total = week_count(year)
    def rank(row: dict[str, str]) -> tuple:
        candidate = row_week(row, year)
        delta = abs(candidate - week)
        distance = min(delta, total - delta)
        return (distance, row["category"] != "messier", row["iso"], label(row))
    result = sorted(rows, key=rank)[:count]
    if len(result) != count:
        raise RuntimeError(f"Need {count} objects for {year}-W{week:02d}")
    return result


def replace_block(text: str, year: int, week: int, body: str) -> str:
    heading = f"## ISO {year}-W{week:02d}"
    start = text.find(heading)
    if start < 0:
        raise RuntimeError(f"Missing {heading}")
    next_heading = text.find(f"## ISO {year}-W{week + 1:02d}", start) if week < week_count(year) else len(text)
    section = text[start:next_heading]
    begin = section.find(BEGIN)
    end = section.find(END)
    if begin < 0 or end < begin:
        raise RuntimeError(f"Missing sky-note ownership markers in {heading}")
    end += len(END)
    replacement = f"{BEGIN}\n{body.rstrip()}\n{END}"
    section = section[:begin] + replacement + section[end:]
    return text[:start] + section + text[next_heading:]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("year", type=int)
    args = parser.parse_args()
    year = args.year
    scaffold = ROOT / "year-scaffolds" / f"almanack-{year}.md"
    source = ROOT / f"fixed-object-sky-notes-{year}.csv"
    routes_source = ROOT / "curated-observing-routes.json"
    out = ROOT / f"observing-descriptors-{year}"
    if not scaffold.exists() or not source.exists():
        raise SystemExit(f"Missing scaffold or fixed-object source for {year}")

    with source.open(encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    routes = json.loads(routes_source.read_text(encoding="utf-8")).get("routes", [])

    if out.exists():
        shutil.rmtree(out)
    objects_dir = out / "objects"
    routes_dir = out / "routes"
    objects_dir.mkdir(parents=True)
    routes_dir.mkdir(parents=True)
    hrefs: dict[int, str] = {}

    for index, row in enumerate(rows):
        filename = slug(row)
        hrefs[index] = f"objects/{filename}"
        payload = {
            "schema": "star-almanack.observing-object.v1",
            "iso_year": year,
            "iso_week_date": row["iso"],
            "best_visibility_date": row["best"],
            "identity": {
                "category": row["category"],
                "designation": row["object"],
                "display_name": label(row),
                "constellation": row["constellation"],
            },
            "observing": {
                "naked_eye": row["naked_eye"],
                "binoculars": row["binoculars"],
                "telescope": row["telescope"],
            },
            "generated_from": source.name,
        }
        (objects_dir / filename).write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    for route in routes:
        (routes_dir / f"{route['id']}.json").write_text(
            json.dumps({"schema": "star-almanack.observing-route.v1", **route}, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )

    text = scaffold.read_text(encoding="utf-8")
    for week in range(1, week_count(year) + 1):
        choices = selected(rows, year, week)
        identities = " ".join(f"{row['object']} {row['name']}" for row in choices).casefold()
        chosen_routes = [
            route for route in routes
            if all(token.casefold() in identities for token in route.get("applies_to", []))
        ]
        links = []
        records = []
        for row in choices:
            index = rows.index(row)
            href = hrefs[index]
            links.append(f"[{label(row)}](../descriptors/{href})")
            records.append({
                "display_name": label(row),
                "iso_week_date": row["iso"],
                "relationship_to_week": "best_visibility" if row_week(row, year) == week else "nearby_best_visibility",
                "href": href,
            })
        week_id = f"W{week:02d}"
        week_payload = {
            "schema": "star-almanack.observing-week.v1",
            "iso_week": f"{year}-{week_id}",
            "inline_descriptors": records[:4],
            "linked_descriptors": records,
            "curated_routes": [
                {"id": route["id"], "href": f"routes/{route['id']}.json"}
                for route in chosen_routes
            ],
        }
        (out / f"{week_id}.json").write_text(
            json.dumps(week_payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
        )
        paragraphs = [
            "The following observer guidance is derived from this week's machine-readable records."
        ]
        for number, row in enumerate(choices[:4], 1):
            nearby = "" if row_week(row, year) == week else f" Nearby best visibility: {row['iso']}."
            paragraphs.append(
                f"**Descriptor {number} — {label(row)}:** Naked eye: {row['naked_eye']} "
                f"Binoculars: {row['binoculars']}{nearby}"
            )
        paragraphs.extend(f"**Guiding route:** {route['human_guidance']}" for route in chosen_routes)
        paragraphs.append(
            "**Machine-readable descriptors:** "
            + " · ".join([f"[Week index](../descriptors/{week_id}.json)", *links[:5]])
        )
        text = replace_block(text, year, week, "\n\n".join(paragraphs))

    scaffold.write_text(text, encoding="utf-8")
    print(f"Recreated {week_count(year)} Sky Note blocks and descriptor indexes for {year}")


if __name__ == "__main__":
    main()
