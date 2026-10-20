"""Conversions for ocean heat content trends."""

from __future__ import annotations

EARTH_SURFACE_AREA_M2 = 5.10072e14
SECONDS_PER_TROPICAL_YEAR = 365.25 * 24 * 3600

HEATING_RATE_CITATION = (
    "Heating rate (W m⁻²) = (dOHC/dt in J yr⁻¹) / (seconds per year × Earth's surface area 5.10072×10¹⁴ m²); "
    "OHC in 10²² J (NCEI)."
)


def ohc_slope_1e22j_per_year_to_w_m2(slope_1e22_j_per_year: float) -> float:
    joules_per_year = slope_1e22_j_per_year * 1e22
    return joules_per_year / SECONDS_PER_TROPICAL_YEAR / EARTH_SURFACE_AREA_M2


def ohc_slope_1e22j_per_year_to_zj_per_year(slope_1e22_j_per_year: float) -> float:
    return slope_1e22_j_per_year * 10.0
