# The Mathematics of the Star Almanac

The *Star Almanac* is designed to be used without any knowledge of the mathematics behind it. This section is for readers who want to understand, verify, or reproduce the calculations used elsewhere in the Almanac. It may be skipped entirely without affecting the use of the rest of the book.

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

This simple relationship is fundamental to the calculation of the stars' visible dates used throughout the *Star Almanac*.

