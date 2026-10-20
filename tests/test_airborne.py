"""Airborne fraction math."""

from __future__ import annotations

from earth_watch.airborne import airborne_fraction, chart_b_years, growth_ppm_to_gtc


def test_ppm_to_gtc():
    assert growth_ppm_to_gtc(1.0) == 2.124


def test_chart_b_year_cap():
    years = chart_b_years({2023, 2024, 2025}, {2023, 2024, 2025}, gcb_max_year=2024, current_utc_year=2026)
    assert years == [2023, 2024]


def test_airborne_fraction_basic():
    af = airborne_fraction(growth_ppm_to_gtc(2.0), fossil_gtc=8.0, land_use_gtc=1.0)
    assert 0.3 < af < 0.6
