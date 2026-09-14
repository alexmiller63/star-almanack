#!/usr/bin/env python3
"""Compatibility entry point for the year-parameterized Sky Notes generator.

New automation should call generate_fixed_object_sky_notes.py directly.
Invoking this legacy filename preserves the historical one-year 2026 default.
"""
from generate_fixed_object_sky_notes import main


if __name__ == "__main__":
    raise SystemExit(main())
