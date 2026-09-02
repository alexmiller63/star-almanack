#!/usr/bin/env python3
"""Build the expanded 2026 Almanack from the integrated weekly calendar and catalogs."""
from pathlib import Path
import re

ROOT = Path(__file__).parent
calendar = (ROOT / "almanack.md").read_text(encoding="utf-8")
bayer = (ROOT / "expanded-bayer-visibility-2026.csv").read_text(encoding="utf-8")

# almanack.md is the integrated working Almanack and already contains the
# complete ISO 2026 weekly structure. ISO2026.md is the underlying calendar
# source, but it is not the 53-section weekly document.
weeks = re.findall(r"(?m)^## (ISO 2026-W\d{2})\s*$", calendar)
expected = [f"ISO 2026-W{i:02d}" for i in range(1, 54)]
if weeks != expected:
    raise SystemExit(
        f"Expected ISO 2026 W01-W53 in almanack.md, found {len(weeks)} sections"
    )

header = "# Star Almanack — 2026\n\n*A Natural Philosopher's Guide to the Night Sky*\n\n"
objects = (
    "## Expanded α and β Star Catalog\n\n"
    "The complete generated Bayer catalog for 2026 follows. "
    "Best-visibility dates are computed by the Star Almanack visibility rule.\n\n"
    + bayer
)
out = header + calendar.rstrip() + "\n\n" + objects
(ROOT / "almanack-expanded.md").write_text(out, encoding="utf-8")
print(f"Built almanack-expanded.md: {len(weeks)} ISO weeks; {len(bayer.splitlines())-1} Bayer rows")
