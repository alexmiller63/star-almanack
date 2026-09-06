#!/usr/bin/env python3
"""Patch build_expanded_almanack.py for the extended Solar-System ephemeris.

This is intentionally narrow and self-checking: it replaces only the known
7-body ephemeris helper and weekly heading in the existing builder.
"""
from pathlib import Path

path = Path(__file__).parent / "build_expanded_almanack.py"
text = path.read_text(encoding="utf-8")

old = '''    def ephem_table(row):
        cols = [("☉ Sun", row["sun"]), ("☽ Moon", row["moon"]), ("☿ Mercury", row["mercury"]),
                ("♀ Venus", row["venus"]), ("♂ Mars", row["mars"]), ("♃ Jupiter", row["jupiter"]),
                ("♄ Saturn", row["saturn"])]
        return ("| " + " | ".join(x[0] for x in cols) + " |\\n"
                "|---:|---:|---:|---:|---:|---:|\\n"
                "| " + " | ".join(x[1] for x in cols) + " |")
'''
new = '''    def ephem_table(row):
        primary = [("☉ Sun", row["sun"]), ("☽ Moon", row["moon"]), ("☿ Mercury", row["mercury"]),
                   ("♀ Venus", row["venus"]), ("♂ Mars", row["mars"]), ("♃ Jupiter", row["jupiter"]),
                   ("♄ Saturn", row["saturn"])]
        extended = [("♅ Uranus", row["uranus"]), ("♆ Neptune", row["neptune"]), ("⚳ Ceres", row["ceres"])]

        def render(cols):
            return ("| " + " | ".join(x[0] for x in cols) + " |\\n"
                    "|" + "|".join("---:" for _ in cols) + "|\\n"
                    "| " + " | ".join(x[1] for x in cols) + " |")

        return render(primary) + "\\n\\n**Extended targets:**\\n\\n" + render(extended)
'''
if old in text:
    text = text.replace(old, new, 1)
elif 'extended = [("♅ Uranus"' not in text:
    raise SystemExit("Expected legacy ephem_table helper was not found")

text = text.replace('"### Weekly Classical-Planet Ephemeris\\n\\n"', '"### Weekly Solar-System Ephemeris\\n\\n"')
text = text.replace('weekly classical-planet snapshots.', 'weekly Solar-System snapshots.')

path.write_text(text, encoding="utf-8")
print("Patched build_expanded_almanack.py for Uranus, Neptune, and Ceres")
