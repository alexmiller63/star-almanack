from __future__ import annotations

import unittest
from pathlib import Path


class BuildEverythingInterfaceTests(unittest.TestCase):
    def test_workflow_uses_four_simple_range_inputs(self) -> None:
        workflow = (Path(__file__).resolve().parents[1] / ".github/workflows/build-everything.yml").read_text(
            encoding="utf-8"
        )
        for name in ("start_year", "start_week", "end_year", "end_week"):
            self.assertIn(f"      {name}:\n", workflow)
            self.assertIn(f"${{{{ inputs.{name} }}}}", workflow)
        self.assertNotIn("inputs.first_iso_week", workflow)
        self.assertNotIn("inputs.last_iso_week", workflow)
        self.assertIn("FIRST_ISO_WEEK={requested.first}", workflow)
        self.assertIn("LAST_ISO_WEEK={requested.last}", workflow)


if __name__ == "__main__":
    unittest.main()
