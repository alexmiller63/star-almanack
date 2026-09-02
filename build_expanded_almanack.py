#!/usr/bin/env python3
"""Build the expanded 2026 Almanack from the integrated calendar and full fixed-object catalogs."""
from datetime import date, datetime, timedelta
from pathlib import Path
import csv
import re

ROOT = Path(__file__).parent
calendar = (ROOT / "almanack.md").read_text(encoding="utf-8")
source = (ROOT / "ISO2026.md").read_text(encoding="utf-8")
bayer_text = (ROOT / "expanded-bayer-visibility-2026.csv").read_text(encoding="utf-8")
bright_text = (ROOT / "bright-star-visibility-2026.csv").read_text(encoding="utf-8")

with (ROOT / "expanded-bayer-visibility-2026.csv").open(encoding="utf-8", newline="") as f:
    bayer_rows = list(csv.DictReader(f))
with (ROOT / "messier-visibility-2026.csv").open(encoding="utf-8", newline="") as f:
    messier_rows = list(csv.DictReader(f))
with (ROOT / "bright-star-visibility-2026.csv").open(encoding="utf-8", newline="") as f:
    bright_rows = list(csv.DictReader(f))
bright_new_rows = [r for r in bright_rows if r.get("new_non_alpha_beta") == "yes"]

ephemeris = {}
with (ROOT / "weekly-ephemeris-2026.csv").open(encoding="utf-8", newline="") as f:
    for row in csv.DictReader(f):
        ephemeris[row["iso_week"]] = row

expected = [f"ISO 2026-W{i:02d}" for i in range(1, 54)]
weeks = re.findall(r"(?m)^## (ISO 2026-W\d{2})\s*$", calendar)
if weeks != expected[:len(weeks)] or len(weeks) > 53:
    raise SystemExit(f"Unexpected weekly structure in almanack.md: {weeks[-5:]}")

if len(weeks) < 53:
    ingress = []
    for m in re.finditer(r"\| (♒|♓|♈|♉|♊|♋|♌|♍|♎|♏|♐|♑) \([^|]+\) \| \d+° \| (2026-\d\d-\d\d) (\d\d:\d\d:\d\d) \|", source):
        ingress.append((datetime.fromisoformat(f"{m.group(2)}T{m.group(3)}"), m.group(1)))
    ingress.sort()
    if len(ingress) != 12:
        raise SystemExit(f"Expected 12 zodiac ingresses, found {len(ingress)}")

    events = {}
    phase_re = re.compile(r"\| ([🌕🌗🌑🌓] [^|]+) \| (2026-\d\d-\d\d \d\d:\d\d:\d\d) \|")
    for m in phase_re.finditer(source):
        ts = datetime.fromisoformat(m.group(2))
        events.setdefault(ts.date(), []).append(f"{m.group(1)} — {ts:%H:%M:%S} UTC")

    def zodiac_for_day(d):
        boundaries = [(date(2025, 12, 21), "♑")] + [(ts.date(), sign) for ts, sign in ingress]
        last_date, sign = max((x for x in boundaries if x[0] <= d), key=lambda x: x[0])
        return sign, (d - last_date).days + 1

    def ephem_table(row):
        cols = [("☉ Sun", row["sun"]), ("☽ Moon", row["moon"]), ("☿ Mercury", row["mercury"]),
                ("♀ Venus", row["venus"]), ("♂ Mars", row["mars"]), ("♃ Jupiter", row["jupiter"]),
                ("♄ Saturn", row["saturn"])]
        return ("| " + " | ".join(x[0] for x in cols) + " |\n\n"
                "|---:|---:|---:|---:|---:|---:|\n\n"
                "| " + " | ".join(x[1] for x in cols) + " |")

    sign_names = {"♈":"Aries","♉":"Taurus","♊":"Gemini","♋":"Cancer","♌":"Leo","♍":"Virgo",
                  "♎":"Libra","♏":"Scorpio","♐":"Sagittarius","♑":"Capricorn","♒":"Aquarius","♓":"Pisces"}
    additions = []
    for w in range(len(weeks) + 1, 54):
        key = f"2026-W{w:02d}"
        if key not in ephemeris:
            raise SystemExit(f"Missing weekly ephemeris for {key}")
        monday = date.fromisocalendar(2026, w, 1)
        sunday = monday + timedelta(days=6)
        rows = []
        for i in range(7):
            d = monday + timedelta(days=i)
            sign, daynum = zodiac_for_day(d)
            z = f"{sign} ({sign_names[sign]}) {daynum}" if daynum == 1 else f"{sign} {daynum}"
            ev = "<br>".join(events.get(d, ["—"]))
            rows.append(f"| {d:%a, %b %d, %Y} | {z} | {ev} |")
        additions.append(
            f"## ISO {key}\n\n"
            f"**ISO dates:** {key}-1 through {key}-7  \n\n"
            f"**Civil dates:** {monday:%b %d, %Y} – {sunday:%b %d, %Y}\n\n"
            "### Calendar\n\n| Date | Zodiac day | Events |\n\n|---|---|---|\n\n"
            + "\n\n".join(rows) + "\n\n"
            "### Weekly Classical-Planet Ephemeris\n\n"
            f"**Snapshot:** {monday:%B %-d, %Y} · 00:00 UTC\n\n"
            + ephem_table(ephemeris[key]) + "\n\n"
            "### Sky Note\n\nWeekly geocentric tropical planetary positions, sampled Monday at 00:00 UTC.\n\n"
            "### Chart\n\n"
            f"`ISO2026-W{w}-chart.png` — chart slot."
        )
    calendar = calendar.rstrip() + "\n\n" + "\n\n".join(additions)

# Build the complete fixed-object event set by civil date.  Each generated
# row carries conservative aliases used only to suppress a duplicate legacy
# calendar label.  Generated catalog rows are never deduplicated against one
# another, so separately designated components remain intact.
fixed = {}
for row in messier_rows:
    messier = row["messier"]
    fixed.setdefault(row["best_date"], []).append(
        (f"Messier:{messier}", f"Best visibility: {messier}", (messier,))
    )
for idx, row in enumerate(bayer_rows):
    designation = row["bayer"]
    proper = row.get("proper", "").strip()
    label = f"{proper} ({designation})" if proper else designation
    placement_date = row["best_date"]
    if placement_date.startswith("2025-"):
        placement_date = "2026-" + placement_date[5:]
    ident = f"Bayer:{idx}:{row['bayer_code']}:{row['con']}"
    aliases = tuple(x for x in (proper, designation) if x)
    fixed.setdefault(placement_date, []).append((ident, f"Best visibility: {label}", aliases))
for idx, row in enumerate(bright_new_rows):
    proper = (row.get("proper") or "").strip()
    bayer = (row.get("bayer") or "").strip()
    con = (row.get("con") or "").strip()
    name = proper or (f"{bayer} {con}".strip())
    mag_class = (row.get("mag_class") or "").strip()
    label = f"{name} — V{mag_class}" if mag_class else name
    ident = f"Bright:{idx}:{row.get('hyg_id','')}"
    aliases = tuple(x for x in (proper, bayer) if x)
    fixed.setdefault(row["best_date"], []).append((ident, f"Best visibility: {label}", aliases))

seen = set()
row_re = re.compile(r"(?m)^(\| (?:Mon|Tue|Wed|Thu|Fri|Sat|Sun), ([A-Z][a-z]{2}) (\d{2}), (2025|2026|2027) \| [^|]+ \| )([^|]*)( \|)$")
months = {m: i for i, m in enumerate(["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"], 1)}
messier_best_dates = {row["messier"].upper(): row["best_date"] for row in messier_rows}


def legacy_has_alias(existing, aliases):
    """Return True only for conservative identity matches in legacy text."""
    folded = existing.casefold()
    for alias in aliases:
        alias = alias.strip()
        if not alias:
            continue
        if re.fullmatch(r"M\d{1,3}", alias, flags=re.IGNORECASE):
            if re.search(rf"(?<![A-Za-z0-9]){re.escape(alias)}(?!\d)", existing, flags=re.IGNORECASE):
                return True
        elif alias.casefold() in folded:
            return True
    return False


def reconcile_legacy_messier(match):
    """Keep each legacy Messier label only on the catalog's computed best date."""
    d = date(int(match.group(4)), months[match.group(2)], int(match.group(3))).isoformat()
    existing = match.group(5).strip()
    if existing in {"", "—"}:
        return match.group(0)
    parts = existing.split("<br>")
    kept = []
    for part in parts:
        m = re.search(r"(?<![A-Za-z0-9])(M\d{1,3})(?!\d)", part, flags=re.IGNORECASE)
        if part.startswith("Best visibility:") and m:
            canonical_date = messier_best_dates.get(m.group(1).upper())
            if canonical_date and canonical_date != d:
                continue
        kept.append(part)
    rendered = "<br>".join(kept) if kept else "—"
    return match.group(1) + rendered + match.group(6)


# Legacy source prose sometimes carried a Messier object's descriptive label
# on a neighboring date.  Reconcile those by M-number to the generated catalog
# date before injecting fixed-object rows, so the calendar has one occurrence.
calendar = row_re.sub(reconcile_legacy_messier, calendar)


def add_fixed(match):
    d = date(int(match.group(4)), months[match.group(2)], int(match.group(3))).isoformat()
    existing = match.group(5).strip()
    additions = []
    for ident, text, aliases in fixed.get(d, []):
        if ident in seen:
            continue
        # Completeness accounting records the catalog row as placed even when
        # the observer-facing alias is already represented in legacy text.
        seen.add(ident)
        if text in existing or legacy_has_alias(existing, aliases):
            continue
        additions.append(text)
    parts = [] if existing in {"", "—"} else existing.split("<br>")
    parts.extend(additions)
    rendered = "<br>".join(parts) if parts else "—"
    return match.group(1) + rendered + match.group(6)

calendar = row_re.sub(add_fixed, calendar)

if len(messier_rows) != 110:
    raise SystemExit(f"Expected 110 Messier rows, found {len(messier_rows)}")
if len(bright_rows) != 92:
    raise SystemExit(f"Expected 92 reconciled bright-star systems, found {len(bright_rows)}")
if len(bright_new_rows) != 41:
    raise SystemExit(f"Expected 41 new non-alpha/beta bright-star systems, found {len(bright_new_rows)}")
expected_fixed = len(messier_rows) + len(bayer_rows) + len(bright_new_rows)
if len(seen) != expected_fixed:
    raise SystemExit(f"Fixed-object placement incomplete: placed {len(seen)} of {expected_fixed}")

header = "# Star Almanack — 2026\n\n*A Natural Philosopher's Guide to the Night Sky*\n\n"
objects = (
    "## Expanded α and β Star Catalog\n\n"
    "The complete generated Bayer catalog for 2026 follows. Best-visibility dates are computed by the Star Almanack visibility rule.\n\n"
    + bayer_text
    + "\n\n## Second-Magnitude Bright-Star Catalog\n\n"
    "The reconciled naked-eye stellar-system catalog follows. Decimal V values are retained here for provenance; Almanack calendar entries use whole-number V classes.\n\n"
    + bright_text
)
out = header + calendar.rstrip() + "\n\n" + objects
(ROOT / "almanack-expanded.md").write_text(out, encoding="utf-8")
print(f"Built almanack-expanded.md: 53 ISO weeks; 110 Messier objects; {len(bayer_rows)} Bayer rows; {len(bright_new_rows)} new bright-star systems")
