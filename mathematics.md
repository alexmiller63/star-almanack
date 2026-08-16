# The Mathematics

Stephen Hawking tells a story in *A Brief History of Time* about being warned that every equation he included would reduce the book's sales. He therefore tried to write the book without equations, but ultimately allowed himself one: Einstein's famous equation,

$$

E = mc^2

$$

The *Star Almanack* takes a similar approach to mathematics. The mathematics underneath the Almanack may be precise. The reader's interface to the sky should remain simple.

A person should not need to understand celestial coordinate systems merely to find Betelgeuse. The reader should be able to walk outside, look toward Orion, and recognize the reddish-orange star marking his shoulder. But somewhere underneath that simple instruction, the mathematics has to be done.

## How the Calculation Was Discovered

The original best-visibility calculation was developed empirically in a spreadsheet using simple lookup tables. I did not begin with the equations that follow and then implement them in the spreadsheet. I built a spreadsheet method that worked.

The formulas and lookup tables produced dates for stars and other astronomical objects. I then tested those results against information that had not been used to generate them: the established observing seasons of the constellations in which the objects appeared.

For example, Aldebaran belongs to Taurus. Taurus is conventionally identified as a Northern Hemisphere winter constellation. The spreadsheet produced January 12 as Aldebaran's best-visibility date.

That was a pass.

Rigel belongs to Orion, another Northern Hemisphere winter constellation. The spreadsheet produced January 21.

Another pass.

The important point is that the spreadsheet did not know that Taurus was a winter constellation. It did not know that Orion was a winter constellation. The seasonal classifications were not inputs to the calculation. They were independent checks on its results.

I initially tested the spreadsheet against 15 familiar stars. All 15 passed. Having established that the method was producing dates consistent with the independently established observing seasons of their host constellations, I went on to apply the spreadsheet method to around 100 astronomical objects.

Only later did we articulate the mathematics that explains formally what the spreadsheet was already doing.

The history therefore runs in this direction:

**empirical spreadsheet method → independent observational validation → expansion to around 100 objects → mathematical explanation**

The equations below are not the origin of the calculation.

They are an explanation of why the calculation works.

## Best Visibility

For stars and other objects whose celestial coordinates change only slowly, the *Star Almanack* needs a reproducible definition of **best visibility**.

We define it as the annual moment when the object crosses the local meridian at:

**9:00 PM local apparent time.**

Local apparent time is sometimes called **sundial time**. It follows the apparent position of the Sun at the observer's longitude rather than the boundaries of civil time zones or the adjustments of daylight saving time.

At meridian transit, the object's hour angle is 0. Therefore,

$$

\mathrm{LST} = \alpha_{\text{object}}

$$

where LST is local sidereal time and $\alpha_{\text{object}}$ is the object's right ascension.

At **9:00 PM local apparent time**, the apparent Sun has an hour angle of 9 hours. Therefore,

$$

\mathrm{LST} = \alpha_\odot + 9\mathrm{h}

$$

Combining the two expressions gives:

$$

\alpha_{\text{object}} = \alpha_\odot + 9\mathrm{h}

$$

and therefore:

$$

\boxed{\alpha_\odot = \alpha_{\text{object}} - 9\mathrm{h}}

$$

That is the mathematical heart of the calculation.

For a particular star, obtain its right ascension. Subtract 9 hours, wrapping through 24 hours when necessary. Then find the annual instant when the apparent Sun reaches that right ascension. That instant tells us when the object crosses the observer's meridian at **9:00 PM local apparent time**.

There is a particularly elegant consequence:

**Longitude drops out of the calculation.**

We do not need to select New York, London, Sydney, San Bernardino, or any other arbitrary place on Earth. Because we are using local apparent time, the Sun and the object themselves provide the clocks.

## Does It Actually Work?

An elegant equation is not enough. The calculation has to survive contact with the sky.

The original spreadsheet was initially tested against 15 familiar stars. For each one, the calculated best-visibility date was compared with the established observing season of the constellation containing that star.

The test therefore followed this chain:

**object → host constellation → published observing season → calculated date → PASS or FAIL**

The published observing season was independent of the calculation. The spreadsheet knew the astronomical data in its lookup tables. It did not know what season astronomers traditionally associated with Taurus, Orion, Leo, Virgo, Scorpius, Lyra, Cygnus, or the other constellations represented in the test.

The 15 calculated dates were:

- Aldebaran — Jan 12

- Rigel — Jan 21

- Capella — Jan 22

- Betelgeuse — Jan 31

- Sirius — Feb 13

- Procyon — Feb 27

- Pollux — Feb 28

- Regulus — Apr 8

- Spica — May 29

- Arcturus — Jun 11

- Antares — Jul 13

- Vega — Aug 15

- Albireo — Aug 29

- Altair — Sep 4

- Deneb — Sep 18

Each calculated date was then compared with the independently established observing season of the object's host constellation. All 15 agreed with the expected seasonal placement.

**15/15 PASS**

That was the first important evidence that the empirical spreadsheet method was producing something astronomically meaningful. After that initial test, I extended the spreadsheet work to around 100 astronomical objects.

## The Expanded Test

Much later, a separate expanded test set was assembled using 20 familiar astronomical objects: 10 stars and 10 Messier objects. This provided another opportunity to ask whether the method continued to produce dates that agreed with the familiar seasonal organization of the sky.

For 2026, the calculated best-visibility dates were:

- Canopus — Feb 7

- Alpha Centauri — Jun 16

- Achernar — Dec 3

- Acrux — May 15

- Bellatrix — Jan 24

- Fomalhaut — Oct 25

- Castor — Feb 26

- Alkaid — Jun 4

- Dubhe — Apr 23

- Polaris — Dec 16

- M31 Andromeda Galaxy — Nov 20

- M42 Orion Nebula — Jan 26

- M45 Pleiades — Jan 1

- M44 Beehive Cluster — Mar 15

- M13 Hercules Cluster — Jul 16

- M57 Ring Nebula — Aug 19

- M8 Lagoon Nebula — Aug 6

- M20 Trifid Nebula — Aug 6

- M27 Dumbbell Nebula — Sep 6

- M51 Whirlpool Galaxy — May 31

The same validation principle applies. Each object belongs to a constellation. The constellation has an independently established observing season. The calculated date can therefore be checked against that seasonal description.

Objects associated with Orion fall in the Northern Hemisphere winter. The Sagittarius nebulae fall in summer. M13 in Hercules falls in summer. M31 in Andromeda falls in late autumn. Familiar stars of the Big Dipper fall in the spring and early-summer portion of the calendar.

Again, the seasonal information is not part of the calculation.

It is a test of the calculation.

That distinction matters. If we had inserted "winter" into the calculation and then congratulated ourselves when the result came out in winter, we would have proved nothing. Instead, the calculation produces a date from astronomical quantities, and an independent description of the constellation tells us whether that date makes observational sense.

## Precision Without Complexity

The calculations behind the *Star Almanack* may use right ascension, local sidereal time, apparent solar coordinates, precession models, epochs, and other astronomical machinery. The reader does not have to.

The internal calculation can say:

$$

\alpha_\odot = \alpha_{\text{object}} - 9\mathrm{h}

$$

The Almanack can say:

**Look south.**

**Look near Orion.**

**Look during Northern Hemisphere winter.**

**This is the week when the object is best placed at 9:00 PM local apparent time.**

Both descriptions can be correct. They are simply intended for different purposes.

Hawking allowed himself an equation.

The *Star Almanack* will need a few more.

But the equations belong underneath the experience rather than in its way.

The goal is not to make the reader perform astronomy.

The goal is to do enough astronomy that the reader can walk outside, look up, and know what they are looking at.

