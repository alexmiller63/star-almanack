# IAU Constellation Boundary Source Snapshot

## Policy

**Download once, reuse many.**

The Star Almanack shall acquire the authoritative IAU constellation-boundary source files once, preserve that acquisition as source data, and use the preserved local snapshot for all downstream geometry, database imports, validation, and generation. Normal generators shall not repeatedly download the IAU source.

This acquisition layer is intentionally auditable. A source snapshot must retain enough provenance and integrity information for an independent audit to verify exactly what was acquired and to reproduce or compare the acquisition later.

## Authoritative source

IAU archive constellation page:

`https://iauarchive.eso.org/public/themes/constellations/`

The machine-readable boundary TXT resources follow this deterministic pattern:

`https://iauarchive.eso.org/static/public/constellations/txt/{iau_abbreviation}.txt`

where `{iau_abbreviation}` is the lowercase three-letter IAU constellation abbreviation.

Example — Andromeda (`And`):

`https://iauarchive.eso.org/static/public/constellations/txt/and.txt`

The deterministic direct-download resource is preferred over scraping the presentation page.

## Snapshot requirements

For each acquired source file, preserve or derive an audit manifest containing at least:

- IAU constellation abbreviation;
- exact source URL;
- local snapshot path;
- byte size;
- SHA-256 checksum;
- acquisition timestamp in UTC.

The acquisition process must fail rather than silently continue when an expected source is unavailable, empty, duplicated, or otherwise invalid.

## Completeness validation

Completeness must be established from the authoritative IAU source inventory, not from an assumed numeric file count. The acquisition step shall validate that every expected constellation boundary resource is present exactly once and that no unexpected resource is silently accepted.

The official constellation count and the number of source resources are separate assertions and shall be audited separately.

## Reuse rule

After a snapshot has passed completeness and integrity validation:

1. database/import tooling reads the preserved local snapshot;
2. geometry code reads database/import products or the local snapshot as appropriate;
3. Almanack generators do not contact the IAU archive during normal builds;
4. refreshing the authoritative snapshot is a deliberate acquisition operation, never an incidental side effect of generation.

## Audit invariants

An independent audit should be able to establish:

- provenance: every local source maps to an exact authoritative URL;
- completeness: the expected authoritative inventory is represented exactly once;
- integrity: recorded SHA-256 values match the preserved bytes;
- reproducibility: rebuilding from an unchanged snapshot does not require network access;
- idempotence: repeated downstream processing of the same snapshot produces the same canonical result.
