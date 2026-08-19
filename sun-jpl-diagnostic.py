#!/usr/bin/env python3

"""

Star Almanack — compact-Sun versus JPL Horizons diagnostic.

Purpose

-------

Compare the Star Almanack compact solar model with an independent,

high-precision JPL Horizons solar ephemeris.

This program is DIAGNOSTIC ONLY.

It does not modify the eclipse calculation, does not supply data to

eclipse_engine.py, and does not affect the Star Almanack validation

PASS/FAIL result.

Why this diagnostic exists

--------------------------

The Star Almanack eclipse engine currently computes the Sun with a compact

low-precision solar model and transforms the resulting vector into the

mean J2000 ecliptic frame used by the ELP2000-82B lunar evaluator.

Eclipse validation has revealed an epoch-dependent timing residual:

    before J2000:

        calculated greatest-eclipse times tend to be early

    after J2000:

        calculated greatest-eclipse times tend to be late

A transformed-versus-raw Sun experiment showed that bypassing the Sun

frame transformation reduces the timing residual substantially.  However,

that experiment deliberately mixes coordinate frames and therefore cannot

by itself establish that the transformation is wrong.

The next independent question is:

    How accurately does the compact Sun model itself reproduce the

    geocentric Sun position given by JPL Horizons?

This diagnostic answers that question directly.

Reference geometry

------------------

JPL Horizons is asked for a geometric geocentric Sun vector:

    target:

        Sun

    center:

        Earth center

    reference system:

        ICRF / J2000

    reference plane:

        ecliptic

The resulting vector can therefore be compared directly with

eclipse_engine.sun_vector_j2000().

Test epochs

-----------

The epochs deliberately span both sides of J2000:

    1919 eclipse era

    1991 eclipse era

    J2000

    2017 eclipse era

    2024 eclipse era

The diagnostic prints:

    Star Almanack vector

    JPL Horizons vector

    signed ecliptic-longitude residual

    total angular separation

    radial-distance residual

The signed longitude residual is:

    Star Almanack longitude - JPL longitude

normalized to the interval:

    -180 degrees through +180 degrees

This sign is especially important because we are looking for an

epoch-dependent error that may reverse direction around J2000.

Network behavior

----------------

Unlike the permanent frozen regression tests, this diagnostic intentionally

contacts JPL Horizons over the network.

A temporary network or Horizons failure must NOT make the Star Almanack

validation fail.  Such a failure is reported as SKIPPED / UNAVAILABLE and

the diagnostic exits successfully.

Published/reference data remain validation targets only.  The production

eclipse engine never reads JPL Horizons data.

"""

from __future__ import annotations

import json

import math

import re

from urllib.parse import urlencode

from urllib.request import Request, urlopen

import eclipse_engine

HORIZONS_API = "https://ssd.jpl.nasa.gov/api/horizons.api"

# Representative epochs.  Eclipse dates use the published/reference

# greatest-eclipse times already used by the Star Almanack validation work.

#

# J2000 is included because the production date-to-J2000 transformation

# should approach zero there.

TEST_EPOCHS = [

    (

        "1919 eclipse",

        "1919-05-29T13:08:34Z",

    ),

    (

        "1991 eclipse",

        "1991-07-11T19:07:01Z",

    ),

    (

        "J2000",

        "2000-01-01T12:00:00Z",

    ),

    (

        "2017 eclipse",

        "2017-08-21T18:26:40Z",

    ),

    (

        "2024 eclipse",

        "2024-04-08T18:17:20Z",

    ),

]

def wrap_signed_deg(angle: float) -> float:

    """

    Normalize an angle to [-180, +180) degrees.

    """

    return (angle + 180.0) % 360.0 - 180.0

def vector_longitude_deg(v: eclipse_engine.Vec3) -> float:

    """

    Ecliptic longitude of a rectangular vector, degrees.

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

    cosine = max(-1.0, min(1.0, cosine))

    return math.degrees(math.acos(cosine))

def iso_z_to_jd(text: str) -> float:

    """

    Convert the UTC timestamps used by this diagnostic to Julian Date.

    eclipse_engine already owns the calendar-to-JD implementation used by

    the Star Almanack validation layer, so this diagnostic deliberately

    reuses it rather than introducing another calendar implementation.

    """

    date_part, time_part = text.rstrip("Z").split("T")

    year, month, day = (

        int(part)

        for part in date_part.split("-")

    )

    hour, minute, second = (

        int(part)

        for part in time_part.split(":")

    )

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

def approximate_tdb_jd(

    utc_text: str,

) -> float:

    """

    Produce the same approximate TT/TDB argument used by the eclipse engine.

    Horizons receives the requested epoch independently.  The compact Sun

    calculation, however, should be evaluated using the same time convention

    as production eclipse geometry.

    For this diagnostic, TT is used as the practical approximation to TDB,

    matching the existing eclipse-engine design.

    """

    jd_utc = iso_z_to_jd(utc_text)

    year = int(

        utc_text[0:4]

    )

    delta_t = eclipse_engine.delta_t_seconds(

        float(year)

    )

    return jd_utc + delta_t / 86400.0

def horizons_request(

    jd: float,

) -> str:

    """

    Ask JPL Horizons for one geometric geocentric Sun vector.

    COMMAND 10:

        Sun

    CENTER 500@399:

        Earth center

    EPHEM_TYPE VECTORS:

        geometric Cartesian state vector

    REF_SYSTEM ICRF:

        J2000-compatible inertial reference system

    REF_PLANE ECLIPTIC:

        ecliptic reference plane

    TLIST:

        request exactly one epoch

    VEC_TABLE 2:

        position and velocity vector output

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

        "TLIST": f"'{jd:.12f}'",

    }

    url = (

        HORIZONS_API

        + "?"

        + urlencode(params)

    )

    request = Request(

        url,

        headers={

            "User-Agent": (

                "Star-Almanack-JPL-Diagnostic/1.0"

            )

        },

    )

    with urlopen(

        request,

        timeout=30,

    ) as response:

        raw = response.read().decode(

            "utf-8"

        )

    payload = json.loads(raw)

    if "result" not in payload:

        raise RuntimeError(

            "Horizons response did not contain a result field"

        )

    return payload["result"]

def parse_horizons_vector(

    text: str,

) -> eclipse_engine.Vec3:

    """

    Extract X, Y, Z from the Horizons vector block.

    Horizons' human-readable vector output contains a line of the form:

        X = ... Y = ... Z = ...

    Only material between $$SOE and $$EOE is considered, preventing header

    metadata from being mistaken for vector data.

    """

    if "$$SOE" not in text or "$$EOE" not in text:

        raise RuntimeError(

            "Horizons result did not contain an ephemeris data block"

        )

    block = text.split(

        "$$SOE",

        1,

    )[1].split(

        "$$EOE",

        1,

    )[0]

    pattern = re.compile(

        r"X\s*=\s*"

        r"([+-]?\d+(?:\.\d*)?(?:[Ee][+-]?\d+)?)"

        r"\s+Y\s*=\s*"

        r"([+-]?\d+(?:\.\d*)?(?:[Ee][+-]?\d+)?)"

        r"\s+Z\s*=\s*"

        r"([+-]?\d+(?:\.\d*)?(?:[Ee][+-]?\d+)?)"

    )

    match = pattern.search(block)

    if match is None:

        raise RuntimeError(

            "Could not parse X/Y/Z from Horizons vector output"

        )

    return eclipse_engine.Vec3(

        float(match.group(1)),

        float(match.group(2)),

        float(match.group(3)),

    )

def print_vector(

    label: str,

    vector: eclipse_engine.Vec3,

) -> None:

    print(

        f"  {label:<18} "

        f"x={vector.x:+.3f} km  "

        f"y={vector.y:+.3f} km  "

        f"z={vector.z:+.3f} km"

    )

def run_case(

    label: str,

    utc_text: str,

) -> dict[str, float]:

    """

    Run one Star Almanack versus Horizons comparison.

    """

    jd_utc = iso_z_to_jd(

        utc_text

    )

    jd_tdb_approx = approximate_tdb_jd(

        utc_text

    )

    star = eclipse_engine.sun_vector_j2000(

        jd_tdb_approx

    )

    horizons_text = horizons_request(

        jd_utc

    )

    jpl = parse_horizons_vector(

        horizons_text

    )

    star_lon = vector_longitude_deg(

        star

    )

    jpl_lon = vector_longitude_deg(

        jpl

    )

    longitude_residual = wrap_signed_deg(

        star_lon - jpl_lon

    )

    angular_error = angle_between_deg(

        star,

        jpl,

    )

    radial_error = (

        star.norm()

        - jpl.norm()

    )

    print()

    print(label)

    print(f"  UTC epoch:          {utc_text}")

    print(f"  JD UTC:             {jd_utc:.9f}")

    print(

        f"  JD TT/TDB approx:   "

        f"{jd_tdb_approx:.9f}"

    )

    print_vector(

        "Star Almanack:",

        star,

    )

    print_vector(

        "JPL Horizons:",

        jpl,

    )

    print(

        f"  Star longitude:     "

        f"{star_lon:.9f} deg"

    )

    print(

        f"  JPL longitude:      "

        f"{jpl_lon:.9f} deg"

    )

    print(

        f"  signed longitude "

        f"residual: {longitude_residual:+.9f} deg"

    )

    print(

        f"  angular separation: "

        f"{angular_error:.9f} deg"

    )

    print(

        f"  radial residual:    "

        f"{radial_error:+.3f} km"

    )

    return {

        "longitude_residual_deg":

            longitude_residual,

        "angular_error_deg":

            angular_error,

        "radial_error_km":

            radial_error,

    }

def main() -> int:

    print(

        "=== JPL HORIZONS / COMPACT SUN DIAGNOSTIC ==="

    )

    print()

    print(

        "INFORMATIONAL ONLY — "

        "this diagnostic cannot fail the "

        "Star Almanack validation."

    )

    print()

    print(

        "Signed longitude residual = "

        "Star Almanack - JPL Horizons."

    )

    print(

        "The principal question is whether the "

        "residual changes systematically with epoch."

    )

    results: list[

        tuple[

            str,

            str,

            dict[str, float],

        ]

    ] = []

    try:

        for label, utc_text in TEST_EPOCHS:

            result = run_case(

                label,

                utc_text,

            )

            results.append(

                (

                    label,

                    utc_text,

                    result,

                )

            )

    except Exception as exc:

        print()

        print(

            "JPL SUN DIAGNOSTIC: "

            "SKIPPED / UNAVAILABLE"

        )

        print(

            f"  {type(exc).__name__}: {exc}"

        )

        print()

        print(

            "This is an informational network "

            "diagnostic and does not affect PASS/FAIL."

        )

        return 0

    print()

    print(

        "=== SIGNED LONGITUDE RESIDUAL SUMMARY ==="

    )

    for label, utc_text, result in results:

        residual = result[

            "longitude_residual_deg"

        ]

        print(

            f"  {label:<16} "

            f"{utc_text:<21} "

            f"{residual:+.9f} deg"

        )

    before = [

        result["longitude_residual_deg"]

        for label, utc_text, result in results

        if utc_text < "2000-01-01T12:00:00Z"

    ]

    after = [

        result["longitude_residual_deg"]

        for label, utc_text, result in results

        if utc_text > "2000-01-01T12:00:00Z"

    ]

    if before and after:

        mean_before = sum(before) / len(

            before

        )

        mean_after = sum(after) / len(

            after

        )

        print()

        print(

            f"  mean before J2000: "

            f"{mean_before:+.9f} deg"

        )

        print(

            f"  mean after J2000:  "

            f"{mean_after:+.9f} deg"

        )

        if (

            mean_before < 0.0

            and mean_after > 0.0

        ) or (

            mean_before > 0.0

            and mean_after < 0.0

        ):

            print()

            print(

                "  OBSERVATION: mean signed Sun "

                "longitude residual reverses sign "

                "across J2000."

            )

        else:

            print()

            print(

                "  OBSERVATION: mean signed Sun "

                "longitude residual does NOT "

                "reverse sign across J2000."

            )

    print()

    print(

        "JPL SUN DIAGNOSTIC: COMPLETE "

        "(informational only)"

    )

    return 0

if __name__ == "__main__":

    raise SystemExit(main())
    
    