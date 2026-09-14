from __future__ import annotations

import datetime as dt
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from build_almanack_range import build
from iso_week_range import IsoWeek, IsoWeekRange
from generate_weekly_ephemeris import parse_horizons_result
from generate_year_scaffolds import render_year
from publish_weekly_pages import publish_range


class IsoWeekRangeTests(unittest.TestCase):
    def test_requested_range_is_209_weeks(self) -> None:
        requested = IsoWeekRange.parse("2025-W01", "2028-W52")
        self.assertEqual(len(requested), 209)
        self.assertEqual(requested.weeks()[0], IsoWeek(2025, 1))
        self.assertEqual(requested.weeks()[-1], IsoWeek(2028, 52))
        self.assertEqual({year: len(weeks) for year, weeks in requested.by_year().items()},
                         {2025: 52, 2026: 53, 2027: 52, 2028: 52})

    def test_nonexistent_week_53_is_rejected(self) -> None:
        with self.assertRaises(ValueError):
            IsoWeek.parse("2028-W53")

    def test_reverse_range_is_rejected(self) -> None:
        with self.assertRaises(ValueError):
            IsoWeekRange.parse("2026-W02", "2026-W01")

    def test_partial_range_groups_at_year_boundary(self) -> None:
        requested = IsoWeekRange.parse("2026-W52", "2027-W02")
        self.assertEqual(requested.by_year(), {2026: (52, 53), 2027: (1, 2)})
        self.assertEqual(requested.first.monday, dt.date(2026, 12, 21))

    def test_horizons_parser_requires_exact_range_length(self) -> None:
        response = "header\nDate__(UT)__HR:MN,ObsEcLon,\n$$SOE\n2025-Jan-01,12.5,\n2025-Jan-08,13.5,\n$$EOE\n"
        self.assertEqual(parse_horizons_result(response, 2), [12.5, 13.5])
        with self.assertRaises(RuntimeError):
            parse_horizons_result(response, 3)

    def test_partial_publication_uses_exact_outer_boundaries(self) -> None:
        requested = IsoWeekRange.parse("2026-W53", "2027-W02")
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "year-scaffolds").mkdir()
            for year, weeks in requested.by_year().items():
                (root / "year-scaffolds" / f"almanack-{year}.md").write_text(
                    render_year(year, weeks), encoding="utf-8"
                )
                for name in ("observing-descriptors", "planet-finder-descriptors", "artwork-descriptors"):
                    target = root / (f"{name}-{year}" if name != "observing-descriptors" else f"observing-descriptors-{year}")
                    target.mkdir()
                    (target / "placeholder.json").write_text(json.dumps({}), encoding="utf-8")
            self.assertEqual(publish_range(requested, root), 3)
            first = (root / "site/2026/W53/index.html").read_text(encoding="utf-8")
            middle = (root / "site/2027/W01/index.html").read_text(encoding="utf-8")
            last = (root / "site/2027/W02/index.html").read_text(encoding="utf-8")
            self.assertIn("<span>← Previous</span>", first)
            self.assertIn('href="../../2027/W01/"', first)
            self.assertIn('href="../../2026/W53/"', middle)
            self.assertIn("<span>Next →</span>", last)

    @patch("build_almanack_range.subprocess.run")
    def test_build_everything_passes_one_range_through_every_stage(self, mocked_run) -> None:
        build("2026-W53", "2027-W02")
        commands = [call.args[0] for call in mocked_run.call_args_list]
        self.assertIn([commands[0][0], "generate_year_scaffolds.py", "2026-W53", "2027-W02"], commands)
        self.assertIn([commands[0][0], "generate_calendar_event_range.py", "2026-W53", "2027-W02"], commands)
        self.assertIn([commands[0][0], "generate_weekly_ephemeris.py", "2026-W53", "2027-W02"], commands)
        self.assertIn([commands[0][0], "populate_scaffold_sky_notes.py", "2026"], commands)
        self.assertIn([commands[0][0], "populate_scaffold_sky_notes.py", "2027"], commands)
        self.assertEqual(commands[-3][1:], ["publish_weekly_pages.py", "2026-W53", "2027-W02"])
        self.assertEqual(commands[-2][1:], ["add_greek_latin_toggle.py", "2026-W53", "2027-W02"])
        self.assertEqual(commands[-1][1:], ["add_observing_aid_notation.py", "2026-W53", "2027-W02"])


if __name__ == "__main__":
    unittest.main()
