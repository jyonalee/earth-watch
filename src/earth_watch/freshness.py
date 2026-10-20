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
    "gistemp_glb_ts_dsst": "annual",
    "hadcrut5_global_monthly": "monthly",
    "hadcrut5_global_annual": "annual",
    "berkeley_earth_land_ocean": "annual",
    "gcb_global_budget_2025": "gcb",
    "ncei_ohc_0_700m_yearly": "annual",
    "ncei_ohc_0_2000m_yearly": "annual",
    "ncei_cag_ocean_sst": "annual",
}


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


def last_data_point_from_frame(source_id: str, frame: Any) -> LastDataPoint | None:
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
