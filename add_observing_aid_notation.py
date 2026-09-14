#!/usr/bin/env python3
"""Make observing-aid glyphs participate in Greek/Latin/Mixed notation modes.

Greek/Symbols: glyph only (👁, B, 🔭)
Latin: words only (Naked eye, Binoculars, Telescope)
Mixed Learner: glyph plus word
"""
import argparse
from pathlib import Path

from iso_week_range import IsoWeekRange

ROOT = Path(__file__).parent / "site" / "2026"

OLD_RENDER = "function render(s,value){s.replaceChildren();let a=Array.from(value);if(a.length&&glyphs.has(a[0])){let q=document.createElement('span');q.className='almanack-glyph';q.textContent=a[0]+VS;s.append(q);let rest=a.slice(1).join('').replace(/^\\ufe0e/,'');if(rest)s.append(document.createTextNode(rest))}else{s.textContent=value}}"

NEW_RENDER = "function render(s,value){s.replaceChildren();if(s.dataset.observingAid==='1'&&value===s.dataset.greek){let q=document.createElement('span');q.className='almanack-glyph';q.textContent=value;s.append(q);return}let a=Array.from(value);if(a.length&&glyphs.has(a[0])){let q=document.createElement('span');q.className='almanack-glyph';q.textContent=a[0]+VS;s.append(q);let rest=a.slice(1).join('').replace(/^\\ufe0e/,'');if(rest)s.append(document.createTextNode(rest))}else{s.textContent=value}}"

ANCHOR = "document.querySelectorAll('.zodiac-notation-source').forEach(s=>{let x=s.textContent.charAt(0);if(z[x]){s.className='notation-item';s.dataset.greek=x+VS;s.dataset.latin=z[x];s.dataset.mixed=x+VS+'\\n'+z[x]}});"

AID_JS = r"""
const observingAids={'👁':'Naked eye','B':'Binoculars','🔭':'Telescope'};
document.querySelectorAll('table.calendar tbody td:nth-child(3) .almanack-glyph').forEach(s=>{let x=s.textContent.replace(VS,'').trim();if(observingAids[x]){s.className='notation-item observing-aid';s.dataset.observingAid='1';s.dataset.greek=x;s.dataset.latin=observingAids[x];s.dataset.mixed=x+' '+observingAids[x]}});
""".strip()


def patch(page: Path) -> None:
    text = page.read_text(encoding="utf-8")
    if "const observingAids=" in text:
        return
    if OLD_RENDER not in text:
        raise SystemExit(f"Notation render function not found in {page}")
    if ANCHOR not in text:
        raise SystemExit(f"Notation initialization anchor not found in {page}")
    text = text.replace(OLD_RENDER, NEW_RENDER, 1)
    text = text.replace(ANCHOR, ANCHOR + "\n" + AID_JS, 1)
    page.write_text(text, encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("first_iso_week", nargs="?")
    parser.add_argument("last_iso_week", nargs="?")
    parser.add_argument("--site-root", type=Path, default=Path(__file__).parent / "site")
    args = parser.parse_args()
    if args.first_iso_week:
        requested = IsoWeekRange.parse(args.first_iso_week, args.last_iso_week)
        pages = [args.site_root / str(item.year) / f"W{item.week:02d}" / "index.html" for item in requested.weeks()]
    else:
        pages = sorted(ROOT.glob("W??/index.html"))
    missing = [page for page in pages if not page.exists()]
    if missing:
        raise SystemExit(f"Missing weekly pages: {missing[:5]}")
    for page in pages:
        patch(page)
    print(f"Added notation-aware observing aids to {len(pages)} weekly pages")


if __name__ == "__main__":
    main()
