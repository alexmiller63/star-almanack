#!/usr/bin/env python3
"""Enrich every stellar calendar entry with consistent observer-facing metadata.

Source files:
- expanded-bayer-visibility-2026.csv: authoritative α/β Bayer identity, coordinates, magnitude, date
- bright-star-visibility-2026.csv: authoritative V<=2.50 bright-star layer and dates
- bright-variable-reconciliation.csv: repository GCVS reconciliation for known bright variables

Output:
- rewrites stellar entries in almanack-expanded.md after build_expanded_almanack.py

Display convention:
  Proper name (Bayer) — V N.NN — Declination-band Season
  or, for non-variable stars:
  Proper name (Bayer) — Declination-band Season

The source decimal magnitude is preserved for variable stars only. V precedes the
magnitude only for variable stars; non-variable stars do not display a magnitude.

Declination Band is derived from declination using the tropics (±23.44°):
Northern / Tropical / Southern. Season is the northern-calendar observing season
of the best-visibility civil date: Winter / Spring / Summer / Autumn.
"""
from __future__ import annotations

import csv
import re
from collections import defaultdict
from datetime import date
from pathlib import Path

ROOT = Path(__file__).parent
TARGET = ROOT / "almanack-expanded.md"
BAYER = ROOT / "expanded-bayer-visibility-2026.csv"
BRIGHT = ROOT / "bright-star-visibility-2026.csv"
VARIABLES = ROOT / "bright-variable-reconciliation.csv"

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


def clean_mag(value: str) -> str:
    """Preserve the catalog decimal magnitude rather than rounding it."""
    value = (value or "").strip()
    if not value:
        return ""
    try:
        float(value)
    except ValueError:
        return value
    return value


def variable_keys() -> set[str]:
    out = set()
    if not VARIABLES.exists():
        return out
    with VARIABLES.open(encoding="utf-8", newline="") as f:
        for row in csv.DictReader(f):
            name = (row.get("name") or "").strip().casefold()
            if name:
                out.add(name)
    return out


def latin_key(code: str, con: str) -> str:
    m = re.fullmatch(r"([A-Z][a-z]{2})(?:-?(\d+))?", (code or "").strip())
    if not m:
        return f"{code} {con}".strip().casefold()
    return f"{m.group(1).casefold()} {con}".strip().casefold()


def canonical(row: dict[str, str], variables: set[str]) -> str:
    proper = (row.get("proper") or "").strip()
    code = (row.get("bayer_code") or row.get("bayer") or "").strip()
    con = (row.get("con") or "").strip()
    designation = (row.get("bayer") or "").strip()
    if not designation or not designation.startswith(tuple(GREEK.values())):
        designation = bayer_display(code, con)
    name = f"{proper} ({designation})" if proper else designation
    mag = clean_mag(row.get("mag") or row.get("representative_vmax") or row.get("catalog_v") or "")
    d = date.fromisoformat(row["best_date"])
    parts = [name]
    is_variable = latin_key(code, con) in variables
    if is_variable and mag:
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
    variables = variable_keys()
    by_date: dict[str, list[tuple[list[str], str]]] = defaultdict(list)
    seen = set()

    with BRIGHT.open(encoding="utf-8", newline="") as f:
        for row in csv.DictReader(f):
            row = dict(row)
            row["bayer_code"] = row.get("bayer", "")
            key = (row["best_date"], (row.get("proper") or "").casefold(), latin_key(row.get("bayer", ""), row.get("con", "")))
            seen.add(key)
            by_date[row["best_date"]].append((aliases(row), canonical(row, variables)))

    with BAYER.open(encoding="utf-8", newline="") as f:
        for row in csv.DictReader(f):
            key = (row["best_date"], (row.get("proper") or "").casefold(), latin_key(row.get("bayer_code", ""), row.get("con", "")))
            if key in seen:
                continue
            by_date[row["best_date"]].append((aliases(row), canonical(row, variables)))
    return by_date


ROW_RE = re.compile(
    r"(?m)^(\| (?:Mon|Tue|Wed|Thu|Fri|Sat|Sun), ([A-Z][a-z]{2}) (\d{2}), (2025|2026|2027) \| [^|]+ \| )([^|]*)( \|)$"
)
MONTHS = {m: i for i, m in enumerate(["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"], 1)}


def enrich_cell(date_iso: str, cell: str, stars: dict[str, list[tuple[list[str], str]]]) -> str:
    if not cell.strip() or cell.strip() == "—":
        return cell
    parts = cell.split("<br>")
    candidates = stars.get(date_iso, [])
    out = []
    for part in parts:
        replacement = None
        folded = part.casefold()
        for star_aliases, label in candidates:
            if any(alias.casefold() in folded for alias in star_aliases if alias):
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

    expected = "Enif (ε Peg) — V 2.38 — Tropical Autumn"
    if expected not in updated:
        raise SystemExit(f"Expected enriched Enif entry not found: {expected}")
    if "Enif (ε Peg) — V 2 — Tropical Autumn" in updated:
        raise SystemExit("Rounded Enif magnitude survived")
    if " — variable — " in updated:
        raise SystemExit("Obsolete variable word survived")
    print("Enriched stellar calendar entries; variable-only magnitude regression PASS")


if __name__ == "__main__":
    main()
