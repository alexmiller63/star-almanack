#!/usr/bin/env python3

"""

Star Almanack — compact-Sun / frame-conversion prosecution lineup.

Purpose

-------

Separate two possible sources of the epoch-dependent solar error seen in

Star Almanack eclipse validation:

    1. the compact solar model itself

    2. the ecliptic-of-date -> J2000 frame conversion

The existing sun-jpl-diagnostic.py compares only the final production

Sun vector against JPL Horizons.  That is useful, but the final vector

contains both effects:

    compact solar model

        +

    production frame transformation

This diagnostic puts the suspects in separate lineups.

For every test epoch it computes four Sun vectors:

    RAW COMPACT

        Star Almanack compact solar model in mean ecliptic-of-date

        coordinates, before the production frame transformation.

    PRODUCTION

        eclipse_engine.sun_vector_j2000(), exactly as used by the

        production eclipse calculation.

    ERFA TRANSFORMED

        The same raw compact vector transformed independently from

        mean ecliptic-of-date to J2000 ecliptic using ERFA / IAU 2006

        reference-frame routines.

    JPL HORIZONS

        Independent geometric geocentric Sun vector from JPL Horizons

        in ICRF/J2000 ecliptic coordinates.

The JPL vector is also independently transformed by ERFA into

ecliptic-of-date coordinates.

This permits three especially important measurements:

    MODEL-ONLY RESIDUAL

        raw compact Sun

            minus

        JPL Sun transformed to ecliptic-of-date

    FRAME DISAGREEMENT

        production transformed compact Sun

            minus

        ERFA-transformed compact Sun

    PRODUCTION RESIDUAL

        production transformed compact Sun

            minus

        JPL Sun in J2000 ecliptic

Interpretation

--------------

If MODEL-ONLY RESIDUAL is large:

    the compact solar model itself contributes real error.

If FRAME DISAGREEMENT is large:

    the production date-to-J2000 transformation contributes real error.

If both are large:

    both members of the crime family are guilty.

If both become small after correction but eclipse timing still has a

systematic residual:

    the surviving residual becomes evidence for another culprit elsewhere

    in the eclipse calculation.

Independent frame authority

---------------------------

This diagnostic uses PyERFA, the Python wrapper around ERFA, which is

derived from the IAU SOFA Standards of Fundamental Astronomy routines.

ERFA's ecm06() supplies the IAU 2006 rotation matrix from ICRS equatorial

coordinates to mean ecliptic coordinates for a specified TT date.

The transformation performed here is therefore independent of the

classical IAU-1976 precession implementation inside eclipse_engine.py.

Time convention

---------------

The same production approximate dynamical JD used by the eclipse engine is

used for the compact Sun and for the JPL Horizons request.

ERFA's frame routines formally accept TT.  For this diagnostic the

production approximate TDB/TT argument is used as TT for the frame rotation.

The TDB-TT difference is vastly too small to explain degree-scale

epoch-dependent frame errors and is irrelevant to the question being tested.

Network behavior

----------------

This diagnostic intentionally contacts JPL Horizons.

A Horizons/network failure is diagnostic unavailability, not a Star

Almanack validation failure.  The program reports the failure and exits

successfully.

This file is DIAGNOSTIC ONLY.  It does not modify production eclipse

geometry and does not supply JPL data to eclipse_engine.py.

"""

from __future__ import annotations

import json

import math

import re

from urllib.parse import urlencode

from urllib.request import Request, urlopen

import erfa

import numpy as np

import eclipse_engine

HORIZONS_API = "https://ssd.jpl.nasa.gov/api/horizons.api"

J2000_JD = 2451545.0

AU_KM = eclipse_engine.AU_KM

DEG = math.pi / 180.0

# ---------------------------------------------------------------------------

# Representative epochs

# ---------------------------------------------------------------------------

TEST_EPOCHS = [

    (

        "1919 eclipse",

        "1919-05-29T13:08:34Z",

    ),

    (

        "1963 eclipse",

        "1963-07-20T20:35:38Z",

    ),

    (

        "1991 eclipse",

        "1991-07-11T19:06:03Z",

    ),

    (

        "J2000",

        "2000-01-01T12:00:00Z",

    ),

    (

        "2017 eclipse",

        "2017-08-21T18:25:30Z",

    ),

    (

        "2024 eclipse",

        "2024-04-08T18:17:15Z",

    ),

]

# ---------------------------------------------------------------------------

# General vector helpers

# ---------------------------------------------------------------------------

def wrap_signed_deg(angle: float) -> float:

    """

    Normalize degrees to [-180, +180).

    """

    return (angle + 180.0) % 360.0 - 180.0

def vector_longitude_deg(v: eclipse_engine.Vec3) -> float:

    """

    Ecliptic longitude of a rectangular vector.

    """

    return math.degrees(

        math.atan2(

            v.y,

            v.x,

        )

    ) % 360.0

def angle_between_deg(

    a: eclipse_engine.Vec3,

    b: eclipse_engine.Vec3,

) -> float:

    """

    Three-dimensional angular separation between two vectors.

    """

    denom = a.norm() * b.norm()

    if denom == 0.0:

        return float("nan")

    cosine = a.dot(b) / denom

    cosine = max(

        -1.0,

        min(

            1.0,

            cosine,

        ),

    )

    return math.degrees(

        math.acos(cosine)

    )

def vec_to_numpy(

    v: eclipse_engine.Vec3,

) -> np.ndarray:

    """

    Convert Star Almanack Vec3 to a NumPy vector.

    """

    return np.array(

        [

            v.x,

            v.y,

            v.z,

        ],

        dtype=float,

    )

def numpy_to_vec(

    a: np.ndarray,

) -> eclipse_engine.Vec3:

    """

    Convert a three-element NumPy vector to Star Almanack Vec3.

    """

    return eclipse_engine.Vec3(

        float(a[0]),

        float(a[1]),

        float(a[2]),

    )

def print_vector(

    label: str,

    vector: eclipse_engine.Vec3,

) -> None:

    """

    Print a rectangular vector.

    """

    print(

        f"  {label:<22}"

        f"x={vector.x:+.3f} km  "

        f"y={vector.y:+.3f} km  "

        f"z={vector.z:+.3f} km"

    )

# ---------------------------------------------------------------------------

# Civil timestamp -> production dynamical argument

# ---------------------------------------------------------------------------

def iso_z_to_jd(

    text: str,

) -> float:

    """

    Convert an ISO UTC-like timestamp to Julian Date using the same calendar

    routine used by the production eclipse engine.

    """

    date_part, time_part = text.rstrip("Z").split("T")

    year, month, day = (

        int(part)

        for part in date_part.split("-")

    )

    hour_text, minute_text, second_text = time_part.split(":")

    hour = int(hour_text)

    minute = int(minute_text)

    second = float(second_text)

    decimal_hour = (

        hour

        + minute / 60.0

        + second / 3600.0

    )

    return eclipse_engine.gregorian_to_jd(

        year,

        month,

        day,

        decimal_hour,

    )

def production_tdb_jd(

    civil_text: str,

) -> tuple[float, float]:

    """

    Return the civil JD and the same approximate dynamical JD used by the

    production eclipse engine.

    """

    jd_civil = iso_z_to_jd(

        civil_text

    )

    jd_tdb = eclipse_engine.utc_to_tdb_approx(

        jd_civil

    )

    return (

        jd_civil,

        jd_tdb,

    )

# ---------------------------------------------------------------------------

# Raw Star Almanack compact solar model

# ---------------------------------------------------------------------------

def compact_sun_ecliptic_of_date(

    jd_tdb: float,

) -> eclipse_engine.Vec3:

    """

    Evaluate the Star Almanack compact Sun exactly as production does,

    but STOP before the ecliptic-of-date -> J2000 frame transformation.

    The coefficients intentionally duplicate those currently used by

    eclipse_engine.sun_vector_j2000() so this diagnostic isolates only the

    transformation stage.

    Output:

        mean ecliptic-of-date rectangular vector, kilometers

    """

    d = jd_tdb - 2451543.5

    w = (

        282.9404

        + 0.0000470935 * d

    ) % 360.0

    e = (

        0.016709

        - 0.000000001151 * d

    )

    M = (

        356.0470

        + 0.9856002585 * d

    ) % 360.0

    w_rad = w * DEG

    M_rad = M * DEG

    # Solve Kepler's equation using the same Newton iteration as production.

    E = M_rad

    for _ in range(12):

        f = (

            E

            - e * math.sin(E)

            - M_rad

        )

        fp = (

            1.0

            - e * math.cos(E)

        )

        step = f / fp

        E -= step

        if abs(step) < 1e-14:

            break

    x_orbit = (

        math.cos(E)

        - e

    )

    y_orbit = (

        math.sqrt(

            1.0 - e * e

        )

        * math.sin(E)

    )

    r_au = math.hypot(

        x_orbit,

        y_orbit,

    )

    true_anomaly = math.atan2(

        y_orbit,

        x_orbit,

    )

    longitude = (

        true_anomaly

        + w_rad

    )

    return eclipse_engine.Vec3(

        r_au * math.cos(longitude) * AU_KM,

        r_au * math.sin(longitude) * AU_KM,

        0.0,

    )

# ---------------------------------------------------------------------------

# Independent ERFA frame transformations

# ---------------------------------------------------------------------------

def erfa_ecliptic_matrix(

    jd_tt: float,

) -> np.ndarray:

    """

    IAU 2006 ICRS-equatorial -> mean-ecliptic-of-date rotation matrix.

    ERFA accepts TT as a two-part Julian Date.

    Splitting around J2000 preserves numerical precision.

    """

    date1 = J2000_JD

    date2 = jd_tt - J2000_JD

    matrix = erfa.ecm06(

        date1,

        date2,

    )

    return np.asarray(

        matrix,

        dtype=float,

    )

def erfa_ecliptic_date_to_j2000(

    vector_date: eclipse_engine.Vec3,

    jd_tt: float,

) -> eclipse_engine.Vec3:

    """

    Transform mean ecliptic-of-date -> J2000 mean ecliptic independently.

    ERFA ecm06(date) maps:

        ICRS equatorial -> ecliptic of date

    Therefore:

        ecliptic of date -> ICRS

    is the transpose of that rotation.

    We then apply the J2000 ecliptic matrix:

        ICRS -> J2000 ecliptic

    """

    date_matrix = erfa_ecliptic_matrix(

        jd_tt

    )

    j2000_matrix = erfa_ecliptic_matrix(

        J2000_JD

    )

    v_date = vec_to_numpy(

        vector_date

    )

    # Ecliptic of date -> ICRS.

    v_icrs = date_matrix.T @ v_date

    # ICRS -> J2000 ecliptic.

    v_j2000 = j2000_matrix @ v_icrs

    return numpy_to_vec(

        v_j2000

    )

def erfa_ecliptic_j2000_to_date(

    vector_j2000: eclipse_engine.Vec3,

    jd_tt: float,

) -> eclipse_engine.Vec3:

    """

    Transform J2000 mean ecliptic -> mean ecliptic-of-date independently.

    This is used to put the JPL reference vector in the same frame as the

    RAW compact Sun.

    """

    date_matrix = erfa_ecliptic_matrix(

        jd_tt

    )

    j2000_matrix = erfa_ecliptic_matrix(

        J2000_JD

    )

    v_j2000 = vec_to_numpy(

        vector_j2000

    )

    # J2000 ecliptic -> ICRS.

    v_icrs = j2000_matrix.T @ v_j2000

    # ICRS -> ecliptic of date.

    v_date = date_matrix @ v_icrs

    return numpy_to_vec(

        v_date

    )

# ---------------------------------------------------------------------------

# JPL Horizons

# ---------------------------------------------------------------------------

def horizons_request(

    jd_tdb: float,

) -> str:

    """

    Request a geometric geocentric Sun vector from JPL Horizons.

    Target:

        Sun

    Center:

        Earth center

    Reference system:

        ICRF

    Reference plane:

        ecliptic

    Time scale:

        TDB

    Corrections:

        NONE

    """

    params = {

        "format": "json",

        "COMMAND": "'10'",

        "CENTER": "'500@399'",

        "EPHEM_TYPE": "'VECTORS'",

        "REF_SYSTEM": "'ICRF'",

        "REF_PLANE": "'ECLIPTIC'",

        "OUT_UNITS": "'KM-S'",

        "VEC_TABLE": "'2'",

        "VEC_CORR": "'NONE'",

        "CSV_FORMAT": "'NO'",

        "TIME_TYPE": "'TDB'",

        "TLIST_TYPE": "'JD'",

        "TLIST": f"'{jd_tdb:.12f}'",

    }

    url = (

        HORIZONS_API

        + "?"

        + urlencode(params)

    )

    request = Request(

        url,

        headers={

            "User-Agent":

                "Star-Almanack-Sun-Frame-Lineup-Diagnostic/1.0"

        },

    )

    with urlopen(

        request,

        timeout=30,

    ) as response:

        raw = response.read().decode(

            "utf-8"

        )

    payload = json.loads(

        raw

    )

    if "result" not in payload:

        raise RuntimeError(

            "Horizons response did not contain a result field"

        )

    return payload["result"]

def parse_horizons_vector(

    text: str,

) -> eclipse_engine.Vec3:

    """

    Extract X, Y, Z from the Horizons vector ephemeris block.

    """

    if "$$SOE" not in text or "$$EOE" not in text:

        raise RuntimeError(

            "Horizons result did not contain an ephemeris data block"

        )

    block = (

        text

        .split(

            "$$SOE",

            1,

        )[1]

        .split(

            "$$EOE",

            1,

        )[0]

    )

    pattern = re.compile(

        r"X\s*=\s*"

        r"([+-]?\d+(?:\.\d*)?(?:[Ee][+-]?\d+)?)"

        r"\s+Y\s*=\s*"

        r"([+-]?\d+(?:\.\d*)?(?:[Ee][+-]?\d+)?)"

        r"\s+Z\s*=\s*"

        r"([+-]?\d+(?:\.\d*)?(?:[Ee][+-]?\d+)?)"

    )

    match = pattern.search(

        block

    )

    if match is None:

        raise RuntimeError(

            "Could not parse X/Y/Z from Horizons vector output"

        )

    return eclipse_engine.Vec3(

        float(match.group(1)),

        float(match.group(2)),

        float(match.group(3)),

    )

# ---------------------------------------------------------------------------

# One prosecution-lineup case

# ---------------------------------------------------------------------------

def run_case(

    label: str,

    civil_text: str,

) -> dict[str, float]:

    """

    Run one complete model / frame / production comparison.

    """

    (

        jd_civil,

        jd_tdb,

    ) = production_tdb_jd(

        civil_text

    )

    # Suspect 1:

    # compact model before production frame conversion.

    raw_compact = compact_sun_ecliptic_of_date(

        jd_tdb

    )

    # Existing production result.

    production = eclipse_engine.sun_vector_j2000(

        jd_tdb

    )

    # Independently transform the exact same raw vector.

    erfa_transformed = erfa_ecliptic_date_to_j2000(

        raw_compact,

        jd_tdb,

    )

    # Independent external reference.

    horizons_text = horizons_request(

        jd_tdb

    )

    jpl_j2000 = parse_horizons_vector(

        horizons_text

    )

    # Put JPL into the raw compact model's frame.

    jpl_date = erfa_ecliptic_j2000_to_date(

        jpl_j2000,

        jd_tdb,

    )

    raw_lon = vector_longitude_deg(

        raw_compact

    )

    jpl_date_lon = vector_longitude_deg(

        jpl_date

    )

    production_lon = vector_longitude_deg(

        production

    )

    erfa_lon = vector_longitude_deg(

        erfa_transformed

    )

    jpl_j2000_lon = vector_longitude_deg(

        jpl_j2000

    )

    # ------------------------------------------------------------------

    # Principal evidence

    # ------------------------------------------------------------------

    model_only_residual = wrap_signed_deg(

        raw_lon

        - jpl_date_lon

    )

    frame_disagreement = wrap_signed_deg(

        production_lon

        - erfa_lon

    )

    production_residual = wrap_signed_deg(

        production_lon

        - jpl_j2000_lon

    )

    erfa_combined_residual = wrap_signed_deg(

        erfa_lon

        - jpl_j2000_lon

    )

    # How much longitude shift does each transformation apply?

    production_frame_shift = wrap_signed_deg(

        production_lon

        - raw_lon

    )

    erfa_frame_shift = wrap_signed_deg(

        erfa_lon

        - raw_lon

    )

    # Three-dimensional versions of the frame comparison.

    frame_angular_disagreement = angle_between_deg(

        production,

        erfa_transformed,

    )

    production_angular_error = angle_between_deg(

        production,

        jpl_j2000,

    )

    erfa_angular_error = angle_between_deg(

        erfa_transformed,

        jpl_j2000,

    )

    model_angular_error = angle_between_deg(

        raw_compact,

        jpl_date,

    )

    adopted_offset_seconds = (

        jd_tdb

        - jd_civil

    ) * 86400.0

    print()

    print("=" * 78)

    print(label)

    print("=" * 78)

    print(

        f"  reference civil epoch:      "

        f"{civil_text}"

    )

    print(

        f"  JD civil input:             "

        f"{jd_civil:.12f}"

    )

    print(

        f"  production dynamical JD:    "

        f"{jd_tdb:.12f}"

    )

    print(

        f"  adopted time offset:        "

        f"{adopted_offset_seconds:+.6f} s"

    )

    print()

    print("  VECTORS")

    print_vector(

        "RAW compact/date:",

        raw_compact,

    )

    print_vector(

        "JPL/date via ERFA:",

        jpl_date,

    )

    print_vector(

        "PRODUCTION/J2000:",

        production,

    )

    print_vector(

        "ERFA/J2000:",

        erfa_transformed,

    )

    print_vector(

        "JPL/J2000:",

        jpl_j2000,

    )

    print()

    print("  LONGITUDES")

    print(

        f"  RAW compact/date:           "

        f"{raw_lon:.9f} deg"

    )

    print(

        f"  JPL/date via ERFA:          "

        f"{jpl_date_lon:.9f} deg"

    )

    print(

        f"  PRODUCTION/J2000:           "

        f"{production_lon:.9f} deg"

    )

    print(

        f"  ERFA/J2000:                 "

        f"{erfa_lon:.9f} deg"

    )

    print(

        f"  JPL/J2000:                  "

        f"{jpl_j2000_lon:.9f} deg"

    )

    print()

    print("  PROSECUTION EVIDENCE")

    print(

        f"  MODEL-ONLY residual:        "

        f"{model_only_residual:+.9f} deg"

    )

    print(

        f"  FRAME disagreement:         "

        f"{frame_disagreement:+.9f} deg"

    )

    print(

        f"  PRODUCTION residual:        "

        f"{production_residual:+.9f} deg"

    )

    print(

        f"  ERFA combined residual:     "

        f"{erfa_combined_residual:+.9f} deg"

    )

    print()

    print("  FRAME SHIFTS")

    print(

        f"  production frame shift:     "

        f"{production_frame_shift:+.9f} deg"

    )

    print(

        f"  ERFA frame shift:           "

        f"{erfa_frame_shift:+.9f} deg"

    )

    print(

        f"  shift disagreement:         "

        f"{frame_disagreement:+.9f} deg"

    )

    print()

    print("  THREE-DIMENSIONAL CHECKS")

    print(

        f"  model-only angular error:   "

        f"{model_angular_error:.9f} deg"

    )

    print(

        f"  frame angular disagreement: "

        f"{frame_angular_disagreement:.9f} deg"

    )

    print(

        f"  production angular error:   "

        f"{production_angular_error:.9f} deg"

    )

    print(

        f"  ERFA angular error:         "

        f"{erfa_angular_error:.9f} deg"

    )

    return {

        "model_only_residual_deg":

            model_only_residual,

        "frame_disagreement_deg":

            frame_disagreement,

        "production_residual_deg":

            production_residual,

        "erfa_combined_residual_deg":

            erfa_combined_residual,

        "production_frame_shift_deg":

            production_frame_shift,

        "erfa_frame_shift_deg":

            erfa_frame_shift,

        "model_angular_error_deg":

            model_angular_error,

        "frame_angular_disagreement_deg":

            frame_angular_disagreement,

        "production_angular_error_deg":

            production_angular_error,

        "erfa_angular_error_deg":

            erfa_angular_error,

    }

# ---------------------------------------------------------------------------

# Summary helpers

# ---------------------------------------------------------------------------

def mean(

    values: list[float],

) -> float:

    """

    Arithmetic mean.

    """

    if not values:

        return float("nan")

    return sum(values) / len(values)

def mean_abs(

    values: list[float],

) -> float:

    """

    Mean absolute value.

    """

    if not values:

        return float("nan")

    return (

        sum(

            abs(value)

            for value in values

        )

        / len(values)

    )

def print_summary(

    results: list[

        tuple[

            str,

            dict[str, float],

        ]

    ],

) -> None:

    """

    Print compact cross-epoch prosecution summary.

    """

    print()

    print()

    print("=" * 78)

    print("PROSECUTION SUMMARY")

    print("=" * 78)

    print()

    print(

        f"{'epoch':<18}"

        f"{'model-only':>16}"

        f"{'frame':>16}"

        f"{'production':>16}"

    )

    print(

        f"{'':<18}"

        f"{'(deg)':>16}"

        f"{'(deg)':>16}"

        f"{'(deg)':>16}"

    )

    print("-" * 66)

    for label, result in results:

        print(

            f"{label:<18}"

            f"{result['model_only_residual_deg']:>+16.9f}"

            f"{result['frame_disagreement_deg']:>+16.9f}"

            f"{result['production_residual_deg']:>+16.9f}"

        )

    model_values = [

        result["model_only_residual_deg"]

        for _, result in results

    ]

    frame_values = [

        result["frame_disagreement_deg"]

        for _, result in results

    ]

    production_values = [

        result["production_residual_deg"]

        for _, result in results

    ]

    print()

    print("ALL-EPOCH STATISTICS")

    print(

        f"  mean model-only residual:       "

        f"{mean(model_values):+.9f} deg"

    )

    print(

        f"  mean |model-only residual|:     "

        f"{mean_abs(model_values):.9f} deg"

    )

    print(

        f"  mean frame disagreement:        "

        f"{mean(frame_values):+.9f} deg"

    )

    print(

        f"  mean |frame disagreement|:      "

        f"{mean_abs(frame_values):.9f} deg"

    )

    print(

        f"  mean production residual:       "

        f"{mean(production_values):+.9f} deg"

    )

    print(

        f"  mean |production residual|:     "

        f"{mean_abs(production_values):.9f} deg"

    )

    before = [

        result

        for label, result in results

        if label in {

            "1919 eclipse",

            "1963 eclipse",

            "1991 eclipse",

        }

    ]

    after = [

        result

        for label, result in results

        if label in {

            "2017 eclipse",

            "2024 eclipse",

        }

    ]

    print()

    print("BEFORE / AFTER J2000")

    if before:

        print(

            f"  model mean before J2000:        "

            f"{mean([r['model_only_residual_deg'] for r in before]):+.9f} deg"

        )

        print(

            f"  frame mean before J2000:        "

            f"{mean([r['frame_disagreement_deg'] for r in before]):+.9f} deg"

        )

        print(

            f"  production mean before J2000:   "

            f"{mean([r['production_residual_deg'] for r in before]):+.9f} deg"

        )

    if after:

        print(

            f"  model mean after J2000:         "

            f"{mean([r['model_only_residual_deg'] for r in after]):+.9f} deg"

        )

        print(

            f"  frame mean after J2000:         "

            f"{mean([r['frame_disagreement_deg'] for r in after]):+.9f} deg"

        )

        print(

            f"  production mean after J2000:    "

            f"{mean([r['production_residual_deg'] for r in after]):+.9f} deg"

        )

    print()

    print("INTERPRETATION KEY")

    print()

    print(

        "  MODEL-ONLY residual large"

        "  -> compact solar model contributes error."

    )

    print(

        "  FRAME disagreement large"

        "   -> production frame conversion contributes error."

    )

    print(

        "  Both large"

        "                  -> both suspects are guilty."

    )

    print(

        "  Residual remains after both"

        " -> continue searching for another culprit."

    )

# ---------------------------------------------------------------------------

# Main

# ---------------------------------------------------------------------------

def main() -> int:

    """

    Run the complete prosecution lineup.

    """

    print(

        "STAR ALMANACK SUN / FRAME PROSECUTION LINEUP"

    )

    print(

        "=" * 78

    )

    print()

    print(

        "Independent authorities:"

    )

    print(

        "  solar position: JPL Horizons"

    )

    print(

        "  frame conversion: ERFA / IAU 2006"

    )

    print()

    print(

        "This diagnostic does NOT modify production eclipse geometry."

    )

    results: list[

        tuple[

            str,

            dict[str, float],

        ]

    ] = []

    try:

        for label, civil_text in TEST_EPOCHS:

            result = run_case(

                label,

                civil_text,

            )

            results.append(

                (

                    label,

                    result,

                )

            )

    except Exception as exc:

        print()

        print("=" * 78)

        print(

            "SUN / FRAME LINEUP SKIPPED / UNAVAILABLE"

        )

        print("=" * 78)

        print(

            f"{type(exc).__name__}: {exc}"

        )

        print()

        print(

            "This diagnostic depends on PyERFA and live JPL Horizons access."

        )

        print(

            "Diagnostic unavailability does not constitute a Star Almanack"

        )

        print(

            "validation failure."

        )

        return 0

    print_summary(

        results

    )

    print()

    print(

        "SUN / FRAME PROSECUTION LINEUP COMPLETE"

    )

    return 0

if __name__ == "__main__":

    raise SystemExit(

        main()

    )