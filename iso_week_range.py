#!/usr/bin/env python3
"""Validated inclusive ISO-week ranges shared by Almanack generators."""
from __future__ import annotations

import datetime as dt
import re
from collections import defaultdict
from dataclasses import dataclass

ISO_WEEK_RE = re.compile(r"^(\d{4})-W(\d{2})$")


@dataclass(frozen=True, order=True)
class IsoWeek:
    year: int
    week: int

    @classmethod
    def parse(cls, value: str) -> "IsoWeek":
        match = ISO_WEEK_RE.fullmatch(value.strip())
        if not match:
            raise ValueError(f"ISO week must use YYYY-Www format: {value!r}")
        result = cls(int(match.group(1)), int(match.group(2)))
        # fromisocalendar is the authority for whether W53 exists in a year.
        dt.date.fromisocalendar(result.year, result.week, 1)
        return result

    @property
    def monday(self) -> dt.date:
        return dt.date.fromisocalendar(self.year, self.week, 1)

    @property
    def sunday(self) -> dt.date:
        return dt.date.fromisocalendar(self.year, self.week, 7)

    def __str__(self) -> str:
        return f"{self.year:04d}-W{self.week:02d}"


@dataclass(frozen=True)
class IsoWeekRange:
    first: IsoWeek
    last: IsoWeek

    def __post_init__(self) -> None:
        if self.last.monday < self.first.monday:
            raise ValueError("Last ISO week cannot precede first ISO week")

    @classmethod
    def parse(cls, first: str, last: str | None = None) -> "IsoWeekRange":
        start = IsoWeek.parse(first)
        return cls(start, IsoWeek.parse(last) if last else start)

    def weeks(self) -> tuple[IsoWeek, ...]:
        result: list[IsoWeek] = []
        current = self.first.monday
        while current <= self.last.monday:
            iso = current.isocalendar()
            result.append(IsoWeek(iso.year, iso.week))
            current += dt.timedelta(days=7)
        return tuple(result)

    def by_year(self) -> dict[int, tuple[int, ...]]:
        grouped: dict[int, list[int]] = defaultdict(list)
        for item in self.weeks():
            grouped[item.year].append(item.week)
        return {year: tuple(weeks) for year, weeks in grouped.items()}

    def contains(self, year: int, week: int) -> bool:
        monday = dt.date.fromisocalendar(year, week, 1)
        return self.first.monday <= monday <= self.last.monday

    def __len__(self) -> int:
        return ((self.last.monday - self.first.monday).days // 7) + 1


def range_from_legacy_years(start_year: int, end_year: int | None = None) -> IsoWeekRange:
    final = start_year if end_year is None else end_year
    if final < start_year:
        raise ValueError("End year cannot be earlier than start year")
    last_week = dt.date(final, 12, 28).isocalendar().week
    return IsoWeekRange(IsoWeek(start_year, 1), IsoWeek(final, last_week))
