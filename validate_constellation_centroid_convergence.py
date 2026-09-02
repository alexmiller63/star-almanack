#!/usr/bin/env python3
"""Test numerical convergence of constellation area centroids.

Recompute all 88 IAU constellation centroids at three sampling resolutions and
compare both the spherical centroid displacement and the resulting Star
Almanack Night of Observance date.  This is an implementation-validation test,
not an input to the astronomical model.
"""

from __future__ import annotations

import csv
import datetime as dt
import math
from pathlib import Path

from compute_bayer_visibility_2026 import best_visibility
from compute_constellation_observance_2026 import CONSTELLATIONS, centroid_for

STEPS = (0.20, 0.10, 0.05)
CACHE_DIR = Path('.cache/iau-constellation-boundaries')
OUTPUT = Path('constellation-centroid-convergence-2026.csv')


def angular_separation_deg(ra1_h: float, dec1_deg: float, ra2_h: float, dec2_deg: float) -> float:
    r1 = math.radians(ra1_h * 15.0)
    r2 = math.radians(ra2_h * 15.0)
    d1 = math.radians(dec1_deg)
    d2 = math.radians(dec2_deg)
    dot = (
        math.cos(d1) * math.cos(d2) * math.cos(r1 - r2)
        + math.sin(d1) * math.sin(d2)
    )
    dot = max(-1.0, min(1.0, dot))
    return math.degrees(math.acos(dot))


def day_shift(a: dt.date, b: dt.date) -> int:
    return abs((a - b).days)


def main() -> None:
    if len(CONSTELLATIONS) != 88 or len({abbr for _, abbr in CONSTELLATIONS}) != 88:
        raise SystemExit('Constellation table must contain exactly 88 unique IAU abbreviations')

    rows = []
    exact_010_005 = 0
    within_one_day_010_005 = 0
    max_sep_010_005 = 0.0
    max_shift_010_005 = 0

    for name, abbr in CONSTELLATIONS:
        solutions = {}
        for step in STEPS:
            ra_h, dec_deg, area = centroid_for(abbr, CACHE_DIR, step)
            instant, date = best_visibility(ra_h)
            solutions[step] = (ra_h, dec_deg, area, instant, date)

        r020, d020, a020, _, date020 = solutions[0.20]
        r010, d010, a010, _, date010 = solutions[0.10]
        r005, d005, a005, _, date005 = solutions[0.05]

        sep_020_010 = angular_separation_deg(r020, d020, r010, d010)
        sep_010_005 = angular_separation_deg(r010, d010, r005, d005)
        shift_020_010 = day_shift(date020, date010)
        shift_010_005 = day_shift(date010, date005)

        exact_010_005 += date010 == date005
        within_one_day_010_005 += shift_010_005 <= 1
        max_sep_010_005 = max(max_sep_010_005, sep_010_005)
        max_shift_010_005 = max(max_shift_010_005, shift_010_005)

        rows.append({
            'name': name,
            'abbr': abbr,
            'ra_h_0.20': f'{r020:.8f}',
            'dec_deg_0.20': f'{d020:.8f}',
            'area_sq_deg_0.20': f'{a020:.4f}',
            'date_0.20': date020.isoformat(),
            'ra_h_0.10': f'{r010:.8f}',
            'dec_deg_0.10': f'{d010:.8f}',
            'area_sq_deg_0.10': f'{a010:.4f}',
            'date_0.10': date010.isoformat(),
            'ra_h_0.05': f'{r005:.8f}',
            'dec_deg_0.05': f'{d005:.8f}',
            'area_sq_deg_0.05': f'{a005:.4f}',
            'date_0.05': date005.isoformat(),
            'centroid_shift_deg_0.20_to_0.10': f'{sep_020_010:.6f}',
            'centroid_shift_deg_0.10_to_0.05': f'{sep_010_005:.6f}',
            'date_shift_days_0.20_to_0.10': str(shift_020_010),
            'date_shift_days_0.10_to_0.05': str(shift_010_005),
        })
        print(
            f'{abbr:3s} {name:20s} '
            f'{date020} -> {date010} -> {date005}; '
            f'fine shift {sep_010_005:.4f} deg / {shift_010_005} d'
        )

    with OUTPUT.open('w', newline='', encoding='utf-8') as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)

    print()
    print(f'0.10° vs 0.05° exact-date agreement: {exact_010_005}/88')
    print(f'0.10° vs 0.05° within 1 day: {within_one_day_010_005}/88')
    print(f'Max 0.10° -> 0.05° centroid displacement: {max_sep_010_005:.6f}°')
    print(f'Max 0.10° -> 0.05° Night-of-Observance shift: {max_shift_010_005} day(s)')
    print(f'Wrote {len(rows)} rows to {OUTPUT}')


if __name__ == '__main__':
    main()
