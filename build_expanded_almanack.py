#!/usr/bin/env python3
"""Build the expanded 2026 Almanack from the integrated calendar and catalogs."""
from datetime import date, datetime, timedelta
from pathlib import Path
import csv
import re

ROOT = Path(__file__).parent
calendar = (ROOT / "almanack.md").read_text(encoding="utf-8")
source = (ROOT / "ISO2026.md").read_text(encoding="utf-8")
bayer = (ROOT / "expanded-bayer-visibility-2026.csv").read_text(encoding="utf-8")
ephemeris = {}
with (ROOT / "weekly-ephemeris-2026.csv").open(encoding="utf-8", newline="") as f:
    for row in csv.DictReader(f):
        ephemeris[row["iso_week"]] = row

expected = [f"ISO 2026-W{i:02d}" for i in range(1, 54)]
weeks = re.findall(r"(?m)^## (ISO 2026-W\d{2})\s*$", calendar)
if weeks != expected[:len(weeks)] or len(weeks) > 53:
    raise SystemExit(f"Unexpected weekly structure in almanack.md: {weeks[-5:]}")

# The integrated Almanack currently contains W01-W25. Complete W26-W53 here
# from the canonical zodiac/lunar source and the generated weekly ephemeris.
if len(weeks) < 53:
    ingress = []
    for m in re.finditer(r"\| (♒|♓|♈|♉|♊|♋|♌|♍|♎|♏|♐|♑) \([^|]+\) \| \d+° \| (2026-\d\d-\d\d) (\d\d:\d\d:\d\d) \|", source):
        ingress.append((datetime.fromisoformat(f"{m.group(2)}T{m.group(3)}"), m.group(1)))
    ingress.sort()
    if len(ingress) != 12:
        raise SystemExit(f"Expected 12 zodiac ingresses, found {len(ingress)}")

    # Selected-object and lunar events already validated in ISO2026.md.
    events = {}
    object_re = re.compile(r"\| ([^|]+) \| ([^|]+) \| ([A-Z][a-z]{2} \d{1,2}) \| ([^|]+) \|")
    for m in object_re.finditer(source):
        name, bayer_code, md, classification = [x.strip() for x in m.groups()]
        if name in {"Star", "Object"} or name.startswith("---"):
            continue
        try:
            d = datetime.strptime(f"{md} 2026", "%b %d %Y").date()
        except ValueError:
            continue
        label = f"{name} ({bayer_code})" if bayer_code else name
        events.setdefault(d, []).append(f"Best visibility: {label} — {classification}")

    phase_re = re.compile(r"\| ([🌕🌗🌑🌓] [^|]+) \| (2026-\d\d-\d\d \d\d:\d\d:\d\d) \|")
    for m in phase_re.finditer(source):
        ts = datetime.fromisoformat(m.group(2))
        events.setdefault(ts.date(), []).append(f"{m.group(1)} — {ts:%H:%M:%S} UTC")

    # Zodiac day from the published/calculated ingress instants in ISO2026.md.
    def zodiac_for_day(d):
        current = ingress[0][1]
        for ts, sign in ingress:
            if datetime.combine(d, datetime.min.time()) >= ts:
                current = sign
            else:
                break
        signs = [x[1] for x in ingress]
        # Find the sign's ordinal in the tropical sequence, including Capricorn
        # at the start of 2026.
        sign_index = {s: i for i, s in enumerate(["♒","♓","♈","♉","♊","♋","♌","♍","♎","♏","♐","♑"])}
        start = datetime(2025, 12, 21)
        # Determine the most recent ingress among the boundary plus 2026 ingresses.
        boundaries = [(datetime(2025,12,21,15,3,5), "♑")] + ingress
        last_ts, sign = max((x for x in boundaries if x[0] <= datetime.combine(d, datetime.min.time())), key=lambda x:x[0])
        day = (d - last_ts.date()).days + 1
        return sign, day

    def iso_dates(w):
        return date.fromisocalendar(2026, w, 1)

    def ephem_table(row):
        cols = [("☉ Sun", row["sun"]), ("☽ Moon", row["moon"]), ("☿ Mercury", row["mercury"]),
                ("♀ Venus", row["venus"]), ("♂ Mars", row["mars"]), ("♃ Jupiter", row["jupiter"]),
                ("♄ Saturn", row["saturn"])]
        return ("| " + " | ".join(x[0] for x in cols) + " |\n\n"
                "|---:|---:|---:|---:|---:|---:|---:|\n\n"
                "| " + " | ".join(x[1] for x in cols) + " |")

    additions = []
    for w in range(len(weeks) + 1, 54):
        key = f"2026-W{w:02d}"
        if key not in ephemeris:
            raise SystemExit(f"Missing weekly ephemeris for {key}")
        monday = iso_dates(w)
        sunday = monday + timedelta(days=6)
        rows = []
        for i in range(7):
            d = monday + timedelta(days=i)
            sign, daynum = zodiac_for_day(d)
            sign_name = {"♈":"Aries","♉":"Taurus","♊":"Gemini","♋":"Cancer","♌":"Leo","♍":"Virgo","♎":"Libra","♏":"Scorpio","♐":"Sagittarius","♑":"Capricorn","♒":"Aquarius","♓":"Pisces"}[sign]
            z = f"{sign} ({sign_name}) {daynum}" if daynum == 1 else f"{sign} {daynum}"
            ev = "<br>".join(events.get(d, ["—"]))
            rows.append(f"| {d:%a, %b %d, %Y} | {z} | {ev} |")
        additions.append(
            f"## {key}\n\n"
            f"**ISO dates:** {key}-1 through {key}-7  \n\n"
            f"**Civil dates:** {monday:%b %d, %Y} – {sunday:%b %d, %Y}\n\n"
            "### Calendar\n\n"
            "| Date | Zodiac day | Events |\n\n"
            "|---|---|---|\n\n" + "\n\n".join(rows) + "\n\n"
            "### Weekly Classical-Planet Ephemeris\n\n"
            f"**Snapshot:** {monday:%B %-d, %Y} · 00:00 UTC\n\n"
            + ephem_table(ephemeris[key]) + "\n\n"
            "### Sky Note\n\n"
            "Weekly geocentric tropical planetary positions, sampled Monday at 00:00 UTC.\n\n"
            "### Chart\n\n"
            f"`ISO2026-W{w}-chart.png` — chart slot."
        )
    calendar = calendar.rstrip() + "\n\n" + "\n\n".join(additions)

header = "# Star Almanack — 2026\n\n*A Natural Philosopher's Guide to the Night Sky*\n\n"
objects = (
    "## Expanded α and β Star Catalog\n\n"
    "The complete generated Bayer catalog for 2026 follows. "
    "Best-visibility dates are computed by the Star Almanack visibility rule.\n\n"
    + bayer
)
out = header + calendar.rstrip() + "\n\n" + objects
(ROOT / "almanack-expanded.md").write_text(out, encoding="utf-8")
print(f"Built almanack-expanded.md: 53 ISO weeks; {len(bayer.splitlines())-1} Bayer rows")
