#!/usr/bin/env python3
"""Enrich every stellar calendar entry with consistent observer-facing metadata.

Source files:
- expanded-bayer-visibility-2026.csv: authoritative α/β Bayer identity, coordinates, magnitude, date
- bright-star-visibility-2026.csv: authoritative V<=2.50 bright-star layer and dates

Output:
- rewrites stellar entries in almanack-expanded.md after build_expanded_almanack.py

Display convention:
  Proper name (Bayer) — V N — Declination-band Season

The authoritative source magnitude remains decimal. Almanack calendar text rounds
stellar magnitudes to the nearest whole number; chart presentation uses one decimal
place. Every catalog-backed stellar entry with an authoritative source magnitude
displays that magnitude.

Declination Band is derived from declination using the tropics (±23.44°):
Northern / Tropical / Southern. Season is the northern-calendar observing season
of the best-visibility civil date: Winter / Spring / Summer / Autumn.
"""
from __future__ import annotations

import csv
import re
from collections import defaultdict
from datetime import date
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from pathlib import Path

ROOT = Path(__file__).parent
TARGET = ROOT / "almanack-expanded.md"
BAYER = ROOT / "expanded-bayer-visibility-2026.csv"
BRIGHT = ROOT / "bright-star-visibility-2026.csv"

GREEK = {
    "Alp": "α", "Bet": "β", "Gam": "γ", "Del": "δ", "Eps": "ε",
    "Zet": "ζ", "Eta": "η", "The": "θ", "Iot": "ι", "Kap": "κ",
    "Lam": "λ", "Mu": "μ", "Nu": "ν", "Xi": "ξ", "Omi": "ο",
    "Pi": "π", "Rho": "ρ", "Sig": "σ", "Tau": "τ", "Ups": "υ",
    "Phi": "φ", "Chi": "χ", "Psi": "ψ", "Ome": "ω",
}


def bayer_display(code: str, con: str) -> str:
    m = re.fullmatch(r"([A-Z][a-z]{2})(?:-?(\d+))?", (code or "").strip())
    if not m:
        return f"{code} {con}".strip()
    symbol = GREEK.get(m.group(1), m.group(1))
    suffix = m.group(2) or ""
    return f"{symbol}{suffix} {con}".strip()


def declination_band(dec_deg: str) -> str:
    dec = float(dec_deg)
    if dec > 23.44:
        return "Northern"
    if dec < -23.44:
        return "Southern"
    return "Tropical"


def season_for(d: date) -> str:
    md = (d.month, d.day)
    if (3, 20) <= md < (6, 21):
        return "Spring"
    if (6, 21) <= md < (9, 22):
        return "Summer"
    if (9, 22) <= md < (12, 21):
        return "Autumn"
    return "Winter"


def whole_mag(value: str) -> str:
    """Round an authoritative decimal magnitude to a whole Almanack magnitude."""
    value = (value or "").strip()
    if not value:
        return ""
    try:
        rounded = Decimal(value).quantize(Decimal("1"), rounding=ROUND_HALF_UP)
    except InvalidOperation:
        return value
    return str(int(rounded))


def latin_key(code: str, con: str) -> str:
    m = re.fullmatch(r"([A-Z][a-z]{2})(?:-?(\d+))?", (code or "").strip())
    if not m:
        return f"{code} {con}".strip().casefold()
    suffix = m.group(2)
    if suffix:
        return f"{m.group(1).casefold()} {suffix} {con}".strip().casefold()
    return f"{m.group(1).casefold()} {con}".strip().casefold()


def canonical(row: dict[str, str]) -> str:
    proper = (row.get("proper") or "").strip()
    code = (row.get("bayer_code") or row.get("bayer") or "").strip()
    con = (row.get("con") or "").strip()
    designation = (row.get("bayer") or "").strip()
    if not designation or not designation.startswith(tuple(GREEK.values())):
        designation = bayer_display(code, con)
    name = f"{proper} ({designation})" if proper else designation
    source_mag = row.get("mag") or row.get("representative_vmax") or row.get("catalog_v") or ""
    mag = whole_mag(source_mag)
    d = date.fromisoformat(row["best_date"])
    parts = [name]
    if mag:
        parts.append(f"V {mag}")
    parts.append(f"{declination_band(row['dec_deg'])} {season_for(d)}")
    return " — ".join(parts)


def aliases(row: dict[str, str]) -> list[str]:
    proper = (row.get("proper") or "").strip()
    designation = (row.get("bayer") or "").strip()
    code = (row.get("bayer_code") or row.get("bayer") or "").strip()
    con = (row.get("con") or "").strip()
    short = bayer_display(code, con)
    vals = [proper, designation if designation.startswith(tuple(GREEK.values())) else "", short]
    return [v for v in vals if v]


def load_stars() -> dict[str, list[tuple[list[str], str]]]:
    by_date: dict[str, list[tuple[list[str], str]]] = defaultdict(list)
    seen = set()

    with BRIGHT.open(encoding="utf-8", newline="") as f:
        for row in csv.DictReader(f):
            row = dict(row)
            row["bayer_code"] = row.get("bayer", "")
            key = (row["best_date"], (row.get("proper") or "").casefold(), latin_key(row.get("bayer", ""), row.get("con", "")))
            seen.add(key)
            by_date[row["best_date"]].append((aliases(row), canonical(row)))

    with BAYER.open(encoding="utf-8", newline="") as f:
        for row in csv.DictReader(f):
            key = (row["best_date"], (row.get("proper") or "").casefold(), latin_key(row.get("bayer_code", ""), row.get("con", "")))
            if key in seen:
                continue
            by_date[row["best_date"]].append((aliases(row), canonical(row)))
    return by_date


ROW_RE = re.compile(
    r"(?m)^(\| (?:Mon|Tue|Wed|Thu|Fri|Sat|Sun), ([A-Z][a-z]{2}) (\d{2}), (2025|2026|2027) \| [^|]+ \| )([^|]*)( \|)$"
)
MONTHS = {m: i for i, m in enumerate(["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"], 1)}


def alias_matches(part: str, alias: str) -> bool:
    """Match one raw stellar token without swallowing a longer proper name."""
    p = part.strip().casefold()
    a = alias.strip().casefold()
    return p == a or p.startswith(a + " (") or p.startswith(a + " —")


def enrich_cell(date_iso: str, cell: str, stars: dict[str, list[tuple[list[str], str]]]) -> str:
    if not cell.strip() or cell.strip() == "—":
        return cell
    parts = cell.split("<br>")
    candidates = stars.get(date_iso, [])
    out = []
    for part in parts:
        replacement = None
        for star_aliases, label in candidates:
            if any(alias_matches(part, alias) for alias in star_aliases if alias):
                replacement = label
                break
        out.append(replacement or part)
    deduped = []
    seen = set()
    for part in out:
        if part not in seen:
            seen.add(part)
            deduped.append(part)
    return "<br>".join(deduped)


def main() -> None:
    text = TARGET.read_text(encoding="utf-8")
    stars = load_stars()

    def repl(m: re.Match[str]) -> str:
        d = date(int(m.group(4)), MONTHS[m.group(2)], int(m.group(3))).isoformat()
        return m.group(1) + enrich_cell(d, m.group(5), stars) + m.group(6)

    updated = ROW_RE.sub(repl, text)
    TARGET.write_text(updated, encoding="utf-8")

    expected = "Enif (ε Peg) — V 2 — Tropical Autumn"
    if expected not in updated:
        raise SystemExit(f"Expected enriched Enif entry not found: {expected}")
    diadem = "Diadem (α Com) — V 4 — Tropical Spring"
    if diadem not in updated:
        raise SystemExit(f"Expected enriched Diadem entry not found: {diadem}")
    if re.search(r"\bV\s+[+-]?\d+\.\d+", updated):
        raise SystemExit("Decimal stellar magnitude survived Almanack rendering")
    if " — variable — " in updated:
        raise SystemExit("Obsolete variable word survived")
    print("Enriched stellar calendar entries; whole-number catalog magnitudes PASS")


if __name__ == "__main__":
    main()
