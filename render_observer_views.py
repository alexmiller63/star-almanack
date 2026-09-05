#!/usr/bin/env python3
"""Render source-driven observer views for Star Almanack.

This script produces three reproducible views from catalog coordinates:

* finder     — wide field for locating the target
* binoculars — 10x50-class view
* telescope  — 6-inch-class low-power eyepiece view

The renderings are catalog-derived diagrams, not astrophotographs.  The
Almanack can explain that convention once in its legend/front matter and
caption individual figures simply as, for example:

    Eyepiece view · 6-inch telescope · 50× · 1.2° field

No network access is used.  Star coordinates and magnitudes come only from
an input catalog supplied on the command line.  The target center is read
from fixed-objects.yaml so the astronomical source remains upstream of the
rendering code.

Expected star-catalog CSV columns:

    ra_deg,dec_deg,mag[,label]

Optional proper-motion columns are also accepted:

    pmra_masyr,pmdec_masyr,epoch

`pmra_masyr` is assumed to be mu_alpha*cos(delta), the usual catalog form.
If proper-motion columns are absent, coordinates are used as supplied.

Examples:

    python render_observer_views.py M35 stars.csv --view finder
    python render_observer_views.py M35 stars.csv --view binoculars
    python render_observer_views.py M35 stars.csv --view telescope
    python render_observer_views.py M35 stars.csv --view all --out-dir views

SVG is the default output because it is text, scales cleanly in Jekyll, and
keeps generated binary files out of the source repository.  PNG may be
requested explicitly with --format png.
"""

from __future__ import annotations

import argparse
import csv
import math
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

import matplotlib.pyplot as plt


@dataclass(frozen=True)
class ViewPreset:
    key: str
    title: str
    field_deg: float
    limiting_mag: float
    aperture: str | None = None
    magnification: str | None = None

    @property
    def caption(self) -> str:
        if self.key == "finder":
            return f"Finder chart · {self.field_deg:g}° field"
        if self.key == "binoculars":
            return (
                f"Binocular view · {self.aperture} · {self.magnification} · "
                f"{self.field_deg:g}° field"
            )
        return (
            f"Eyepiece view · {self.aperture} · {self.magnification} · "
            f"{self.field_deg:g}° field"
        )


PRESETS = {
    "finder": ViewPreset(
        key="finder",
        title="Finder chart",
        field_deg=10.0,
        limiting_mag=7.0,
    ),
    "binoculars": ViewPreset(
        key="binoculars",
        title="Binocular view",
        field_deg=6.5,
        limiting_mag=9.5,
        aperture="10×50 binoculars",
        magnification="10×",
    ),
    "telescope": ViewPreset(
        key="telescope",
        title="Eyepiece view",
        field_deg=1.2,
        limiting_mag=12.5,
        aperture="6-inch telescope",
        magnification="50×",
    ),
}


@dataclass
class Star:
    ra_deg: float
    dec_deg: float
    mag: float
    label: str = ""


@dataclass(frozen=True)
class Target:
    designation: str
    ra_deg: float
    dec_deg: float
    name: str | None
    ngc_or_ic: str | None


def _split_yaml_row(text: str) -> list[str]:
    """Split the simple bracket-row format used by fixed-objects.yaml."""
    # This source file deliberately uses compact YAML flow sequences.  We do
    # not need a YAML dependency merely to retrieve designation, coordinates,
    # and names, but quoted commas must still be respected.
    row = next(csv.reader([text], skipinitialspace=True))
    return [item.strip().strip("'\"") for item in row]


def load_target(path: Path, designation: str) -> Target:
    wanted = designation.upper()
    pattern = re.compile(r"^\s*-\s*\[(.*)\]\s*$")

    for line in path.read_text(encoding="utf-8").splitlines():
        match = pattern.match(line)
        if not match:
            continue
        fields = _split_yaml_row(match.group(1))
        if not fields or fields[0].upper() != wanted:
            continue

        # Messier schema:
        # id, ngc, name, type, con, ra_h, dec_deg, mag, size_arcmin, best, iso
        if len(fields) < 8:
            raise ValueError(f"Malformed fixed-object row for {designation}")

        ngc = fields[1] if fields[1].lower() not in {"", "null", "none"} else None
        if ngc and ngc.isdigit():
            ngc = f"NGC {ngc}"
        name = fields[2] if fields[2].lower() not in {"", "null", "none"} else None
        ra_deg = float(fields[5]) * 15.0
        dec_deg = float(fields[6])
        return Target(wanted, ra_deg, dec_deg, name, ngc)

    raise KeyError(f"Target {designation!r} not found in {path}")


def apply_proper_motion(
    ra_deg: float,
    dec_deg: float,
    pmra_masyr: float | None,
    pmdec_masyr: float | None,
    epoch: float | None,
    target_epoch: float,
) -> tuple[float, float]:
    if pmra_masyr is None or pmdec_masyr is None or epoch is None:
        return ra_deg, dec_deg

    years = target_epoch - epoch
    cos_dec = math.cos(math.radians(dec_deg))
    if abs(cos_dec) < 1e-12:
        dra_deg = 0.0
    else:
        dra_deg = (pmra_masyr * years) / (3_600_000.0 * cos_dec)
    ddec_deg = (pmdec_masyr * years) / 3_600_000.0
    return (ra_deg + dra_deg) % 360.0, dec_deg + ddec_deg


def load_stars(path: Path, target_epoch: float) -> list[Star]:
    stars: list[Star] = []
    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        required = {"ra_deg", "dec_deg", "mag"}
        missing = required - set(reader.fieldnames or [])
        if missing:
            raise ValueError(
                f"Star catalog is missing required columns: {', '.join(sorted(missing))}"
            )

        for row in reader:
            ra = float(row["ra_deg"])
            dec = float(row["dec_deg"])
            mag = float(row["mag"])
            label = (row.get("label") or "").strip()

            def optional_float(key: str) -> float | None:
                value = (row.get(key) or "").strip()
                return float(value) if value else None

            ra, dec = apply_proper_motion(
                ra,
                dec,
                optional_float("pmra_masyr"),
                optional_float("pmdec_masyr"),
                optional_float("epoch"),
                target_epoch,
            )
            stars.append(Star(ra, dec, mag, label))
    return stars


def tangent_plane(
    ra_deg: float,
    dec_deg: float,
    center_ra_deg: float,
    center_dec_deg: float,
) -> tuple[float, float] | None:
    """Gnomonic projection, returned in angular-degree-like tangent units."""
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


def angular_separation_deg(
    ra1_deg: float, dec1_deg: float, ra2_deg: float, dec2_deg: float
) -> float:
    ra1, dec1, ra2, dec2 = map(
        math.radians, (ra1_deg, dec1_deg, ra2_deg, dec2_deg)
    )
    value = (
        math.sin(dec1) * math.sin(dec2)
        + math.cos(dec1) * math.cos(dec2) * math.cos(ra1 - ra2)
    )
    return math.degrees(math.acos(max(-1.0, min(1.0, value))))


def visible_stars(stars: Iterable[Star], target: Target, preset: ViewPreset) -> list[Star]:
    radius = preset.field_deg / 2.0
    return [
        star
        for star in stars
        if star.mag <= preset.limiting_mag
        and angular_separation_deg(
            star.ra_deg, star.dec_deg, target.ra_deg, target.dec_deg
        )
        <= radius * 1.05
    ]


def marker_area(mag: float, limiting_mag: float) -> float:
    """Map stellar magnitude to a restrained plotted disk area."""
    # Flux ratio would make bright stars overwhelmingly large.  This compressed
    # relation retains magnitude hierarchy while remaining readable in print.
    return max(2.0, 5.0 + 5.0 * (limiting_mag - mag))


def render_view(
    target: Target,
    stars: list[Star],
    preset: ViewPreset,
    output: Path,
    dpi: int,
) -> None:
    selected = visible_stars(stars, target, preset)
    projected: list[tuple[float, float, Star]] = []
    for star in selected:
        xy = tangent_plane(star.ra_deg, star.dec_deg, target.ra_deg, target.dec_deg)
        if xy is not None:
            projected.append((xy[0], xy[1], star))

    fig, ax = plt.subplots(figsize=(7.2, 7.2))
    radius = preset.field_deg / 2.0

    # Astronomical charts conventionally put east to the left.  This is also a
    # useful neutral default for observer diagrams; a later instrument-specific
    # orientation layer can rotate/flip the view without changing source data.
    ax.set_xlim(radius, -radius)
    ax.set_ylim(-radius, radius)
    ax.set_aspect("equal", adjustable="box")

    if projected:
        xs = [p[0] for p in projected]
        ys = [p[1] for p in projected]
        sizes = [marker_area(p[2].mag, preset.limiting_mag) for p in projected]
        ax.scatter(xs, ys, s=sizes)

    if preset.key == "finder":
        # Label only catalog stars that have supplied labels; no guessed names.
        for x, y, star in projected:
            if star.label and star.mag <= 5.0:
                ax.annotate(star.label, (x, y), xytext=(4, 4), textcoords="offset points", fontsize=7)

    ax.scatter([0.0], [0.0], marker="+", s=100)

    target_label = target.designation
    if target.name:
        target_label += f" · {target.name}"
    elif target.ngc_or_ic:
        target_label += f" · {target.ngc_or_ic}"

    ax.set_title(f"{target_label}\n{preset.caption}")
    ax.set_xlabel("East ←   angular offset   → West")
    ax.set_ylabel("South   angular offset   North")
    ax.grid(False)

    # Eyepiece and binocular fields are circular.  The finder remains square to
    # maximize contextual information and make cardinal orientation obvious.
    if preset.key in {"binoculars", "telescope"}:
        circle = plt.Circle((0, 0), radius, fill=False)
        ax.add_patch(circle)
        ax.set_clip_path(circle)

    fig.tight_layout()
    output.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output, dpi=dpi, bbox_inches="tight")
    plt.close(fig)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("target", help="Fixed-object designation, for example M35")
    parser.add_argument("star_catalog", type=Path, help="CSV star catalog")
    parser.add_argument(
        "--fixed-objects",
        type=Path,
        default=Path("fixed-objects.yaml"),
        help="authoritative fixed-object source (default: fixed-objects.yaml)",
    )
    parser.add_argument(
        "--view",
        choices=["finder", "binoculars", "telescope", "all"],
        default="all",
        help="view to render (default: all)",
    )
    parser.add_argument(
        "--out-dir",
        type=Path,
        default=Path("observer-views"),
        help="output directory (default: observer-views)",
    )
    parser.add_argument(
        "--format",
        choices=["svg", "png"],
        default="svg",
        help="output format (default: svg)",
    )
    parser.add_argument(
        "--epoch",
        type=float,
        default=2026.0,
        help="target epoch for optional proper-motion propagation (default: 2026.0)",
    )
    parser.add_argument("--dpi", type=int, default=180, help="PNG/SVG save DPI metadata")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    target = load_target(args.fixed_objects, args.target)
    stars = load_stars(args.star_catalog, args.epoch)

    keys = list(PRESETS) if args.view == "all" else [args.view]
    for key in keys:
        preset = PRESETS[key]
        filename = f"{target.designation}-{key}.{args.format}"
        output = args.out_dir / filename
        render_view(target, stars, preset, output, args.dpi)
        print(f"wrote {output} — {preset.caption}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
