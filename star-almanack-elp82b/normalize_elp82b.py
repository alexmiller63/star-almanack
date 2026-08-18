#!/usr/bin/env python3
"""
Normalize the 36 fixed-format CDS ELP2000-82B coefficient files.

Why a separate normalizer?
--------------------------
The original CDS VI/79 files are the archival model data.  We keep them
unaltered.  This tool converts them into a compact, machine-readable copy for
the Star Almanack evaluator while retaining provenance.

The evaluator should never edit the raw CDS files.

Status
------
The exact fixed-width parser is intentionally versioned separately.  The
archive's own Fortran reference (`elp82b.f`) is the parsing authority.  This
program first checks that all 36 files are present and emits a manifest with
hashes.  The numeric parser will be completed only from that reference format;
we do not guess field widths.
"""

from pathlib import Path
import argparse, hashlib, json

def sha256(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()

def make_manifest(src: Path, out: Path) -> None:
    files = []
    for i in range(1, 37):
        p = src / f"ELP{i}"
        if not p.exists():
            raise SystemExit(f"missing {p}")
        files.append({
            "name": p.name,
            "bytes": p.stat().st_size,
            "sha256": sha256(p),
        })
    for name in ("ReadMe", "elp82b.f", "example.f", "elp82b.ps"):
        p = src / name
        if p.exists():
            files.append({
                "name": p.name,
                "bytes": p.stat().st_size,
                "sha256": sha256(p),
            })

    payload = {
        "model": "ELP2000-82B",
        "source_catalog": "CDS/VizieR VI/79",
        "files": files,
    }
    out.write_text(json.dumps(payload, indent=2) + "\n")
    print(f"wrote {out}")

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("source_directory", type=Path)
    ap.add_argument("manifest", type=Path)
    a = ap.parse_args()
    make_manifest(a.source_directory, a.manifest)
