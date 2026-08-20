# The Mathematics of the Star Almanack

**About this file.** This file is the technical mathematical reference for the *Star Almanack*. It records the definitions, equations, astronomical models, numerical conventions, algorithms, and validation rules underlying the calculations used throughout the project. It is intended both to explain the mathematics and to make the calculations reproducible. The ordinary reader does not need this material in order to use the *Star Almanack*; the reader-facing explanation of the project's mathematics is maintained separately in `mathematics.md`.

## 1. Time and the Celestial Sphere

The apparent motion of the stars begins with a simple fact: Earth rotates.

Relative to the Sun, an average day is 24 hours long. Relative to the distant stars, however, Earth completes one rotation in approximately

$$

23^{\mathrm h}56^{\mathrm m}4^{\mathrm s}.

$$

This is the **sidereal day**.

Because Earth also travels around the Sun while it rotates, it must turn slightly more than one complete rotation for the Sun to return to the same position in the sky. The difference is approximately 4 minutes per day.

This produces one of the most useful rules in the Almanac:

> **At the same civil time, the stars appear approximately 4 minutes earlier each successive night.**

Equivalently, a particular star reaches the same position in the sky about 2 hours earlier after 1 month.

### Right Ascension and Declination

A star's position on the celestial sphere can be described using **right ascension** and **declination**.

Right ascension, written

$$

\alpha,

$$

is analogous to longitude on Earth. It is normally measured in hours, minutes, and seconds:

$$

0^{\mathrm h} \leq \alpha < 24^{\mathrm h}.

$$

Declination, written

$$

\delta,

$$

is analogous to latitude and is measured north or south of the celestial equator:

$$

-90^\circ \leq \delta \leq +90^\circ.

$$

A star therefore has celestial coordinates of the form

$$

(\alpha,\delta).

$$

These coordinates provide the starting point for calculating when a star culminates, when it is visible, and where it appears in the sky.

### Hour Angle

The **hour angle** of a celestial object measures how far Earth's rotation has carried the object from the local meridian.

If

$$

\theta

$$

is the local sidereal time and

$$

\alpha

$$

is the object's right ascension, then its hour angle is

$$

H=\theta-\alpha.

$$

When

$$

H=0,

$$

the object is on the local meridian. It is then said to **culminate**.

Thus culmination occurs when

$$

\theta=\alpha.

$$

This simple relationship is fundamental to the calculation of the stars' visible dates used throughout the *Star Almanack*.

## Ephemerides

An **ephemeris** is a table of calculated positions of an astronomical object at specified times.

The basic problem is straightforward to state:

> Given a particular instant, where is the object?

The calculation is more complicated because astronomical positions are not fixed. The Sun, Moon, and planets move continuously against the background stars, while even stellar coordinates change slowly because of effects such as precession and proper motion.

### Julian Date

Astronomical calculations benefit from representing time as a continuously increasing number rather than as a combination of years, months, days, hours, minutes, and seconds.

The standard astronomical system is the **Julian Date**, abbreviated JD.

Julian Date counts days continuously from an astronomical epoch. Fractions of a day represent the time within the day.

For example, a difference between 2 Julian Dates can be written simply as

$$

\Delta t = JD_2 - JD_1.

$$

If

$$

\Delta t = 1,

$$

the 2 instants are exactly 1 day apart.

If

$$

\Delta t = 0.5,

$$

they are 12 hours apart.

Thus calendar dates can first be converted into Julian Dates, calculations can be performed using ordinary arithmetic, and the results can then be converted back into calendar dates and times.

### Rounding Julian Dates at Civil Midnight

When a calculated Julian Date is converted back into a civil UTC time, the *Star Almanack* first rounds and normalizes the **instant itself** to the resolution that will be displayed, and only then decomposes that instant into a Gregorian date and a clock time.

That order is deliberate.

Suppose a computed instant lies less than half a second before midnight. At whole-second resolution, the correct result is not

**23:59:60**

and it is not

**86400 seconds on the previous day**.

It is

**00:00:00 on the following day.**

In symbols, if $JD$ is the computed Julian Date and the displayed resolution is 1 second, the implementation first forms an integer number of whole seconds,

$$

S=\left\lfloor 86400\,JD+\frac{1}{2}\right\rfloor,

$$

and then uses

$$

JD_{\mathrm{norm}}=\frac{S}{86400}.

$$

The normalized Julian Date is then converted into the Gregorian date and UTC clock time.

This makes the day boundary part of the arithmetic rather than a special repair performed afterward. Rounding across midnight naturally advances the civil date before the calendar is decomposed.

This detail is also a software-safety rule. An earlier implementation decomposed the calendar first, rounded the seconds afterward, and then attempted to repair a value of 86400 seconds by recursively calling the same conversion routine. At the exact boundary, the correction could leave the Julian Date unchanged. The routine therefore encountered the same condition again, called itself again, and eventually failed with an infinite-recursion error.

The Almanack now follows the stronger invariant:

> **Normalize the astronomical instant first; decompose it into date and time exactly once.**

The aggregate validation harness contains explicit regression cases on both sides of midnight, including values just below and just above the rounding threshold. These tests are release-blocking because every astronomical result that is eventually presented as a UTC timestamp depends on this conversion behaving correctly.

### Epochs

A celestial coordinate is meaningful only in relation to time.

For stars, coordinates are commonly given for a standard **epoch**, such as J2000.0. Because Earth's rotational axis slowly changes direction, the celestial coordinate grid changes with time.

This motion is called **precession**.

A star whose coordinates are given as

$$

(\alpha_0,\delta_0)

$$

at one epoch will therefore generally have slightly different coordinates

$$

(\alpha,\delta)

$$

at another epoch.

For sufficiently precise calculations, the coordinates must be transformed from the catalog epoch to the epoch of observation.

Stars may also possess **proper motion**: an actual change in their apparent direction caused by their motion through space relative to the Sun.

Thus a modern stellar position may require both

$$

\text{catalog position}

\rightarrow

\text{proper-motion correction}

\rightarrow

\text{precession correction}.

$$

### Moving Objects

For the Sun, Moon, and planets, the situation is different.

Their changing positions are not merely corrections to nearly fixed coordinates. Their motion across the celestial sphere is itself one of the quantities the ephemeris is intended to describe.

At a given time $t$, we can think of an ephemeris as providing a function

$$

(\alpha,\delta)=f(t),

$$

where $\alpha$ is right ascension and $\delta$ is declination.

For calculations involving the zodiac, it is often more useful to express the same position in ecliptic coordinates:

$$

(\lambda,\beta)=g(t),

$$

where $\lambda$ is ecliptic longitude and $\beta$ is ecliptic latitude.

Ecliptic longitude is particularly important because the Sun's annual motion, the zodiac, planetary positions, and lunar phase calculations can all be related naturally to the ecliptic.

### Interpolation

An ephemeris does not necessarily need to calculate and store a position for every possible instant.

Suppose an object's ecliptic longitude is known at 2 nearby times:

$$

\lambda_1=\lambda(t_1)

$$

and

$$

\lambda_2=\lambda(t_2).

$$

For sufficiently short intervals and sufficiently smooth motion, an intermediate value can be estimated by linear interpolation:

$$

\lambda(t)

=

\lambda_1

+

\frac{t-t_1}{t_2-t_1}

(\lambda_2-\lambda_1).

$$

More accurate work may require higher-order interpolation or direct recalculation of the object's position.

The principle, however, remains the same:

**calculate the astronomical position with sufficient precision for the purpose of the Almanack, then present the result in a form useful to the reader.**

The ephemeris is therefore part of the mathematical machinery underneath several other parts of the *Star Almanack*. Lunar phases require the positions of the Sun and Moon. Zodiac positions require ecliptic longitude. Horoscope calculations require the positions of the relevant astronomical bodies.

The tables may look simple.

The simplicity is deliberate.

