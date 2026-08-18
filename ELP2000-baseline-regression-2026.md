# Star Almanack — Lunar Ephemeris Upgrade Regression

## Purpose

Before replacing the recovered compact Moon model with ELP2000-82B, quantify the error of the compact model at the 4 independently calculated 2026 eclipse maxima.

The compact engine remains the regression baseline. An independent local lunar ephemeris was used only as a validation reference; its coordinates are not imported into the Star Almanack calculation.

## Results

| Eclipse maximum (UTC) | Δ longitude | Δ latitude | Δ distance |
|---|---:|---:|---:|
| 2026-02-17 12:14:49 | +0.257′ | +0.864′ | +2,044 km |
| 2026-03-03 11:31:48 | −0.938′ | −0.527′ | +2,918 km |
| 2026-08-12 17:48:45 | −0.560′ | +0.502′ | +4,517 km |
| 2026-08-28 04:10:20 | −1.035′ | +0.029′ | +1,689 km |

Residuals are compact model minus validation reference. Longitude and latitude are geocentric ecliptic coordinates of date.

## Interpretation

The angular position of the compact Moon is already quite good at the eclipse epochs: all 4 longitude residuals are about 1 arcminute or less, and all 4 latitude residuals are below 1 arcminute.

The conspicuous weakness is **lunar distance**. The compact model places the Moon too far away by roughly 1,700–4,500 km in these 4 cases. That matters strongly for eclipse work because lunar distance controls both the Moon's apparent semidiameter and its horizontal parallax. Those quantities enter directly into shadow-cone geometry, eclipse magnitude, and contact times.

This explains why the compact engine can correctly identify and classify the 2026 eclipses while still leaving minute-scale errors in detailed eclipse circumstances.

## ELP2000-82B upgrade target

The ELP2000-82B layer should improve all 3 lunar coordinates, but the first critical acceptance test is distance. At each eclipse epoch we will compare:

1. geocentric ecliptic longitude,
2. geocentric ecliptic latitude,
3. geocentric lunar distance,
4. resulting lunar semidiameter and parallax,
5. recalculated eclipse maximum and contacts.

The independent reference remains validation only, never an input to the Almanack's predictions.
