#!/usr/bin/env python3
"""Shared, ownership-safe replacement helpers for generated scaffold blocks."""
from __future__ import annotations

import datetime as dt
import re
from collections.abc import Callable
from pathlib import Path


def iso_week_count(year: int) -> int:
    return dt.date(year, 12, 28).isocalendar().week


def replace_owner_blocks(
    text: str,
    year: int,
    owner: str,
    render: Callable[[int], str],
) -> str:
    """Replace every block owned by *owner*, leaving all other bytes alone."""
    begin = f"<!-- BEGIN GENERATED: {owner} -->"
    end = f"<!-- END GENERATED: {owner} -->"
    weeks = iso_week_count(year)

    for week in range(1, weeks + 1):
        heading = f"## ISO {year}-W{week:02d}"
        start = text.find(heading)
        if start < 0:
            raise RuntimeError(f"Missing {heading}")
        next_match = re.search(rf"(?m)^## ISO {year}-W\d{{2}}\s*$", text[start + len(heading):])
        stop = start + len(heading) + next_match.start() if next_match else len(text)
        section = text[start:stop]
        block_start = section.find(begin)
        block_end = section.find(end)
        if block_start < 0 or block_end < block_start:
            raise RuntimeError(f"Missing {owner} ownership markers in {heading}")
        block_end += len(end)
        body = render(week).rstrip()
        replacement = f"{begin}\n{body}\n{end}"
        section = section[:block_start] + replacement + section[block_end:]
        text = text[:start] + section + text[stop:]

    if text.count(begin) != weeks or text.count(end) != weeks:
        raise RuntimeError(f"Unexpected {owner} ownership-marker count for {year}")
    return text


def write_atomic(path: Path, text: str) -> None:
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(text, encoding="utf-8")
    temporary.replace(path)
