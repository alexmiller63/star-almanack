#!/usr/bin/env python3
"""Build the 53-week 2026 Almanack from the canonical calendar and catalogs."""
from pathlib import Path
import re

ROOT = Path(__file__).parent
calendar = (ROOT / "ISO2026.md").read_text(encoding="utf-8")
bayer = (ROOT / "expanded-bayer-visibility-2026.csv").read_text(encoding="utf-8")

weeks = re.findall(r"(?ms)^## (ISO 2026-W\d{2})\s*$.*?(?=^## ISO 2026-W\d{2}\s*$|\Z)", calendar)
if len(weeks) != 53:
    raise SystemExit(f"Expected 53 ISO weeks in ISO2026.md, found {len(weeks)}")

# Preserve the validated calendar material verbatim and append the complete
# expanded fixed-object catalog as a generated reference layer. The website
# publisher will split the resulting document into the 53 week pages.
header = "# Star Almanack — 2026\n\n*A Natural Philosopher's Guide to the Night Sky*\n\n"
objects = "## Expanded α and β Star Catalog\n\nThe complete generated Bayer catalog for 2026 follows. Best-visibility dates are computed by the Star Almanack visibility rule.\n\n" + bayer
out = header + calendar + "\n\n" + objects
(ROOT / "almanack-expanded.md").write_text(out, encoding="utf-8")
print(f"Built almanack-expanded.md: {len(weeks)} ISO weeks; {len(bayer.splitlines())-1} Bayer rows")
