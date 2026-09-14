#!/usr/bin/env python3
"""Build machine-readable observing descriptors, then derive weekly prose and links."""
from __future__ import annotations

import csv
import hashlib
import json
import re
import shutil
from pathlib import Path

ROOT = Path(__file__).parent
YEAR = 2026
SOURCE = ROOT / f"fixed-object-sky-notes-{YEAR}.csv"
ROUTES = ROOT / "curated-observing-routes.json"
ALMANACK = ROOT / "almanack-expanded.md"
OUT = ROOT / f"observing-descriptors-{YEAR}"
WEEK_RE = re.compile(r"^(\d{4})-W(\d{2})-[1-7]$")


def slug_for(row: dict[str, str]) -> str:
    identity = "|".join((row["category"], row["object"], row["constellation"], row["name"], row["best"]))
    stem = re.sub(r"[^a-z0-9]+", "-", identity.casefold()).strip("-") or "object"
    digest = hashlib.sha1(identity.encode("utf-8")).hexdigest()[:8]
    return f"{stem[:64]}-{digest}.json"


def week_number(row: dict[str, str]) -> int:
    match = WEEK_RE.fullmatch(row["iso"])
    if not match or int(match.group(1)) != YEAR:
        raise ValueError(f"Invalid ISO date in descriptor source: {row['iso']!r}")
    return int(match.group(2))


def display_name(row: dict[str, str]) -> str:
    return row["name"] or row["object"]


def relevant_rows(rows: list[dict[str, str]], target_week: int, count: int = 6) -> list[dict[str, str]]:
    def rank(row: dict[str, str]):
        week = week_number(row)
        direct = abs(week - target_week)
        distance = min(direct, 53 - direct)
        category = 0 if row["category"] == "messier" else 1
        named = 0 if " — " in display_name(row) else 1
        return (distance, category, named, row["iso"], display_name(row))
    chosen = sorted(rows, key=rank)[:count]
    if len(chosen) != count:
        raise RuntimeError(f"Expected {count} descriptor links for W{target_week:02d}, found {len(chosen)}")
    return chosen


def route_matches(route: dict, row: dict[str, str]) -> bool:
    haystack = f"{row['object']} {row['name']}".casefold()
    return any(token.casefold() in haystack for token in route.get("applies_to", []))


def replace_week_block(text: str, week: str, block: str) -> str:
    heading = f"## ISO {YEAR}-{week}"
    start = text.find(heading)
    if start < 0:
        raise RuntimeError(f"Missing {heading}")
    next_match = re.search(rf"(?m)^## ISO {YEAR}-W\d{{2}}\s*$", text[start + len(heading):])
    end = start + len(heading) + (next_match.start() if next_match else len(text))
    section = text[start:end]
    sky = re.search(r"(?ms)(^### Sky Note\s*$\n\n)(.*?)(?=^### Chart\s*$)", section)
    if not sky:
        raise RuntimeError(f"Missing Sky Note section in {week}")
    prose = sky.group(2).rstrip()
    prose = re.sub(r"(?ms)\n*^#### Observer descriptors\s*$.*\Z", "", prose).rstrip()
    replacement = sky.group(1) + prose + "\n\n" + block.rstrip() + "\n\n"
    section = section[:sky.start()] + replacement + section[sky.end():]
    return text[:start] + section + text[end:]


def main() -> None:
    with SOURCE.open(encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    if not rows:
        raise SystemExit("Fixed-object Sky Note source is empty")
    route_data = json.loads(ROUTES.read_text(encoding="utf-8"))
    routes = route_data.get("routes", [])

    if OUT.exists():
        shutil.rmtree(OUT)
    objects_dir = OUT / "objects"
    routes_dir = OUT / "routes"
    objects_dir.mkdir(parents=True)
    routes_dir.mkdir(parents=True)

    href_by_identity: dict[tuple[str, str, str, str, str], str] = {}
    for row in rows:
        filename = slug_for(row)
        href = f"objects/{filename}"
        key = (row["category"], row["object"], row["constellation"], row["name"], row["best"])
        if key in href_by_identity:
            raise RuntimeError(f"Duplicate descriptor identity: {key}")
        href_by_identity[key] = href
        relationships = [
            {"type": "curated_observing_route", "id": route["id"], "href": f"../routes/{route['id']}.json"}
            for route in routes if route_matches(route, row)
        ]
        payload = {
            "schema": "star-almanack.observing-object.v1",
            "iso_year": YEAR,
            "iso_week_date": row["iso"],
            "best_visibility_date": row["best"],
            "identity": {
                "category": row["category"],
                "designation": row["object"],
                "display_name": display_name(row),
                "constellation": row["constellation"],
            },
            "context": {"in_visible_milky_way": row["in_milky_way"] == "yes"},
            "observing": {
                "naked_eye": row["naked_eye"],
                "binoculars": row["binoculars"],
                "telescope": row["telescope"],
            },
            "relationships": relationships,
            "generated_from": SOURCE.name,
        }
        (objects_dir / filename).write_text(
            json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
        )

    for route in routes:
        (routes_dir / f"{route['id']}.json").write_text(
            json.dumps(
                {"schema": "star-almanack.observing-route.v1", **route},
                indent=2,
                ensure_ascii=False,
            ) + "\n",
            encoding="utf-8",
        )

    text = ALMANACK.read_text(encoding="utf-8")
    for number in range(1, 54):
        week = f"W{number:02d}"
        selected = relevant_rows(rows, number, 6)
        inline = selected[:4]
        selected_routes = [
            route for route in routes
            if sum(route_matches(route, row) for row in selected) >= 2
        ]
        links = []
        items = []
        for row in selected:
            key = (row["category"], row["object"], row["constellation"], row["name"], row["best"])
            href = href_by_identity[key]
            links.append({"title": display_name(row), "href": href})
            items.append({
                "display_name": display_name(row),
                "relationship_to_week": "best_visibility" if week_number(row) == number else "nearby_best_visibility",
                "iso_week_date": row["iso"],
                "href": href,
            })
        week_payload = {
            "schema": "star-almanack.observing-week.v1",
            "iso_week": f"{YEAR}-{week}",
            "selection_policy": {
                "inline_descriptor_count": 4,
                "linked_descriptor_count": 6,
                "ordering": "same-week first, then nearest best-visibility week; Messier objects preferred",
            },
            "inline_descriptors": items[:4],
            "linked_descriptors": items,
            "curated_routes": [
                {"id": route["id"], "href": f"routes/{route['id']}.json"}
                for route in selected_routes
            ],
        }
        (OUT / f"{week}.json").write_text(
            json.dumps(week_payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
        )

        paragraphs = ["#### Observer descriptors"]
        paragraphs.append(
            "The following observer guidance is derived from the machine-readable records for this week."
        )
        for index, row in enumerate(inline, 1):
            near = "" if week_number(row) == number else f" Nearby best visibility: {row['iso']}."
            paragraphs.append(
                f"**Descriptor {index} — {display_name(row)}:** "
                f"Naked eye: {row['naked_eye']} "
                f"Binoculars: {row['binoculars']}{near}"
            )
        for route in selected_routes:
            paragraphs.append(f"**Guiding route:** {route['human_guidance']}")
        link_markup = [f"[Week index](../descriptors/{week}.json)"]
        link_markup.extend(
            f"[{entry['title']}](../descriptors/{entry['href']})" for entry in links[:5]
        )
        paragraphs.append("**Machine-readable descriptors:** " + " · ".join(link_markup))
        text = replace_week_block(text, week, "\n\n".join(paragraphs))

    ALMANACK.write_text(text, encoding="utf-8")
    print(f"Recreated {len(rows)} object descriptors, {len(routes)} route descriptors, and 53 weekly indexes")
    print("Derived 4 inline descriptors and 6 machine-readable links for every Sky Note")


if __name__ == "__main__":
    main()
