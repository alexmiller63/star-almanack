#!/usr/bin/env python3
"""Add a Greek/Latin notation toggle to the 2026 weekly pages.

Greek mode preserves the Almanack's compact astronomical symbols. Latin mode
expands Bayer designations, zodiac signs, and ephemeris body symbols to full
words for readability.
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

TOGGLE_HTML = r'''<div class="bayer-toggle-wrap"><div class="bayer-toggle" role="group" aria-label="Astronomical notation"><span class="bayer-toggle-label">Notation:</span><button type="button" data-bayer-mode="greek" aria-pressed="true">Greek</button><button type="button" data-bayer-mode="latin" aria-pressed="false">Latin</button></div></div>'''

TOGGLE_JS = r'''<script>
(function () {
  const greekNames = {
    'α':'Alpha','β':'Beta','γ':'Gamma','δ':'Delta','ε':'Epsilon','ζ':'Zeta','η':'Eta','θ':'Theta',
    'ι':'Iota','κ':'Kappa','λ':'Lambda','μ':'Mu','ν':'Nu','ξ':'Xi','ο':'Omicron','π':'Pi',
    'ρ':'Rho','σ':'Sigma','τ':'Tau','υ':'Upsilon','φ':'Phi','χ':'Chi','ψ':'Psi','ω':'Omega'
  };
  const constellations = {
    And:'Andromedae',Ant:'Antliae',Aps:'Apodis',Aqr:'Aquarii',Aql:'Aquilae',Ara:'Arae',Ari:'Arietis',Aur:'Aurigae',
    Boo:'Bootis',Cae:'Caeli',Cam:'Camelopardalis',Cnc:'Cancri',CVn:'Canum Venaticorum',CMa:'Canis Majoris',CMi:'Canis Minoris',
    Cap:'Capricorni',Car:'Carinae',Cas:'Cassiopeiae',Cen:'Centauri',Cep:'Cephei',Cet:'Ceti',Cha:'Chamaeleontis',Cir:'Circini',
    Col:'Columbae',Com:'Comae Berenices',CrA:'Coronae Australis',CrB:'Coronae Borealis',Crv:'Corvi',Crt:'Crateris',Cru:'Crucis',
    Cyg:'Cygni',Del:'Delphini',Dor:'Doradus',Dra:'Draconis',Equ:'Equulei',Eri:'Eridani',For:'Fornacis',Gem:'Geminorum',Gru:'Gruis',
    Her:'Herculis',Hor:'Horologii',Hya:'Hydrae',Hyi:'Hydri',Ind:'Indi',Lac:'Lacertae',Leo:'Leonis',LMi:'Leonis Minoris',Lep:'Leporis',
    Lib:'Librae',Lup:'Lupi',Lyn:'Lyncis',Lyr:'Lyrae',Men:'Mensae',Mic:'Microscopii',Mon:'Monocerotis',Mus:'Muscae',Nor:'Normae',
    Oct:'Octantis',Oph:'Ophiuchi',Ori:'Orionis',Pav:'Pavonis',Peg:'Pegasi',Per:'Persei',Phe:'Phoenicis',Pic:'Pictoris',Psc:'Piscium',
    PsA:'Piscis Austrini',Pup:'Puppis',Pyx:'Pyxidis',Ret:'Reticuli',Sge:'Sagittae',Sgr:'Sagittarii',Sco:'Scorpii',Scl:'Sculptoris',
    Sct:'Scuti',Ser:'Serpentis',Sex:'Sextantis',Tau:'Tauri',Tel:'Telescopii',Tri:'Trianguli',TrA:'Trianguli Australis',Tuc:'Tucanae',
    UMa:'Ursae Majoris',UMi:'Ursae Minoris',Vel:'Velorum',Vir:'Virginis',Vol:'Volantis',Vul:'Vulpeculae'
  };
  const zodiac = {'♈':'Aries','♉':'Taurus','♊':'Gemini','♋':'Cancer','♌':'Leo','♍':'Virgo','♎':'Libra','♏':'Scorpio','♐':'Sagittarius','♑':'Capricorn','♒':'Aquarius','♓':'Pisces'};
  const bodies = {'☉':'Sun','☽':'Moon','☿':'Mercury','♀':'Venus','♂':'Mars','♃':'Jupiter','♄':'Saturn'};
  const main = document.querySelector('main');
  if (!main) return;

  function makeSpan(greek, latin) {
    const span = document.createElement('span');
    span.className = 'notation-item';
    span.dataset.greek = greek;
    span.dataset.latin = latin;
    span.textContent = greek;
    return span;
  }

  document.querySelectorAll('.zodiac-glyph').forEach(function (span) {
    const glyph = span.textContent.charAt(0);
    if (!zodiac[glyph]) return;
    span.classList.add('notation-item');
    span.dataset.greek = glyph;
    span.dataset.latin = zodiac[glyph];
  });

  const bayerRe = /([αβγδεζηθικλμνξοπρστυφχψω])(\d+)?\s+([A-Z][A-Za-z]{2})\b/g;
  const symbolRe = /[☉☽☿♀♂♃♄]/g;
  const greekRe = /([αβγδεζηθικλμνξοπρστυφχψω])(\d+)?/g;
  const walker = document.createTreeWalker(main, NodeFilter.SHOW_TEXT);
  const nodes = [];
  while (walker.nextNode()) {
    const node = walker.currentNode;
    if (node.parentElement && node.parentElement.closest('.notation-item')) continue;
    if (bayerRe.test(node.nodeValue) || symbolRe.test(node.nodeValue) || greekRe.test(node.nodeValue)) nodes.push(node);
    bayerRe.lastIndex = symbolRe.lastIndex = greekRe.lastIndex = 0;
  }

  function replaceNode(node) {
    const text = node.nodeValue;
    const combined = new RegExp(bayerRe.source + '|' + symbolRe.source + '|' + greekRe.source, 'g');
    const frag = document.createDocumentFragment();
    let last = 0;
    let match;
    while ((match = combined.exec(text)) !== null) {
      frag.append(document.createTextNode(text.slice(last, match.index)));
      const token = match[0];
      let latin = token;
      const bm = token.match(/^([αβγδεζηθικλμνξοπρστυφχψω])(\d+)?\s+([A-Z][A-Za-z]{2})$/);
      if (bm) {
        latin = greekNames[bm[1]] + (bm[2] || '') + ' ' + (constellations[bm[3]] || bm[3]);
      } else if (bodies[token]) {
        latin = bodies[token];
      } else {
        const gm = token.match(/^([αβγδεζηθικλμνξοπρστυφχψω])(\d+)?$/);
        if (gm) latin = greekNames[gm[1]] + (gm[2] || '');
      }
      frag.append(makeSpan(token, latin));
      last = match.index + token.length;
    }
    frag.append(document.createTextNode(text.slice(last)));
    node.replaceWith(frag);
  }
  nodes.forEach(replaceNode);

  const buttons = document.querySelectorAll('[data-bayer-mode]');
  function setMode(mode) {
    document.querySelectorAll('.notation-item').forEach(function (span) {
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
    print("Added Greek/Latin notation toggle to 53 weekly pages")


if __name__ == "__main__":
    main()
