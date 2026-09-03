# Star Almanack Source of Truth

This file documents which repository files are authoritative and which files are generated. Generated weekly pages and rendered HTML are never the source of truth.

## Stellar data

### Bayer alpha/beta layer

Authoritative catalog data:

- `expanded-bayer-stars.csv` — stellar identity, Bayer designation, proper name where available, constellation abbreviation, right ascension, declination, magnitude, and catalog identifiers.
- `expanded-bayer-visibility-2026.csv` — generated 2026 best-visibility placement for the Bayer catalog.

Builders:

- `build_bayer_catalog.py`
- `compute_bayer_visibility_2026.py`

### Bright-star layer

Authoritative catalog data:

- `bright-stars-2mag.csv` — reconciled naked-eye stellar-system catalog.
- `bright-star-visibility-2026.csv` — generated 2026 best-visibility placement. This preserves proper name, Bayer code, constellation abbreviation, right ascension, declination, decimal V magnitude, source/provenance, catalog identifiers, best date, and ISO week date.
- `bright-variable-reconciliation.csv` — authoritative variability enrichment for bright stars where the GCVS reconciliation identifies a variable star.

Builders/audits:

- `build_bright_star_catalog.py`
- `compute_bright_star_visibility_2026.py`
- `reconcile_bright_variables.py`
- `audit_gcvs_bright_boundary.py`

### Special stars

Authoritative catalog data:

- `special-star-catalog.csv`
- `special-stars.yaml` where editorial material beyond the compact catalog is required.

Generated 2026 placement:

- `special-star-visibility-2026.csv`

## Messier objects

Authoritative/generated fixed-object data are carried in the repository Messier source and `messier-visibility-2026.csv`; the latter supplies the 2026 best-visibility placement used by the expanded Almanack builder.

## Almanack integration

`build_expanded_almanack.py` combines the calendar and fixed-object catalogs into `almanack-expanded.md`.

`enrich_stellar_entries.py` is the mandatory stellar presentation pass. It reads the Bayer visibility catalog, bright-star visibility catalog, and reconciled bright-variable data and normalizes catalog-backed stellar entries so the published Almanack does not discard Bayer designation, decimal magnitude, known-variable status, latitude zone, or observing season.

`publish_weekly_pages.py` converts the integrated and enriched Almanack into the weekly pages under `site/2026/W01/` through `site/2026/W53/`.

Therefore:

**Catalog CSV/YAML → visibility computation → `build_expanded_almanack.py` → `enrich_stellar_entries.py` → `almanack-expanded.md` → `publish_weekly_pages.py` → weekly HTML.**

The weekly HTML is output, not source.

## Required stellar display fields

Every observer-facing stellar entry SHALL preserve and display, when applicable:

- proper name;
- Bayer designation, using the Greek letter rather than the three-letter Latin code;
- constellation via the Bayer constellation abbreviation;
- decimal visual magnitude, not merely a whole-number magnitude class;
- variable-star status when the reconciled variable-star source identifies the star as variable;
- observing season;
- latitude/orientation zone derived consistently from declination;
- best-visibility civil date and ISO week placement.

The compact canonical calendar form is:

`Proper name (Bayer) — Vmag — variable [when catalogued] — Latitude-zone Season`

Latitude zone is derived from declination using the tropical boundaries:

- declination > +23.44°: Northern;
- −23.44° through +23.44°: Tropical;
- declination < −23.44°: Southern.

Season is derived from the best-visibility civil date using Winter, Spring, Summer, and Autumn.

A presentation layer MUST NOT discard authoritative catalog fields merely to shorten an entry. Compact presentation may abbreviate wording, but it must preserve the required information above.

## Example: Enif

The authoritative bright-star visibility row for Enif identifies:

- Bayer code: `Eps` → `ε`;
- constellation: `Peg` (Pegasus);
- declination: approximately `+9.875°`;
- decimal V magnitude: `2.38`;
- best date: `2026-10-05` (`2026-W41-1`).

The variable-star reconciliation identifies `eps Peg` as variable. The canonical observer-facing entry is therefore:

`Enif (ε Peg) — V2.38 — variable — Tropical Autumn`

## Maintenance rule

When a stellar entry is wrong or incomplete, correct the appropriate catalog, visibility computation, or enrichment source and regenerate. Do not hand-patch a single weekly HTML page except while diagnosing a rendering problem.
