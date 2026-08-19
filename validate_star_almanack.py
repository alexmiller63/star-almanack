#!/usr/bin/env python3
"""
Star Almanack — aggregate validation harness.

One command, one final PASS/FAIL, with section-level diagnostics.

Required sections:
  1. ELP2000-82B lunar reference regression.
  2. Julian-Date / UTC boundary regression.

Eclipse section:
  3. Historical solar eclipses.
  4. Mark Twain negative control.
  5. Future "Jell-O" NASA prediction comparisons.

The eclipse engine is always exercised.  While required_now is false in
eclipse-validation-cases.yaml, eclipse failures are reported diagnostically
but do not fail the overall workflow.  Once the eclipse layer is satisfactory,
set required_now: true and the same tests become release-blocking.

Important:
Published eclipse data are used only as validation targets.  eclipse_engine.py
does not read the validation catalog.

Why the UTC boundary tests are release-blocking
------------------------------------------------
The eclipse engine converts calculated Julian Dates back to civil UTC strings.
A rounding edge immediately before midnight once produced 86400 seconds within
a day.  The old repair recursively called the same conversion routine and, at
the exact boundary, could call itself with the same value indefinitely.

The production converter now normalizes the astronomical instant to whole-
second resolution before decomposing it into a calendar date and clock time.
The tests below deliberately straddle midnight so that this invariant remains
protected against future "cleanup" changes.
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

import eclipse_engine  # noqa: E402


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
        result = lunar_elp.evaluate(
            normalized,
            float(case["jd_tdb"]),
            precision_rad=0.0,
        )
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
    print(
        f"\nLUNAR SECTION: {'PASS' if ok else 'FAIL'} "
        f"({count - failures}/{count})"
    )
    return ok, count - failures, count


def validate_utc_boundaries() -> tuple[bool, int, int]:
    """
    Regression-test Julian-Date -> UTC conversion across a civil midnight.

    These cases are intentionally small and artificial.  They are not
    astronomical validation targets; they test a software invariant needed by
    every later astronomical result that is formatted as a UTC timestamp.

    The critical rule is:

        round/normalize the instant first,
        then decompose it into calendar date + time.

    That rule guarantees that a value rounding across midnight becomes the
    following date at 00:00:00 rather than the impossible state "86400 seconds
    on the previous date".
    """
    print("\n=== 2. JULIAN-DATE / UTC BOUNDARY TESTS ===")

    midnight = eclipse_engine.gregorian_to_jd(2026, 8, 19, 0.0)

    cases = [
        (
            "just before rounding threshold",
            midnight - 0.6 / 86400.0,
            "2026-08-18T23:59:59Z",
        ),
        (
            "just after rounding threshold",
            midnight - 0.4 / 86400.0,
            "2026-08-19T00:00:00Z",
        ),
        (
            "exact midnight",
            midnight,
            "2026-08-19T00:00:00Z",
        ),
        (
            "just after midnight, below next-second threshold",
            midnight + 0.4 / 86400.0,
            "2026-08-19T00:00:00Z",
        ),
        (
            "just after midnight, above next-second threshold",
            midnight + 0.6 / 86400.0,
            "2026-08-19T00:00:01Z",
        ),
    ]

    passed_count = 0

    for label, jd, expected in cases:
        try:
            calculated = eclipse_engine.jd_to_iso_utc(jd)
            passed = calculated == expected
        except Exception as exc:
            calculated = f"{type(exc).__name__}: {exc}"
            passed = False

        print(f"\n{label}")
        print(f"  JD:          {jd:.12f}")
        print(f"  calculated:  {calculated}")
        print(f"  expected:    {expected}")
        print(f"  {'PASS' if passed else 'FAIL'}")

        if passed:
            passed_count += 1

    total = len(cases)
    ok = passed_count == total

    print(
        f"\nUTC BOUNDARY SECTION: {'PASS' if ok else 'FAIL'} "
        f"({passed_count}/{total})"
    )
    return ok, passed_count, total


def _parse_iso_z(text: str) -> datetime:
    return datetime.fromisoformat(text.replace("Z", "+00:00"))


def _seconds_difference(calculated: str, expected: str) -> float:
    a = _parse_iso_z(calculated)
    b = _parse_iso_z(expected)
    return abs((a - b).total_seconds())


def _run_eclipse_case(
    engine: eclipse_engine.EclipseEngine,
    case: dict,
    *,
    time_tolerance_seconds: float,
) -> bool:
    event = engine.find_solar_eclipse(case["date_utc"])

    expected_exists = bool(case["expected_exists"])
    existence_ok = event.eclipse_exists == expected_exists

    print(f"\n{case['id']} — {case['label']}")
    print(f"  requested date:       {case['date_utc']}")
    print(
        f"  calculated eclipse:   "
        f"{'yes' if event.eclipse_exists else 'no'}"
    )
    print(
        f"  expected eclipse:     "
        f"{'yes' if expected_exists else 'no'}"
    )

    if not expected_exists:
        print(f"  closest alignment:    {event.greatest_utc}")
        print(f"  classification:       {event.eclipse_type}")
        print(
            f"  eclipse margin:       "
            f"{event.geometry.eclipse_margin_km:+.3f} km"
        )
        print(f"  {'PASS' if existence_ok else 'FAIL'}")
        return existence_ok

    expected_type = str(case["expected_type"])
    type_ok = event.eclipse_type == expected_type

    expected_time = case.get("expected_greatest_utc")
    if expected_time is None:
        expected_time = case.get("nasa_greatest_utc")

    time_ok = True
    time_error = None
    if expected_time:
        time_error = _seconds_difference(event.greatest_utc, expected_time)
        time_ok = time_error <= time_tolerance_seconds

    print(f"  calculated type:      {event.eclipse_type}")
    print(f"  expected type:        {expected_type}")
    print(f"  calculated greatest:  {event.greatest_utc}")

    if expected_time:
        print(f"  expected greatest:    {expected_time}")
        print(f"  time error:           {time_error:.1f} s")
        print(f"  time tolerance:       {time_tolerance_seconds:.1f} s")

    # Magnitude is deliberately not graded yet.  The current eclipse engine
    # computes shadow-axis geometry and classification but does not yet expose
    # a conventional catalog eclipse magnitude.  Keeping that explicit avoids
    # silently pretending to validate a quantity we have not calculated.
    magnitude_target = case.get("expected_magnitude")
    if magnitude_target is None:
        magnitude_target = case.get("nasa_magnitude")
    if magnitude_target is not None:
        print(
            f"  magnitude target:     {float(magnitude_target):.4f} "
            "(registered; calculation not yet implemented)"
        )

    passed = existence_ok and type_ok and time_ok
    print(f"  {'PASS' if passed else 'FAIL'}")
    return passed


def validate_eclipses() -> tuple[bool, int, int, bool]:
    spec = load_yaml(ECLIPSE_CASES)
    historical = spec.get("historical", [])
    negative = spec.get("negative_controls", [])
    future = spec.get("future_jello", {}).get("cases", [])
    all_cases = historical + negative + future

    required = bool(spec.get("required_now", False))
    tolerance = float(
        spec.get("tolerances", {}).get("greatest_time_seconds", 120)
    )

    print("\n=== 3. SOLAR ECLIPSE GEOMETRY TESTS ===")
    print(f"  Historical positive controls: {len(historical)}")
    print(f"  Negative controls:            {len(negative)}")
    print(f"  Future Jell-O comparisons:    {len(future)}")
    print(
        f"  enforcement:                  "
        f"{'REQUIRED' if required else 'DIAGNOSTIC'}"
    )

    engine = eclipse_engine.EclipseEngine(MODEL)

    passed = 0
    for case in all_cases:
        if _run_eclipse_case(
            engine,
            case,
            time_tolerance_seconds=tolerance,
        ):
            passed += 1

    total = len(all_cases)
    ok = passed == total

    print(
        f"\nECLIPSE SECTION: {'PASS' if ok else 'FAIL'} "
        f"({passed}/{total})"
    )
    if not required:
        print(
            "  NOTE: Eclipse results are diagnostic until "
            "required_now is set to true."
        )

    return ok, passed, total, required


def main() -> None:
    print("Star Almanack — complete validation")
    print(f"UTC run time: {datetime.now(timezone.utc).isoformat()}")

    lunar_ok, lunar_passed, lunar_total = validate_lunar()
    utc_ok, utc_passed, utc_total = validate_utc_boundaries()
    eclipse_ok, eclipse_passed, eclipse_total, eclipse_required = (
        validate_eclipses()
    )

    # Lunar-reference correctness and time-conversion correctness are always
    # required.  Eclipse catalog comparisons remain diagnostic until the
    # validation YAML explicitly promotes them to release-blocking status.
    required_results = [lunar_ok, utc_ok]
    if eclipse_required:
        required_results.append(eclipse_ok)

    overall = all(required_results)

    print("\n=== FINAL RESULT ===")
    print(f"Required lunar cases: {lunar_passed}/{lunar_total} passed")
    print(f"Required UTC boundary cases: {utc_passed}/{utc_total} passed")

    if eclipse_required:
        print(
            f"Required eclipse cases: "
            f"{eclipse_passed}/{eclipse_total} passed"
        )
    else:
        print(
            f"Diagnostic eclipse cases: "
            f"{eclipse_passed}/{eclipse_total} passed"
        )

    print(f"STAR ALMANACK VALIDATION: {'PASS' if overall else 'FAIL'}")
    raise SystemExit(0 if overall else 1)


if __name__ == "__main__":
    main()
