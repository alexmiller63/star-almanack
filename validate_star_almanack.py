#!/usr/bin/env python3

"""

Star Almanack — aggregate validation harness.

One command, one final PASS/FAIL, with section-level diagnostics.

Required sections:

  1. ELP2000-82B lunar reference regression.

  2. Julian-Date / UTC boundary regression.

Diagnostic sections:

  3. Sun frame / J2000 diagnostic.

  4. Solar eclipse geometry tests.

The eclipse engine is always exercised. While required_now is false in

eclipse-validation-cases.yaml, eclipse failures are reported diagnostically

but do not fail the overall workflow. Once the eclipse layer is satisfactory,

set required_now: true and the same tests become release-blocking.

Important:

Published eclipse data are used only as validation targets. eclipse_engine.py

does not read the validation catalog.

Why the UTC boundary tests are release-blocking

------------------------------------------------

The eclipse engine converts calculated Julian Dates back to civil UTC strings.

A rounding edge immediately before midnight once produced 86400 seconds within

a day. The old repair recursively called the same conversion routine and, at

the exact boundary, could call itself with the same value indefinitely.

The production converter now normalizes the astronomical instant to whole-

second resolution before decomposing it into a calendar date and clock time.

The tests below deliberately straddle midnight so that this invariant remains

protected against future "cleanup" changes.

Why the Sun-frame diagnostic exists

-----------------------------------

The ELP2000-82B lunar evaluator independently validates against the Bureau des

Longitudes reference implementation and returns geocentric rectangular

coordinates in the mean dynamical ecliptic and inertial equinox of J2000.

The compact Sun model begins with a vector treated by the eclipse engine as

ecliptic-of-date. The production code then rotates that vector to

equatorial-of-date, precesses it to J2000, and rotates it back to the J2000

ecliptic.

The eclipse timing residuals vary strongly with epoch. This diagnostic observes

the Sun vector immediately before and after that frame-conversion boundary at

dates on both sides of J2000.

It changes no production calculation and has no PASS/FAIL status.

Why the eclipse geometry diagnostics exist

-------------------------------------------

When a positive eclipse case has a published/reference greatest-eclipse time,

the harness evaluates the Star Almanack geometry at BOTH:

  * the engine's calculated greatest-eclipse instant, and

  * the published/reference greatest-eclipse instant.

This does not change the calculation, classification, search algorithm, or

PASS/FAIL rules. It is instrumentation only.

The comparison helps distinguish two classes of defect:

  * search defect:

      the reference instant has the better Star Almanack geometry, but the

      search routine selected another instant;

  * geometry/ephemeris/frame defect:

      Star Almanack's own geometry is genuinely better at the calculated

      instant, meaning the displaced result originates upstream of the search.

The diagnostic is intentionally general and runs for every positive eclipse

case that supplies an expected/reference greatest-eclipse time.

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

    These cases are intentionally small and artificial. They are not

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

def _iso_z_to_jd(text: str) -> float:

    """

    Convert an ISO-8601 UTC timestamp to Julian Date using the eclipse engine's

    own Gregorian-calendar convention.

    This helper is diagnostic only. It deliberately reuses

    eclipse_engine.gregorian_to_jd() so the comparison does not introduce a

    second, independent calendar-to-JD implementation.

    """

    dt = _parse_iso_z(text).astimezone(timezone.utc)

    hour = (

        dt.hour

        + dt.minute / 60.0

        + dt.second / 3600.0

        + dt.microsecond / 3_600_000_000.0

    )

    return eclipse_engine.gregorian_to_jd(

        dt.year,

        dt.month,

        dt.day,

        hour,

    )

def _angle_between_deg(

    a: eclipse_engine.Vec3,

    b: eclipse_engine.Vec3,

) -> float:

    """Return the smaller angle between two non-zero vectors in degrees."""

    denom = a.norm() * b.norm()

    if denom == 0.0:

        return float("nan")

    cosine = a.dot(b) / denom

    # Floating-point roundoff can produce a value infinitesimally outside the

    # mathematical [-1, +1] domain of acos().

    cosine = max(-1.0, min(1.0, cosine))

    return math.degrees(math.acos(cosine))

def _print_vec(label: str, v: eclipse_engine.Vec3) -> None:

    print(

        f"      {label:<5} "

        f"x={v.x:+.3f} km  "

        f"y={v.y:+.3f} km  "

        f"z={v.z:+.3f} km"

    )

def _compact_sun_ecliptic_of_date(

    jd_tdb: float,

) -> eclipse_engine.Vec3:

    """

    Reconstruct the compact Sun vector before the production J2000 frame

    transformation.

    This is diagnostic instrumentation only. It deliberately duplicates the

    orbital portion of eclipse_engine.sun_vector_j2000() so that validation can

    observe the vector on both sides of the frame-conversion boundary without

    changing production behavior.

    The returned vector is the compact model's geocentric ecliptic-of-date

    vector, in kilometers.

    """

    d = jd_tdb - 2451543.5

    w = (

        (282.9404 + 0.0000470935 * d) % 360.0

    ) * eclipse_engine.DEG

    e = 0.016709 - 0.000000001151 * d

    M = (

        (356.0470 + 0.9856002585 * d) % 360.0

    ) * eclipse_engine.DEG

    # Solve Kepler's equation exactly as the production Sun routine does.

    E = M

    for _ in range(12):

        f = E - e * math.sin(E) - M

        fp = 1.0 - e * math.cos(E)

        step = f / fp

        E -= step

        if abs(step) < 1e-14:

            break

    x = math.cos(E) - e

    y = math.sqrt(1.0 - e * e) * math.sin(E)

    r_au = math.hypot(x, y)

    true_anom = math.atan2(y, x)

    lon = true_anom + w

    return eclipse_engine.Vec3(

        r_au * math.cos(lon) * eclipse_engine.AU_KM,

        r_au * math.sin(lon) * eclipse_engine.AU_KM,

        0.0,

    )

def validate_sun_frame_diagnostic() -> None:

    """

    Observe the Sun vector immediately before and after its current J2000

    transformation at epochs spanning both sides of J2000.

    Purpose

    -------

    Eclipse timing errors presently increase and change with epoch. The lunar

    evaluator independently validates against the ELP2000-82B Fortran reference

    and already returns J2000 ecliptic coordinates. This diagnostic therefore

    isolates the Sun-side frame conversion without altering it.

    If the angular displacement introduced by the Sun frame transformation is

    essentially zero at J2000 and grows with distance from J2000, that confirms

    the transformation itself is epoch-dependent. Correlation between that

    displacement and the observed eclipse timing errors would make the

    interpretation of the compact Sun coefficients' reference frame the next

    object of investigation.

    This section is INFORMATIONAL ONLY. It has no PASS/FAIL result and cannot

    affect the aggregate validation status.

    """

    print("\n=== 3. SUN FRAME / J2000 DIAGNOSTIC ===")

    print("  enforcement:                  DIAGNOSTIC ONLY")

    print("  Moon frame:                   ELP2000-82B J2000 ecliptic")

    print("  raw Sun:                      compact ecliptic-of-date assumption")

    print("  transformed Sun:              current production J2000 conversion")

    print(

        "  question:                     how much angular displacement "

        "does that conversion introduce?"

    )

    # These epochs deliberately bracket J2000 and include eclipse epochs whose

    # timing residuals are already recorded by the permanent eclipse suite.

    epochs = [

        ("1919 eclipse epoch", "1919-05-29T13:08:34Z"),

        ("1991 eclipse epoch", "1991-07-11T19:06:03Z"),

        ("J2000 epoch", "2000-01-01T12:00:00Z"),

        ("2017 eclipse epoch", "2017-08-21T18:25:30Z"),

        ("2024 eclipse epoch", "2024-04-08T18:17:15Z"),

        ("2028 eclipse epoch", "2028-07-22T02:56:39Z"),

    ]

    engine = eclipse_engine.EclipseEngine(MODEL)

    for label, iso_utc in epochs:

        jd_utc = _iso_z_to_jd(iso_utc)

        # Reuse the production geometry path to obtain exactly the same

        # approximate TDB argument, transformed Sun, and ELP2000 Moon that the

        # eclipse calculation uses.

        geometry = engine.geometry_at_utc_jd(jd_utc)

        raw_sun = _compact_sun_ecliptic_of_date(

            geometry.jd_tdb_approx

        )

        transformed_sun = geometry.sun

        moon = geometry.moon

        frame_shift_deg = _angle_between_deg(

            raw_sun,

            transformed_sun,

        )

        epoch_offset_years = (

            geometry.jd_tdb_approx - 2451545.0

        ) / 365.25

        print(f"\n{label}")

        print(f"  UTC:                         {iso_utc}")

        print(f"  JD TDB approx:               {geometry.jd_tdb_approx:.12f}")

        print(f"  years from J2000:            {epoch_offset_years:+.6f}")

        print(f"  Sun frame angular shift:     {frame_shift_deg:.9f} deg")

        _print_vec("Raw", raw_sun)

        _print_vec("J2000", transformed_sun)

        _print_vec("Moon", moon)

    print(

        "\nSUN FRAME DIAGNOSTIC: INFORMATIONAL "

        "(does not affect final PASS/FAIL)"

    )

def _print_geometry_snapshot(

    label: str,

    iso_utc: str,

    geometry: eclipse_engine.SolarGeometry,

) -> None:

    """

    Print the quantities most useful for locating a displaced eclipse minimum.

    axis_distance_km is the objective minimized by EclipseEngine's search.

    Sun-Moon angular separation is included as an intuitive secondary measure;

    it is NOT substituted for the production shadow-axis objective.

    """

    separation_deg = _angle_between_deg(

        geometry.sun,

        geometry.moon,

    )

    print(f"\n    {label}")

    print(f"      UTC:                 {iso_utc}")

    print(f"      JD UTC:              {geometry.jd_utc:.12f}")

    print(f"      JD TDB approx:       {geometry.jd_tdb_approx:.12f}")

    print(f"      Sun-Moon separation: {separation_deg:.9f} deg")

    print(f"      axis distance:       {geometry.axis_distance_km:.3f} km")

    print(f"      q(min):              {geometry.q_min_km:.3f} km")

    print(f"      eclipse margin:      {geometry.eclipse_margin_km:+.3f} km")

    print(f"      central margin:      {geometry.central_margin_km:+.3f} km")

    print(f"      eclipse type:        {geometry.eclipse_type}")

    _print_vec("Sun", geometry.sun)

    _print_vec("Moon", geometry.moon)

def _print_reference_geometry_diagnostic(

    engine: eclipse_engine.EclipseEngine,

    event: eclipse_engine.SolarEclipseEvent,

    expected_time: str,

) -> None:

    """

    Compare Star Almanack geometry at calculated and reference greatest times.

    No reference value is fed into the eclipse calculation or search. The

    reference instant is evaluated only after the engine has independently

    produced its result.

    """

    reference_jd = _iso_z_to_jd(expected_time)

    reference_geometry = engine.geometry_at_utc_jd(reference_jd)

    calculated_geometry = event.geometry

    _print_geometry_snapshot(

        "geometry at CALCULATED greatest",

        event.greatest_utc,

        calculated_geometry,

    )

    _print_geometry_snapshot(

        "geometry at REFERENCE greatest",

        expected_time,

        reference_geometry,

    )

    axis_delta = (

        reference_geometry.axis_distance_km

        - calculated_geometry.axis_distance_km

    )

    sep_calc = _angle_between_deg(

        calculated_geometry.sun,

        calculated_geometry.moon,

    )

    sep_ref = _angle_between_deg(

        reference_geometry.sun,

        reference_geometry.moon,

    )

    separation_delta = sep_ref - sep_calc

    print("\n    diagnostic comparison")

    print(

        f"      reference - calculated axis distance: "

        f"{axis_delta:+.3f} km"

    )

    print(

        f"      reference - calculated angular sep.:  "

        f"{separation_delta:+.9f} deg"

    )

    if axis_delta < 0.0:

        print(

            "      search clue: reference time has SMALLER axis distance; "

            "inspect search/bracketing."

        )

    elif axis_delta > 0.0:

        print(

            "      geometry clue: calculated time has SMALLER axis distance; "

            "inspect ephemeris/frame/time inputs."

        )

    else:

        print(

            "      geometry clue: axis distances are equal at displayed "

            "precision."

        )

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

        time_error = _seconds_difference(

            event.greatest_utc,

            expected_time,

        )

        time_ok = time_error <= time_tolerance_seconds

    print(f"  calculated type:      {event.eclipse_type}")

    print(f"  expected type:        {expected_type}")

    print(f"  calculated greatest:  {event.greatest_utc}")

    if expected_time:

        print(f"  expected greatest:    {expected_time}")

        print(f"  time error:           {time_error:.1f} s")

        print(f"  time tolerance:       {time_tolerance_seconds:.1f} s")

        # Diagnostic only. The reference time is never used to influence the

        # engine's independently calculated event.

        _print_reference_geometry_diagnostic(

            engine,

            event,

            expected_time,

        )

    # Magnitude is deliberately not graded yet. The current eclipse engine

    # computes shadow-axis geometry and classification but does not yet expose

    # a conventional catalog eclipse magnitude. Keeping that explicit avoids

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

        spec.get(

            "tolerances",

            {},

        ).get(

            "greatest_time_seconds",

            120,

        )

    )

    print("\n=== 4. SOLAR ECLIPSE GEOMETRY TESTS ===")

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

    # This section is intentionally diagnostic only. It is not included in

    # required_results and therefore cannot change the workflow's exit status.

    validate_sun_frame_diagnostic()

    eclipse_ok, eclipse_passed, eclipse_total, eclipse_required = (

        validate_eclipses()

    )

    # Lunar-reference correctness and time-conversion correctness are always

    # required. Eclipse catalog comparisons remain diagnostic until the

    # validation YAML explicitly promotes them to release-blocking status.

    required_results = [

        lunar_ok,

        utc_ok,

    ]

    if eclipse_required:

        required_results.append(eclipse_ok)

    overall = all(required_results)

    print("\n=== FINAL RESULT ===")

    print(

        f"Required lunar cases: "

        f"{lunar_passed}/{lunar_total} passed"

    )

    print(

        f"Required UTC boundary cases: "

        f"{utc_passed}/{utc_total} passed"

    )

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

    print(

        f"STAR ALMANACK VALIDATION: "

        f"{'PASS' if overall else 'FAIL'}"

    )

    raise SystemExit(0 if overall else 1)

if __name__ == "__main__":

    main()

