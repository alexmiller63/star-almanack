#!/usr/bin/env python3
"""
Star Almanack lunar engine — ELP2000-82B bootstrap and evaluator harness.

This module is deliberately split from ephemeris_engine.py.  The original
compact engine remains the regression baseline.

ELP2000-82B source data:
    CDS/VizieR catalogue VI/79
    https://cdsarc.cds.unistra.fr/ftp/VI/79/

The catalogue contains 36 coefficient files (ELP1 ... ELP36), plus the
reference Fortran subroutine elp82b.f and example.f.

This file does NOT import a published lunar ephemeris table.  It obtains model
coefficients and evaluates the lunar theory locally.

Time argument:
    TT (Terrestrial Time), expressed as Julian centuries from J2000.0.

The bootstrap command downloads the official coefficient files from CDS:
    python lunar_elp.py bootstrap data/elp82b

A second command verifies that all expected files are present:
    python lunar_elp.py verify data/elp82b

The numerical evaluator will be connected to the normalized coefficients
produced by normalize_elp82b.py.  Keeping bootstrap/normalization separate makes
the adopted model data auditable and reproducible.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from urllib.request import urlopen, Request
import argparse
import math
import sys

CDS_BASE = "https://cdsarc.cds.unistra.fr/ftp/VI/79"

# Expected record counts from CDS ReadMe VI/79.
EXPECTED_RECORDS = {
    1: 1024, 2: 919, 3: 705,
    4: 348, 5: 317, 6: 238,
    7: 15, 8: 12, 9: 9,
    10: 14329, 11: 5234, 12: 6632,
    13: 4385, 14: 834, 15: 1716,
    16: 171, 17: 151, 18: 115,
    19: 227, 20: 189, 21: 170,
    22: 4, 23: 3, 24: 3,
    25: 7, 26: 5, 27: 6,
    28: 21, 29: 13, 30: 15,
    31: 12, 32: 5, 33: 11,
    34: 29, 35: 14, 36: 20,
}

AUX_FILES = ("ReadMe", "elp82b.f", "example.f", "elp82b.ps")


def _download(url: str, dest: Path) -> None:
    req = Request(url, headers={"User-Agent": "Star-Almanack/1.0"})
    with urlopen(req, timeout=60) as r:
        data = r.read()
    dest.write_bytes(data)


def bootstrap(directory: Path) -> None:
    directory.mkdir(parents=True, exist_ok=True)
    for name in AUX_FILES:
        dest = directory / name
        if not dest.exists():
            print(f"fetch {name}")
            _download(f"{CDS_BASE}/{name}", dest)
    for i in range(1, 37):
        name = f"ELP{i}"
        dest = directory / name
        if not dest.exists():
            print(f"fetch {name}")
            _download(f"{CDS_BASE}/{name}", dest)
    verify(directory)


def count_records(path: Path) -> int:
    # CDS files contain one heading record followed by the data records described
    # by the catalogue.  Blank lines are ignored.
    with path.open("r", encoding="ascii", errors="replace") as f:
        return sum(1 for line in f if line.strip())


def verify(directory: Path) -> None:
    missing = []
    for i in range(1, 37):
        p = directory / f"ELP{i}"
        if not p.exists():
            missing.append(p.name)
    for name in AUX_FILES:
        if not (directory / name).exists():
            missing.append(name)
    if missing:
        raise SystemExit("Missing ELP2000-82B files: " + ", ".join(missing))

    print("ELP2000-82B archive present.")
    print("Coefficient tables:")
    for i in range(1, 37):
        p = directory / f"ELP{i}"
        print(f"  ELP{i:02d}: {p.stat().st_size:>9} bytes")
    print("Verification passed: all 36 coefficient tables and reference files are present.")


# ---- Mean arguments ---------------------------------------------------------
# Coefficients are the ELP2000-82B argument polynomials documented by the
# reference implementation, expressed in arcseconds and evaluated in Julian
# centuries of TT from J2000.0.

W1 = (785939.95571, 1732559343.73604, -5.8883, 0.006604, -0.00003169)
W2 = (300071.67475, 14643420.2632, -38.2776, -0.045047, 0.00021301)
W3 = (450160.39816, -6967919.3622, 6.3622, 0.007625, -0.00003586)
T_EARTH = (361679.22059, 129597742.2758, -0.0202, 0.000009, 0.00000015)
PERIHELION = (370574.42753, 1161.2283, 0.5327, -0.000138, 0.0)

PLANETARY_ARGUMENTS = (
    (908103.25986, 538101628.68898),   # Mercury
    (655127.28305, 210664136.43355),   # Venus
    (361679.22059, 129597742.2758),    # Earth
    (1279559.78866, 68905077.59284),   # Mars
    (123665.34212, 10925660.42861),    # Jupiter
    (180278.89694, 4399609.65932),     # Saturn
    (1130598.01841, 1542481.19393),    # Uranus
    (1095655.19575, 786550.32074),     # Neptune
)

ARCSEC_PER_CIRCLE = 1296000.0


def poly(c, t):
    s = 0.0
    p = 1.0
    for x in c:
        s += x * p
        p *= t
    return s


@dataclass(frozen=True)
class Arguments:
    D: float
    lp: float
    l: float
    F: float
    zeta: float
    planets: tuple[float, ...]


def arguments_tt(jd_tt: float) -> Arguments:
    """Return ELP angular arguments in radians."""
    t = (jd_tt - 2451545.0) / 36525.0
    w1 = poly(W1, t)
    w2 = poly(W2, t)
    w3 = poly(W3, t)
    te = poly(T_EARTH, t)
    per = poly(PERIHELION, t)

    D = w1 - te + 648000.0
    lp = te - per
    l = w1 - w2
    F = w1 - w3

    # ELP precession argument zeta = W1(linearized for this argument) + p*t.
    zeta = W1[0] + W1[1] * t + 5029.0966 * t

    planets = tuple(a0 + a1*t for (a0, a1) in PLANETARY_ARGUMENTS)

    conv = math.pi / 648000.0
    wrap = lambda x: (x % ARCSEC_PER_CIRCLE) * conv
    return Arguments(
        D=wrap(D), lp=wrap(lp), l=wrap(l), F=wrap(F),
        zeta=wrap(zeta),
        planets=tuple(wrap(x) for x in planets),
    )


def main(argv=None):
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="command", required=True)
    p = sub.add_parser("bootstrap", help="download official CDS VI/79 model files")
    p.add_argument("directory", type=Path)
    p = sub.add_parser("verify", help="verify archive files are present")
    p.add_argument("directory", type=Path)
    p = sub.add_parser("arguments", help="print ELP arguments for JD(TT)")
    p.add_argument("jd_tt", type=float)
    args = ap.parse_args(argv)

    if args.command == "bootstrap":
        bootstrap(args.directory)
    elif args.command == "verify":
        verify(args.directory)
    else:
        a = arguments_tt(args.jd_tt)
        print(a)


if __name__ == "__main__":
    main()
