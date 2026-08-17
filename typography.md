# Star Almanack Typography

## Purpose

This document defines the typographic and symbolic conventions used throughout Star Almanack.

The Almanack should present a large amount of astronomical and calendrical information clearly and compactly. Traditional astronomical and astrological symbols are used where appropriate to reduce visual clutter while preserving meaning.

## General Symbol Rule

Where an established astronomical or astrological symbol exists, Star Almanack should prefer the symbol over repeatedly spelling out its name.

Symbols should not, however, require prior knowledge from the reader.

Therefore:

1. The front matter will contain a symbol key identifying the symbols used throughout the Almanack.

2. The first occurrence of a symbol in the Almanack proper will be followed by its name in parentheses.

3. Subsequent occurrences may use the symbol alone.

Example:

First occurrence:

♈ (Aries) 1

Following occurrence:

♈ 2

## Zodiac Symbols

The twelve tropical zodiac signs use their traditional symbols:

| Sign | Symbol |

|---|:---:|

| Aries | ♈ |

| Taurus | ♉ |

| Gemini | ♊ |

| Cancer | ♋ |

| Leo | ♌ |

| Virgo | ♍ |

| Libra | ♎ |

| Scorpio | ♏ |

| Sagittarius | ♐ |

| Capricorn | ♑ |

| Aquarius | ♒ |

| Pisces | ♓ |

The symbol represents the sign as a 30-degree division of tropical ecliptic longitude. It should not be interpreted as an assertion that the tropical sign coincides with the modern boundaries of the constellation bearing the same name.

## Tropical-Year Dates

Dates within the tropical year should use the zodiac symbol followed by the numbered day of the sign.

For example:

♈ (Aries) 1

♈ 2

♈ 3

After Aries has been introduced, its name does not need to be repeated with each date.

When the next sign first appears, it is introduced in the same manner:

♉ (Taurus) 1

followed by:

♉ 2

♉ 3

This convention considerably reduces clutter in calendar displays.

## Planetary Symbols

Traditional astronomical symbols should also be used for the Sun, Moon, and planets where practical.

| Body | Symbol |

|---|:---:|

| Sun | ☉ |

| Moon | ☽ |

| Mercury | ☿ |

| Venus | ♀ |

| Earth | ♁ |

| Mars | ♂ |

| Jupiter | ♃ |

| Saturn | ♄ |

| Uranus | ♅ |

| Neptune | ♆ |

| Pluto | ♇ |

As with zodiac symbols, the first occurrence of a planetary symbol in the Almanack proper should identify it in parentheses.

For example:

☉ (Sun)

Later occurrences may simply use:

☉

## Symbol Key

The front matter should include a clearly visible symbol key containing, at minimum:

- the twelve zodiac symbols;

- the Sun and Moon;

- the planetary symbols used in that edition;

- any additional astronomical symbols used in calendars, charts, tables, or horoscopes.

The symbol key serves as the permanent reference. The first-use convention allows the reader to learn the notation naturally while reading.

## Design Principle

Symbols are not merely decorative.

They form part of the information architecture of Star Almanack. A familiar symbol can communicate the same information as a word while occupying substantially less space.

This becomes particularly important when several astronomical, calendrical, or astrological facts must appear within a single calendar entry.

The goal is therefore:

**Introduce the symbol clearly once, then let the symbol do the work.**

## Classification Order

Star Almanack presents an object's reader-facing classification in the order:

**Declination band + observing season**

For example:

- **Northern Summer**

- **Tropical Winter**

- **Southern Spring**

This ordering is intentional.

Astronomical convention normally places right ascension before declination. Star Almanack reverses that conceptual order for its reader-facing classification.

The declination band comes first because it tells the reader **where** the object lies in the celestial sphere. The observing season comes second because it tells the reader **when** the object is favorably placed in the evening sky.

Arctic and Antarctic objects are not assigned an observing season and are therefore identified simply as:

- **Arctic**

- **Antarctic**

## Weekly Classical-Planet Ephemeris

Star Almanack uses a fixed weekly ephemeris to generate the horoscope wheel for each ISO week.

The weekly ephemeris is calculated independently from the typesetting process. Typesetting reads the preserved astronomical data and does not perform its own astronomical calculations.

### Sampling Rule

For each ISO week, calculate the positions of the 7 traditional wandering bodies at:

**Monday 00:00 UTC**

The bodies are:

- ☉ Sun

- ☽ Moon

- ☿ Mercury

- ♀ Venus

- ♂ Mars

- ♃ Jupiter

- ♄ Saturn

These are the 7 traditional planets in the historical astronomical and astrological sense, including the Sun and Moon.

### Coordinate

For each body, calculate its:

**geocentric tropical ecliptic longitude**

The longitude should be preserved numerically at sufficient precision for reproducible plotting.

For reader-facing tables and charts, convert the longitude into:

**zodiac symbol + degree + arcminute**

For example:

`♑ 7°42′`

The raw numerical longitude should remain available underneath the presentation layer.

### ISO 2026 Coverage

ISO week-numbering year 2026 contains 53 weeks.

The ephemeris therefore contains:

**53 weekly snapshots × 7 bodies = 371 calculated positions**

The first sample is:

**2026-W01 — Monday, Dec 29, 2025 at 00:00 UTC**

The final sample is:

**2026-W53 — Monday, Dec 28, 2026 at 00:00 UTC**

### Ephemeris Table Format

The working table should use astronomical symbols directly:

| ISO Week | Monday 00:00 UTC | ☉ | ☽ | ☿ | ♀ | ♂ | ♃ | ♄ |

|---|---|---:|---:|---:|---:|---:|---:|---:|

| 2026-W01 | Dec 29, 2025 | … | … | … | … | … | … | … |

| 2026-W02 | Jan 5, 2026 | … | … | … | … | … | … | … |

### Weekly Horoscope Wheel

Each ISO week receives a circular horoscope chart.

The wheel is divided into 12 equal 30° slices corresponding to the tropical zodiac.

The zodiac symbols appear inside the slices:

♈ ♉ ♊ ♋ ♌ ♍ ♎ ♏ ♐ ♑ ♒ ♓

The 7 classical planets are plotted at their calculated tropical longitudes:

☉ ☽ ☿ ♀ ♂ ♃ ♄

The weekly chart is therefore a graphical representation of the preserved ephemeris rather than a separately calculated result.

### Orientation

The wheel uses a fixed zodiac orientation for every week.

The First Point of Aries is placed at the standard fixed reference position used by Star Almanack, and zodiac longitude increases counterclockwise around the wheel.

Because the chart is not location-dependent, it contains no houses and no Ascendant.

### Separation of Calculation and Presentation

The calculation layer determines the astronomical positions.

The data layer preserves those positions.

The typesetting layer draws the weekly wheel from the preserved data.

Therefore:

**calculation → preserved ephemeris → typesetting → horoscope wheel**

A change to graphic design must not alter the astronomical values.

A change to the astronomical calculation must be regenerated and validated before the resulting values are used by typesetting.

