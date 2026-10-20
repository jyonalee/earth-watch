"""Per-source cadence, last-observation extraction, and stale thresholds."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Literal

from earth_watch.fetchers.base import SourceRecord

Cadence = Literal["monthly", "annual", "gcb"]

STALE_THRESHOLD_MONTHS: dict[Cadence, int] = {
    "monthly": 4,
    "annual": 20,
    "gcb": 24,
}

SOURCE_CADENCE: dict[str, Cadence] = {
    "gml_co2_annmean_mlo": "annual",
    "gml_co2_gr_mlo": "annual",
    "gml_co2_mm_mlo": "monthly",
    "gml_co2_gr_global": "annual",
    "gistemp_glb_ts_dsst": "monthly",
    "hadcrut5_global_monthly": "monthly",
    "hadcrut5_global_annual": "annual",
    "berkeley_earth_land_ocean": "annual",
    "gcb_global_budget_2025": "gcb",
    "ncei_ohc_0_700m_yearly": "annual",
    "ncei_ohc_0_2000m_yearly": "annual",
    "ncei_cag_ocean_sst": "annual",
}

SOURCE_KNOWN_LAG: dict[str, bool] = {
    "berkeley_earth_land_ocean": True,
}


def known_lag_for_source(source_id: str) -> bool:
    return SOURCE_KNOWN_LAG.get(source_id, False)


@dataclass(frozen=True, slots=True)
class LastDataPoint:
    year: int
    month: int | None = None

    def as_dict(self) -> dict[str, int]:
        if self.month is None:
            return {"year": self.year}
        return {"year": self.year, "month": self.month}


def cadence_for_source(source_id: str) -> Cadence:
    return SOURCE_CADENCE.get(source_id, "annual")


def stale_threshold_months(cadence: Cadence) -> int:
    return STALE_THRESHOLD_MONTHS[cadence]


def _months_since(point: LastDataPoint, as_of: datetime) -> float:
    as_of_ym = as_of.year * 12 + as_of.month
    if point.month is None:
        point_ym = point.year * 12 + 12
    else:
        point_ym = point.year * 12 + point.month
    return float(as_of_ym - point_ym)


def is_stale(
    point: LastDataPoint | None,
    *,
    cadence: Cadence,
    as_of: datetime,
) -> bool:
    if point is None:
        return True
    return _months_since(point, as_of) > stale_threshold_months(cadence)


def last_data_point_from_record(record: SourceRecord) -> LastDataPoint | None:
    return last_data_point_from_frame(record.spec.source_id, record.frame)


_GISTEMP_MONTH_COLS = (
    "Jan",
    "Feb",
    "Mar",
    "Apr",
    "May",
    "Jun",
    "Jul",
    "Aug",
    "Sep",
    "Oct",
    "Nov",
    "Dec",
)


def _gistemp_last_data_point(frame: list[dict[str, Any]]) -> LastDataPoint | None:
    if not frame:
        return None
    latest_year = max(int(row["Year"]) for row in frame)
    latest_row = next(row for row in reversed(frame) if int(row["Year"]) == latest_year)
    last_month: int | None = None
    for month_name, month_num in zip(_GISTEMP_MONTH_COLS, range(1, 13), strict=True):
        if latest_row.get(month_name) is not None:
            last_month = month_num
    if last_month is None:
        return None
    return LastDataPoint(year=latest_year, month=last_month)


def last_data_point_from_frame(source_id: str, frame: Any) -> LastDataPoint | None:
    if source_id == "gistemp_glb_ts_dsst":
        if isinstance(frame, list):
            return _gistemp_last_data_point(frame)
        return None

    if source_id == "ncei_cag_ocean_sst":
        monthly = frame.get("monthly") or []
        annual = frame.get("annual") or []
        if monthly:
            last = monthly[-1]
            return LastDataPoint(year=int(last["year"]), month=int(last["month"]))
        if annual:
            return LastDataPoint(year=int(annual[-1]["year"]))
        return None

    if isinstance(frame, list):
        if not frame:
            return None
        last = frame[-1]
        if "month" in last and last.get("month") is not None:
            return LastDataPoint(year=int(last["year"]), month=int(last["month"]))
        if "year" in last:
            return LastDataPoint(year=int(last["year"]))
        return None

    if isinstance(frame, dict):
        annual = frame.get("annual")
        if isinstance(annual, list) and annual:
            return LastDataPoint(year=int(annual[-1]["year"]))
    return None
