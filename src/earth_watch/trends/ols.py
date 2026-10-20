"""Ordinary least squares with AR(1)-adjusted slope uncertainty (stdlib only)."""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Sequence


@dataclass(frozen=True, slots=True)
class TrendFit:
    year_start: int
    year_end: int
    n: int
    slope_per_year_c: float
    intercept_c: float
    slope_per_decade_c: float
    ci95_low_per_decade_c: float
    ci95_high_per_decade_c: float
    ar1_rho: float
    effective_n: float
    residual_std_c: float


@dataclass(frozen=True, slots=True)
class SlopeComparison:
    delta_slope_per_decade_c: float
    ci95_low_per_decade_c: float
    ci95_high_per_decade_c: float
    intervals_separate: bool


@dataclass(frozen=True, slots=True)
class QuadraticAcceleration:
    quadratic_term_per_year2: float
    ci95_low_per_year2: float
    ci95_high_per_year2: float
    linear_term_per_year_c: float


def _t_critical_95(df: float) -> float:
    if df >= 60:
        return 1.96
    table = {
        1: 12.706,
        2: 4.303,
        3: 3.182,
        4: 2.776,
        5: 2.571,
        10: 2.228,
        20: 2.086,
        30: 2.042,
        40: 2.021,
        50: 2.009,
    }
    df_int = max(1, min(50, int(df)))
    return table.get(df_int, 2.0)


def linear_trend(years: Sequence[int], values: Sequence[float]) -> TrendFit:
    if len(years) != len(values):
        raise ValueError("years and values length mismatch")
    n = len(years)
    if n < 3:
        raise ValueError("need at least 3 points for trend")

    x = [float(y) for y in years]
    y = [float(v) for v in values]
    x_mean = sum(x) / n
    y_mean = sum(y) / n
    sxx = sum((xi - x_mean) ** 2 for xi in x)
    if sxx <= 0:
        raise ValueError("degenerate x spread")

    slope = sum((xi - x_mean) * (yi - y_mean) for xi, yi in zip(x, y)) / sxx
    intercept = y_mean - slope * x_mean
    residuals = [yi - (intercept + slope * xi) for xi, yi in zip(x, y)]
    df = n - 2
    rss = sum(r * r for r in residuals)
    residual_std = math.sqrt(rss / df) if df > 0 else 0.0
    se_slope = math.sqrt(rss / df / sxx) if df > 0 else float("inf")

    rho = 0.0
    if n > 2 and rss > 0:
        rho = sum(residuals[i] * residuals[i - 1] for i in range(1, n)) / rss
        rho = max(-0.99, min(0.99, rho))

    if abs(rho) < 1.0:
        n_eff = n * (1.0 - rho) / (1.0 + rho)
    else:
        n_eff = float(n)
    n_eff = max(3.0, min(float(n), n_eff))

    se_adj = se_slope * math.sqrt(n / n_eff)
    t_crit = _t_critical_95(n_eff - 2)
    half_width_decade = t_crit * se_adj * 10.0
    slope_decade = slope * 10.0

    return TrendFit(
        year_start=int(min(years)),
        year_end=int(max(years)),
        n=n,
        slope_per_year_c=slope,
        intercept_c=intercept,
        slope_per_decade_c=slope_decade,
        ci95_low_per_decade_c=slope_decade - half_width_decade,
        ci95_high_per_decade_c=slope_decade + half_width_decade,
        ar1_rho=rho,
        effective_n=n_eff,
        residual_std_c=residual_std,
    )


def compare_slopes(recent: TrendFit, long: TrendFit) -> SlopeComparison:
    delta = recent.slope_per_decade_c - long.slope_per_decade_c
    se_recent = (recent.ci95_high_per_decade_c - recent.slope_per_decade_c) / 1.96
    se_long = (long.ci95_high_per_decade_c - long.slope_per_decade_c) / 1.96
    se_delta = math.sqrt(se_recent**2 + se_long**2)
    half = 1.96 * se_delta
    low = delta - half
    high = delta + half
    separate = (low > 0) or (high < 0)
    return SlopeComparison(
        delta_slope_per_decade_c=delta,
        ci95_low_per_decade_c=low,
        ci95_high_per_decade_c=high,
        intervals_separate=separate,
    )


def quadratic_acceleration(years: Sequence[int], values: Sequence[float]) -> QuadraticAcceleration:
    n = len(years)
    if n < 5:
        raise ValueError("need at least 5 points for quadratic fit")
    x = [float(y) for y in years]
    y = [float(v) for v in values]

    s0 = float(n)
    s1 = sum(x)
    s2 = sum(xi * xi for xi in x)
    s3 = sum(xi * xi * xi for xi in x)
    s4 = sum(xi**4 for xi in x)
    sy = sum(y)
    sxy = sum(xi * yi for xi, yi in zip(x, y))
    sx2y = sum(xi * xi * yi for xi, yi in zip(x, y))

    def det3(
        a11: float,
        a12: float,
        a13: float,
        a21: float,
        a22: float,
        a23: float,
        a31: float,
        a32: float,
        a33: float,
    ) -> float:
        return (
            a11 * (a22 * a33 - a23 * a32)
            - a12 * (a21 * a33 - a23 * a31)
            + a13 * (a21 * a32 - a22 * a31)
        )

    m_det = det3(s0, s1, s2, s1, s2, s3, s2, s3, s4)
    if abs(m_det) < 1e-12:
        raise ValueError("singular normal equations")

    a = det3(sy, s1, s2, sxy, s2, s3, sx2y, s3, s4) / m_det
    b = det3(s0, sy, s2, s1, sxy, s3, s2, sx2y, s4) / m_det
    c = det3(s0, s1, sy, s1, s2, sxy, s2, s3, sx2y) / m_det

    fitted = [a + b * xi + c * xi * xi for xi in x]
    residuals = [yi - fi for yi, fi in zip(y, fitted)]
    df = n - 3
    rss = sum(r * r for r in residuals)
    if df <= 0 or rss <= 0:
        return QuadraticAcceleration(
            quadratic_term_per_year2=c,
            ci95_low_per_year2=c,
            ci95_high_per_year2=c,
            linear_term_per_year_c=b,
        )

    xtx = [[s0, s1, s2], [s1, s2, s3], [s2, s3, s4]]
    inv = _invert_3x3(xtx)
    sigma2 = rss / df
    var_c = sigma2 * inv[2][2]
    se_c = math.sqrt(max(var_c, 0.0))
    t_crit = _t_critical_95(df)
    return QuadraticAcceleration(
        quadratic_term_per_year2=c,
        ci95_low_per_year2=c - t_crit * se_c,
        ci95_high_per_year2=c + t_crit * se_c,
        linear_term_per_year_c=b,
    )


def _invert_3x3(m: list[list[float]]) -> list[list[float]]:
    det = _det3(m)
    if abs(det) < 1e-15:
        raise ValueError("singular matrix")
    inv_det = 1.0 / det
    return [
        [
            inv_det
            * (
                m[1][1] * m[2][2]
                - m[1][2] * m[2][1]
            ),
            inv_det
            * (
                -(m[0][1] * m[2][2] - m[0][2] * m[2][1])
            ),
            inv_det
            * (
                m[0][1] * m[1][2] - m[0][2] * m[1][1]
            ),
        ],
        [
            inv_det
            * (
                -(m[1][0] * m[2][2] - m[1][2] * m[2][0])
            ),
            inv_det
            * (
                m[0][0] * m[2][2] - m[0][2] * m[2][0]
            ),
            inv_det
            * (
                -(m[0][0] * m[1][2] - m[0][2] * m[1][0])
            ),
        ],
        [
            inv_det
            * (
                m[1][0] * m[2][1] - m[1][1] * m[2][0]
            ),
            inv_det
            * (
                -(m[0][0] * m[2][1] - m[0][1] * m[2][0])
            ),
            inv_det
            * (
                m[0][0] * m[1][1] - m[0][1] * m[1][0]
            ),
        ],
    ]


def _det3(m: list[list[float]]) -> float:
    return (
        m[0][0] * (m[1][1] * m[2][2] - m[1][2] * m[2][1])
        - m[0][1] * (m[1][0] * m[2][2] - m[1][2] * m[2][0])
        + m[0][2] * (m[1][0] * m[2][1] - m[1][1] * m[2][0])
    )
