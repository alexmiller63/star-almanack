#!/usr/bin/env python3
"""Calculate zodiac ingresses and lunar phases from Star Almanack engines."""
from __future__ import annotations

import argparse
import datetime as dt
import json
import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
ELP_DIR = ROOT / "star-almanack-elp82b"
sys.path.insert(0, str(ELP_DIR))

import eclipse_engine
import lunar_elp

UTC = dt.timezone.utc
DEG = math.pi / 180.0
SIGNS = [
    ("♈", "Aries"), ("♉", "Taurus"), ("♊", "Gemini"), ("♋", "Cancer"),
    ("♌", "Leo"), ("♍", "Virgo"), ("♎", "Libra"), ("♏", "Scorpio"),
    ("♐", "Sagittarius"), ("♑", "Capricorn"), ("♒", "Aquarius"), ("♓", "Pisces"),
]
PHASES = [
    (0.0, "🌑", "New Moon"),
    (90.0, "🌓", "First Quarter"),
    (180.0, "🌕", "Full Moon"),
    (270.0, "🌗", "Last Quarter"),
]


def jd_utc(moment: dt.datetime) -> float:
    day_fraction = (
        moment.hour + (moment.minute + (moment.second + moment.microsecond / 1e6) / 60.0) / 60.0
    ) / 24.0
    return eclipse_engine.gregorian_to_jd(moment.year, moment.month, moment.day, day_fraction)


def datetime_utc(jd: float) -> dt.datetime:
    unix = (jd - 2440587.5) * 86400.0
    return dt.datetime.fromtimestamp(unix, UTC)


def sun_longitude(jd_tdb: float) -> float:
    d = jd_tdb - 2451543.5
    perihelion = (282.9404 + 0.0000470935 * d) * DEG
    eccentricity = 0.016709 - 0.000000001151 * d
    mean_anomaly = (356.0470 + 0.9856002585 * d) * DEG
    mean_anomaly %= 2.0 * math.pi
    eccentric_anomaly = mean_anomaly
    for _ in range(12):
        eccentric_anomaly -= (
            eccentric_anomaly - eccentricity * math.sin(eccentric_anomaly) - mean_anomaly
        ) / (1.0 - eccentricity * math.cos(eccentric_anomaly))
    x = math.cos(eccentric_anomaly) - eccentricity
    y = math.sqrt(1.0 - eccentricity * eccentricity) * math.sin(eccentric_anomaly)
    return (math.atan2(y, x) + perihelion) % (2.0 * math.pi)


def angular_error(angle: float, target: float) -> float:
    return math.atan2(math.sin(angle - target), math.cos(angle - target))


def bisect_crossing(function, low: float, high: float) -> float:
    f_low = function(low)
    f_high = function(high)
    if not (f_low <= 0.0 <= f_high or f_high <= 0.0 <= f_low):
        raise ValueError("Root is not bracketed")
    for _ in range(60):
        middle = (low + high) / 2.0
        f_middle = function(middle)
        if abs(high - low) * 86400.0 < 0.05:
            return middle
        if (f_low <= 0.0 <= f_middle) or (f_middle <= 0.0 <= f_low):
            high, f_high = middle, f_middle
        else:
            low, f_low = middle, f_middle
    return (low + high) / 2.0


def crossings(function, start: float, end: float, step: float) -> list[float]:
    roots = []
    left = start
    f_left = function(left)
    while left < end:
        right = min(end, left + step)
        f_right = function(right)
        if f_left == 0.0 or (
            f_left * f_right < 0.0 and abs(f_left) < math.pi / 2 and abs(f_right) < math.pi / 2
        ):
            root = left if f_left == 0.0 else bisect_crossing(function, left, right)
            if not roots or abs(root - roots[-1]) > 0.25:
                roots.append(root)
        left, f_left = right, f_right
    return roots


def calculate(year: int, normalized: dict) -> dict:
    start_utc = dt.datetime(year, 1, 1, tzinfo=UTC)
    end_utc = dt.datetime(year + 1, 1, 1, tzinfo=UTC)
    start = jd_utc(start_utc)
    end = jd_utc(end_utc)

    ingresses = []
    for index, (symbol, name) in enumerate(SIGNS):
        target = index * 30.0 * DEG
        function = lambda jd, target=target: angular_error(
            sun_longitude(eclipse_engine.utc_to_tdb_approx(jd)), target
        )
        for root in crossings(function, start, end, 2.0):
            moment = datetime_utc(root)
            ingresses.append({
                "symbol": symbol,
                "name": name,
                "longitude_degrees": index * 30,
                "utc": moment.strftime("%Y-%m-%dT%H:%M:%SZ"),
            })

    phases = []
    def moon_longitude(jd: float) -> float:
        tdb = eclipse_engine.utc_to_tdb_approx(jd)
        return lunar_elp.evaluate(normalized, tdb).spherical.longitude_rad % (2.0 * math.pi)

    for target_degrees, symbol, name in PHASES:
        target = target_degrees * DEG
        function = lambda jd, target=target: angular_error(
            moon_longitude(jd) - sun_longitude(eclipse_engine.utc_to_tdb_approx(jd)), target
        )
        for root in crossings(function, start, end, 0.75):
            moment = datetime_utc(root)
            phases.append({
                "symbol": symbol,
                "name": name,
                "elongation_degrees": int(target_degrees),
                "utc": moment.strftime("%Y-%m-%dT%H:%M:%SZ"),
            })

    ingresses.sort(key=lambda event: event["utc"])
    phases.sort(key=lambda event: event["utc"])
    if len(ingresses) != 12:
        raise RuntimeError(f"Expected 12 ingresses for {year}, found {len(ingresses)}")
    if not 48 <= len(phases) <= 51:
        raise RuntimeError(f"Unexpected lunar phase count for {year}: {len(phases)}")
    return {
        "schema": "star-almanack.calendar-events.v1",
        "year": year,
        "engines": {
            "solar": "Star Almanack compact apparent geocentric Sun",
            "lunar": "ELP2000-82B, all normalized terms",
        },
        "zodiac_ingresses": ingresses,
        "lunar_phases": phases,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("year", type=int)
    parser.add_argument(
        "--manifest",
        type=Path,
        default=ELP_DIR / "elp82b-manifest.json",
    )
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    normalized = lunar_elp.load_normalized(args.manifest)
    payload = calculate(args.year, normalized)
    output = args.output or ROOT / f"calendar-events-{args.year}.json"
    output.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"Wrote {len(payload['zodiac_ingresses'])} ingresses and {len(payload['lunar_phases'])} phases to {output}")


if __name__ == "__main__":
    main()
