# Star Almanack Notes

Continuous project log. Append new entries; do not rewrite prior entries except to correct a documented factual error.

## 2026-09-02 — Expanded 2026 Almanack and Bayer audit

The expanded 2026 Star Almanack now covers the complete ISO 2026 week-year, W01 through W53. ISO 2026 extends beyond the Gregorian year boundary into January 2027; this matters for fixed-object placement. In particular, β Reticuli has a computed best-visibility instant on 2026-12-31 20:05 UTC that rounds to 2027-01-01, which is still ISO 2026-W53-5. The builder was corrected to treat the Almanack as an ISO week-year rather than restricting event injection to Gregorian dates whose year field is 2026.

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

## 2026-09-02 — Authoritative gap audit, first pass

The first authoritative cross-check confirms that the current 159-row source catalog is missing genuine Bayer-designated systems. These are not inferred from constellation naming conventions; they are supported by SIMBAD/CDS identifiers or catalog-backed coordinate records.

Confirmed omissions to add:

- α¹ and α² Canum Venaticorum. SIMBAD explicitly identifies α¹ CVn (HD 112412) and α² CVn / Cor Caroli (HD 112413).
- α¹ and α² Capricorni. SIMBAD recognizes the α Capricorni pair and specifically resolves α² Cap; catalog-backed astrometry separately identifies α¹ Cap.
- α Centauri. SIMBAD explicitly recognizes α Cen A and α Cen B; the Bayer identity belongs to the Alpha Centauri system rather than to a missing modern constellation letter.
- α¹ and α² Crucis. Catalog-backed records explicitly identify Alpha1 Crucis and Alpha2 Crucis; α¹ is Acrux.
- α¹ and α² Herculis. SIMBAD identifies α Her as a multiple system and the Washington Double Star Catalog resolves Alpha1 Herculis and Alpha2 Herculis.
- α¹ and α² Librae. Standard catalog records explicitly identify both numbered Bayer components.
- β¹ and β² Sagittarii. SIMBAD-backed records explicitly identify β¹ Sgr and β² Sgr.
- β¹ and β² Scorpii. Standard catalog records explicitly identify both numbered Bayer components.
- β¹ and β² Tucanae. Standard catalog records explicitly identify both numbered Bayer components.

These entries should be added as numbered Bayer entries where numbering is part of the designation. α Centauri should not be artificially converted into α¹/α²; A and B are stellar components of the α Cen system, not numbered Bayer designations.

Legitimate gaps remain legitimate and should stay absent unless contrary catalog evidence is found. The audit therefore distinguishes “no α/β exists in the modern Bayer scheme” from “our source extraction missed an existing Bayer designation.”

Next implementation step: add a small auditable supplemental Bayer source for the confirmed omissions, carrying source provenance and coordinates, then feed that supplement through the same 2026 best-visibility computation and completeness checks instead of editing generated output by hand.

## 2026-09-02 — Bright-star variability and star-note policy

For a future Bright 50 catalog, rank stars by a reproducible representative maximum apparent visual brightness rather than by a one-off exceptional historical observation. This keeps the ranking stable enough to reproduce while still respecting ordinary variability.

Variable and eruptive behavior belongs in the individual star notes. Add a standard field, **Outbursts and exceptional brightness**, whenever applicable. Use it for unusual maxima or minima, eclipses, eruptions, major dimming events, and historically noteworthy departures from the star's representative range. Examples include Betelgeuse's 2019–2020 Great Dimming, Algol's regular eclipses, Mira's unusually bright maxima, and similar exceptional behavior in other variable stars.

The ranking and the notes therefore serve different purposes: the Bright 50 ranking uses a representative maximum, while the star note preserves exceptional observations and outbursts without allowing a rare event to destabilize the catalog order.
