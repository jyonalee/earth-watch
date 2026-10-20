"""Airborne fraction helpers."""

from __future__ import annotations

import math
from typing import Any

from earth_watch.constants import PPM_CO2_TO_GTC

FOSSIL_RELATIVE_SIGMA = 0.05
LAND_USE_SIGMA_GTC = 0.7
SMOOTHING_WINDOW_YEARS = 10


def growth_ppm_to_gtc(growth_ppm: float) -> float:
    return growth_ppm * PPM_CO2_TO_GTC


def emissions_sigma_gtc(fossil_gtc: float, land_use_gtc: float) -> float:
    fossil_sigma = FOSSIL_RELATIVE_SIGMA * fossil_gtc
    return math.sqrt(fossil_sigma**2 + LAND_USE_SIGMA_GTC**2)


def airborne_fraction(
    growth_gtc: float,
    fossil_gtc: float,
    land_use_gtc: float,
) -> float:
    total = fossil_gtc + land_use_gtc
    if total <= 0:
        raise ValueError("non-positive emissions")
    return growth_gtc / total


def airborne_fraction_fossil_only(growth_gtc: float, fossil_gtc: float) -> float:
    if fossil_gtc <= 0:
        raise ValueError("non-positive fossil emissions")
    return growth_gtc / fossil_gtc


def airborne_fraction_sigma(
    af: float,
    growth_gtc: float,
    growth_sigma_gtc: float,
    emissions_gtc: float,
    emissions_sigma_gtc: float,
) -> float:
    if growth_gtc <= 0 or emissions_gtc <= 0:
        return 0.0
    rel_g = growth_sigma_gtc / growth_gtc
    rel_e = emissions_sigma_gtc / emissions_gtc
    return abs(af) * math.sqrt(rel_g**2 + rel_e**2)


def centered_mean(values: list[float], window: int) -> list[float | None]:
    if window < 1:
        raise ValueError("window must be positive")
    before = (window - 1) // 2
    after = window // 2
    out: list[float | None] = []
    for i in range(len(values)):
        lo = i - before
        hi = i + after
        if lo < 0 or hi >= len(values):
            out.append(None)
            continue
        chunk = values[lo : hi + 1]
        out.append(sum(chunk) / len(chunk))
    return out


def chart_b_years(
    gcb_years: set[int],
    gml_years: set[int],
    *,
    gcb_max_year: int,
    current_utc_year: int,
) -> list[int]:
    cap = min(gcb_max_year, current_utc_year - 1)
    return sorted(y for y in gcb_years if y in gml_years and y <= cap)
