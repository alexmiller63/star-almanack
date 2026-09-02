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

CSS = """
:root { color-scheme: light dark; }
* { box-sizing: border-box; }
body { margin: 0; font-family: Georgia, 'Times New Roman', serif; line-height: 1.55; background: #f7f4ec; color: #1f2833; }
a { color: #244d74; }
header, footer { background: #0f2740; color: #fff; }
header a, footer a { color: #dcecff; }
.wrap { max-width: 980px; margin: 0 auto; padding: 1.1rem 1.25rem; }
main.wrap { background: #fff; min-height: 75vh; padding-top: 2rem; padding-bottom: 3rem; }
.brand { font-size: 1.2rem; font-weight: 700; }
.subtitle { opacity: .85; }
nav.weeknav { display: flex; justify-content: space-between; align-items: center; gap: 1rem; margin: 1.4rem 0; }
nav.weeknav a, nav.weeknav span { display: inline-block; padding: .5rem .7rem; border: 1px solid #c5ced7; border-radius: .35rem; text-decoration: none; }
h1, h2, h3 { line-height: 1.2; color: #15324e; }
table { width: 100%; border-collapse: collapse; margin: 1rem 0 1.6rem; font-size: .94rem; }
th, td { border: 1px solid #cfd6dd; padding: .55rem .65rem; vertical-align: top; }
th { background: #edf2f6; text-align: left; }
code { background: #eef1f3; padding: .08rem .25rem; border-radius: .2rem; }
.weekgrid { display: grid; grid-template-columns: repeat(auto-fit, minmax(120px,1fr)); gap: .65rem; padding: 0; list-style: none; }
.weekgrid a { display: block; padding: .75rem; border: 1px solid #cbd3da; border-radius: .4rem; text-decoration: none; background: #fafcfd; }
@media (prefers-color-scheme: dark) {
 body { background: #111821; color: #dbe5ee; }
 main.wrap { background: #17202b; }
 h1,h2,h3 { color: #eef7ff; }
 th { background: #233142; }
 th,td { border-color: #425166; }
 code { background: #233142; }
 .weekgrid a { background: #1d2937; border-color: #435268; }
 nav.weeknav a, nav.weeknav span { border-color: #435268; }
}
""".strip()


def inline_markup(text: str) -> str:
    # Preserve deliberate <br> separators from the generated Almanack while
    # escaping all other source text first.
    sentinel = "@@BR@@"
    text = text.replace("<br>", sentinel)
    text = html.escape(text)
    text = re.sub(r"`([^`]+)`", r"<code>\1</code>", text)
    text = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", text)
    text = re.sub(r"(?<!\*)\*([^*]+)\*(?!\*)", r"<em>\1</em>", text)
    return text.replace(sentinel, "<br>")


def is_separator_row(line: str) -> bool:
    cells = [c.strip() for c in line.strip().strip("|").split("|")]
    return bool(cells) and all(re.fullmatch(r":?-{3,}:?", c or "") for c in cells)


def parse_table(lines: list[str], start: int) -> tuple[str, int]:
    rows: list[list[str]] = []
    i = start
    while i < len(lines) and lines[i].lstrip().startswith("|"):
        if not is_separator_row(lines[i]):
            rows.append([c.strip() for c in lines[i].strip().strip("|").split("|")])
        i += 1
    if not rows:
        return "", i
    head = rows[0]
    body = rows[1:]
    out = ["<table><thead><tr>"]
    out.extend(f"<th>{inline_markup(c)}</th>" for c in head)
    out.append("</tr></thead><tbody>")
    for row in body:
        out.append("<tr>")
        out.extend(f"<td>{inline_markup(c)}</td>" for c in row)
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
            # Weekly source begins at ##; render it as the page H1.
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
    # Index is one directory shallower than weekly pages, so give it its own shell links.
    index = shell("2026 weekly index", index_body).replace('href="../index.html"', 'href="index.html"')
    (OUT / "index.html").write_text(index, encoding="utf-8")

    generated = list(OUT.glob("W??/index.html"))
    if len(generated) != 53:
        raise SystemExit(f"Expected 53 weekly HTML pages, generated {len(generated)}")
    print("Published 53 weekly HTML pages plus the 2026 index under site/2026/")


if __name__ == "__main__":
    build()
