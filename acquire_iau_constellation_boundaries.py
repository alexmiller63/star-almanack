#!/usr/bin/env python3
"""Acquire an auditable local snapshot of IAU constellation boundary TXT files.

This is an explicit acquisition tool, not part of normal Almanack generation.
Downstream code must reuse the preserved snapshot without network access.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
import sys
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urljoin

INDEX_URL = "https://iauarchive.eso.org/public/themes/constellations/"
DIRECT_TEMPLATE = "https://iauarchive.eso.org/static/public/constellations/txt/{abbr}.txt"
DEFAULT_ROOT = Path("source-data/iau/constellation-boundaries")
USER_AGENT = "Star-Almanack-IAU-boundary-acquisition/1.0"

# Discover the authoritative inventory from the IAU presentation page, then use
# the deterministic direct-download URLs for the preserved source resources.
TXT_LINK_RE = re.compile(
    r'''(?:href=["'])(?P<href>[^"']*/constellations/txt/(?P<abbr>[a-z]{3})\.txt)(?:["'])''',
    re.IGNORECASE,
)


def fetch_bytes(url: str) -> bytes:
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(request, timeout=30) as response:
        data = response.read()
    if not data:
        raise RuntimeError(f"empty response: {url}")
    return data


def discover_inventory(index_html: bytes) -> list[str]:
    text = index_html.decode("utf-8", errors="strict")
    abbreviations = [m.group("abbr").lower() for m in TXT_LINK_RE.finditer(text)]
    if not abbreviations:
        raise RuntimeError("no constellation boundary TXT links found on IAU index")
    duplicates = sorted({abbr for abbr in abbreviations if abbreviations.count(abbr) > 1})
    if duplicates:
        raise RuntimeError(f"duplicate IAU boundary resources in index: {', '.join(duplicates)}")
    return sorted(abbreviations)


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=DEFAULT_ROOT)
    parser.add_argument(
        "--replace",
        action="store_true",
        help="deliberately replace an existing snapshot instead of refusing to overwrite it",
    )
    args = parser.parse_args()

    root: Path = args.root
    raw_dir = root / "raw"
    manifest_path = root / "manifest.csv"
    provenance_path = root / "provenance.json"

    if root.exists() and any(root.iterdir()) and not args.replace:
        raise SystemExit(
            f"snapshot already exists at {root}; reuse it, or pass --replace for a deliberate refresh"
        )

    raw_dir.mkdir(parents=True, exist_ok=True)
    acquired_at = datetime.now(timezone.utc).replace(microsecond=0).isoformat()

    index_html = fetch_bytes(INDEX_URL)
    inventory = discover_inventory(index_html)

    rows: list[dict[str, str | int]] = []
    seen: set[str] = set()
    for abbr in inventory:
        if abbr in seen:
            raise RuntimeError(f"duplicate abbreviation during acquisition: {abbr}")
        seen.add(abbr)

        url = DIRECT_TEMPLATE.format(abbr=abbr)
        data = fetch_bytes(url)
        # Boundary resources are textual numeric tables. Reject an HTML error
        # page even if a server returns it with HTTP 200.
        head = data[:512].lower()
        if b"<html" in head or b"<!doctype" in head:
            raise RuntimeError(f"unexpected HTML instead of TXT boundary data: {url}")

        destination = raw_dir / f"{abbr}.txt"
        destination.write_bytes(data)
        rows.append(
            {
                "iau_abbreviation": abbr,
                "source_url": url,
                "local_path": destination.as_posix(),
                "byte_size": len(data),
                "sha256": sha256(data),
                "acquired_at_utc": acquired_at,
            }
        )

    actual_files = sorted(p.stem for p in raw_dir.glob("*.txt"))
    if actual_files != inventory:
        raise RuntimeError("local snapshot inventory does not exactly match authoritative inventory")

    with manifest_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=[
                "iau_abbreviation",
                "source_url",
                "local_path",
                "byte_size",
                "sha256",
                "acquired_at_utc",
            ],
        )
        writer.writeheader()
        writer.writerows(rows)

    provenance = {
        "schema_version": 1,
        "policy": "download once, reuse many",
        "authoritative_index_url": INDEX_URL,
        "direct_download_template": DIRECT_TEMPLATE,
        "acquired_at_utc": acquired_at,
        "authoritative_inventory_count": len(inventory),
        "authoritative_inventory": inventory,
        "index_sha256": sha256(index_html),
        "manifest": manifest_path.as_posix(),
        "raw_directory": raw_dir.as_posix(),
    }
    provenance_path.write_text(
        json.dumps(provenance, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )

    print(f"IAU boundary snapshot acquired: {len(inventory)} resources")
    print(f"Manifest: {manifest_path}")
    print(f"Provenance: {provenance_path}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise SystemExit(1)
