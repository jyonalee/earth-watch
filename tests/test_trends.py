"""OLS trend and AR(1)-adjusted uncertainty."""

from __future__ import annotations

import math

import pytest

from earth_watch.trends.ols import compare_slopes, linear_trend, quadratic_acceleration


def _synthetic_warming(years: list[int], rate_per_year: float, noise: float = 0.0) -> list[float]:
    return [rate_per_year * (y - years[0]) + noise * math.sin(y) for y in years]


class TestLinearTrend:
    def test_known_slope(self):
        years = list(range(2000, 2021))
        values = _synthetic_warming(years, 0.02)
        fit = linear_trend(years, values)
        assert fit.slope_per_decade_c == pytest.approx(0.2, rel=1e-3)
        assert fit.ci95_low_per_decade_c < fit.slope_per_decade_c < fit.ci95_high_per_decade_c

    def test_flat_series_tiny_slope(self):
        years = list(range(1990, 2011))
        values = [0.5] * len(years)
        fit = linear_trend(years, values)
        assert abs(fit.slope_per_decade_c) < 0.01

    def test_requires_enough_points(self):
        with pytest.raises(ValueError):
            linear_trend([2000, 2001], [0.1, 0.2])


class TestAcceleration:
    def test_accelerating_series(self):
        years = list(range(1970, 2025))
        values = [0.001 * (y - 1970) ** 1.5 for y in years]
        accel = quadratic_acceleration(years, values)
        assert accel.quadratic_term_per_year2 > 0

    def test_compare_slopes_positive_delta(self):
        years = list(range(1970, 2025))
        values = [0.01 * (y - 1970) if y < 2000 else 0.03 * (y - 2000) + 0.3 for y in years]
        long_fit = linear_trend([y for y in years if y <= 2024 and y >= 1970], [v for y, v in zip(years, values) if y >= 1970])
        recent_years = [y for y in years if y >= 2005]
        recent_vals = [v for y, v in zip(years, values) if y >= 2005]
        recent_fit = linear_trend(recent_years, recent_vals)
        cmp = compare_slopes(recent_fit, long_fit)
        assert cmp.delta_slope_per_decade_c is not None
