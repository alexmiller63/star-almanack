#!/usr/bin/env python3
"""Apply curated observer-first Sky Notes to the generated 2026 Almanack."""
from pathlib import Path
import json
import re

ROOT = Path(__file__).parent
ALMANACK = ROOT / "almanack-expanded.md"
NOTES = ROOT / "sky-notes-2026.json"
NOTES_DIR = ROOT / "sky-notes-2026"
EXPECTED_WEEKS = {f"W{i:02d}" for i in range(1, 54)}
PLACEHOLDER_NOTE = "Weekly geocentric tropical planetary positions, sampled Monday at 00:00 UTC."


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
    for week, payload in sorted(weeks.items()):
        note = payload.get("note", "").strip()
        if not re.fullmatch(r"W(?:0[1-9]|[1-4]\d|5[0-3])", week):
            raise SystemExit(f"Invalid week key: {week}")
        if not note:
            raise SystemExit(f"Empty note for {week}")
        if note == PLACEHOLDER_NOTE:
            raise SystemExit(f"Placeholder Sky Note survived for {week}")
        text = replace_week_note(text, week, note)
    ALMANACK.write_text(text, encoding="utf-8")
    print("Applied and verified curated Sky Notes for all 53 weeks")


if __name__ == "__main__":
    main()
