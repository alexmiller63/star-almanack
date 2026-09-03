#!/usr/bin/env python3
"""Publish the expanded 2026 Star Almanack as 53 static weekly HTML pages.

Input:  almanack-expanded.md
Output: site/2026/index.html and site/2026/W01..W53/index.html

The publisher deliberately uses only the Python standard library so GitHub
Actions can regenerate the site reproducibly without an extra Markdown stack.
It supports the Markdown constructs used by the weekly Almanack: headings,
paragraphs, bold/emphasis, inline code, and pipe tables.
"""

from __future__ import annotations

import html
import re
import shutil
from pathlib import Path

ROOT = Path(__file__).parent
SOURCE = ROOT / "almanack-expanded.md"
OUT = ROOT / "site" / "2026"
WEEK_RE = re.compile(r"(?m)^## (ISO 2026-W(\d{2}))\s*$")

ZODIAC_NAMES = {
    "♈": "Aries",
    "♉": "Taurus",
    "♊": "Gemini",
    "♋": "Cancer",
    "♌": "Leo",
    "♍": "Virgo",
    "♎": "Libra",
    "♏": "Scorpio",
    "♐": "Sagittarius",
    "♑": "Capricorn",
    "♒": "Aquarius",
    "♓": "Pisces",
}

CSS = """
:root {
  color-scheme: light dark;
  --ink: #202833;
  --muted: #66717d;
  --navy: #102a43;
  --navy-2: #173f5f;
  --link: #245c86;
  --paper: #fffdf8;
  --page: #eee9df;
  --rule: #d8d2c8;
  --soft: #f4f1ea;
  --soft-blue: #edf4f8;
}
* { box-sizing: border-box; }
html { font-size: 17px; }
body {
  margin: 0;
  font-family: Georgia, 'Times New Roman', serif;
  line-height: 1.65;
  background: var(--page);
  color: var(--ink);
  -webkit-font-smoothing: antialiased;
}
a, a:visited { color: var(--link); text-underline-offset: .15em; }
a:hover { text-decoration-thickness: 2px; }
header, footer { background: var(--navy); color: #fff; }
header { border-bottom: 4px solid #c5a45c; }
header a, header a:visited, footer a, footer a:visited { color: #eef7ff; }
.wrap { max-width: 1080px; margin: 0 auto; padding: 1.15rem 1.5rem; }
main.wrap {
  background: var(--paper);
  min-height: 76vh;
  padding: 2rem 2.4rem 3.25rem;
  box-shadow: 0 0 28px rgba(25, 35, 45, .08);
}
.brand { font-size: 1.35rem; font-weight: 700; letter-spacing: .015em; }
.brand a { text-decoration: none; }
.subtitle { margin-top: .1rem; opacity: .86; font-size: .94rem; letter-spacing: .02em; }
nav.weeknav {
  display: grid;
  grid-template-columns: 1fr auto 1fr;
  align-items: center;
  gap: .8rem;
  margin: .4rem 0 2rem;
  font-family: system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
  font-size: .9rem;
}
nav.weeknav > :last-child { justify-self: end; }
nav.weeknav a, nav.weeknav a:visited, nav.weeknav span {
  display: inline-block;
  min-width: 5.5rem;
  padding: .58rem .8rem;
  border: 1px solid #c8d3dc;
  border-radius: .45rem;
  text-decoration: none;
  text-align: center;
  color: var(--link);
  background: #fff;
}
nav.weeknav a:hover { background: var(--soft-blue); border-color: #9fb7c8; }
nav.weeknav span { color: #89929b; background: #f5f5f3; }
h1, h2, h3 { line-height: 1.2; color: #17344d; }
h1 { margin: .3rem 0 1rem; font-size: clamp(2rem, 5vw, 2.75rem); letter-spacing: -.02em; }
h2 { margin: 2.25rem 0 .8rem; padding-bottom: .35rem; border-bottom: 1px solid var(--rule); font-size: 1.42rem; }
h3 { margin-top: 1.7rem; }
p { max-width: 72ch; margin: .7rem 0 1rem; }
strong { color: #162d42; }
table {
  width: 100%;
  border-collapse: separate;
  border-spacing: 0;
  margin: 1rem 0 2rem;
  font-family: system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
  font-size: .93rem;
  line-height: 1.45;
  border: 1px solid #cbd3da;
  border-radius: .5rem;
  overflow: hidden;
}
th, td { padding: .7rem .8rem; vertical-align: top; border-right: 1px solid #d6dde3; border-bottom: 1px solid #d6dde3; }
th:last-child, td:last-child { border-right: 0; }
tbody tr:last-child td { border-bottom: 0; }
th { background: #e8f0f5; text-align: left; color: #17344d; font-weight: 700; }
tbody tr:nth-child(even) td { background: #fbfaf7; }
table.calendar { display: table; table-layout: fixed; }
table.calendar td:first-child { width: 25%; white-space: nowrap; font-weight: 600; }
table.calendar td:nth-child(2) { width: 13%; white-space: nowrap; text-align: center; }
table.calendar td:nth-child(3) { line-height: 1.6; }
table.ephemeris { font-size: .9rem; }
table.ephemeris th, table.ephemeris td { text-align: center; }
table.ephemeris td { white-space: nowrap; padding-top: .8rem; padding-bottom: .8rem; }
.zodiac-glyph {
  font-family: Georgia, 'Times New Roman', serif;
  font-variant-emoji: text;
  color: currentColor;
}
.zodiac-name { display: block; font-family: Georgia, 'Times New Roman', serif; font-size: .78rem; color: var(--muted); margin-top: .12rem; }
code { background: #eef1f3; padding: .1rem .3rem; border-radius: .25rem; font-size: .9em; }
.weekgrid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(145px, 1fr));
  gap: .7rem;
  padding: 0;
  margin: 1.5rem 0 0;
  list-style: none;
  font-family: system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
}
.weekgrid a, .weekgrid a:visited {
  display: block;
  padding: .85rem .9rem;
  border: 1px solid #cbd3da;
  border-radius: .5rem;
  text-decoration: none;
  text-align: center;
  background: #fff;
  color: var(--link);
  font-weight: 650;
}
.weekgrid a:hover { background: var(--soft-blue); border-color: #9fb7c8; transform: translateY(-1px); }
footer { font-family: system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; font-size: .88rem; }
footer .wrap { padding-top: 1.3rem; padding-bottom: 1.3rem; opacity: .9; }
@media (max-width: 760px) {
  html { font-size: 16px; }
  .wrap { padding-left: 1rem; padding-right: 1rem; }
  main.wrap { padding: 1.35rem 1rem 2.5rem; box-shadow: none; }
  nav.weeknav { gap: .4rem; margin-bottom: 1.5rem; }
  nav.weeknav a, nav.weeknav a:visited, nav.weeknav span { min-width: 0; padding: .6rem .45rem; }
  table { font-size: .9rem; }
  table.calendar { display: table; width: 100%; table-layout: fixed; overflow: hidden; }
  table.calendar th, table.calendar td { padding: .6rem .55rem; }
  table.calendar td:first-child { width: 30%; min-width: 0; white-space: normal; }
  table.calendar td:nth-child(2) { width: 18%; min-width: 0; white-space: nowrap; }
  table.calendar td:nth-child(3) { width: 52%; min-width: 0; overflow-wrap: anywhere; }
  table.ephemeris { display: block; overflow-x: auto; -webkit-overflow-scrolling: touch; font-size: .86rem; }
  .weekgrid { grid-template-columns: repeat(2, minmax(0, 1fr)); }
}
@media (prefers-color-scheme: dark) {
  :root {
    --ink: #dce6ef;
    --muted: #a7b4c0;
    --link: #9fd0ff;
    --paper: #17212b;
    --page: #10171f;
    --rule: #394957;
    --soft-blue: #203549;
  }
  body { background: var(--page); color: var(--ink); }
  main.wrap { background: var(--paper); box-shadow: none; }
  h1, h2, h3, strong { color: #f1f7fb; }
  th { background: #223444; color: #eef7ff; }
  th, td { border-color: #40505e; }
  table { border-color: #40505e; }
  tbody tr:nth-child(even) td { background: #1b2732; }
  code { background: #263643; }
  .weekgrid a, .weekgrid a:visited,
  nav.weeknav a, nav.weeknav a:visited { background: #1c2a36; border-color: #405567; color: #b6dcff; }
  .weekgrid a:hover, nav.weeknav a:hover { background: #253b4e; }
  nav.weeknav span { background: #1a242d; border-color: #384956; color: #7f909f; }
}
""".strip()


def inline_markup(text: str) -> str:
    sentinel = "@@BR@@"
    text = text.replace("<br>", sentinel)
    text = html.escape(text)
    # Force every zodiac sign, including ingress signs in event prose, to
    # monochrome text presentation instead of a platform-colored emoji.
    for glyph in ZODIAC_NAMES:
        text = text.replace(glyph + "\ufe0f", glyph).replace(glyph + "\ufe0e", glyph)
        text = text.replace(glyph, zodiac_glyph(glyph))
    text = re.sub(r"`([^`]+)`", r"<code>\1</code>", text)
    text = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", text)
    text = re.sub(r"(?<!\*)\*([^*]+)\*(?!\*)", r"<em>\1</em>", text)
    return text.replace(sentinel, "<br>")


def is_separator_row(line: str) -> bool:
    cells = [c.strip() for c in line.strip().strip("|").split("|")]
    return bool(cells) and all(re.fullmatch(r":?-{3,}:?", c or "") for c in cells)


def zodiac_glyph(glyph: str) -> str:
    """Render a zodiac sign as monochrome text, never as a color emoji."""
    return f'<span class="zodiac-glyph">{html.escape(glyph)}&#xfe0e;</span>'


def format_zodiac_cell(text: str, include_name: bool = False) -> str:
    stripped = text.strip()
    if stripped and stripped[0] in ZODIAC_NAMES:
        glyph = stripped[0]
        remainder = stripped[1:].strip()
        if not include_name:
            remainder = re.sub(
                rf"^\({re.escape(ZODIAC_NAMES[glyph])}\)\s*",
                "",
                remainder,
            )
        name = f'<span class="zodiac-name">{ZODIAC_NAMES[glyph]}</span>' if include_name else ""
        spacer = " " if remainder else ""
        return f"{zodiac_glyph(glyph)}{spacer}{inline_markup(remainder)}{name}"
    return inline_markup(text)


def format_ephemeris_cell(text: str) -> str:
    return format_zodiac_cell(text, include_name=True)


def parse_table(lines: list[str], start: int) -> tuple[str, int]:
    rows: list[list[str]] = []
    i = start
    while i < len(lines):
        line = lines[i]
        if not line.strip():
            j = i + 1
            while j < len(lines) and not lines[j].strip():
                j += 1
            if j < len(lines) and lines[j].lstrip().startswith("|"):
                i = j
                continue
            break
        if not line.lstrip().startswith("|"):
            break
        if not is_separator_row(line):
            rows.append([c.strip() for c in line.strip().strip("|").split("|")])
        i += 1

    if not rows:
        return "", i

    head = rows[0]
    body = rows[1:]
    is_ephemeris = len(head) == 7 and head[0].startswith("☉ Sun") and head[-1].startswith("♄ Saturn")
    is_calendar = len(head) == 3 and head == ["Date", "Zodiac day", "Events"]
    table_class = ' class="ephemeris"' if is_ephemeris else (' class="calendar"' if is_calendar else "")
    out = [f"<table{table_class}><thead><tr>"]
    out.extend(f"<th>{inline_markup(c)}</th>" for c in head)
    out.append("</tr></thead><tbody>")
    for row in body:
        out.append("<tr>")
        for index, c in enumerate(row):
            if is_ephemeris:
                cell = format_ephemeris_cell(c)
            elif is_calendar and index == 1:
                cell = format_zodiac_cell(c)
            else:
                cell = inline_markup(c)
            out.append(f"<td>{cell}</td>")
        out.append("</tr>")
    out.append("</tbody></table>")
    return "".join(out), i


def markdown_fragment(md: str) -> str:
    lines = md.splitlines()
    out: list[str] = []
    para: list[str] = []

    def flush_para() -> None:
        if para:
            text = " ".join(x.strip() for x in para).strip()
            if text:
                out.append(f"<p>{inline_markup(text)}</p>")
            para.clear()

    i = 0
    while i < len(lines):
        line = lines[i]
        stripped = line.strip()
        if not stripped:
            flush_para()
            i += 1
            continue
        if line.lstrip().startswith("|"):
            flush_para()
            table, i = parse_table(lines, i)
            out.append(table)
            continue
        m = re.match(r"^(#{1,4})\s+(.+)$", line)
        if m:
            flush_para()
            level = len(m.group(1))
            rendered_level = max(1, level - 1)
            out.append(f"<h{rendered_level}>{inline_markup(m.group(2))}</h{rendered_level}>")
            i += 1
            continue
        para.append(line)
        i += 1
    flush_para()
    return "\n".join(out)


def shell(title: str, body: str, nav: str = "") -> str:
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{html.escape(title)} · Star Almanack</title>
<style>{CSS}</style>
</head>
<body>
<header><div class="wrap"><div class="brand"><a href="../index.html">Star Almanack — 2026</a></div><div class="subtitle">A Natural Philosopher's Guide to the Night Sky</div></div></header>
<main class="wrap">{nav}{body}{nav}</main>
<footer><div class="wrap">Star Almanack · ISO week-year 2026</div></footer>
</body></html>
"""


def week_nav(week: int) -> str:
    prev_link = f'<a rel="prev" href="../W{week-1:02d}/index.html">← W{week-1:02d}</a>' if week > 1 else "<span>← Start</span>"
    next_link = f'<a rel="next" href="../W{week+1:02d}/index.html">W{week+1:02d} →</a>' if week < 53 else "<span>End →</span>"
    return f'<nav class="weeknav">{prev_link}<a href="../index.html">2026 index</a>{next_link}</nav>'


def split_weeks(text: str) -> list[tuple[int, str]]:
    matches = list(WEEK_RE.finditer(text))
    if len(matches) != 53:
        raise SystemExit(f"Expected 53 weekly sections, found {len(matches)}")
    result = []
    for idx, match in enumerate(matches):
        start = match.start()
        end = matches[idx + 1].start() if idx + 1 < len(matches) else text.find("\n## Expanded α and β Star Catalog", start)
        if end == -1:
            end = len(text)
        week = int(match.group(2))
        result.append((week, text[start:end].strip()))
    return result


def build() -> None:
    text = SOURCE.read_text(encoding="utf-8")
    weeks = split_weeks(text)
    if OUT.exists():
        shutil.rmtree(OUT)
    OUT.mkdir(parents=True)

    links = []
    for week, md in weeks:
        page_dir = OUT / f"W{week:02d}"
        page_dir.mkdir()
        page = shell(f"ISO 2026-W{week:02d}", markdown_fragment(md), week_nav(week))
        (page_dir / "index.html").write_text(page, encoding="utf-8")
        links.append(f'<li><a href="W{week:02d}/index.html">ISO 2026-W{week:02d}</a></li>')

    index_body = (
        "<h1>Star Almanack — 2026</h1>"
        "<p>Browse all 53 ISO weeks of the 2026 Star Almanack. "
        "ISO 2026 begins Monday, December 29, 2025 and ends Sunday, January 3, 2027.</p>"
        f'<ul class="weekgrid">{"".join(links)}</ul>'
    )
    index = shell("2026 weekly index", index_body).replace('href="../index.html"', 'href="index.html"')
    (OUT / "index.html").write_text(index, encoding="utf-8")

    generated = list(OUT.glob("W??/index.html"))
    if len(generated) != 53:
        raise SystemExit(f"Expected 53 weekly HTML pages, generated {len(generated)}")
    print("Published 53 weekly HTML pages plus the 2026 index under site/2026/")


if __name__ == "__main__":
    build()
