"""95% CI of the OLS fitted line (trend uncertainty)."""

from __future__ import annotations

from earth_watch.trends.ols import fitted_line_points, linear_trend


def test_fitted_line_ci_narrows_at_center():
    years = list(range(1980, 2021))
    values = [0.02 * (y - 1980) + (0.05 if y % 3 else -0.03) for y in years]
    fit = linear_trend(years, values)
    pts = fitted_line_points(fit, [1985, 2000, 2020])
    widths = [p["band_high_c"] - p["band_low_c"] for p in pts]
    assert widths[1] < widths[0]
    assert widths[1] < widths[2]
    assert all(p.get("band_kind") == "trend_uncertainty" for p in pts)
