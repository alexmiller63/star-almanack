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
import shutil
import sys
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urljoin, urlparse

INDEX_URL = "https://iauarchive.eso.org/public/themes/constellations/"
DEFAULT_ROOT = Path("source-data/iau/constellation-boundaries")
USER_AGENT = "Star-Almanack-IAU-boundary-acquisition/1.1"

# Inventory is the set of actual TXT resources linked by the authoritative IAU
# page. Do not collapse resources by constellation abbreviation: Serpens is one
# constellation (SER) represented by two distinct boundary resources, Caput and
# Cauda.
TXT_LINK_RE = re.compile(
    r'''href=["'](?P<href>[^"']*/constellations/txt/[^"']+\.txt)["']''',
    re.IGNORECASE,
)
ROW_RE = re.compile(
    r"^\s*\d{1,2}\s+\d{1,2}\s+\d{1,2}(?:\.\d+)?\|\s*[+-]?\d+(?:\.\d+)?\|(?P<label>[A-Za-z]{3}\d*)\s*$"
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
    urls = [urljoin(INDEX_URL, m.group("href")) for m in TXT_LINK_RE.finditer(text)]
    if not urls:
        raise RuntimeError("no constellation boundary TXT links found on IAU index")
    duplicates = sorted({url for url in urls if urls.count(url) > 1})
    if duplicates:
        raise RuntimeError("duplicate IAU boundary resource URLs in index: " + ", ".join(duplicates))
    return sorted(urls)


def boundary_abbreviation(data: bytes, url: str) -> str:
    text = data.decode("utf-8", errors="strict")
    abbreviations: set[str] = set()
    data_rows = 0
    for line in text.splitlines():
        if not line.strip():
            continue
        match = ROW_RE.match(line)
        if not match:
            raise RuntimeError(f"invalid boundary row in {url}: {line!r}")
        data_rows += 1
        label = match.group("label").upper()
        # The IAU boundary resources label the two Serpens polygons SER1 and
        # SER2.  The numeric suffix identifies the resource/polygon, while the
        # underlying IAU constellation abbreviation remains SER.
        abbreviations.add(label[:3])
    if not data_rows:
        raise RuntimeError(f"no boundary coordinate rows in {url}")
    if len(abbreviations) != 1:
        raise RuntimeError(f"multiple constellation abbreviations in {url}: {sorted(abbreviations)}")
    return next(iter(abbreviations))


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=DEFAULT_ROOT)
    parser.add_argument(
        "--replace",
        action="store_true",
        help="deliberately replace an existing snapshot after a complete staged acquisition",
    )
    args = parser.parse_args()

    root: Path = args.root
    if root.exists() and any(root.iterdir()) and not args.replace:
        raise SystemExit(
            f"snapshot already exists at {root}; reuse it, or pass --replace for a deliberate refresh"
        )

    staging = root.with_name(root.name + ".staging")
    if staging.exists():
        shutil.rmtree(staging)
    raw_dir = staging / "raw"
    raw_dir.mkdir(parents=True, exist_ok=True)
    manifest_path = staging / "manifest.csv"
    provenance_path = staging / "provenance.json"
    index_path = staging / "authoritative-index.html"
    acquired_at = datetime.now(timezone.utc).replace(microsecond=0).isoformat()

    try:
        index_html = fetch_bytes(INDEX_URL)
        index_path.write_bytes(index_html)
        inventory = discover_inventory(index_html)

        rows: list[dict[str, str | int]] = []
        filenames: set[str] = set()
        constellation_abbreviations: set[str] = set()

        for url in inventory:
            filename = Path(urlparse(url).path).name
            if not filename or filename in filenames:
                raise RuntimeError(f"duplicate or invalid boundary filename: {filename!r}")
            filenames.add(filename)

            data = fetch_bytes(url)
            head = data[:512].lower()
            if b"<html" in head or b"<!doctype" in head:
                raise RuntimeError(f"unexpected HTML instead of TXT boundary data: {url}")

            abbr = boundary_abbreviation(data, url)
            constellation_abbreviations.add(abbr)
            destination = raw_dir / filename
            destination.write_bytes(data)
            rows.append(
                {
                    "iau_abbreviation": abbr,
                    "resource_filename": filename,
                    "source_url": url,
                    "local_path": f"raw/{filename}",
                    "byte_size": len(data),
                    "sha256": sha256(data),
                    "acquired_at_utc": acquired_at,
                }
            )

        actual_files = sorted(p.name for p in raw_dir.glob("*.txt"))
        expected_files = sorted(filenames)
        if actual_files != expected_files:
            raise RuntimeError("local snapshot inventory does not exactly match authoritative inventory")

        # The IAU recognizes 88 constellations. Serpens contributes two linked
        # boundary resources, so the authoritative page must yield 89 resources
        # representing 88 unique constellation abbreviations.
        if len(constellation_abbreviations) != 88:
            raise RuntimeError(
                f"expected 88 unique IAU constellation abbreviations, found {len(constellation_abbreviations)}"
            )
        if len(inventory) != 89:
            raise RuntimeError(f"expected 89 IAU boundary resources, found {len(inventory)}")
        ser_rows = [row for row in rows if row["iau_abbreviation"] == "SER"]
        if len(ser_rows) != 2:
            raise RuntimeError(f"expected two Serpens boundary resources, found {len(ser_rows)}")

        with manifest_path.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(
                handle,
                fieldnames=[
                    "iau_abbreviation",
                    "resource_filename",
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
            "schema_version": 2,
            "policy": "download once, reuse many",
            "authoritative_index_url": INDEX_URL,
            "acquired_at_utc": acquired_at,
            "authoritative_resource_count": len(inventory),
            "unique_constellation_count": len(constellation_abbreviations),
            "authoritative_inventory": inventory,
            "index_local_path": "authoritative-index.html",
            "index_sha256": sha256(index_html),
            "manifest": "manifest.csv",
            "raw_directory": "raw",
        }
        provenance_path.write_text(
            json.dumps(provenance, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )

        if root.exists():
            shutil.rmtree(root)
        staging.rename(root)
    except Exception:
        if staging.exists():
            shutil.rmtree(staging)
        raise

    print(f"IAU boundary snapshot acquired: {len(inventory)} resources")
    print(f"Unique IAU constellations represented: {len(constellation_abbreviations)}")
    print(f"Manifest: {root / 'manifest.csv'}")
    print(f"Provenance: {root / 'provenance.json'}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise SystemExit(1)
