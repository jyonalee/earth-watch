"""Chart (c): where the heat goes — OHC and global ocean SST."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Sequence

from earth_watch.fetchers.base import SourceRecord
from earth_watch.ocean_physics import (
    HEATING_RATE_CITATION,
    ohc_slope_1e22j_per_year_to_w_m2,
    ohc_slope_1e22j_per_year_to_zj_per_year,
)
from earth_watch.sources import (
    NCEI_CAG_OCEAN_ANNUAL,
    NCEI_OHC_0_2000M_YEARLY,
    NCEI_OHC_0_700M_YEARLY,
)
from earth_watch.trends.ols import TrendFit, compare_slopes, fitted_line_points, linear_trend

CHART_C_LATEST_KEY = "aggregates/latest/chart_c_ocean_heat.json"
RECENT_WINDOW_YEARS = 20

_OHC_700_META = {
    "label": "NOAA NCEI global ocean heat content 0–700 m",
    "url": NCEI_OHC_0_700M_YEARLY.url,
    "license": "NOAA / U.S. Government (see ncei.noaa.gov)",
}
_OHC_2000_META = {
    "label": "NOAA NCEI global ocean heat content 0–2000 m",
    "url": NCEI_OHC_0_2000M_YEARLY.url,
    "license": "NOAA / U.S. Government (see ncei.noaa.gov)",
}
_SST_META = {
    "label": "NOAA NCEI Climate at a Glance — global ocean SST anomaly",
    "url": NCEI_CAG_OCEAN_ANNUAL.url,
    "license": "NOAA / U.S. Government (Climate at a Glance terms)",
    "baseline": "1901-2000",
}


def _record_by_id(records: Sequence[SourceRecord]) -> dict[str, SourceRecord]:
    return {r.spec.source_id: r for r in records}


def _complete_years(years: list[int], run_at: datetime) -> list[int]:
    cap = run_at.astimezone(timezone.utc).year - 1
    return sorted(y for y in years if y <= cap)


def _ohc_series(record: SourceRecord, complete: list[int]) -> list[dict[str, Any]]:
    by_year = {int(r["year"]): r for r in record.frame}
    return [
        {
            "year": y,
            "ohc_1e22j": round(float(by_year[y]["ohc_1e22j"]), 4),
            "sigma_1e22j": round(float(by_year[y]["sigma_1e22j"]), 4),
        }
        for y in complete
        if y in by_year
    ]


def _trend_block(years: list[int], values: list[float], trend_start: int) -> dict[str, Any]:
    ty = [y for y in years if y >= trend_start]
    tv = [values[years.index(y)] for y in ty]
    fit = linear_trend(ty, tv)
    recent_start = max(ty) - RECENT_WINDOW_YEARS + 1
    ry = [y for y in ty if y >= recent_start]
    rv = [values[years.index(y)] for y in ry]
    recent_fit = linear_trend(ry, rv)
    cmp = compare_slopes(recent_fit, fit)
    long_out = _fit_summary(fit, values_are_ohc=True)
    long_out["trend_line"] = fitted_line_points(fit, ty)
    return {
        "trend_start_year": trend_start,
        "long": long_out,
        "recent_20y": _fit_summary(recent_fit, values_are_ohc=True),
        "acceleration": {
            "recent_minus_long_slope_per_decade": round(cmp.delta_slope_per_decade_c, 5),
            "ci95_low_per_decade": round(cmp.ci95_low_per_decade_c, 5),
            "ci95_high_per_decade": round(cmp.ci95_high_per_decade_c, 5),
            "intervals_separate": cmp.intervals_separate,
        },
    }


def _fit_summary(fit: TrendFit, *, values_are_ohc: bool) -> dict[str, Any]:
    out: dict[str, Any] = {
        "year_start": fit.year_start,
        "year_end": fit.year_end,
        "slope_per_year": round(fit.slope_per_year_c, 5),
        "slope_per_decade": round(fit.slope_per_decade_c, 5),
        "ci95_low_per_decade": round(fit.ci95_low_per_decade_c, 5),
        "ci95_high_per_decade": round(fit.ci95_high_per_decade_c, 5),
    }
    if values_are_ohc:
        out["slope_zj_per_year"] = round(ohc_slope_1e22j_per_year_to_zj_per_year(fit.slope_per_year_c), 4)
        out["heating_rate_w_m2"] = round(ohc_slope_1e22j_per_year_to_w_m2(fit.slope_per_year_c), 4)
    return out


def _monthly_to_annual_rows(annual: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {"year": r["year"], "month": 12, "anomaly_c": r["anomaly_c"]}
        for r in annual[-1:]
    ]


def _monthly_to_annual(monthly: list[dict[str, Any]], complete: list[int]) -> list[dict[str, Any]]:
    by_year_month: dict[tuple[int, int], float] = {}
    for row in monthly:
        if row["month"] is None:
            continue
        by_year_month[(int(row["year"]), int(row["month"]))] = float(row["anomaly_c"])
    annual: list[dict[str, Any]] = []
    for year in complete:
        vals = [by_year_month[(year, m)] for m in range(1, 13) if (year, m) in by_year_month]
        if len(vals) != 12:
            continue
        annual.append({"year": year, "anomaly_c": round(sum(vals) / 12, 4)})
    return annual


def _latest_months(monthly: list[dict[str, Any]], count: int = 6) -> list[dict[str, Any]]:
    rows = [r for r in monthly if r["month"] is not None]
    rows.sort(key=lambda r: (r["year"], r["month"]))
    tail = rows[-count:]
    return [
        {
            "year": r["year"],
            "month": r["month"],
            "anomaly_c": round(float(r["anomaly_c"]), 4),
            "note": "anomaly vs 1901-2000 climatology (NCEI published departure)",
        }
        for r in tail
    ]


def build_chart_c_payload(
    records: Sequence[SourceRecord],
    run_at: datetime | None = None,
) -> dict[str, Any]:
    run_at = run_at or datetime.now(timezone.utc)
    by_id = _record_by_id(records)
    required = (
        NCEI_OHC_0_700M_YEARLY.source_id,
        NCEI_OHC_0_2000M_YEARLY.source_id,
        NCEI_CAG_OCEAN_ANNUAL.source_id,
    )
    for sid in required:
        if sid not in by_id:
            raise ValueError(f"missing source record {sid}")

    ohc700_raw = [int(r["year"]) for r in by_id[NCEI_OHC_0_700M_YEARLY.source_id].frame]
    ohc2000_raw = [int(r["year"]) for r in by_id[NCEI_OHC_0_2000M_YEARLY.source_id].frame]
    complete = _complete_years(sorted(set(ohc700_raw) & set(ohc2000_raw)), run_at)

    sst_frame = by_id[NCEI_CAG_OCEAN_ANNUAL.source_id].frame
    sst_annual_raw = sst_frame["annual"]
    sst_complete = _complete_years([int(r["year"]) for r in sst_annual_raw], run_at)
    sst_annual = [
        {"year": r["year"], "anomaly_c": round(float(r["anomaly_c"]), 4)}
        for r in sst_annual_raw
        if r["year"] in sst_complete
    ]
    monthly = sst_frame.get("monthly") or []
    if not monthly and sst_annual:
        monthly = _monthly_to_annual_rows(sst_annual)
    if not sst_annual:
        raise ValueError("no complete SST annual years")

    last_complete = min(complete[-1], sst_annual[-1]["year"])
    aligned = [y for y in complete if y <= last_complete]

    ohc700 = _ohc_series(by_id[NCEI_OHC_0_700M_YEARLY.source_id], aligned)
    ohc2000 = _ohc_series(by_id[NCEI_OHC_0_2000M_YEARLY.source_id], aligned)

    y700 = [r["year"] for r in ohc700]
    v700 = [r["ohc_1e22j"] for r in ohc700]
    y2000 = [r["year"] for r in ohc2000]
    v2000 = [r["ohc_1e22j"] for r in ohc2000]

    trend700 = _trend_block(y700, v700, trend_start=1970)
    trend2000 = _trend_block(y2000, v2000, trend_start=y2000[0])

    sst_years = [r["year"] for r in sst_annual]
    sst_vals = [r["anomaly_c"] for r in sst_annual]
    sst_fit = linear_trend([y for y in sst_years if y >= 1970], [v for y, v in zip(sst_years, sst_vals) if y >= 1970])

    latest_months = _latest_months(monthly)

    facts = [
        (
            f"Through complete year {last_complete}, global 0–2000 m OHC reached "
            f"{ohc2000[-1]['ohc_1e22j']:.2f}×10²² J "
            f"(±{ohc2000[-1]['sigma_1e22j']:.2f}×10²² J, 1σ)."
        ),
        (
            f"0–2000 m OHC trend {trend2000['long']['year_start']}–{trend2000['long']['year_end']}: "
            f"{trend2000['long']['slope_zj_per_year']:.2f} ZJ yr⁻¹ "
            f"({trend2000['long']['heating_rate_w_m2']:.3f} W m⁻²); "
            f"95% CI on slope {trend2000['long']['ci95_low_per_decade']:.2f} to "
            f"{trend2000['long']['ci95_high_per_decade']:.2f} (10²² J decade⁻¹)."
        ),
        (
            f"Global ocean SST anomaly (1901–2000 baseline): latest annual {sst_annual[-1]['anomaly_c']:.2f} °C "
            f"({sst_annual[-1]['year']}); trend since 1970 {sst_fit.slope_per_decade_c:.3f} °C decade⁻¹ "
            f"(95% CI {sst_fit.ci95_low_per_decade_c:.3f} to {sst_fit.ci95_high_per_decade_c:.3f})."
        ),
    ]

    accel = trend2000["acceleration"]
    if accel["intervals_separate"] and accel["recent_minus_long_slope_per_decade"] > 0:
        read = (
            "Most excess heat goes into the ocean. The 0–2000 m heat content trend has strengthened in the "
            "last 20 years compared with the longer record (non-overlapping 95% CIs on the slope difference)."
        )
    elif accel["intervals_separate"] and accel["recent_minus_long_slope_per_decade"] < 0:
        read = (
            "Ocean heat content is still rising, but the recent 20-year OHC trend is slower than the longer "
            "record suggests (slope-difference 95% CIs do not overlap)."
        )
    else:
        read = (
            "Most excess heat goes into the ocean. The 0–2000 m heat content series shows a sustained rise; "
            "recent and long-window OHC trend uncertainties overlap, so clear acceleration is not established."
        )

    return {
        "chart": "c_ocean_heat",
        "last_complete_year": last_complete,
        "heating_rate_citation": HEATING_RATE_CITATION,
        "sources": [_OHC_700_META, _OHC_2000_META, _SST_META],
        "ohc": {
            "units": "10^22 J",
            "0_700m": {"annual": ohc700, "trends": trend700},
            "0_2000m": {"annual": ohc2000, "trends": trend2000},
        },
        "sst": {
            "baseline": "1901-2000",
            "annual": sst_annual,
            "latest_months": latest_months,
            "trend_since_1970": _fit_summary(sst_fit, values_are_ohc=False),
        },
        "facts": facts,
        "read": read,
    }


def chart_c_json_bytes(payload: dict[str, Any]) -> bytes:
    import json

    return (json.dumps(payload, indent=2, sort_keys=True) + "\n").encode("utf-8")
