"""Chart (a): global warming — aligned annual anomalies and trends."""

from __future__ import annotations

from typing import Any, Sequence

from earth_watch.fetchers.base import SourceRecord
from earth_watch.sources import (
    BERKELEY_LAND_OCEAN,
    GISTEMP_GLOBAL,
    HADCRUT5_GLOBAL_ANNUAL,
)
from earth_watch.trends.ols import TrendFit, compare_slopes, linear_trend, quadratic_acceleration

CHART_A_SOURCE_ID = "chart_a_warming"
CHART_A_LATEST_KEY = "aggregates/latest/chart_a_warming.json"

COMMON_BASELINE_LABEL = "1951-1980"
COMMON_BASELINE_START = 1951
COMMON_BASELINE_END = 1980
LONG_TREND_START = 1970
RECENT_WINDOW_YEARS = 20

_DATASET_META = {
    GISTEMP_GLOBAL.source_id: {
        "label": "NASA GISTEMP v4 global",
        "url": GISTEMP_GLOBAL.url,
        "license": "NASA open data policy (see data.giss.nasa.gov)",
        "native_baseline": "1951-1980",
    },
    HADCRUT5_GLOBAL_ANNUAL.source_id: {
        "label": "Met Office HadCRUT5 global",
        "url": HADCRUT5_GLOBAL_ANNUAL.url,
        "license": "Open Government Licence v3.0 (Met Office)",
        "native_baseline": "1961-1990",
    },
    BERKELEY_LAND_OCEAN.source_id: {
        "label": "Berkeley Earth land+ocean (air above sea ice)",
        "url": BERKELEY_LAND_OCEAN.url,
        "license": "Berkeley Earth open data (see berkeleyearth.org)",
        "native_baseline": "1951-1980",
    },
}


def _record_by_id(records: Sequence[SourceRecord]) -> dict[str, SourceRecord]:
    return {r.spec.source_id: r for r in records}


def _rebaseline_offset(values_by_year: dict[int, float], native_baseline: str) -> float:
    if native_baseline == COMMON_BASELINE_LABEL:
        return 0.0
    baseline_vals = [
        values_by_year[y]
        for y in range(COMMON_BASELINE_START, COMMON_BASELINE_END + 1)
        if y in values_by_year
    ]
    if len(baseline_vals) < 20:
        raise ValueError(f"insufficient baseline years for {native_baseline}")
    return -sum(baseline_vals) / len(baseline_vals)


def _annual_gistemp(record: SourceRecord) -> dict[int, float]:
    out: dict[int, float] = {}
    for row in record.frame:
        jd = row.get("J-D")
        if jd is not None:
            out[int(row["Year"])] = float(jd)
    return out


def _annual_hadcrut(record: SourceRecord) -> dict[int, float]:
    return {int(r["year"]): float(r["anomaly_c"]) for r in record.frame}


def _annual_berkeley(record: SourceRecord) -> dict[int, float]:
    return {int(r["year"]): float(r["anomaly_c"]) for r in record.frame}


def _align_annual(values: dict[int, float], offset: float) -> list[dict[str, Any]]:
    years = sorted(values)
    return [
        {"year": y, "anomaly_c": round(values[y] + offset, 4)}
        for y in years
    ]


def _trend_dict(fit: TrendFit) -> dict[str, Any]:
    return {
        "year_start": fit.year_start,
        "year_end": fit.year_end,
        "n": fit.n,
        "slope_per_decade_c": round(fit.slope_per_decade_c, 5),
        "ci95_low_per_decade_c": round(fit.ci95_low_per_decade_c, 5),
        "ci95_high_per_decade_c": round(fit.ci95_high_per_decade_c, 5),
        "ar1_rho": round(fit.ar1_rho, 4),
        "effective_n": round(fit.effective_n, 2),
    }


def _trend_line(fit: TrendFit, years: list[int]) -> list[dict[str, float]]:
    points = []
    for y in years:
        val = fit.intercept_c + fit.slope_per_year_c * y
        se_annual = fit.residual_std_c
        half_band = 1.96 * se_annual
        points.append(
            {
                "year": y,
                "trend_c": round(val, 4),
                "band_low_c": round(val - half_band, 4),
                "band_high_c": round(val + half_band, 4),
            }
        )
    return points


def _fit_windows(annual: list[dict[str, Any]]) -> tuple[TrendFit, TrendFit]:
    by_year = {p["year"]: p["anomaly_c"] for p in annual}
    max_year = max(by_year)
    long_years = [y for y in range(LONG_TREND_START, max_year + 1) if y in by_year]
    long_vals = [by_year[y] for y in long_years]
    long_fit = linear_trend(long_years, long_vals)

    recent_start = max_year - RECENT_WINDOW_YEARS + 1
    recent_years = [y for y in range(recent_start, max_year + 1) if y in by_year]
    recent_vals = [by_year[y] for y in recent_years]
    recent_fit = linear_trend(recent_years, recent_vals)
    return long_fit, recent_fit


def build_chart_a_payload(records: Sequence[SourceRecord]) -> dict[str, Any]:
    by_id = _record_by_id(records)
    required = (
        GISTEMP_GLOBAL.source_id,
        HADCRUT5_GLOBAL_ANNUAL.source_id,
        BERKELEY_LAND_OCEAN.source_id,
    )
    for source_id in required:
        if source_id not in by_id:
            raise ValueError(f"missing source record {source_id}")

    extractors = {
        GISTEMP_GLOBAL.source_id: _annual_gistemp,
        HADCRUT5_GLOBAL_ANNUAL.source_id: _annual_hadcrut,
        BERKELEY_LAND_OCEAN.source_id: _annual_berkeley,
    }

    series_out: list[dict[str, Any]] = []
    acceleration: dict[str, Any] = {}
    interpretation_facts: list[str] = []

    for source_id in (
        GISTEMP_GLOBAL.source_id,
        HADCRUT5_GLOBAL_ANNUAL.source_id,
        BERKELEY_LAND_OCEAN.source_id,
    ):
        meta = _DATASET_META[source_id]
        raw = extractors[source_id](by_id[source_id])
        offset = _rebaseline_offset(raw, meta["native_baseline"])
        annual = _align_annual(raw, offset)
        long_fit, recent_fit = _fit_windows(annual)
        plot_years = [p["year"] for p in annual if p["year"] >= LONG_TREND_START]
        quad = quadratic_acceleration(
            [p["year"] for p in annual if p["year"] >= LONG_TREND_START],
            [p["anomaly_c"] for p in annual if p["year"] >= LONG_TREND_START],
        )
        cmp = compare_slopes(recent_fit, long_fit)
        acceleration[source_id] = {
            "recent_minus_long_slope_per_decade_c": round(cmp.delta_slope_per_decade_c, 5),
            "ci95_low_per_decade_c": round(cmp.ci95_low_per_decade_c, 5),
            "ci95_high_per_decade_c": round(cmp.ci95_high_per_decade_c, 5),
            "intervals_separate": cmp.intervals_separate,
            "quadratic_term_per_year2": round(quad.quadratic_term_per_year2, 8),
            "quadratic_ci95_low_per_year2": round(quad.ci95_low_per_year2, 8),
            "quadratic_ci95_high_per_year2": round(quad.ci95_high_per_year2, 8),
        }
        latest = annual[-1]
        interpretation_facts.append(
            f"{meta['label']}: {long_fit.year_start}–{long_fit.year_end} trend "
            f"{long_fit.slope_per_decade_c:.2f} °C/decade "
            f"(95% CI {long_fit.ci95_low_per_decade_c:.2f} to {long_fit.ci95_high_per_decade_c:.2f}); "
            f"last {RECENT_WINDOW_YEARS} years {recent_fit.slope_per_decade_c:.2f} °C/decade "
            f"(95% CI {recent_fit.ci95_low_per_decade_c:.2f} to {recent_fit.ci95_high_per_decade_c:.2f})."
        )
        series_out.append(
            {
                "source_id": source_id,
                "label": meta["label"],
                "url": meta["url"],
                "license": meta["license"],
                "native_baseline": meta["native_baseline"],
                "rebaseline_offset_c": round(offset, 5),
                "data_as_of_year": latest["year"],
                "annual": annual,
                "trends": {
                    "from_1970": _trend_dict(long_fit),
                    "recent_20y": _trend_dict(recent_fit),
                },
                "trend_lines": {
                    "from_1970": _trend_line(long_fit, plot_years),
                },
            }
        )

    any_accel = any(acceleration[s]["intervals_separate"] for s in acceleration)
    read = (
        "All three global temperature records show warming since 1970. "
        f"Recent {RECENT_WINDOW_YEARS}-year slopes are compared with the longer 1970–present fit; "
        "acceleration is only suggested when those trend intervals do not overlap."
    )
    if not any_accel:
        read += " With current data, the recent and long-window trend intervals overlap for every series."

    return {
        "chart": "a_warming",
        "baseline": {
            "label": COMMON_BASELINE_LABEL,
            "start_year": COMMON_BASELINE_START,
            "end_year": COMMON_BASELINE_END,
            "method": "subtract mean native anomalies over baseline years when native period differs",
        },
        "series": series_out,
        "acceleration": acceleration,
        "facts": interpretation_facts,
        "read": read,
    }


def chart_a_json_bytes(payload: dict[str, Any]) -> bytes:
    import json

    return (json.dumps(payload, indent=2, sort_keys=True) + "\n").encode("utf-8")
