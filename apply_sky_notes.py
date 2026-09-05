#!/usr/bin/env python3
"""Apply curated observer-first Sky Notes to the generated 2026 Almanack."""
from pathlib import Path
import json
import re

ROOT = Path(__file__).parent
ALMANACK = ROOT / "almanack-expanded.md"
NOTES = ROOT / "sky-notes-2026.json"
NOTES_DIR = ROOT / "sky-notes-2026"


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
    """Load the legacy catalog, then overlay modular week files when present."""
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
        text = replace_week_note(text, week, note)
    ALMANACK.write_text(text, encoding="utf-8")
    print(f"Applied curated Sky Notes to {len(weeks)} week(s)")


if __name__ == "__main__":
    main()
