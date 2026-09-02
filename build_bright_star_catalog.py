#!/usr/bin/env python3
"""Build the Star Almanack second-magnitude bright-star catalog.

Selection rule:
    representative maximum Johnson V <= +2.50

Baseline rows come from a pinned HYG v4.1 catalog supplied on the command line.
Stable stars use catalog V magnitude as representative maximum unless an
explicit audited override is supplied. The script also marks whether each
selected object is already represented by the audited alpha/beta Bayer layer.
"""

from __future__ import annotations

import argparse
import csv
import re
from pathlib import Path

BAYER_RE = re.compile(r"^(Alp|Bet)(\d*)$")


def parse_float(value: str) -> float | None:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def load_alpha_beta_keys(path: Path) -> set[tuple[str, str]]:
    keys: set[tuple[str, str]] = set()
    with path.open(newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            code = (row.get("bayer_code") or "").strip()
            con = (row.get("con") or "").strip()
            if code and con:
                keys.add((code, con))
    return keys


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("hyg", type=Path)
    parser.add_argument("output", type=Path, nargs="?", default=Path("bright-stars-2mag.csv"))
    parser.add_argument("--bayer", type=Path, default=Path("expanded-bayer-stars.csv"))
    parser.add_argument("--limit", type=float, default=2.50)
    args = parser.parse_args()

    alpha_beta = load_alpha_beta_keys(args.bayer)

    with args.hyg.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))

    selected = []
    for row in rows:
        mag = parse_float(row.get("mag", ""))
        if mag is None or mag > args.limit:
            continue

        proper = (row.get("proper") or "").strip()
        con = (row.get("con") or "").strip()
        bayer = (row.get("bayer") or "").strip()
        bayer_code = ""
        if bayer:
            match = BAYER_RE.match(bayer)
            if match:
                bayer_code = match.group(1) + match.group(2)

        is_alpha_beta = bool(bayer_code and con and (bayer_code, con) in alpha_beta)
        selected.append({
            "proper": proper,
            "bayer": bayer,
            "con": con,
            "ra_h": row.get("ra", ""),
            "dec_deg": row.get("dec", ""),
            "catalog_v": row.get("mag", ""),
            "representative_vmax": row.get("mag", ""),
            "brightness_basis": "HYG v4.1 catalog V (stable baseline)",
            "in_alpha_beta_layer": "yes" if is_alpha_beta else "no",
            "hyg_id": row.get("id", ""),
            "hip": row.get("hip", ""),
            "hd": row.get("hd", ""),
            "hr": row.get("hr", ""),
        })

    selected.sort(key=lambda r: (float(r["representative_vmax"]), r["proper"] or r["bayer"], r["con"]))

    fieldnames = [
        "proper", "bayer", "con", "ra_h", "dec_deg", "catalog_v",
        "representative_vmax", "brightness_basis", "in_alpha_beta_layer",
        "hyg_id", "hip", "hd", "hr",
    ]
    with args.output.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(selected)

    non_ab = sum(r["in_alpha_beta_layer"] == "no" for r in selected)
    print(f"Selected {len(selected)} HYG baseline rows at V <= {args.limit:.2f}")
    print(f"New non-alpha/beta baseline rows: {non_ab}")
    print("Variable-star boundary audit remains required by bright-stars-2mag-spec.md")


if __name__ == "__main__":
    main()
