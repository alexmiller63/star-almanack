#!/usr/bin/env python3
"""Render catalog-driven stellar finder charts with constellation figures.

The renderer uses the same pinned HYG v4.1 source family as the Star Almanack
stellar catalogs. Catalog positions are never moved to make the constellation
art fit. The figure is an editorial line overlay anchored to catalog stars.

Figure policy:
- normal figure stars: V <= 4.0
- justified structural exceptions: V <= 4.5
- canonical asterisms are preserved even when a member is fainter
- finder labels use Greek Bayer symbols + proper names
- stars crossing the figure constellation boundary include the IAU abbreviation
- Aquarius includes the official IAU J2000 boundary polygon

The Aquarius boundary coordinates below are the IAU-published J2000 boundary
coordinates for AQR:
https://iauarchive.eso.org/static/public/constellations/txt/aqr.txt
"""

from __future__ import annotations

import argparse
import csv
import json
import math
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

import matplotlib.pyplot as plt

GREEK_BAYER = {
    "Alp": "α", "Bet": "β", "Gam": "γ", "Del": "δ", "Eps": "ε",
    "Zet": "ζ", "Eta": "η", "The": "θ", "Iot": "ι", "Kap": "κ",
    "Lam": "λ", "Mu": "μ", "Nu": "ν", "Xi": "ξ", "Omi": "ο",
    "Pi": "π", "Rho": "ρ", "Sig": "σ", "Tau": "τ", "Ups": "υ",
    "Phi": "φ", "Chi": "χ", "Psi": "ψ", "Ome": "ω",
}

# Official IAU J2000 Aquarius boundary. RA is converted from h:m:s to degrees.
IAU_BOUNDARIES_J2000 = {
    "Aqr": [
        (309.59884625, 0.4361772),
        (309.57987750, 2.4360874),
        (314.08109708, 2.4773185),
        (321.58347125, 2.5393796),
        (323.58427042, 2.5544112),
        (323.57874875, 3.3043909),
        (326.58021875, 3.3256676),
        (326.58708625, 2.3256910),
        (331.58875500, 2.3576119),
        (331.58726708, 2.6076074),
        (342.84221708, 2.6622071),
        (342.84971250, 0.6622211),
        (342.86470375, -3.3377509),
        (359.10221125, -3.3042023),
        (359.10329875, -6.3042021),
        (359.11056458, -24.8042011),
        (346.68096625, -24.8250446),
        (329.77028875, -24.9040413),
        (329.65616250, -8.4043999),
        (321.66841500, -8.4602947),
        (321.71645125, -14.4601107),
        (309.74390125, -14.5631361),
        (309.68464792, -8.5634165),
    ]
}

FIGURE_BLUE = "#2457a6"
ASTERISM_GREEN = "#208a3b"
BOUNDARY_GRAY = "#777777"


@dataclass(frozen=True)
class Star:
    ra_deg: float
    dec_deg: float
    mag: float
    proper: str
    bayer: str
    con: str
    hyg_id: str

    @property
    def ref(self) -> str:
        return f"{self.bayer} {self.con}".strip()

    def display_label(self, figure_constellation: str) -> str:
        greek = greek_bayer_symbol(self.bayer)
        bayer = f"{greek} {self.con}" if self.con != figure_constellation else greek
        return " ".join(part for part in (bayer, self.proper) if part)

    def target_label(self) -> str:
        greek = greek_bayer_symbol(self.bayer)
        return " ".join(part for part in (self.proper, greek, self.con) if part)


def greek_bayer_symbol(bayer: str) -> str:
    if not bayer:
        return ""
    prefix = bayer[:3].title()
    symbol = GREEK_BAYER.get(prefix)
    if not symbol:
        return bayer
    return f"{symbol}{bayer[3:]}"


def load_hyg(path: Path) -> list[Star]:
    stars = []
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        required = {"id", "ra", "dec", "mag", "proper", "bayer", "con"}
        missing = required - set(reader.fieldnames or [])
        if missing:
            raise ValueError("HYG catalog missing columns: " + ", ".join(sorted(missing)))
        for row in reader:
            ra, dec, mag = ((row.get(k) or "").strip() for k in ("ra", "dec", "mag"))
            if not ra or not dec or not mag:
                continue
            stars.append(Star(float(ra) * 15.0, float(dec), float(mag),
                              (row.get("proper") or "").strip(),
                              (row.get("bayer") or "").strip(),
                              (row.get("con") or "").strip(),
                              (row.get("id") or "").strip()))
    return stars


def star_index(stars: Iterable[Star]) -> dict[str, Star]:
    index = {}
    for star in sorted(stars, key=lambda item: item.mag):
        if not star.bayer or not star.con:
            continue
        index.setdefault(star.ref, star)
        prefix = star.bayer[:3].title()
        if prefix in GREEK_BAYER:
            index.setdefault(f"{prefix} {star.con}", star)
    return index


def angular_separation_deg(a: Star, ra_deg: float, dec_deg: float) -> float:
    ra1, dec1, ra2, dec2 = map(math.radians, (a.ra_deg, a.dec_deg, ra_deg, dec_deg))
    value = math.sin(dec1) * math.sin(dec2) + math.cos(dec1) * math.cos(dec2) * math.cos(ra1 - ra2)
    return math.degrees(math.acos(max(-1.0, min(1.0, value))))


def tangent_plane(ra_deg, dec_deg, center_ra_deg, center_dec_deg):
    ra, dec, ra0, dec0 = map(math.radians, (ra_deg, dec_deg, center_ra_deg, center_dec_deg))
    dra = (ra - ra0 + math.pi) % (2 * math.pi) - math.pi
    cosc = math.sin(dec0) * math.sin(dec) + math.cos(dec0) * math.cos(dec) * math.cos(dra)
    if cosc <= 0:
        return None
    x = math.cos(dec) * math.sin(dra) / cosc
    y = (math.cos(dec0) * math.sin(dec) - math.sin(dec0) * math.cos(dec) * math.cos(dra)) / cosc
    return math.degrees(math.atan(x)), math.degrees(math.atan(y))


def spherical_center(stars: Iterable[Star]):
    vectors = []
    for star in stars:
        ra, dec = map(math.radians, (star.ra_deg, star.dec_deg))
        vectors.append((math.cos(dec) * math.cos(ra), math.cos(dec) * math.sin(ra), math.sin(dec)))
    x, y, z = (sum(v[i] for v in vectors) for i in range(3))
    return math.degrees(math.atan2(y, x)) % 360.0, math.degrees(math.atan2(z, math.hypot(x, y)))


def all_refs(spec):
    refs = {spec["target"]}
    for path in spec.get("figure_paths", []):
        refs.update(path)
    for ast in spec.get("asterisms", []):
        for path in ast.get("paths", []):
            refs.update(path)
    return refs


def validate_spec(spec, index):
    missing = sorted(ref for ref in all_refs(spec) if ref not in index)
    if missing:
        raise ValueError("Configured HYG stars not found: " + ", ".join(missing))
    normal = float(spec.get("figure_cutoff", 4.0))
    exception = float(spec.get("exception_cutoff", 4.5))
    exceptions = set(spec.get("exceptions", []))
    ast_refs = {ref for ast in spec.get("asterisms", []) for path in ast.get("paths", []) for ref in path}
    for ref in {ref for path in spec.get("figure_paths", []) for ref in path}:
        star = index[ref]
        if ref in ast_refs or star.mag <= normal or (ref in exceptions and star.mag <= exception):
            continue
        raise ValueError(f"{ref} is V={star.mag:.2f}; outside figure policy")


def marker_area(mag, limiting_mag):
    return max(2.0, 5.0 + 5.0 * (limiting_mag - mag))


def draw_path(ax, path, index, center, linewidth, color):
    points = []
    for ref in path:
        s = index[ref]
        xy = tangent_plane(s.ra_deg, s.dec_deg, *center)
        if xy is not None:
            points.append(xy)
    if len(points) >= 2:
        ax.plot([p[0] for p in points], [p[1] for p in points],
                linewidth=linewidth, alpha=0.9, color=color, zorder=2)


def draw_iau_boundary(ax, constellation, center):
    boundary = IAU_BOUNDARIES_J2000.get(constellation)
    if not boundary:
        return
    points = []
    for ra_deg, dec_deg in boundary + [boundary[0]]:
        xy = tangent_plane(ra_deg, dec_deg, *center)
        if xy is not None:
            points.append(xy)
    if len(points) >= 2:
        ax.plot([p[0] for p in points], [p[1] for p in points],
                linewidth=1.15, linestyle=(0, (4, 3)), color=BOUNDARY_GRAY,
                alpha=0.9, zorder=1)


def render_figure(name, spec, stars, out_dir):
    index = star_index(stars)
    validate_spec(spec, index)
    center = spherical_center([index[r] for r in all_refs(spec)])
    field_deg = float(spec["field_deg"])
    radius = field_deg / 2
    limiting_mag = 7.0
    visible = [s for s in stars if s.mag <= limiting_mag and angular_separation_deg(s, *center) <= radius * 1.05]
    projected = []
    for s in visible:
        xy = tangent_plane(s.ra_deg, s.dec_deg, *center)
        if xy is not None:
            projected.append((*xy, s))

    fig, ax = plt.subplots(figsize=(8.2, 8.2))
    ax.set_xlim(radius, -radius)
    ax.set_ylim(-radius, radius)
    ax.set_aspect("equal")

    draw_iau_boundary(ax, spec["constellation"], center)

    if projected:
        ax.scatter([p[0] for p in projected], [p[1] for p in projected],
                   s=[marker_area(p[2].mag, limiting_mag) for p in projected],
                   color="black", zorder=3)

    # Constellation figure in blue; canonical asterisms get their own emphasis.
    for path in spec.get("figure_paths", []):
        draw_path(ax, path, index, center, 2.35, FIGURE_BLUE)

    for ast in spec.get("asterisms", []):
        ast_color = ASTERISM_GREEN if ast["name"] == "Water Jar" else FIGURE_BLUE
        ast_width = 3.15 if ast["name"] == "Water Jar" else 2.8
        for path in ast.get("paths", []):
            draw_path(ax, path, index, center, ast_width, ast_color)
        ast_stars = [index[r] for path in ast.get("paths", []) for r in path]
        ara, adec = spherical_center(ast_stars)
        xy = tangent_plane(ara, adec, *center)
        if xy is not None:
            offset = ast.get("label_offset", [0, 16])
            ax.annotate(ast["name"], xy, xytext=tuple(offset), textcoords="offset points",
                        ha="center", fontsize=8, color="black",
                        bbox=dict(facecolor="white", edgecolor="none", pad=1.5), zorder=6)

    label_refs = {r for path in spec.get("figure_paths", []) for r in path}
    for ast in spec.get("asterisms", []):
        for path in ast.get("paths", []):
            label_refs.update(path)

    figure_con = spec["constellation"]
    target_ref = spec["target"]
    for ref in sorted(label_refs):
        if ref == target_ref:
            continue
        s = index[ref]
        xy = tangent_plane(s.ra_deg, s.dec_deg, *center)
        label = s.display_label(figure_con)
        if xy is not None and label:
            ax.annotate(label, xy, xytext=(4, 4), textcoords="offset points", fontsize=7,
                        bbox=dict(facecolor="white", edgecolor="none", pad=0.6), zorder=6)

    target = index[target_ref]
    txy = tangent_plane(target.ra_deg, target.dec_deg, *center)
    if txy is not None:
        # Short-shaft arrow immediately above the target star.
        ax.annotate("", xy=txy, xytext=(txy[0], txy[1] + 1.6),
                    arrowprops=dict(arrowstyle="-|>", mutation_scale=12,
                                    linewidth=1.4, color="black"), zorder=7)
        # Target label belongs beside the star, not elsewhere on the chart.
        ax.annotate(target.target_label(), txy, xytext=(9, 0), textcoords="offset points",
                    ha="left", va="center", fontsize=8,
                    bbox=dict(facecolor="white", edgecolor="none", pad=0.8), zorder=7)

    ax.set_title(f"{target.target_label()}\nFinder chart · {field_deg:g}° field")
    ax.text(.5, .015, spec["caption"], transform=ax.transAxes,
            ha="center", va="bottom", fontsize=8)
    ax.set_xticks([])
    ax.set_yticks([])
    ax.set_xlabel("")
    ax.set_ylabel("")
    ax.grid(False)

    out_dir.mkdir(parents=True, exist_ok=True)
    output = out_dir / f"{spec['target_name'].lower()}-finder.svg"
    fig.tight_layout()
    fig.savefig(output, bbox_inches="tight")
    plt.close(fig)
    return output


def parse_args():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("hyg_catalog", type=Path)
    p.add_argument("--config", type=Path, default=Path("constellation-figures.json"))
    p.add_argument("--figure", default="all")
    p.add_argument("--out-dir", type=Path, default=Path("observer-views/W41"))
    return p.parse_args()


def main():
    args = parse_args()
    specs = json.loads(args.config.read_text(encoding="utf-8"))
    stars = load_hyg(args.hyg_catalog)
    names = list(specs) if args.figure.lower() == "all" else [args.figure]
    for name in names:
        if name not in specs:
            raise KeyError(f"Unknown figure {name!r}; choices: {', '.join(specs)}")
        print(f"wrote {render_figure(name, specs[name], stars, args.out_dir)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
