#!/usr/bin/env python3
"""Apply curated observer-first Sky Notes to the generated 2026 Almanack."""
from pathlib import Path
import csv
import io
import json
import re

ROOT = Path(__file__).parent
ALMANACK = ROOT / "almanack-expanded.md"
NOTES = ROOT / "sky-notes-2026.json"
NOTES_DIR = ROOT / "sky-notes-2026"
FIXED_OBJECTS = ROOT / "fixed-objects.yaml"
EXPECTED_WEEKS = {f"W{i:02d}" for i in range(1, 54)}
PLACEHOLDER_NOTE = "Weekly geocentric tropical planetary positions, sampled Monday at 00:00 UTC."

TYPE_NAMES = {
    "SN": "supernova remnant",
    "GC": "globular cluster",
    "OC": "open cluster",
    "DN": "diffuse nebula",
    "PN": "planetary nebula",
    "AS": "asterism",
    "DS": "double star",
    "MW": "Milky Way star cloud",
    "SG": "spiral galaxy",
    "BG": "barred galaxy",
    "LG": "lenticular galaxy",
    "EG": "elliptical galaxy",
    "IG": "irregular galaxy",
}


def replace_week_note(text: str, week: str, note: str) -> str:
    week_heading = f"## ISO 2026-{week}"
    start = text.find(week_heading)
    if start < 0:
        raise SystemExit(f"Missing {week_heading}")
    next_week = re.search(r"(?m)^## ISO 2026-W\d{2}\s*$", text[start + len(week_heading):])
    end = start + len(week_heading) + (next_week.start() if next_week else len(text))
    section = text[start:end]
    pattern = re.compile(r"(?ms)^### Sky Note\s*\n\n.*?(?=^### Chart\s*$)")
    if not pattern.search(section):
        raise SystemExit(f"Missing Sky Note section in {week}")
    replacement = "### Sky Note\n\n" + note.strip() + "\n\n"
    updated = pattern.sub(replacement, section, count=1)
    return text[:start] + updated + text[end:]


def load_messier_catalog() -> dict[str, tuple[str | None, str | None, str]]:
    """Read Messier names and types from the fixed-object source of truth."""
    catalog: dict[str, tuple[str | None, str | None, str]] = {}
    text = FIXED_OBJECTS.read_text(encoding="utf-8")
    in_messier = False
    for line in text.splitlines():
        if line.strip() == "messier:":
            in_messier = True
            continue
        if in_messier and line and not line.startswith(" "):
            break
        if not in_messier:
            continue
        m = re.match(r"\s*-\s*\[(.*)\]\s*$", line)
        if not m:
            continue
        row = next(csv.reader(io.StringIO(m.group(1)), skipinitialspace=True))
        if len(row) < 4:
            continue
        messier = row[0].strip()
        if not re.fullmatch(r"M(?:[1-9]\d?|10\d|110)", messier):
            continue
        ngc = row[1].strip()
        name = row[2].strip()
        type_code = row[3].strip()
        if ngc.lower() == "null":
            ngc = None
        if name.lower() == "null":
            name = None
        object_type = TYPE_NAMES.get(type_code, type_code.lower())
        catalog[messier] = (ngc, name, object_type)
    if len(catalog) != 110:
        raise SystemExit(f"Expected 110 Messier source objects, found {len(catalog)}")
    return catalog


def indefinite_article(noun_phrase: str) -> str:
    return "an" if noun_phrase[:1].lower() in "aeiou" else "a"


def expand_messier_mentions(note: str, catalog: dict[str, tuple[str | None, str | None, str]]) -> str:
    """Expand bare Messier designations in prose with a name/identifier and object type."""
    pattern = re.compile(r"(?<![A-Za-z0-9])M(110|10\d|[1-9]\d?)(?!\d)")

    def repl(match: re.Match[str]) -> str:
        designation = "M" + match.group(1)
        # Do not double-expand notes that are already editorially expanded.
        tail = note[match.end():match.end() + 3]
        if tail.startswith(",") or tail.startswith(" ("):
            return designation
        ngc, name, object_type = catalog[designation]
        article = indefinite_article(object_type)
        if name:
            return f"{designation}, the {name}, {article} {object_type}"
        if ngc:
            catalog_name = ngc if not ngc.isdigit() else f"NGC {ngc}"
            return f"{designation} ({catalog_name}), {article} {object_type}"
        return f"{designation}, {article} {object_type}"

    return pattern.sub(repl, note)


def load_notes() -> dict:
    """Load the legacy catalog, then merge modular week files."""
    data = json.loads(NOTES.read_text(encoding="utf-8"))
    weeks = dict(data.get("weeks", {}))
    if NOTES_DIR.exists():
        for path in sorted(NOTES_DIR.glob("W[0-5][0-9].json")):
            payload = json.loads(path.read_text(encoding="utf-8"))
            week = path.stem
            declared = payload.get("week", week)
            if declared != week:
                raise SystemExit(f"Week mismatch in {path}: {declared} != {week}")
            if week in weeks:
                raise SystemExit(f"Duplicate curated Sky Note for {week}: legacy catalog and {path}")
            weeks[week] = payload

    actual = set(weeks)
    missing = sorted(EXPECTED_WEEKS - actual)
    extra = sorted(actual - EXPECTED_WEEKS)
    if missing or extra:
        raise SystemExit(f"Curated Sky Note coverage invalid: missing={missing}, extra={extra}")
    if len(weeks) != 53:
        raise SystemExit(f"Expected exactly 53 curated Sky Notes, found {len(weeks)}")
    return weeks


def main():
    text = ALMANACK.read_text(encoding="utf-8")
    weeks = load_notes()
    messier_catalog = load_messier_catalog()
    for week, payload in sorted(weeks.items()):
        note = payload.get("note", "").strip()
        if not re.fullmatch(r"W(?:0[1-9]|[1-4]\d|5[0-3])", week):
            raise SystemExit(f"Invalid week key: {week}")
        if not note:
            raise SystemExit(f"Empty note for {week}")
        if note == PLACEHOLDER_NOTE:
            raise SystemExit(f"Placeholder Sky Note survived for {week}")
        note = expand_messier_mentions(note, messier_catalog)
        text = replace_week_note(text, week, note)
    ALMANACK.write_text(text, encoding="utf-8")
    print("Applied and verified curated Sky Notes for all 53 weeks with expanded Messier prose")


if __name__ == "__main__":
    main()
