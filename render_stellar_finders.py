#!/usr/bin/env python3
"""Render catalog-driven stellar finder charts with constellation figures."""
from __future__ import annotations
import argparse, csv, json, math
from dataclasses import dataclass
from pathlib import Path
import matplotlib.pyplot as plt

GREEK_BAYER={"Alp":"α","Bet":"β","Gam":"γ","Del":"δ","Eps":"ε","Zet":"ζ","Eta":"η","The":"θ","Iot":"ι","Kap":"κ","Lam":"λ","Mu":"μ","Nu":"ν","Xi":"ξ","Omi":"ο","Pi":"π","Rho":"ρ","Sig":"σ","Tau":"τ","Ups":"υ","Phi":"φ","Chi":"χ","Psi":"ψ","Ome":"ω"}
IAU_BOUNDARIES_J2000={"Aqr":[(309.59884625,0.4361772),(309.57987750,2.4360874),(314.08109708,2.4773185),(321.58347125,2.5393796),(323.58427042,2.5544112),(323.57874875,3.3043909),(326.58021875,3.3256676),(326.58708625,2.3256910),(331.58875500,2.3576119),(331.58726708,2.6076074),(342.84221708,2.6622071),(342.84971250,0.6622211),(342.86470375,-3.3377509),(359.10221125,-3.3042023),(359.10329875,-6.3042021),(359.11056458,-24.8042011),(346.68096625,-24.8250446),(329.77028875,-24.9040413),(329.65616250,-8.4043999),(321.66841500,-8.4602947),(321.71645125,-14.4601107),(309.74390125,-14.5631361),(309.68464792,-8.5634165)]}
NIGHT="#071423"; STAR="#f7f7f2"; FIGURE_BLUE="#5c8fe8"; ASTERISM_GREEN="#59c86d"; BOUNDARY="#c4ccd8"; TEXT="#f3f5f7"

@dataclass(frozen=True)
class Star:
    ra_deg:float; dec_deg:float; mag:float; proper:str; bayer:str; con:str; hyg_id:str; hip:str
    @property
    def ref(self): return f"{self.bayer} {self.con}".strip()
    @property
    def hip_ref(self): return f"HIP {self.hip}" if self.hip else ""
    def display_label(self,figure_constellation):
        g=greek_bayer_symbol(self.bayer)
        b=f"{g} {self.con}" if g and self.con!=figure_constellation else g
        return " ".join(x for x in (b,self.proper) if x) or self.hip_ref or f"HYG {self.hyg_id}"
    def target_label(self): return " ".join(x for x in (self.proper,greek_bayer_symbol(self.bayer),self.con) if x)

def greek_bayer_symbol(bayer):
    if not bayer:return ""
    return f"{GREEK_BAYER.get(bayer[:3].title(),bayer)}{bayer[3:] if bayer[:3].title() in GREEK_BAYER else ''}"

def load_hyg(path):
    out=[]
    with path.open("r",encoding="utf-8-sig",newline="") as h:
        for r in csv.DictReader(h):
            if not all((r.get(k) or "").strip() for k in ("ra","dec","mag")):continue
            out.append(Star(float(r["ra"])*15,float(r["dec"]),float(r["mag"]),(r.get("proper") or "").strip(),(r.get("bayer") or "").strip(),(r.get("con") or "").strip(),(r.get("id") or "").strip(),(r.get("hip") or "").strip()))
    return out

def star_index(stars):
    d={}
    for s in sorted(stars,key=lambda x:x.mag):
        if s.hip_ref:d.setdefault(s.hip_ref,s)
        if s.bayer and s.con:
            d.setdefault(s.ref,s);p=s.bayer[:3].title()
            if p in GREEK_BAYER:d.setdefault(f"{p} {s.con}",s)
    return d

def sep(s,ra,dec):
    a,b,c,d=map(math.radians,(s.ra_deg,s.dec_deg,ra,dec));v=math.sin(b)*math.sin(d)+math.cos(b)*math.cos(d)*math.cos(a-c)
    return math.degrees(math.acos(max(-1,min(1,v))))
def project(ra,dec,ra0,dec0):
    ra,dec,ra0,dec0=map(math.radians,(ra,dec,ra0,dec0));dra=(ra-ra0+math.pi)%(2*math.pi)-math.pi
    cosc=math.sin(dec0)*math.sin(dec)+math.cos(dec0)*math.cos(dec)*math.cos(dra)
    if cosc<=0:return None
    x=math.cos(dec)*math.sin(dra)/cosc;y=(math.cos(dec0)*math.sin(dec)-math.sin(dec0)*math.cos(dec)*math.cos(dra))/cosc
    return math.degrees(math.atan(x)),math.degrees(math.atan(y))
def spherical_center(stars):
    v=[]
    for s in stars:
        r,d=map(math.radians,(s.ra_deg,s.dec_deg));v.append((math.cos(d)*math.cos(r),math.cos(d)*math.sin(r),math.sin(d)))
    x,y,z=(sum(a[i] for a in v) for i in range(3));return math.degrees(math.atan2(y,x))%360,math.degrees(math.atan2(z,math.hypot(x,y)))
def all_refs(spec):
    r={spec["target"]}
    for p in spec.get("figure_paths",[]):r.update(p)
    for a in spec.get("asterisms",[]):
        for p in a.get("paths",[]):r.update(p)
    return r
def center_refs(spec):
    r={spec["target"]}
    for p in spec.get("figure_paths",[]):r.update(p)
    return r
def marker_area(m,lim):return max(2,5+5*(lim-m))
def draw_path(ax,path,index,center,lw,color):
    pts=[project(index[r].ra_deg,index[r].dec_deg,*center) for r in path];pts=[p for p in pts if p]
    if len(pts)>=2:ax.plot([p[0] for p in pts],[p[1] for p in pts],lw=lw,color=color,alpha=.95,zorder=2)
def boundary_projected(con,center):
    b=IAU_BOUNDARIES_J2000.get(con,[]);return [p for ra,dec in b if (p:=project(ra,dec,*center))]
def draw_boundary(ax,con,center):
    pts=boundary_projected(con,center)
    if len(pts)>=2:
        pts=pts+[pts[0]];ax.plot([p[0] for p in pts],[p[1] for p in pts],lw=2.0,color=BOUNDARY,alpha=.98,zorder=1)

def render_figure(name,spec,stars,out_dir):
    idx=star_index(stars);missing=sorted(r for r in all_refs(spec) if r not in idx)
    if missing:raise ValueError("Configured stars not found: "+", ".join(missing))
    center=spherical_center([idx[r] for r in center_refs(spec)])
    tight_aqr=spec["constellation"]=="Aqr"
    if tight_aqr:
        bp=boundary_projected("Aqr",center);xs=[p[0] for p in bp];ys=[p[1] for p in bp]
        padx=max(1.2,(max(xs)-min(xs))*.045);pady=max(1.2,(max(ys)-min(ys))*.06)
        xmin,xmax=min(xs)-padx,max(xs)+padx;ymin,ymax=min(ys)-pady,max(ys)+pady
        vis=[s for s in stars if (p:=project(s.ra_deg,s.dec_deg,*center)) and xmin<=p[0]<=xmax and ymin<=p[1]<=ymax and s.mag<=7]
    else:
        radius=float(spec["field_deg"])/2;xmin,xmax=-radius,radius;ymin,ymax=-radius,radius
        vis=[s for s in stars if s.mag<=7 and sep(s,*center)<=radius*1.05]
    proj=[(*p,s) for s in vis if (p:=project(s.ra_deg,s.dec_deg,*center))]
    fig,ax=plt.subplots(figsize=(9.0,6.8) if tight_aqr else (8.2,8.2),facecolor=NIGHT);ax.set_facecolor(NIGHT)
    ax.set_xlim(xmax,xmin);ax.set_ylim(ymin,ymax);ax.set_aspect("equal");draw_boundary(ax,spec["constellation"],center)
    if proj:ax.scatter([p[0] for p in proj],[p[1] for p in proj],s=[marker_area(p[2].mag,7) for p in proj],color=STAR,zorder=3)
    for p in spec.get("figure_paths",[]):draw_path(ax,p,idx,center,2.7,FIGURE_BLUE)
    for a in spec.get("asterisms",[]):
        if tight_aqr and a["name"]!="Water Jar":continue
        color=ASTERISM_GREEN if a["name"]=="Water Jar" else FIGURE_BLUE;lw=3.5 if a["name"]=="Water Jar" else 2.8
        for p in a.get("paths",[]):draw_path(ax,p,idx,center,lw,color)
        ss=[idx[r] for p in a.get("paths",[]) for r in p];xy=project(*spherical_center(ss),*center)
        if xy:ax.annotate(a["name"],xy,xytext=tuple(a.get("label_offset",[0,16])),textcoords="offset points",ha="center",fontsize=8,color=color,bbox=dict(facecolor=NIGHT,edgecolor="none",pad=1.2),zorder=6)
    labels={r for p in spec.get("figure_paths",[]) for r in p}
    target_ref=spec["target"]
    label_offsets=spec.get("label_offsets",{})
    for r in sorted(labels):
        if r==target_ref:continue
        s=idx[r];xy=project(s.ra_deg,s.dec_deg,*center);lab=s.display_label(spec["constellation"])
        if xy:
            off=tuple(label_offsets.get(r,[5,5]))
            ha="right" if off[0]<0 else "left"
            va="top" if off[1]<0 else "bottom"
            ax.annotate(lab,xy,xytext=off,textcoords="offset points",ha=ha,va=va,fontsize=7.5,color=TEXT,bbox=dict(facecolor=NIGHT,edgecolor="none",pad=.6),zorder=6)
    t=idx[target_ref];txy=project(t.ra_deg,t.dec_deg,*center)
    if txy:
        tx,ty=txy;span=ymax-ymin
        ax.annotate("",xy=(tx,ty+span*.025),xytext=(tx,ty+span*.16),arrowprops=dict(arrowstyle="-|>",mutation_scale=34,linewidth=4.0,color=STAR,shrinkA=0,shrinkB=0),zorder=8)
        ax.annotate(t.target_label(),txy,xytext=(16,0),textcoords="offset points",ha="left",va="center",fontsize=10,color=TEXT,bbox=dict(facecolor=NIGHT,edgecolor="none",pad=1),zorder=8)
    ax.set_title(f"{t.target_label()} Finder",color=TEXT,fontsize=14,pad=12)
    ax.text(.5,.015,spec["caption"],transform=ax.transAxes,ha="center",va="bottom",fontsize=8,color=TEXT)
    ax.text(.5,-.035,"East ←                                      → West",transform=ax.transAxes,ha="center",va="top",fontsize=8,color=TEXT)
    ax.set_xticks([]);ax.set_yticks([]);ax.grid(False)
    for sp in ax.spines.values():sp.set_visible(False)
    out_dir.mkdir(parents=True,exist_ok=True);out=out_dir/f"{spec['target_name'].lower()}-finder.svg"
    fig.tight_layout();fig.savefig(out,bbox_inches="tight",facecolor=fig.get_facecolor());plt.close(fig);return out

def main():
    p=argparse.ArgumentParser();p.add_argument("hyg_catalog",type=Path);p.add_argument("--config",type=Path,default=Path("constellation-figures.json"));p.add_argument("--figure",default="all");p.add_argument("--out-dir",type=Path,default=Path("observer-views/W41"));a=p.parse_args()
    specs=json.loads(a.config.read_text());stars=load_hyg(a.hyg_catalog);names=list(specs) if a.figure.lower()=="all" else [a.figure]
    for n in names:print(f"wrote {render_figure(n,specs[n],stars,a.out_dir)}")
if __name__=="__main__":main()
