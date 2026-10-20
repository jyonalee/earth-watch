"""NOAA NCEI Climate at a Glance — global ocean temperature JSON."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any

from earth_watch.fetchers.base import (
    AsyncBytesFetcher,
    BaseFetcher,
    FetchResult,
    SourceRecord,
    SourceValidationError,
)
from earth_watch.sources import NCEI_CAG_OCEAN_ANNUAL, SourceSpec

_CAG_BASE = (
    "https://www.ncei.noaa.gov/access/monitoring/climate-at-a-glance/global/time-series/globe/ocean"
)


def _parse_cag_json(content: bytes) -> dict[str, Any]:
    try:
        payload = json.loads(content.decode("utf-8"))
    except json.JSONDecodeError as exc:
        raise SourceValidationError(f"cag: invalid json: {exc}") from exc
    if "data" not in payload or not isinstance(payload["data"], dict):
        raise SourceValidationError("cag: missing data object")
    return payload


def _anomaly_value(value: Any) -> float | None:
    if value is None or value == "":
        return None
    if isinstance(value, dict):
        raw = value.get("departure")
        if raw is None:
            return None
        return float(raw)
    return float(value)


def _annual_rows(data: dict[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for key, value in data.items():
        anomaly = _anomaly_value(value)
        if anomaly is None:
            continue
        text = str(key).strip()
        if len(text) != 4:
            continue
        rows.append({"year": int(text), "month": None, "anomaly_c": anomaly})
    rows.sort(key=lambda r: r["year"])
    return rows


def _monthly_url(year: int, month: int) -> str:
    return f"{_CAG_BASE}/1/{month}/{year}-{year}.json"


class NceiCagOceanSstFetcher(BaseFetcher):
    """Annual global ocean SST from CAG plus monthly values for the latest complete year."""

    spec: SourceSpec = NCEI_CAG_OCEAN_ANNUAL

    def parse(self, content: bytes) -> dict[str, Any]:
        payload = _parse_cag_json(content)
        return {"annual": _annual_rows(payload["data"]), "monthly": []}

    def validate(self, frame: dict[str, Any]) -> None:
        annual = frame.get("annual") or []
        if len(annual) < 20:
            raise SourceValidationError(f"{self.spec.source_id}: too few annual points")
        anomalies = [r["anomaly_c"] for r in annual]
        if min(anomalies) < -5 or max(anomalies) > 5:
            raise SourceValidationError(f"{self.spec.source_id}: anomaly out of range")

    def compute_aggregates(self, frame: dict[str, Any]) -> dict[str, Any]:
        annual = frame["annual"]
        monthly = frame.get("monthly") or []
        latest_a = annual[-1]
        out: dict[str, Any] = {
            "baseline": "1901-2000",
            "latest_annual": {"year": latest_a["year"], "anomaly_c": latest_a["anomaly_c"]},
        }
        if monthly:
            latest_m = monthly[-1]
            out["latest_month"] = {
                "year": latest_m["year"],
                "month": latest_m["month"],
                "anomaly_c": latest_m["anomaly_c"],
            }
        return out

    async def run_async(self, get_bytes: AsyncBytesFetcher) -> SourceRecord:
        annual_content = await get_bytes(self.spec.url)
        fetched_at = datetime.now(timezone.utc)
        fetch = FetchResult.from_bytes(self.spec, annual_content, fetched_at)
        frame = self.parse(annual_content)
        run_year = datetime.now(timezone.utc).year - 1
        monthly_rows: list[dict[str, Any]] = []
        for month in range(1, 13):
            url = _monthly_url(run_year, month)
            try:
                content = await get_bytes(url)
            except SourceValidationError:
                continue
            payload = _parse_cag_json(content)
            for key, value in payload["data"].items():
                anomaly = _anomaly_value(value)
                if anomaly is None:
                    continue
                text = str(key).strip()
                if len(text) == 4:
                    monthly_rows.append(
                        {"year": int(text), "month": month, "anomaly_c": anomaly}
                    )
                elif len(text) == 6:
                    monthly_rows.append(
                        {
                            "year": int(text[:4]),
                            "month": int(text[4:6]),
                            "anomaly_c": anomaly,
                        }
                    )
        frame["monthly"] = sorted(monthly_rows, key=lambda r: (r["year"], r["month"] or 0))
        self.validate(frame)
        aggregates = self.compute_aggregates(frame)
        return SourceRecord(spec=self.spec, fetch=fetch, frame=frame, aggregates=aggregates)
