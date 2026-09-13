#!/usr/bin/env python3
"""Apply curated observer-first Sky Notes to the generated 2026 Almanack.

Planetary context is consumed from the Star Almanack's canonical weekly
planetary data file.  This module does not query Horizons or any other external
ephemeris service.  It also emits machine-readable artwork descriptors that
reference the accepted constellation-figure definitions.
"""
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
WEEKLY_EPHEMERIS = ROOT / "weekly-ephemeris-2026.csv"
CONSTELLATION_FIGURES = ROOT / "constellation-figures.json"
ARTWORK_DESCRIPTORS = ROOT / "sky-note-artwork-descriptors-2026.json"
EXPECTED_WEEKS = {f"W{i:02d}" for i in range(1, 54)}
PLACEHOLDER_NOTE = "Weekly geocentric tropical planetary positions, sampled Monday at 00:00 UTC."

# Observer-first anchors. These are intentionally selective rather than repetitive:
# asterisms are highlighted when they are especially useful for orientation or star-hopping.
ASTERISM_NOTES = {
    "W02": "**Asterism:** Orion's Belt is an easy three-star anchor for winter orientation; follow the Belt southeast toward Sirius and northwest toward Aldebaran.",
    "W05": "**Asterism:** The Winter Triangle—Sirius, Procyon, and Betelgeuse—gives a large naked-eye frame for the season's bright-star field.",
    "W09": "**Asterism:** The Winter Hexagon links Capella, Aldebaran, Rigel, Sirius, Procyon, and Pollux into a broad guide around the winter sky.",
    "W16": "**Asterism:** The Sickle of Leo, beginning at Regulus, is the easiest pattern for tracing the head and mane of Leo.",
    "W20": "**Asterism:** The Big Dipper is an observing tool as much as a familiar pattern: its pointer stars lead to Polaris, while the handle arcs toward Arcturus.",
    "W23": "**Asterism:** The Spring Triangle—Arcturus, Spica, and Regulus—provides a wide seasonal framework for finding the brighter spring constellations.",
    "W28": "**Asterism:** The Keystone of Hercules is a compact four-star doorway into Hercules and a practical starting point for locating the Great Hercules Globular.",
    "W31": "**Asterism:** The Teapot of Sagittarius is one of the best summer Milky Way anchors; its spout points into the richest star-cloud region toward the Galactic center.",
    "W33": "**Asterism:** The Summer Triangle—Vega, Deneb, and Altair—dominates the evening sky and provides a large-scale map for Lyra, Cygnus, and Aquila.",
    "W36": "**Asterism:** The Northern Cross, formed by the brightest stars of Cygnus, lies along the Milky Way and is a useful bridge between Deneb and the rich star fields to the south.",
    "W40": "**Asterism:** The Great Square of Pegasus is the principal autumn signpost; its four corners open paths toward Andromeda, Pisces, and the fainter autumn constellations.",
    "W46": "**Asterism:** The Circlet of Pisces is a subtle but useful small-ring pattern southwest of the Great Square, especially under darker skies.",
    "W50": "**Asterism:** Cassiopeia's familiar W shape is a strong northern anchor and a practical guide into the dense Milky Way fields of Cassiopeia and Perseus.",
}

# 2026 maxima and observing circumstances are based on the International Meteor
# Organization Meteor Shower Calendar 2026. Keep these concise and observational.
METEOR_NOTES = {
    "W01": "**Meteor shower:** The Quadrantids peak on January 3. Their maximum is usually sharp, but bright moonlight is an important limitation in 2026.",
    "W17": "**Meteor shower:** The April Lyrids peak on April 22, with the nominal 2026 maximum near 19:40 UT. The expected ZHR is about 18, and moonlight should not be a major obstacle.",
    "W19": "**Meteor shower:** The η-Aquariids peak on May 6. The shower can be strong, especially from lower latitudes and the Southern Hemisphere, but the waning gibbous Moon interferes in 2026.",
    "W31": "**Meteor showers:** The Southern δ-Aquariids and α-Capricornids both reach maximum around July 31. The δ-Aquariids provide the higher rate, while the α-Capricornids are noted for slower meteors and occasional bright events.",
    "W33": "**Meteor shower:** The Perseids peak around August 13 with a nominal ZHR near 100. New Moon falls on August 12, making 2026 especially favorable for dark-sky observing.",
    "W43": "**Meteor shower:** The Orionids peak on October 21 with a typical ZHR of 20 or more. The 2026 maximum is favorably placed with little moonlight interference.",
    "W47": "**Meteor shower:** The Leonids peak on November 17, with the regular nodal maximum near 23:45 UT and an expected ZHR around 15. Moonlight should not seriously hinder the peak.",
    "W51": "**Meteor shower:** The Geminids peak on December 14 and are the year's strongest dependable shower, with a nominal ZHR near 150. Only a waxing crescent Moon is present near maximum.",
    "W52": "**Meteor shower:** The Ursids peak on December 22 near 22:00 UT. A nearly full Moon makes the 2026 return difficult for visual observing.",
}

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

PLANET_FIELDS = ("mercury", "venus", "mars", "jupiter", "saturn")
PLANET_NAMES = {
    "mercury": "Mercury",
    "venus": "Venus",
    "mars": "Mars",
    "jupiter": "Jupiter",
    "saturn": "Saturn",
}
SIGNS = "♈♉♊♋♌♍♎♏♐♑♒♓"


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


def zodiac_longitude(value: str) -> float:
    """Parse the Almanack's zodiac notation into absolute tropical longitude."""
    m = re.fullmatch(r"\s*([♈♉♊♋♌♍♎♏♐♑♒♓])\s*(\d{1,2})°(\d{2})′\s*", value)
    if not m:
        raise ValueError(f"Unrecognized zodiac value: {value!r}")
    return SIGNS.index(m.group(1)) * 30.0 + int(m.group(2)) + int(m.group(3)) / 60.0


def angular_separation(a: float, b: float) -> float:
    d = abs(a - b) % 360.0
    return min(d, 360.0 - d)


def load_planetary_context() -> dict[str, dict[str, str]]:
    """Load already-calculated Almanack weekly positions; never query a service here."""
    with WEEKLY_EPHEMERIS.open(encoding="utf-8", newline="") as f:
        rows = list(csv.DictReader(f))
    result = {}
    for row in rows:
        key = row.get("iso_week", "")
        m = re.fullmatch(r"2026-(W\d{2})", key)
        if not m:
            continue
        result[m.group(1)] = row
    missing = sorted(EXPECTED_WEEKS - set(result))
    if missing:
        raise SystemExit(f"Canonical weekly planetary data missing weeks: {missing}")
    return result


def planetary_note(row: dict[str, str]) -> str | None:
    """Report only unusually close planet-planet longitude groupings.

    This intentionally uses the shared Almanack snapshot rather than computing
    another ephemeris inside Sky Notes. A 5° threshold keeps the prose selective.
    """
    positions = {field: zodiac_longitude(row[field]) for field in PLANET_FIELDS}
    candidates = []
    fields = list(PLANET_FIELDS)
    for i, left in enumerate(fields):
        for right in fields[i + 1:]:
            separation = angular_separation(positions[left], positions[right])
            if separation <= 5.0:
                candidates.append((separation, left, right))
    if not candidates:
        return None
    separation, left, right = min(candidates)
    return (
        f"**Planet watch:** {PLANET_NAMES[left]} and {PLANET_NAMES[right]} are "
        f"about {separation:.1f}° apart in tropical longitude at the Almanack's "
        "Monday 00:00 UTC weekly snapshot."
    )


def enrich_observer_note(week: str, note: str, planetary: dict[str, dict[str, str]]) -> str:
    """Append high-value observer anchors without displacing the curated prose."""
    additions = []
    if week in ASTERISM_NOTES:
        additions.append(ASTERISM_NOTES[week])
    pnote = planetary_note(planetary[week])
    if pnote:
        additions.append(pnote)
    if week in METEOR_NOTES:
        additions.append(METEOR_NOTES[week])
    if not additions:
        return note
    return note.rstrip() + "\n\n" + "\n\n".join(additions)


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


def artwork_descriptor_for(week: str, note: str, figures: dict) -> dict | None:
    """Create an artwork-generator handoff only when an accepted figure applies."""
    text = note.lower()
    chosen = None
    if any(token in text for token in ("pegasus", "enif", "great square", "m15")):
        chosen = "Pegasus"
    elif any(token in text for token in ("aquarius", "sadalmelik", "water jar")):
        chosen = "Aquarius"
    if not chosen or chosen not in figures:
        return None

    figure = figures[chosen]
    featured = []
    for asterism in figure.get("asterisms", []):
        if asterism["name"].lower() in text or (
            chosen == "Pegasus" and asterism["name"] == "Great Square of Pegasus"
        ):
            featured.append(asterism["name"])

    targets = []
    if figure.get("target_name") and figure["target_name"].lower() in text:
        targets.append(figure["target_name"])
    for obj in figure.get("deep_sky_objects", []):
        if obj["name"].lower() in text:
            targets.append(obj["name"])

    return {
        "week": week,
        "constellation": chosen,
        "figure_source": "constellation-figures.json",
        "figure_standard": "accepted Martz/MacRobert stick figure",
        "constellation_line_color": "blue",
        "featured_asterism_color": "green",
        "featured_asterisms": featured,
        "circle_targets": targets,
        "instructions": (
            "Use the accepted figure paths exactly; do not invent a replacement stick figure. "
            "Draw the constellation in blue, emphasize the featured asterism in green, and circle "
            "named observing targets when present."
        ),
    }


def write_artwork_descriptors(weeks: dict) -> int:
    figures = json.loads(CONSTELLATION_FIGURES.read_text(encoding="utf-8"))
    descriptors = []
    for week, payload in sorted(weeks.items()):
        descriptor = artwork_descriptor_for(week, payload.get("note", ""), figures)
        if descriptor:
            descriptors.append(descriptor)
    output = {
        "year": 2026,
        "purpose": "Sky Notes artwork-generator handoff",
        "descriptors": descriptors,
    }
    ARTWORK_DESCRIPTORS.write_text(json.dumps(output, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return len(descriptors)


def main():
    text = ALMANACK.read_text(encoding="utf-8")
    weeks = load_notes()
    messier_catalog = load_messier_catalog()
    planetary = load_planetary_context()
    for week, payload in sorted(weeks.items()):
        note = payload.get("note", "").strip()
        if not re.fullmatch(r"W(?:0[1-9]|[1-4]\d|5[0-3])", week):
            raise SystemExit(f"Invalid week key: {week}")
        if not note:
            raise SystemExit(f"Empty note for {week}")
        if note == PLACEHOLDER_NOTE:
            raise SystemExit(f"Placeholder Sky Note survived for {week}")
        note = enrich_observer_note(week, note, planetary)
        note = expand_messier_mentions(note, messier_catalog)
        text = replace_week_note(text, week, note)
    ALMANACK.write_text(text, encoding="utf-8")
    descriptor_count = write_artwork_descriptors(weeks)
    print(
        "Applied curated Sky Notes for all 53 weeks using shared Almanack planetary data; "
        f"wrote {descriptor_count} accepted-figure artwork descriptors"
    )


if __name__ == "__main__":
    main()
