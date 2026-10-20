"""Trend estimation for Earth Watch charts."""

from earth_watch.trends.ols import TrendFit, compare_slopes, linear_trend, quadratic_acceleration

__all__ = [
    "TrendFit",
    "compare_slopes",
    "linear_trend",
    "quadratic_acceleration",
]
