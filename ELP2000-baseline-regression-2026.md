# ELP2000 Baseline Regression — 2026

This file preserves test cases for improving the Star Almanack lunar
ephemeris while retaining the recovered compact lunar model as a baseline.

The purpose is incremental regression testing: add one verified case,
make the improved lunar evaluator reproduce or improve upon it, then add
additional cases.

## Case 1 — 2026-W01

Sampling time:

**2025-12-29 00:00 UTC**

Preserved Moon position from `ephem.md`:

**♈ 22°56′**

Equivalent geocentric tropical ecliptic longitude:

**22.933333°**

Recovered compact lunar engine:

**22.909695°**

Residual:

**−0.023638°**

or approximately:

**−1.42 arcminutes**

Result:

**1/1 BASELINE REPRODUCED**

This case establishes the first regression anchor. Future lunar-model
improvements should be compared against this preserved result rather than
silently replacing the baseline.
