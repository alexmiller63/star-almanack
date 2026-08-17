# Star Almanack — Book Map

## Purpose

This document is the working structural map of *Star Almanack: A Natural Philosopher’s Guide to the Night Sky*.

It identifies:

- the reader-facing structure of the finished book;

- the existing repository material that feeds each section;

- supporting methodology and validation;

- production specifications;

- working files that are not intended to appear directly in the finished book.

The governing principle is simple:

**The reader should not need to understand the mathematics in order to use the Almanack.**

The observing experience comes first. The mathematics remains available underneath it.

---

# Front Matter

## Half Title

*Star Almanack*

## Title Page

**Star Almanack**

*A Natural Philosopher’s Guide to the Night Sky*

Alexander Ferrari Miller

## Copyright and Publication Page

Include:

- copyright notice;

- edition and publication year;

- publisher;

- ISBN;

- astronomical-data acknowledgments;

- calculation and software acknowledgments;

- artwork and typography credits as appropriate.

## Dedication

Optional.

## Epigraph

To be selected.

## Table of Contents

Generated from the final book structure.

## Preface

Why *Star Almanack* exists.

Introduce the idea of an astronomical almanack organized around the experience of someone actually looking at the sky.

The book should answer practical questions such as:

- What is it called?

- How is it pronounced?

- When is it best visible?

- Where do I look?

- What will it look like?

- What helps me find it?

Source material:

- `README.md`

## How to Use This Almanack

A short practical introduction to the conventions used throughout the book.

Explain:

- ISO week dates;

- civil dates;

- UTC;

- local time;

- astronomical symbols;

- zodiac symbols;

- planetary symbols;

- weekly charts;

- object entries;

- dates of best visibility;

- pronunciation and IPA;

- basic chart orientation.

Do not require the reader to understand the underlying mathematics.

---

# Part I — Time, Calendars, and the Sky

This part establishes the conceptual framework of the Almanack.

## For Signs and for Seasons

Nature provides motions and cycles.

Human beings construct systems for describing them.

Discuss:

- days;

- years;

- seasons;

- calendars;

- clocks;

- time zones;

- UTC;

- the International Date Line;

- astronomical conventions.

Source:

- `signs-and-seasons.md`

## What Century Was My Grandmother Born In?

Use the author's grandmother's birth in Kyiv to explore the difference between:

- an event;

- the calendar used to record it;

- Julian and Gregorian dates;

- local clock time;

- standardized time;

- historical timekeeping.

Source:

- `grandmother.md`

## The Most Ordinary Day Throughout the World

Explore the search for an instant in 2026 that is deliberately ordinary.

Use the selected instant:

**August 9, 2026 at 10:53 UTC**

Show how one instant becomes different civil dates and times around the world.

Use this to make UTC, time zones, unusual offsets, and the International Date Line concrete.

Source:

- `most-ordinary.md`

Development sources, not intended for direct publication:

- `four-candidates.md`

## ISO Time and the Almanack

Explain why *Star Almanack* uses ISO 8601 week numbering.

Topics:

- ISO week;

- ISO week-year;

- Monday as the first day of the week;

- week-date notation;

- 53-week years;

- relationship between ISO dates and civil dates.

2026 contains 53 ISO weeks.

Source:

- `ISO2026.md`

---

# Part II — The Zodiac and the Calendar of the Sun

## What the Zodiac Means Here

Define the tropical zodiac as twelve equal 30° sectors of ecliptic longitude.

Distinguish:

- zodiac signs;

- astronomical constellations;

- ecliptic longitude;

- the first point of Aries;

- precession.

## The Zodiac Calendar

Explain the Almanack's sign-day calendar.

The ingress date is Sign 1.

Dates count forward until the next ingress.

The resulting calendar follows the actual motion of the Sun rather than forcing every sign into an identical civil-calendar length.

Source material:

- `ISO2026.md`

- `math.md`

- `mathematics.md`

Calculation source:

- `12-candidates.md`

## A Libra Birthday

Use the author's October 9 birthday to illustrate the relationship between familiar astrological date ranges and the Almanack's astronomical zodiac calendar.

Source:

- `birthday-libra.md`

## Get Over It

Essay on precession and the distinction between constellations and the twelve equal sectors of the tropical zodiac.

The zodiac is a coordinate system.

Precession does not invalidate a coordinate system.

Source material:

- `math.md`

- `README.md`

---

# Part III — Finding the Sky

## What "Best Visibility" Means

Define the central Star Almanack observing convention:

**An object's best visibility occurs when it transits the local meridian at 9:00 PM local apparent solar time.**

Explain intuitively:

- culmination;

- transit;

- local meridian;

- right ascension;

- why 9:00 PM was chosen;

- why the date is useful to an observer.

Leave the detailed derivation for the mathematics section.

## The 9:00 PM Argument

The story of the argument with Neil deGrasse Tyson.

Use the story to explain why the Almanack adopts a practical observer-centered convention rather than pretending there is a single naturally ordained clock time for "best visibility."

Source:

- `tyson.md`

## The Two Rabbis

Use the story to explore astronomical calculation, observation, calendars, and the limits of what calculation can declare.

Source:

- `rabbis.md`

## Where in the Sky?

Introduce the coordinates and concepts an observer needs:

- right ascension;

- declination;

- celestial equator;

- meridian;

- altitude and direction;

- northern and southern sky;

- circumpolar objects.

## The Five Sky Bands

Introduce the Almanack's declination-based organization:

- Arctic;

- Northern;

- Tropical;

- Southern;

- Antarctic.

Explain how the bands help readers understand where objects belong in the sky and which observers can see them.

Source:

- `objects.md`

---

# Part IV — The Moon

## The Lunar Cycle

Explain:

- New Moon;

- First Quarter;

- Full Moon;

- Last Quarter;

- synodic month;

- observing consequences of lunar phase.

## Crescent Moon Visibility

Explain the distinction between calculating possible crescent visibility and declaring the beginning of a religious or cultural month.

Governing principle:

> We humbly calculate the crescent; we do not declare the month.

## Named Full Moons

Explain the Almanack's naming system.

Include:

- seasonal Full Moon names;

- the relationship between lunar cycles and astronomical seasons;

- protected seasonal names where applicable;

- the Frost Moon rule;

- the Yule relationship.

Source:

- `moon-names.md`

## The Blue Moon

Use the traditional seasonal definition:

**The third Full Moon in an astronomical season containing four Full Moons.**

Explain why the Almanack uses this definition rather than the later calendar-month definition.

Source:

- `moon-names.md`

---

# Part V — The 2026 Almanack

This is the heart of the book.

Source:

- `almanack.md`

## The Year at a Glance

Present major annual structures together:

- ISO weeks;

- zodiac calendar;

- astronomical seasons;

- lunar phases;

- named Full Moons;

- important annual sky events.

## The 53 Weeks of 2026

One observing unit for each ISO week.

Each weekly unit should contain, as appropriate:

- ISO week number;

- ISO week-date;

- civil dates;

- weekly sky chart;

- Sun position;

- Moon position;

- Mercury position;

- Venus position;

- Mars position;

- Jupiter position;

- Saturn position;

- lunar phase information;

- zodiac information;

- objects near best visibility;

- seasonal observing guidance;

- Sky Notes;

- relevant astronomical events.

## Weekly Classical-Planet Charts

Each week receives a consistent chart using the established chart design.

The classical bodies are:

- ☉ Sun

- ☽ Moon

- ☿ Mercury

- ♀ Venus

- ♂ Mars

- ♃ Jupiter

- ♄ Saturn

Positions are sampled Monday at 00:00 UTC.

Production specification:

- `weekly-chart-design.yaml`

## Weekly Sky Notes

Short reader-facing notes highlighting what is particularly worth noticing during the week.

These should interpret the data rather than merely repeat it.

---

# Part VI — Objects of the Sky

## The Star Almanack Object Catalog

Present the selected catalog of astronomical objects.

Source:

- `objects.md`

## Object Entry Design

Each object entry should answer as many of these questions as applicable:

- What is it called?

- How is it pronounced?

- What kind of object is it?

- Where is it?

- In which sky band does it lie?

- When is it best visible?

- What does it look like?

- Can it be seen with the unaided eye?

- Are binoculars useful?

- Is a telescope useful?

- What nearby stars or patterns help locate it?

- What is scientifically or historically interesting about it?

## Dates of Best Visibility

Provide best-visibility dates for the full object catalog.

The calculation uses the 9:00 PM local apparent solar time convention.

Source material:

- `objects.md`

- `almanack.md`

- `math.md`

## Pronunciation

Provide IPA and useful pronunciation guidance for astronomical names.

Where multiple established pronunciations exist, more than one may be given.

---

# Part VII — Seasons of the Sky

## Astronomical Seasons

Use the actual astronomical boundaries:

- March equinox;

- June solstice;

- September equinox;

- December solstice.

## Seasonal Observing

Organize observing guidance around the changing sky.

Possible divisions:

- March equinox to June solstice;

- June solstice to September equinox;

- September equinox to December solstice;

- December solstice to March equinox.

Discuss:

- prominent stars;

- constellations;

- deep-sky objects;

- Milky Way visibility;

- seasonal planetary circumstances where appropriate.

Source material:

- `objects.md`

- `almanack.md`

---

# Part VIII — Mathematics Under the Almanack

This part is for readers who want to know exactly how the Almanack works.

The practical use of the book must not depend on reading this section.

Sources:

- `math.md`

- `mathematics.md`

## Coordinate Systems

Explain:

- celestial sphere;

- right ascension;

- declination;

- ecliptic longitude;

- equatorial coordinates;

- zodiac coordinates.

## Time Systems

Explain:

- UTC;

- local civil time;

- apparent solar time;

- local apparent solar time;

- sidereal time;

- Local Sidereal Time.

## Best-Visibility Calculation

Derive the relationship between:

- object right ascension;

- solar right ascension;

- meridian transit;

- 9:00 PM local apparent solar time.

Document the calculation used to determine the annual best-visibility date.

## Zodiac Ingress Calculations

Explain how the Sun's apparent ecliptic longitude determines the twelve zodiac boundaries.

## Lunar Calculations

Document:

- lunar phase calculations;

- Full Moon naming logic;

- seasonal Blue Moon determination;

- crescent-visibility methodology and limitations.

## Calendars

Discuss:

- Gregorian calendar;

- Julian calendar;

- ISO week calendar;

- leap years;

- date conversion;

- International Date Line.

---

# Part IX — Validation

The Almanack should show its work.

Source:

- `validation.md`

## Best-Visibility Regression Tests

Document the representative named-star regression set and expanded object testing.

## Zodiac Validation

Compare calculated ingress times with authoritative published ephemerides where available.

Discuss known tolerances rather than pretending independent ephemerides will always produce identical timestamps.

## Lunar Validation

Compare calculated lunar phases against authoritative published values.

## Planetary Ephemeris Validation

Validate the weekly positions of:

- Sun;

- Moon;

- Mercury;

- Venus;

- Mars;

- Jupiter;

- Saturn.

Source:

- `ephem.md`

## Known Limits

State clearly where:

- calculation is approximate;

- conventions are deliberately chosen;

- different authoritative ephemerides may disagree slightly;

- observational circumstances depend on location and conditions.

---

# Reference Material

## Symbols

Reference for:

- zodiac symbols;

- classical-planet symbols;

- astronomical notation.

## Pronunciation Guide

Alphabetical pronunciation and IPA reference.

## Glossary

Terms used throughout the Almanack.

## Tables

Supporting astronomical and calendar tables that are useful to readers but would interrupt the main narrative.

## Bibliography and Sources

Include:

- astronomical ephemerides;

- reference catalogs;

- calendar sources;

- historical references;

- pronunciation sources;

- software and computational resources.

## Acknowledgments

People and organizations that contributed information, criticism, validation, artwork, or assistance.

## Index

Include:

- named stars;

- constellations;

- planets;

- Moon terminology;

- astronomical objects;

- calendar concepts;

- mathematical concepts;

- stories and essays.

---

# Production Material

These repository files support production of the book but are not themselves chapters.

## Typography

`typography.md`

Defines typographic conventions, symbols, and presentation rules.

## Weekly Chart Specification

`weekly-chart-design.yaml`

Defines the geometry and visual conventions of the weekly classical-planet chart.

---

# Development and Calculation Material

These files preserve useful development history or intermediate calculations but are not intended to appear directly in the finished book.

## Zodiac Boundary Candidates

`12-candidates.md`

Working calculated zodiac-boundary times.

## Most Ordinary Day Candidate Work

`four-candidates.md`

Intermediate candidate selection and time-screening work.

## Mathematical Test

`math-test.md`

Calculation/test material.

## Story Baseline

`3-stories-baseline.md`

Preserved baseline material for story development and comparison.

---

# Repository Integration

The principal repository files currently map into the book as follows:

- `README.md` — project principles, reader questions, overview

- `almanack.md` — integrated 2026 Almanack

- `ISO2026.md` — ISO calendar and annual astronomical structure

- `objects.md` — object catalog and sky-band system

- `moon-names.md` — lunar naming and Blue Moon methodology

- `most-ordinary.md` — Most Ordinary Day essay

- `grandmother.md` — calendar/time essay

- `signs-and-seasons.md` — natural-philosophy essay

- `birthday-libra.md` — zodiac story

- `rabbis.md` — calendar/observation story

- `tyson.md` — best-visibility story

- `math.md` — mathematical methodology

- `mathematics.md` — mathematical exposition

- `validation.md` — validation methodology and results

- `ephem.md` — planetary ephemeris material

- `typography.md` — production specification

- `weekly-chart-design.yaml` — chart production specification

- `12-candidates.md` — working zodiac calculations

- `four-candidates.md` — development history

- `math-test.md` — testing material

- `3-stories-baseline.md` — preserved story-development baseline

- `map.md` — this structural map

---

# Working Principle

*Star Almanack* should work on several levels at once.

A reader should be able to open it and simply find something to look at tonight.

A curious reader should be able to understand why the calendar and observing conventions work the way they do.

A technically minded reader should be able to follow the mathematics.

And a skeptical reader should be able to examine the validation.

The mathematics serves the sky.

The book serves the observer.

