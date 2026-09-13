#!/usr/bin/env python3
"""Add the Greek/Latin/Mixed notation teaching layer to the 2026 weekly pages."""
from pathlib import Path

ROOT = Path(__file__).parent / "site" / "2026"

CSS = r'''
.bayer-toggle-wrap{max-width:1080px;margin:0 auto;padding:.75rem 1.5rem 0;font-family:system-ui,-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif}.bayer-toggle{display:flex;align-items:center;justify-content:flex-end;gap:.35rem;flex-wrap:wrap;font-size:.86rem}.bayer-toggle-label{margin-right:.2rem;color:var(--muted)}.bayer-toggle button{appearance:none;border:1px solid #c8d3dc;background:#fff;color:var(--link);padding:.35rem .62rem;border-radius:.4rem;font:inherit;cursor:pointer}.bayer-toggle button[aria-pressed=true]{background:var(--navy);color:#fff;border-color:var(--navy)}.notation-legend{max-width:1080px;margin:0 auto;padding:1rem 1.5rem 1.15rem;font-family:system-ui,-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;font-size:.78rem;line-height:1.55;color:var(--muted);border-top:1px solid var(--rule)}.notation-legend p{max-width:none;margin:.35rem 0}.notation-legend strong{color:inherit}.legend-line{display:flex;flex-wrap:wrap;gap:.12rem .5rem}.legend-item{white-space:nowrap}
.zodiac-day{text-align:center;line-height:1.2}.zodiac-day .notation-item{display:block;white-space:pre-line}.zodiac-day .zodiac-day-number{display:block;margin:0}.visibility-magnitude{white-space:nowrap}.event-parenthetical{white-space:nowrap}
@media(max-width:760px) and (orientation:portrait){.bayer-toggle-wrap,.notation-legend{padding-left:1rem;padding-right:1rem}.bayer-toggle{justify-content:center;flex-wrap:nowrap;gap:.2rem;font-size:.74rem}.bayer-toggle-label{margin-right:.05rem;white-space:nowrap}.bayer-toggle button{padding:.3rem .42rem;white-space:nowrap}table.calendar th,table.calendar td{padding:.55rem .4rem}table.calendar th:first-child,table.calendar td:first-child{width:25%}table.calendar th:nth-child(2),table.calendar td:nth-child(2){width:27%}table.calendar th:nth-child(3),table.calendar td:nth-child(3){width:48%}table.calendar td:first-child{font-size:.82rem;line-height:1.3}table.calendar td:nth-child(2){white-space:normal;text-align:center;font-size:.86rem;overflow-wrap:normal;word-break:normal}table.calendar td:nth-child(3){overflow-wrap:normal;word-break:normal}}
@media(prefers-color-scheme:dark){.bayer-toggle button{background:#1c2a36;border-color:#405567;color:#b6dcff}.bayer-toggle button[aria-pressed=true]{background:#eef7ff;color:#102a43;border-color:#eef7ff}}
'''.strip()

HTML = r'''<div class="bayer-toggle-wrap"><div class="bayer-toggle" role="group" aria-label="Astronomical notation"><span class="bayer-toggle-label">Notation:</span><button type="button" data-bayer-mode="greek" aria-pressed="true">Greek/Symbols</button><button type="button" data-bayer-mode="latin" aria-pressed="false">Latin</button><button type="button" data-bayer-mode="mixed" data-legacy-label="Mixed · Learner" aria-pressed="false">Mixed Learner</button></div></div>'''

GREEK = [('α','Alpha'),('β','Beta'),('γ','Gamma'),('δ','Delta'),('ε','Epsilon'),('ζ','Zeta'),('η','Eta'),('θ','Theta'),('ι','Iota'),('κ','Kappa'),('λ','Lambda'),('μ','Mu'),('ν','Nu'),('ξ','Xi'),('ο','Omicron'),('π','Pi'),('ρ','Rho'),('σ','Sigma'),('τ','Tau'),('υ','Upsilon'),('φ','Phi'),('χ','Chi'),('ψ','Psi'),('ω','Omega')]
ZODIAC = [('♈','Aries'),('♉','Taurus'),('♊','Gemini'),('♋','Cancer'),('♌','Leo'),('♍','Virgo'),('♎','Libra'),('♏','Scorpio'),('♐','Sagittarius'),('♑','Capricorn'),('♒','Aquarius'),('♓','Pisces')]
BODIES = [('☉','Sun'),('☽','Moon'),('☿','Mercury'),('♀','Venus'),('♂','Mars'),('♃','Jupiter'),('♄','Saturn')]

def legend_items(items):
    return ''.join(f'<span class="legend-item"><span class="almanack-glyph">{g}&#xfe0e;</span> {name}</span>' for g,name in items)

LEGEND = ('<aside class="notation-legend" aria-label="Astronomical notation legend">'
    '<p><strong>Greek alphabet</strong></p><div class="legend-line">'+legend_items(GREEK)+'</div>'
    '<p><strong>Zodiac</strong></p><div class="legend-line">'+legend_items(ZODIAC)+'</div>'
    '<p><strong>Ephemerides</strong></p><div class="legend-line">'+legend_items(BODIES)+'</div></aside>')

JS = r'''<script>(function(){
const g={'α':'Alpha','β':'Beta','γ':'Gamma','δ':'Delta','ε':'Epsilon','ζ':'Zeta','η':'Eta','θ':'Theta','ι':'Iota','κ':'Kappa','λ':'Lambda','μ':'Mu','ν':'Nu','ξ':'Xi','ο':'Omicron','π':'Pi','ρ':'Rho','σ':'Sigma','τ':'Tau','υ':'Upsilon','φ':'Phi','χ':'Chi','ψ':'Psi','ω':'Omega'};
const c={And:'Andromedae',Ant:'Antliae',Aps:'Apodis',Aqr:'Aquarii',Aql:'Aquilae',Ara:'Arae',Ari:'Arietis',Aur:'Aurigae',Boo:'Bootis',Cae:'Caeli',Cam:'Camelopardalis',Cnc:'Cancri',CVn:'Canum Venaticorum',CMa:'Canis Majoris',CMi:'Canis Minoris',Cap:'Capricorni',Car:'Carinae',Cas:'Cassiopeiae',Cen:'Centauri',Cep:'Cephei',Cet:'Ceti',Cha:'Chamaeleontis',Cir:'Circini',Col:'Columbae',Com:'Comae Berenices',CrA:'Coronae Australis',CrB:'Coronae Borealis',Crv:'Corvi',Crt:'Crateris',Cru:'Crucis',Cyg:'Cygni',Del:'Delphini',Dor:'Doradus',Dra:'Draconis',Equ:'Equulei',Eri:'Eridani',For:'Fornacis',Gem:'Geminorum',Gru:'Gruis',Her:'Herculis',Hor:'Horologii',Hya:'Hydrae',Hyi:'Hydri',Ind:'Indi',Lac:'Lacertae',Leo:'Leonis',LMi:'Leonis Minoris',Lep:'Leporis',Lib:'Librae',Lup:'Lupi',Lyn:'Lyncis',Lyr:'Lyrae',Men:'Mensae',Mic:'Microscopii',Mon:'Monocerotis',Mus:'Muscae',Nor:'Normae',Oct:'Octantis',Oph:'Ophiuchi',Ori:'Orionis',Pav:'Pavonis',Peg:'Pegasi',Per:'Persei',Phe:'Phoenicis',Pic:'Pictoris',Psc:'Piscium',PsA:'Piscis Austrini',Pup:'Puppis',Pyx:'Pyxidis',Ret:'Reticuli',Sge:'Sagittae',Sgr:'Sagittarii',Sco:'Scorpii',Scl:'Sculptoris',Sct:'Scuti',Ser:'Serpentis',Sex:'Sextantis',Tau:'Tauri',Tel:'Telescopii',Tri:'Trianguli',TrA:'Trianguli Australis',Tuc:'Tucanae',UMa:'Ursae Majoris',UMi:'Ursae Minoris',Vel:'Velorum',Vir:'Virginis',Vol:'Volantis',Vul:'Vulpeculae'};
const z={'♈':'Aries','♉':'Taurus','♊':'Gemini','♋':'Cancer','♌':'Leo','♍':'Virgo','♎':'Libra','♏':'Scorpio','♐':'Sagittarius','♑':'Capricorn','♒':'Aquarius','♓':'Pisces'};
const b={'☉':'Sun','☽':'Moon','☿':'Mercury','♀':'Venus','♂':'Mars','♃':'Jupiter','♄':'Saturn'};
const glyphs=new Set([...Object.keys(g),...Object.keys(z),...Object.keys(b)]),VS='\ufe0e';
function span(greek,latin,mixed){let s=document.createElement('span');s.className='notation-item';s.dataset.greek=greek;s.dataset.latin=latin;s.dataset.mixed=mixed;return s}
function render(s,value){s.replaceChildren();let a=Array.from(value);if(a.length&&glyphs.has(a[0])){let q=document.createElement('span');q.className='almanack-glyph';q.textContent=a[0]+VS;s.append(q);let rest=a.slice(1).join('').replace(/^\ufe0e/,'');if(rest)s.append(document.createTextNode(rest))}else{s.textContent=value}}
document.querySelectorAll('.zodiac-notation-source').forEach(s=>{let x=s.textContent.charAt(0);if(z[x]){s.className='notation-item';s.dataset.greek=x+VS;s.dataset.latin=z[x];s.dataset.mixed=x+VS+'\n'+z[x]}});
document.querySelectorAll('table.calendar tbody td:nth-child(3)').forEach(td=>{td.innerHTML=td.innerHTML.replace(/ — ([^<—]+?) — /g,' — <span class="visibility-magnitude">$1</span> — ')});
let main=document.querySelector('main'),re=/([αβγδεζηθικλμνξοπρστυφχψω])(\d+)?\s+([A-Z][A-Za-z]{2})\b|[☉☽☿♀♂♃♄]|([αβγδεζηθικλμνξοπρστυφχψω])(\d+)?/g,n=[];let w=document.createTreeWalker(main,NodeFilter.SHOW_TEXT);while(w.nextNode()){if(!w.currentNode.parentElement.closest('.notation-item,.almanack-glyph')&&re.test(w.currentNode.nodeValue))n.push(w.currentNode);re.lastIndex=0}
n.forEach(node=>{let t=node.nodeValue,f=document.createDocumentFragment(),last=0,m;re.lastIndex=0;while((m=re.exec(t))){f.append(document.createTextNode(t.slice(last,m.index)));let x=m[0],greek=x,latin=x,mixed=x,bm=x.match(/^([αβγδεζηθικλμνξοπρστυφχψω])(\d+)?\s+([A-Z][A-Za-z]{2})$/),gm=x.match(/^([αβγδεζηθικλμνξοπρστυφχψω])(\d+)?$/);if(bm){let suffix=bm[2]||'',abbr=bm[3],con=c[abbr]||abbr;greek=bm[1]+suffix+' '+abbr;latin=g[bm[1]]+suffix+' '+con;mixed=bm[1]+suffix+' '+g[bm[1]]+suffix+' '+con}else if(b[x]){greek=x+VS;latin=b[x];mixed=x+VS+' '+b[x]}else if(gm){greek=gm[1]+(gm[2]||'');latin=g[gm[1]]+(gm[2]||'');mixed=greek+' '+latin}f.append(span(greek,latin,mixed));last=m.index+x.length}f.append(document.createTextNode(t.slice(last)));node.replaceWith(f)});
document.querySelectorAll('table.calendar tbody td:nth-child(3)').forEach(td=>{td.innerHTML=td.innerHTML.replace(/\(([^()]*)\)/g,'<span class="event-parenthetical">($1)</span>')});
document.querySelectorAll('table.calendar tbody td:nth-child(2)').forEach(td=>{let txt=td.textContent.trim(),m=txt.match(/^([^\d]*?)(\d+)$/);if(!m)return;let number=m[2],nodes=Array.from(td.childNodes);td.classList.add('zodiac-day');nodes.forEach(node=>{if(node.nodeType===3)node.nodeValue=node.nodeValue.replace(/\s*\d+\s*$/,'')});let d=document.createElement('span');d.className='zodiac-day-number';d.textContent=number;td.append(d)});
let buttons=document.querySelectorAll('[data-bayer-mode]');function setMode(mode){document.querySelectorAll('.notation-item').forEach(s=>render(s,s.dataset[mode]||s.dataset.greek));buttons.forEach(x=>x.setAttribute('aria-pressed',x.dataset.bayerMode===mode?'true':'false'));try{localStorage.setItem('star-almanack-bayer-mode',mode)}catch(_){}}buttons.forEach(x=>x.addEventListener('click',()=>setMode(x.dataset.bayerMode)));let initial='greek';try{let s=localStorage.getItem('star-almanack-bayer-mode');if(s==='latin'||s==='greek'||s==='mixed')initial=s}catch(_){}setMode(initial)
})();</script>'''

def add(path: Path) -> None:
    text = path.read_text(encoding="utf-8")
    if 'data-bayer-mode="mixed"' in text: return
    text = text.replace("</style>", CSS + "\n</style>", 1)
    text = text.replace("</header>", "</header>" + HTML, 1)
    text = text.replace("</main>", "</main>" + LEGEND, 1)
    text = text.replace("</body>", JS + "</body>", 1)
    path.write_text(text, encoding="utf-8")

def main() -> None:
    pages = sorted(ROOT.glob("W??/index.html"))
    if len(pages) != 53: raise SystemExit(f"Expected 53 weekly pages, found {len(pages)}")
    for page in pages: add(page)
    print("Added Greek/Symbols, Latin, and Mixed Learner notation modes with bottom legend to 53 weekly pages")

if __name__ == "__main__": main()