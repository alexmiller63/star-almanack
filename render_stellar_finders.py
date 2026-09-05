#!/usr/bin/env python3
"""Render catalog-driven stellar finder charts with constellation figures.

The renderer uses the same pinned HYG v4.1 source family as the Star Almanack
stellar catalogs. Catalog positions are never moved to make the constellation
art fit. The figure is an editorial line overlay anchored to catalog stars.

Figure policy:
- normal figure stars: V <= 4.0
- justified structural exceptions: V <= 4.5
- canonical asterisms are preserved even when a member is fainter
- finder labels: Greek Bayer symbol + proper name, with no constellation suffix

Examples:
    python render_stellar_finders.py hygdata_v41.csv --figure Pegasus
    python render_stellar_finders.py hygdata_v41.csv --figure Aquarius
    python render_stellar_finders.py hygdata_v41.csv --figure all
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

    @property
    def label(self) -> str:
        greek = greek_bayer_symbol(self.bayer)
        if greek and self.proper:
            return f"{greek} {self.proper}"
        if greek:
            return greek
        return self.proper


def greek_bayer_symbol(bayer: str) -> str:
    if not bayer:
        return ""
    prefix = bayer[:3].title()
    symbol = GREEK_BAYER.get(prefix)
    if not symbol:
        return bayer
    return f"{symbol}{bayer[3:]}"


def load_hyg(path: Path) -> list[Star]:
    stars: list[Star] = []
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        required = {"id", "ra", "dec", "mag", "proper", "bayer", "con"}
        missing = required - set(reader.fieldnames or [])
        if missing:
            raise ValueError("HYG catalog missing columns: " + ", ".join(sorted(missing)))

        for row in reader:
            ra = (row.get("ra") or "").strip()
            dec = (row.get("dec") or "").strip()
            mag = (row.get("mag") or "").strip()
            if not ra or not dec or not mag:
                continue
            stars.append(
                Star(
                    ra_deg=float(ra) * 15.0,
                    dec_deg=float(dec),
                    mag=float(mag),
                    proper=(row.get("proper") or "").strip(),
                    bayer=(row.get("bayer") or "").strip(),
                    con=(row.get("con") or "").strip(),
                    hyg_id=(row.get("id") or "").strip(),
                )
            )
    return stars


def star_index(stars: Iterable[Star]) -> dict[str, Star]:
    index: dict[str, Star] = {}
    for star in stars:
        if star.bayer and star.con:
            index.setdefault(star.ref, star)
    return index


def angular_separation_deg(a: Star, ra_deg: float, dec_deg: float) -> float:
    ra1, dec1, ra2, dec2 = map(math.radians, (a.ra_deg, a.dec_deg, ra_deg, dec_deg))
    value = (
        math.sin(dec1) * math.sin(dec2)
        + math.cos(dec1) * math.cos(dec2) * math.cos(ra1 - ra2)
    )
    return math.degrees(math.acos(max(-1.0, min(1.0, value))))


def tangent_plane(
    ra_deg: float, dec_deg: float, center_ra_deg: float, center_dec_deg: float
) -> tuple[float, float] | None:
    ra = math.radians(ra_deg)
    dec = math.radians(dec_deg)
    ra0 = math.radians(center_ra_deg)
    dec0 = math.radians(center_dec_deg)
    dra = (ra - ra0 + math.pi) % (2.0 * math.pi) - math.pi
    cosc = math.sin(dec0) * math.sin(dec) + math.cos(dec0) * math.cos(dec) * math.cos(dra)
    if cosc <= 0:
        return None
    x = math.cos(dec) * math.sin(dra) / cosc
    y = (
        math.cos(dec0) * math.sin(dec)
        - math.sin(dec0) * math.cos(dec) * math.cos(dra)
    ) / cosc
    return math.degrees(math.atan(x)), math.degrees(math.atan(y))


def spherical_center(stars: Iterable[Star]) -> tuple[float, float]:
    vectors = []
    for star in stars:
        ra = math.radians(star.ra_deg)
        dec = math.radians(star.dec_deg)
        vectors.append(
            (
                math.cos(dec) * math.cos(ra),
                math.cos(dec) * math.sin(ra),
                math.sin(dec),
            )
        )
    if not vectors:
        raise ValueError("Cannot center an empty star set")
    x = sum(v[0] for v in vectors)
    y = sum(v[1] for v in vectors)
    z = sum(v[2] for v in vectors)
    return math.degrees(math.atan2(y, x)) % 360.0, math.degrees(math.atan2(z, math.hypot(x, y)))


def all_refs(spec: dict) -> set[str]:
    refs = {spec["target"]}
    for path in spec.get("figure_paths", []):
        refs.update(path)
    for asterism in spec.get("asterisms", []):
        for path in asterism.get("paths", []):
            refs.update(path)
    return refs


def validate_spec(spec: dict, index: dict[str, Star]) -> None:
    missing = sorted(ref for ref in all_refs(spec) if ref not in index)
    if missing:
        raise ValueError("Configured HYG stars not found: " + ", ".join(missing))

    normal_cutoff = float(spec.get("figure_cutoff", 4.0))
    exception_cutoff = float(spec.get("exception_cutoff", 4.5))
    exceptions = set(spec.get("exceptions", []))
    asterism_refs: set[str] = set()
    for asterism in spec.get("asterisms", []):
        for path in asterism.get("paths", []):
            asterism_refs.update(path)

    figure_refs = {ref for path in spec.get("figure_paths", []) for ref in path}
    for ref in sorted(figure_refs):
        star = index[ref]
        if ref in asterism_refs:
            continue
        if star.mag <= normal_cutoff:
            continue
        if ref in exceptions and star.mag <= exception_cutoff:
            continue
        raise ValueError(
            f"{ref} is V={star.mag:.2f}; figure policy requires <= {normal_cutoff:.1f} "
            f"or an explicit exception <= {exception_cutoff:.1f}"
        )


def marker_area(mag: float, limiting_mag: float) -> float:
    return max(2.0, 5.0 + 5.0 * (limiting_mag - mag))


def draw_path(ax, path: list[str], index: dict[str, Star], center: tuple[float, float], linewidth: float) -> None:
    points = []
    for ref in path:
        star = index[ref]
        xy = tangent_plane(star.ra_deg, star.dec_deg, center[0], center[1])
        if xy is not None:
            points.append(xy)
    if len(points) >= 2:
        ax.plot([p[0] for p in points], [p[1] for p in points], linewidth=linewidth, alpha=0.58)


def render_figure(name: str, spec: dict, stars: list[Star], out_dir: Path) -> Path:
    index = star_index(stars)
    validate_spec(spec, index)

    anchors = [index[ref] for ref in all_refs(spec)]
    center = spherical_center(anchors)
    field_deg = float(spec["field_deg"])
    radius = field_deg / 2.0
    limiting_mag = 7.0

    visible = [
        star
        for star in stars
        if star.mag <= limiting_mag
        and angular_separation_deg(star, center[0], center[1]) <= radius * 1.05
    ]

    projected: list[tuple[float, float, Star]] = []
    for star in visible:
        xy = tangent_plane(star.ra_deg, star.dec_deg, center[0], center[1])
        if xy is not None:
            projected.append((xy[0], xy[1], star))

    fig, ax = plt.subplots(figsize=(8.2, 8.2))
    ax.set_xlim(radius, -radius)
    ax.set_ylim(-radius, radius)
    ax.set_aspect("equal", adjustable="box")

    if projected:
        ax.scatter(
            [p[0] for p in projected],
            [p[1] for p in projected],
            s=[marker_area(p[2].mag, limiting_mag) for p in projected],
        )

    for path in spec.get("figure_paths", []):
        draw_path(ax, path, index, center, linewidth=0.9)

    for asterism in spec.get("asterisms", []):
        for path in asterism.get("paths", []):
            draw_path(ax, path, index, center, linewidth=1.8)
        asterism_stars = [index[ref] for path in asterism.get("paths", []) for ref in path]
        axx, ayy = spherical_center(asterism_stars)
        label_xy = tangent_plane(axx, ayy, center[0], center[1])
        if label_xy is not None:
            ax.annotate(asterism["name"], label_xy, xytext=(0, 8), textcoords="offset points", ha="center", fontsize=8)

    label_refs = {ref for path in spec.get("figure_paths", []) for ref in path}
    for asterism in spec.get("asterisms", []):
        for path in asterism.get("paths", []):
            label_refs.update(path)

    for ref in sorted(label_refs):
        star = index[ref]
        xy = tangent_plane(star.ra_deg, star.dec_deg, center[0], center[1])
        if xy is not None and star.label:
            ax.annotate(star.label, xy, xytext=(4, 4), textcoords="offset points", fontsize=7)

    target = index[spec["target"]]
    target_xy = tangent_plane(target.ra_deg, target.dec_deg, center[0], center[1])
    if target_xy is not None:
        ring = plt.Circle(target_xy, max(0.45, field_deg * 0.012), fill=False, linewidth=1.4)
        ax.add_patch(ring)

    ax.set_title(f"{target.label}\nFinder chart · {field_deg:g}° field")
    ax.text(0.5, 0.015, spec["caption"], transform=ax.transAxes, ha="center", va="bottom", fontsize=8)
    ax.set_xlabel("East ←                                      → West")
    ax.set_ylabel("South                                      North")
    ax.set_xticks([])
    ax.set_yticks([])
    ax.grid(False)

    out_dir.mkdir(parents=True, exist_ok=True)
    output = out_dir / f"{spec['target_name'].lower()}-finder.svg"
    fig.tight_layout()
    fig.savefig(output, bbox_inches="tight")
    plt.close(fig)
    return output


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("hyg_catalog", type=Path)
    parser.add_argument("--config", type=Path, default=Path("constellation-figures.json"))
    parser.add_argument("--figure", default="all", help="Pegasus, Aquarius, or all")
    parser.add_argument("--out-dir", type=Path, default=Path("observer-views/W41"))
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    specs = json.loads(args.config.read_text(encoding="utf-8"))
    stars = load_hyg(args.hyg_catalog)
    names = list(specs) if args.figure.lower() == "all" else [args.figure]
    for name in names:
        if name not in specs:
            raise KeyError(f"Unknown figure {name!r}; choices: {', '.join(specs)}")
        output = render_figure(name, specs[name], stars, args.out_dir)
        print(f"wrote {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
