from __future__ import annotations

import csv
import datetime as dt
import hashlib
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from generate_year_scaffolds import render_year
from publish_weekly_pages import week_nav
from scaffold_sections import iso_week_count, replace_owner_blocks

ROOT = Path(__file__).resolve().parents[1]


def digest_tree(root: Path) -> list[tuple[str, str]]:
    return [
        (str(path.relative_to(root)), hashlib.sha256(path.read_bytes()).hexdigest())
        for path in sorted(item for item in root.rglob("*") if item.is_file())
    ]


def write_calendar_sources(root: Path, year: int) -> None:
    signs = [("♑", "Capricorn"), ("♒", "Aquarius"), ("♓", "Pisces"), ("♈", "Aries"),
             ("♉", "Taurus"), ("♊", "Gemini"), ("♋", "Cancer"), ("♌", "Leo"),
             ("♍", "Virgo"), ("♎", "Libra"), ("♏", "Scorpio"), ("♐", "Sagittarius")]
    for civil_year in (year - 1, year, year + 1):
        ingresses = [{
            "symbol": symbol,
            "name": name,
            "longitude_degrees": ((month + 8) % 12) * 30,
            "utc": f"{civil_year}-{month:02d}-20T12:00:00Z",
        } for month, (symbol, name) in enumerate(signs, 1)]
        payload = {
            "schema": "star-almanack.calendar-events.v1", "year": civil_year,
            "engines": {}, "zodiac_ingresses": ingresses, "lunar_phases": [],
        }
        (root / f"calendar-events-{civil_year}.json").write_text(json.dumps(payload), encoding="utf-8")


def write_ephemeris(root: Path, year: int) -> None:
    fields = ["iso_week", "monday_utc", "sun", "moon", "mercury", "venus", "mars",
              "jupiter", "saturn", "uranus", "neptune", "ceres"]
    with (root / f"weekly-ephemeris-{year}.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        for week in range(1, iso_week_count(year) + 1):
            row = {field: "♈ 0°00′" for field in fields[2:]}
            row.update({"iso_week": f"{year}-W{week:02d}",
                        "monday_utc": dt.date.fromisocalendar(year, week, 1).isoformat()})
            writer.writerow(row)


def run(script: str, root: Path, year: int) -> None:
    subprocess.run([sys.executable, str(ROOT / script), str(year), "--root", str(root)],
                   check=True, capture_output=True, text=True)


class ScaffoldPopulationTests(unittest.TestCase):
    def test_owner_replacement_preserves_other_blocks(self) -> None:
        year = 2027
        updated = replace_owner_blocks(render_year(year), year, "calendar", lambda week: f"calendar {week}")
        self.assertIn("calendar 1", updated)
        for owner in ("ephemeris", "sky-note", "planet-finder", "artwork"):
            marker = f"<!-- owner: {owner}; generator must replace this entire block -->"
            self.assertEqual(updated.count(marker), iso_week_count(year))

    def test_navigation_disables_only_outer_boundaries(self) -> None:
        first = week_nav(2026, 1, 2026, 2028)
        self.assertIn("<span>← Previous</span>", first)
        self.assertIn('href="../W02/"', first)
        boundary = week_nav(2026, iso_week_count(2026), 2026, 2028)
        self.assertIn('href="../../2027/W01/"', boundary)
        final = week_nav(2028, iso_week_count(2028), 2026, 2028)
        self.assertIn("<span>Next →</span>", final)

    def test_all_missing_scaffold_populators_are_regenerative(self) -> None:
        year = 2027
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "year-scaffolds").mkdir()
            scaffold = root / "year-scaffolds" / f"almanack-{year}.md"
            scaffold.write_text(render_year(year), encoding="utf-8")
            write_calendar_sources(root, year)
            write_ephemeris(root, year)
            (root / f"sky-note-artwork-descriptors-{year}.json").write_text(json.dumps({
                "year": year,
                "descriptors": [{"week": "W01", "constellation": "Orion",
                                 "figure_source": "constellation-figures.json"}],
            }), encoding="utf-8")
            for directory in (root / f"planet-finder-descriptors-{year}",
                              root / f"artwork-descriptors-{year}"):
                directory.mkdir()
                (directory / "preserved.json").write_text('{"curated": true}\n', encoding="utf-8")
            scripts = ("populate_scaffold_calendar.py", "populate_scaffold_ephemeris.py",
                       "populate_scaffold_planet_finders.py", "populate_scaffold_artwork.py")
            for script in scripts:
                run(script, root, year)
            first = digest_tree(root)
            for script in scripts:
                run(script, root, year)
            self.assertEqual(first, digest_tree(root))
            text = scaffold.read_text(encoding="utf-8")
            for owner in ("calendar", "ephemeris", "planet-finder", "artwork"):
                marker = f"<!-- owner: {owner}; generator must replace this entire block -->"
                self.assertEqual(text.count(marker), 0)
            self.assertEqual(text.count("| Date | Zodiac day | Events |"), iso_week_count(year))
            self.assertEqual(text.count("**Snapshot:**"), iso_week_count(year))
            self.assertEqual(len(list((root / f"planet-finder-descriptors-{year}").glob("W??.json"))), iso_week_count(year))
            self.assertEqual(len(list((root / f"artwork-descriptors-{year}").glob("W??.json"))), iso_week_count(year))
            self.assertTrue((root / f"planet-finder-descriptors-{year}" / "preserved.json").exists())
            self.assertTrue((root / f"artwork-descriptors-{year}" / "preserved.json").exists())


if __name__ == "__main__":
    unittest.main()
