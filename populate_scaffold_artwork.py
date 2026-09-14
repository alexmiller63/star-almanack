#!/usr/bin/env python3
"""Recreate Artwork blocks from an authoritative yearly handoff catalog."""
from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path

from scaffold_sections import iso_week_count, replace_owner_blocks, write_atomic

ROOT = Path(__file__).resolve().parent


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("year", type=int)
    parser.add_argument("--root", type=Path, default=ROOT)
    args = parser.parse_args()
    scaffold = args.root / "year-scaffolds" / f"almanack-{args.year}.md"
    source = args.root / f"sky-note-artwork-descriptors-{args.year}.json"
    if not scaffold.exists() or not source.exists():
        raise SystemExit(f"Missing scaffold or artwork handoff catalog for {args.year}")
    payload = json.loads(source.read_text(encoding="utf-8"))
    if payload.get("year") != args.year or not isinstance(payload.get("descriptors"), list):
        raise ValueError(f"Invalid artwork handoff catalog: {source}")
    by_week: dict[str, list[dict]] = {}
    for descriptor in payload["descriptors"]:
        week = descriptor.get("week", "")
        if week not in {f"W{i:02d}" for i in range(1, iso_week_count(args.year) + 1)}:
            raise ValueError(f"Invalid artwork descriptor week: {week!r}")
        by_week.setdefault(week, []).append(descriptor)

    output = args.root / f"artwork-descriptors-{args.year}"
    if output.exists():
        shutil.rmtree(output)
    output.mkdir(parents=True)
    blocks: dict[int, str] = {}
    for week in range(1, iso_week_count(args.year) + 1):
        week_id = f"W{week:02d}"
        descriptors = by_week.get(week_id, [])
        week_payload = {
            "schema": "star-almanack.artwork-week.v1",
            "iso_week": f"{args.year}-{week_id}",
            "descriptors": descriptors,
            "generated_from": source.name,
        }
        target = output / f"{week_id}.json"
        target.write_text(json.dumps(week_payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        if descriptors:
            names = ", ".join(item["constellation"] for item in descriptors)
            blocks[week] = (
                f"**Artwork handoff:** {names}\n\n"
                f"[Open {week_id} machine-readable artwork descriptor]"
                f"(../artwork-descriptors-{args.year}/{week_id}.json)"
            )
        else:
            blocks[week] = (
                "No artwork is specified by the authoritative handoff catalog for this week.\n\n"
                f"[Open {week_id} machine-readable artwork descriptor]"
                f"(../artwork-descriptors-{args.year}/{week_id}.json)"
            )
    updated = replace_owner_blocks(
        scaffold.read_text(encoding="utf-8"), args.year, "artwork", blocks.__getitem__
    )
    write_atomic(scaffold, updated)
    print(f"Recreated {len(blocks)} Artwork blocks and descriptor files for {args.year}")


if __name__ == "__main__":
    main()
