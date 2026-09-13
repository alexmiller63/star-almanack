# Fixed-Object Data Model Notes

## Fundamental split

Star Almanack fixed-object data is divided into two layers: **timeless data** and **timed data**.

### Timeless data

Timeless data describes the fixed object itself and must not depend on a calendar year.

Examples include:

- object identity and catalog designation
- adopted epoch and coordinates (RA and declination)
- constellation
- object type and magnitude where applicable
- Declination Band
- Season
- Milky Way membership (`YES` / `NO`) under the adopted frozen Milky Way boundary

Declination Band precedes Season in Star Almanack classification and presentation.

`best` dates and ISO dates are not timeless properties and must not be treated as fields intrinsic to a fixed object.

## Timed data

Timed data describes astronomical events associated with a fixed object.

For best visibility, Star Almanack uses the established rule that the object transits at **9:00 PM LApST**.

### Astronomical year

The Star Almanack astronomical year begins when the Sun reaches the **First Point of Aries** and ends at the next passage through the First Point of Aries.

Therefore:

- Astronomical Year 2026 begins at the March 2026 First Point of Aries/equinox.
- Astronomical Year 2026 ends at the March 2027 First Point of Aries/equinox.

This astronomical-year definition is distinct from both the Gregorian calendar year and the ISO week-numbering year.

Each fixed object has exactly **one best-visibility event per astronomical year** under the 9:00 PM LApST transit rule.

### Canonical event timestamp

The canonical astronomical timestamp for a best-visibility event is **Julian Date in Terrestrial Time, JD(TT)**.

A timed best-visibility record should therefore be keyed conceptually by:

- fixed object
- astronomical year
- best-visibility JD(TT)

Human calendar coordinates are derived from the canonical astronomical event rather than defining it.

Derived publication fields may include:

- UTC date/time
- civil calendar date
- ISO week-numbering year
- ISO week
- ISO weekday

The timescale must always be explicit. A bare `JD` field without a timescale is not sufficient for canonical data.

## ISO-year publication layer

Star Almanack weekly publication is organized by **ISO week-numbering year**.

ISO year is a presentation/calendar coordinate, not the identity of the underlying best-visibility astronomical cycle. Near ISO-year boundaries, a single ISO year may contain best-visibility events belonging to different astronomical years. Conversely, best-visibility dates must not be forced into a one-event-per-ISO-year model.

The processing hierarchy is:

```text
Fixed object
  -> timeless astronomical data
  -> astronomical year
  -> one best-visibility event, JD(TT)
  -> derived UTC/civil date
  -> derived ISO year / week / weekday
  -> Star Almanack weekly publication
```

## Data-model rule

Permanent fixed-object catalogs contain timeless data.

Astronomical-year event catalogs contain timed best-visibility data.

ISO calendar data is derived for publication.

This separation prevents Gregorian- or ISO-calendar boundaries from altering the identity of the underlying astronomical event.
