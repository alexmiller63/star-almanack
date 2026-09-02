# Star Almanack Notes

Continuous project log. Append new entries; do not rewrite prior entries except to correct a documented factual error.

## 2026-09-02 — Expanded 2026 Almanack and Bayer audit

The expanded 2026 Almanack now covers the complete ISO 2026 week-year, W01 through W53. ISO 2026 extends beyond the Gregorian year boundary into January 2027; this matters for fixed-object placement. In particular, β Reticuli has a computed best-visibility instant on 2026-12-31 20:05 UTC that rounds to 2027-01-01, which is still ISO 2026-W53-5. The builder was corrected to treat the Almanack as an ISO week-year rather than restricting event injection to Gregorian dates whose year field is 2026.

The fixed-object integration target is all 110 Messier objects plus all catalogued α and β Bayer-designated stars, with separately numbered components retained when appropriate. The successful expanded build currently contains 110 Messier objects and 159 α/β Bayer rows distributed onto the 53 weekly calendar pages by the preserved best-visibility rule.

Bayer completeness is not defined as “every constellation must have both α and β.” Historical Bayer lettering, later constellation boundaries, and the breakup of Argo Navis create legitimate absences. Therefore, missing α/β entries must be audited rather than blindly filled.

Current source-catalog gaps found in the 159-row α/β catalog:

- No α entry: Canes Venatici, Capricornus, Centaurus, Crux, Hercules, Leo Minor, Libra, Norma, Puppis, Vela.
- No β entry: Antlia, Lynx, Norma, Puppis, Sagittarius, Scorpius, Telescopium, Tucana, Vela, Vulpecula.

Working justification rule for future additions:

1. Add an α or β entry only when the Bayer designation is explicitly supported by an authoritative astronomical source, preferably SIMBAD/CDS or another primary/standard catalog.
2. Preserve legitimate historical absences and document why they are absent.
3. Retain separately designated numbered components such as α¹/α² or β¹/β² when the designation is genuinely separate rather than silently collapsing them.
4. Keep the Bayer designation as the stable identity for completeness checking; proper names are supplementary.
5. Do not weaken completeness checks to make a build pass. Resolve catalog, ISO-year, or parsing issues directly.

Initial audit indicates that several current gaps are real catalog omissions rather than legitimate absences. Candidates requiring authoritative confirmation and then addition include α Canum Venaticorum / Cor Caroli components, α Capricorni components, α Centauri, α Crucis components, α Herculis components, α Librae components, β Sagittarii components, β Scorpii components, and β Tucanae components. Conversely, some constellations legitimately lack a modern α or β Bayer designation; examples already identified include Leo Minor, Norma, Puppis, and Vela for α, with several β absences tied to historical boundary changes or incomplete Bayer lettering.

The standard going forward is defensibility and reproducibility: every added Bayer entry should have a traceable astronomical justification, and every intentional gap should be explainable.
