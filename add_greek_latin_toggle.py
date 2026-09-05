#!/usr/bin/env python3
"""Add a Greek/Latin Bayer-designation toggle to the 2026 weekly pages.

Greek symbols remain the default.  Latin mode uses the compact catalog-style
abbreviations already used by the Almanack source tradition (Gam-2, Eps, etc.).
"""

from pathlib import Path

ROOT = Path(__file__).parent / "site" / "2026"

TOGGLE_CSS = r"""
.bayer-toggle-wrap { max-width:1080px; margin:0 auto; padding:.75rem 1.5rem 0; font-family:system-ui,-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif; }
.bayer-toggle { display:flex; align-items:center; justify-content:flex-end; gap:.35rem; font-size:.86rem; }
.bayer-toggle-label { margin-right:.2rem; color:var(--muted); }
.bayer-toggle button { appearance:none; border:1px solid #c8d3dc; background:#fff; color:var(--link); padding:.35rem .62rem; border-radius:.4rem; font:inherit; cursor:pointer; }
.bayer-toggle button[aria-pressed="true"] { background:var(--navy); color:#fff; border-color:var(--navy); }
@media (max-width:760px) { .bayer-toggle-wrap { padding-left:1rem; padding-right:1rem; } }
@media (prefers-color-scheme:dark) { .bayer-toggle button { background:#1c2a36; border-color:#405567; color:#b6dcff; } .bayer-toggle button[aria-pressed="true"] { background:#eef7ff; color:#102a43; border-color:#eef7ff; } }
""".strip()

TOGGLE_HTML = r'''<div class="bayer-toggle-wrap"><div class="bayer-toggle" role="group" aria-label="Bayer designation notation"><span class="bayer-toggle-label">Bayer:</span><button type="button" data-bayer-mode="greek" aria-pressed="true">Greek</button><button type="button" data-bayer-mode="latin" aria-pressed="false">Latin</button></div></div>'''

TOGGLE_JS = r'''<script>
(function () {
  const latin = {
    'α':'Alp','β':'Bet','γ':'Gam','δ':'Del','ε':'Eps','ζ':'Zet','η':'Eta','θ':'The',
    'ι':'Iot','κ':'Kap','λ':'Lam','μ':'Mu','ν':'Nu','ξ':'Xi','ο':'Omi','π':'Pi',
    'ρ':'Rho','σ':'Sig','τ':'Tau','υ':'Ups','φ':'Phi','χ':'Chi','ψ':'Psi','ω':'Ome'
  };
  const main = document.querySelector('main');
  if (!main) return;

  const re = /([αβγδεζηθικλμνξοπρστυφχψω])(\d+)?/g;
  const walker = document.createTreeWalker(main, NodeFilter.SHOW_TEXT);
  const nodes = [];
  while (walker.nextNode()) {
    if (re.test(walker.currentNode.nodeValue)) nodes.push(walker.currentNode);
    re.lastIndex = 0;
  }

  for (const node of nodes) {
    const frag = document.createDocumentFragment();
    let last = 0;
    node.nodeValue.replace(re, function (match, letter, number, offset) {
      frag.append(document.createTextNode(node.nodeValue.slice(last, offset)));
      const span = document.createElement('span');
      span.className = 'bayer-letter';
      span.dataset.greek = match;
      span.dataset.latin = latin[letter] + (number ? '-' + number : '');
      span.textContent = match;
      frag.append(span);
      last = offset + match.length;
      return match;
    });
    frag.append(document.createTextNode(node.nodeValue.slice(last)));
    node.replaceWith(frag);
  }

  const buttons = document.querySelectorAll('[data-bayer-mode]');
  function setMode(mode) {
    document.querySelectorAll('.bayer-letter').forEach(function (span) {
      span.textContent = mode === 'latin' ? span.dataset.latin : span.dataset.greek;
    });
    buttons.forEach(function (button) {
      button.setAttribute('aria-pressed', button.dataset.bayerMode === mode ? 'true' : 'false');
    });
    try { localStorage.setItem('star-almanack-bayer-mode', mode); } catch (_) {}
  }
  buttons.forEach(function (button) {
    button.addEventListener('click', function () { setMode(button.dataset.bayerMode); });
  });
  let initial = 'greek';
  try {
    const saved = localStorage.getItem('star-almanack-bayer-mode');
    if (saved === 'latin' || saved === 'greek') initial = saved;
  } catch (_) {}
  setMode(initial);
})();
</script>'''


def add_toggle(path: Path) -> None:
    text = path.read_text(encoding="utf-8")
    if 'data-bayer-mode="greek"' in text:
        return
    if "</style>" not in text or "</header>" not in text or "</body>" not in text:
        raise RuntimeError(f"Unexpected page shell in {path}")
    text = text.replace("</style>", TOGGLE_CSS + "\n</style>", 1)
    text = text.replace("</header>", "</header>" + TOGGLE_HTML, 1)
    text = text.replace("</body>", TOGGLE_JS + "</body>", 1)
    path.write_text(text, encoding="utf-8")


def main() -> None:
    pages = sorted(ROOT.glob("W??/index.html"))
    if len(pages) != 53:
        raise SystemExit(f"Expected 53 weekly pages, found {len(pages)}")
    for page in pages:
        add_toggle(page)
    print("Added Greek/Latin Bayer toggle to 53 weekly pages")


if __name__ == "__main__":
    main()
