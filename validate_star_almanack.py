#!/usr/bin/env python3
"""
Star Almanack — aggregate validation harness.

One command, one final PASS/FAIL, with section-level diagnostics.

Current required section:
  1. ELP2000-82B lunar reference regression.

Registered but not yet required:
  2. Historical solar eclipses.
  3. Mark Twain negative control.
  4. Future "Jell-O" NASA prediction comparisons.

When the eclipse event-search/classification layer is connected, set
required_now: true in eclipse-validation-cases.yaml and this harness will
treat those sections as required.
"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
import math
import sys

import yaml

ROOT = Path(__file__).resolve().parent
ELP_DIR = ROOT / "star-almanack-elp82b"
LUNAR_CASES = ELP_DIR / "lunar-validation-cases.yaml"
ECLIPSE_CASES = ROOT / "eclipse-validation-cases.yaml"
MODEL = ELP_DIR / "elp82b-manifest.json"

sys.path.insert(0, str(ELP_DIR))
import lunar_elp  # noqa: E402


def load_yaml(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def validate_lunar() -> tuple[bool, int, int]:
    spec = load_yaml(LUNAR_CASES)
    tolerance = float(spec["tolerance_km"])
    normalized = lunar_elp.load_normalized(MODEL)

    print("\n=== 1. LUNAR ELP2000-82B REFERENCE TESTS ===")
    failures = 0

    for case in spec["cases"]:
        result = lunar_elp.evaluate(normalized, float(case["jd_tdb"]), precision_rad=0.0)
        rect = result.rectangular
        exp = case["expected"]

        dx = rect.x_km - float(exp["x_km"])
        dy = rect.y_km - float(exp["y_km"])
        dz = rect.z_km - float(exp["z_km"])
        error = math.sqrt(dx * dx + dy * dy + dz * dz)
        passed = error <= tolerance

        print(f"\n{case['name']}")
        print(f"  dX = {dx:+.9f} km")
        print(f"  dY = {dy:+.9f} km")
        print(f"  dZ = {dz:+.9f} km")
        print(f"  3D = {error:.9f} km")
        print(f"  tolerance = {tolerance:.9f} km")
        print(f"  {'PASS' if passed else 'FAIL'}")

        if not passed:
            failures += 1

    count = len(spec["cases"])
    ok = failures == 0
    print(f"\nLUNAR SECTION: {'PASS' if ok else 'FAIL'} ({count - failures}/{count})")
    return ok, count - failures, count


def validate_eclipse_catalog() -> tuple[bool | None, int]:
    spec = load_yaml(ECLIPSE_CASES)
    historical = spec.get("historical", [])
    negative = spec.get("negative_controls", [])
    future = spec.get("future_jello", {}).get("cases", [])
    count = len(historical) + len(negative) + len(future)

    print("\n=== 2. SOLAR ECLIPSE VALIDATION CATALOG ===")
    print(f"  Historical positive controls: {len(historical)}")
    print(f"  Negative controls:            {len(negative)}")
    print(f"  Future Jell-O comparisons:    {len(future)}")

    required = bool(spec.get("required_now", False))
    if not required:
        print("  STATUS: REGISTERED / NOT YET REQUIRED")
        print("  The cases are frozen, but the event-search/classification layer")
        print("  is not yet connected to this aggregate harness.")
        return None, count

    # Safety: never silently claim eclipse validation if required_now is turned
    # on before the actual event-search/classification runner is implemented.
    print("  FAIL: required_now is true, but eclipse runner is not implemented.")
    return False, count


def main() -> None:
    print("Star Almanack — complete validation")
    print(f"UTC run time: {datetime.now(timezone.utc).isoformat()}")

    lunar_ok, lunar_passed, lunar_total = validate_lunar()
    eclipse_ok, eclipse_total = validate_eclipse_catalog()

    required_results = [lunar_ok]
    if eclipse_ok is not None:
        required_results.append(eclipse_ok)

    overall = all(required_results)

    print("\n=== FINAL RESULT ===")
    print(f"Required lunar cases: {lunar_passed}/{lunar_total} passed")
    if eclipse_ok is None:
        print(f"Registered eclipse cases: {eclipse_total} (not yet required)")
    else:
        print(f"Required eclipse cases: {eclipse_total}")

    print(f"STAR ALMANACK VALIDATION: {'PASS' if overall else 'FAIL'}")
    raise SystemExit(0 if overall else 1)


if __name__ == "__main__":
    main()
