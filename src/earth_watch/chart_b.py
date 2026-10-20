"""Chart (b): airborne fraction — emissions vs atmospheric growth."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Sequence

from earth_watch.airborne import (
    SMOOTHING_WINDOW_YEARS,
    airborne_fraction,
    airborne_fraction_fossil_only,
    airborne_fraction_sigma,
    centered_mean,
    chart_b_years,
    emissions_sigma_gtc,
    growth_ppm_to_gtc,
)
from earth_watch.constants import PPM_CO2_TO_GTC, PPM_CO2_TO_GTC_CITATION
from earth_watch.fetchers.base import SourceRecord
from earth_watch.sources import GCB_GLOBAL_BUDGET_2025, GML_CO2_GR_GLOBAL
from earth_watch.trends.ols import TrendFit, linear_trend

CHART_B_LATEST_KEY = "aggregates/latest/chart_b_airborne_fraction.json"
TREND_START_YEAR = 1960
# When 95% CI includes zero but the lower bound is within this many pp/decade of zero,
# describe a positive central estimate as a hint, not as a clearly flat share.
_CI_LOWER_NEAR_ZERO_PP = 0.5

_GCB_META = {
    "label": "Global Carbon Budget 2025",
    "url": GCB_GLOBAL_BUDGET_2025.url,
    "license": "GCB data use terms (see globalcarbonbudget.org)",
}
_GML_META = {
    "label": "NOAA GML global annual CO₂ increase",
    "url": GML_CO2_GR_GLOBAL.url,
    "license": "NOAA GML data policy (see gml.noaa.gov)",
}


def _record_by_id(records: Sequence[SourceRecord]) -> dict[str, SourceRecord]:
    return {r.spec.source_id: r for r in records}


def _gcb_by_year(record: SourceRecord) -> dict[int, dict[str, float]]:
    return {
        int(r["year"]): {
            "fossil_gtc": float(r["fossil_gtc"]),
            "land_use_gtc": float(r["land_use_gtc"]),
        }
        for r in record.frame
    }


def _gml_by_year(record: SourceRecord) -> dict[int, dict[str, float]]:
    return {
        int(r["year"]): {
            "growth_ppm": float(r["growth_ppm"]),
            "unc_ppm": float(r["unc_ppm"]),
        }
        for r in record.frame
    }


def _trend_dict(fit: TrendFit) -> dict[str, Any]:
    return {
        "year_start": fit.year_start,
        "year_end": fit.year_end,
        "n": fit.n,
        "slope_per_decade": round(fit.slope_per_decade_c, 5),
        "ci95_low_per_decade": round(fit.ci95_low_per_decade_c, 5),
        "ci95_high_per_decade": round(fit.ci95_high_per_decade_c, 5),
        "ar1_rho": round(fit.ar1_rho, 4),
        "effective_n": round(fit.effective_n, 2),
    }


def _read_from_trend(fit: TrendFit) -> str:
    low = fit.ci95_low_per_decade_c
    high = fit.ci95_high_per_decade_c
    low_pp = low * 100.0
    if low <= 0 <= high:
        if fit.slope_per_decade_c > 0 and low_pp >= -_CI_LOWER_NEAR_ZERO_PP:
            return (
                "Since 1960 the airborne-fraction trend is uncertain (the 95% confidence interval "
                "includes zero), but the data hint at a slowly rising share of emissions staying "
                "in the atmosphere—meaning natural sinks are weakening slightly. This is not yet "
                "statistically clear."
            )
        return (
            "The long-term trend in airborne fraction since 1960 is not distinguishable from zero "
            "(95% CI includes zero). Natural sinks are absorbing a roughly constant share of emissions."
        )
    if low > 0:
        return (
            "The airborne fraction has increased since 1960 (95% CI excludes zero). "
            "A rising share of emissions stays in the atmosphere, so sinks are not fully keeping pace."
        )
    return (
        "The airborne fraction has decreased since 1960 (95% CI excludes zero). "
        "Sinks have taken up a growing share of emissions over this period."
    )


def build_chart_b_payload(
    records: Sequence[SourceRecord],
    run_at: datetime | None = None,
) -> dict[str, Any]:
    run_at = run_at or datetime.now(timezone.utc)
    by_id = _record_by_id(records)
    for source_id in (GCB_GLOBAL_BUDGET_2025.source_id, GML_CO2_GR_GLOBAL.source_id):
        if source_id not in by_id:
            raise ValueError(f"missing source record {source_id}")

    gcb = _gcb_by_year(by_id[GCB_GLOBAL_BUDGET_2025.source_id])
    gml = _gml_by_year(by_id[GML_CO2_GR_GLOBAL.source_id])
    gcb_max = max(gcb)
    years = chart_b_years(
        set(gcb),
        set(gml),
        gcb_max_year=gcb_max,
        current_utc_year=run_at.astimezone(timezone.utc).year,
    )
    if not years:
        raise ValueError("no complete chart-b years")

    annual_rows: list[dict[str, Any]] = []
    af_values: list[float] = []
    af_fossil_values: list[float] = []

    for year in years:
        g = gml[year]
        e = gcb[year]
        growth_gtc = growth_ppm_to_gtc(g["growth_ppm"])
        growth_sigma = growth_ppm_to_gtc(g["unc_ppm"])
        fossil = e["fossil_gtc"]
        luc = e["land_use_gtc"]
        total = fossil + luc
        af = airborne_fraction(growth_gtc, fossil, luc)
        af_fossil = airborne_fraction_fossil_only(growth_gtc, fossil)
        em_sigma = emissions_sigma_gtc(fossil, luc)
        af_sigma = airborne_fraction_sigma(af, growth_gtc, growth_sigma, total, em_sigma)
        annual_rows.append(
            {
                "year": year,
                "growth_ppm": round(g["growth_ppm"], 3),
                "growth_gtc": round(growth_gtc, 4),
                "fossil_gtc": round(fossil, 4),
                "land_use_gtc": round(luc, 4),
                "emissions_gtc": round(total, 4),
                "land_use_sigma_gtc": 0.7,
                "airborne_fraction": round(af, 4),
                "airborne_fraction_sigma": round(af_sigma, 4),
                "airborne_fraction_fossil_only": round(af_fossil, 4),
            }
        )
        af_values.append(af)
        af_fossil_values.append(af_fossil)

    smoothed = centered_mean(af_values, SMOOTHING_WINDOW_YEARS)
    for i, row in enumerate(annual_rows):
        val = smoothed[i]
        row["airborne_fraction_smoothed_10y"] = round(val, 4) if val is not None else None

    trend_years = [y for y in years if y >= TREND_START_YEAR]
    trend_af = [annual_rows[years.index(y)]["airborne_fraction"] for y in trend_years]
    trend_fit = linear_trend(trend_years, trend_af)

    last_complete = years[-1]
    latest = annual_rows[-1]
    long_term_rows = [r for r in annual_rows if r["year"] >= TREND_START_YEAR]
    mean_af = sum(r["airborne_fraction"] for r in long_term_rows) / len(long_term_rows)
    smoothed_latest = None
    for row in reversed(annual_rows):
        val = row.get("airborne_fraction_smoothed_10y")
        if val is not None:
            smoothed_latest = val
            break

    facts = [
        (
            f"Through complete year {last_complete}, airborne fraction was "
            f"{latest['airborne_fraction']:.1%} "
            f"(±{latest['airborne_fraction_sigma']:.1%} 1σ) using global emissions and NOAA GML growth."
        ),
        (
            f"Long-term context (since {TREND_START_YEAR}): mean airborne fraction "
            f"{mean_af:.1%}; latest {SMOOTHING_WINDOW_YEARS}-year smoothed value "
            f"{smoothed_latest:.1%} (through {last_complete})."
            if smoothed_latest is not None
            else (
                f"Long-term context (since {TREND_START_YEAR}): mean airborne fraction {mean_af:.1%}."
            )
        ),
        (
            "Single years swing widely with El Niño/La Niña and fire seasons—a high year like 2024 "
            "does not by itself mark a new normal; compare the long-term mean and 10-year smooth."
        ),
        (
            f"Airborne fraction trend since {TREND_START_YEAR}: "
            f"{trend_fit.slope_per_decade_c * 100:.2f} percentage points per decade "
            f"(95% CI {trend_fit.ci95_low_per_decade_c * 100:.2f} to "
            f"{trend_fit.ci95_high_per_decade_c * 100:.2f})."
        ),
        (
            f"Land-use change emissions uncertainty (±0.7 GtC/yr, 1σ) dominates emission-side error; "
            f"latest land-use flux {latest['land_use_gtc']:.2f} GtC/yr vs fossil {latest['fossil_gtc']:.2f} GtC/yr."
        ),
    ]

    return {
        "chart": "b_airborne_fraction",
        "last_complete_year": last_complete,
        "ppm_to_gtc_factor": PPM_CO2_TO_GTC,
        "ppm_to_gtc_citation": PPM_CO2_TO_GTC_CITATION,
        "smoothing": {"method": "centered_mean", "window_years": SMOOTHING_WINDOW_YEARS},
        "sources": [_GCB_META, _GML_META],
        "annual": annual_rows,
        "trend": {
            "from_year": TREND_START_YEAR,
            "airborne_fraction": _trend_dict(trend_fit),
        },
        "facts": facts,
        "read": _read_from_trend(trend_fit),
    }


def chart_b_json_bytes(payload: dict[str, Any]) -> bytes:
    import json

    return (json.dumps(payload, indent=2, sort_keys=True) + "\n").encode("utf-8")
