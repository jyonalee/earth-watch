"""Met Office HadCRUT5 global summary series."""

from __future__ import annotations

import csv
import io
from typing import Any

from earth_watch.fetchers.base import BaseFetcher, SourceValidationError
from earth_watch.sources import HADCRUT5_GLOBAL_ANNUAL, HADCRUT5_GLOBAL_MONTHLY

_ANNUAL_HEADER = (
    "Time,Anomaly (deg C),Lower confidence limit (2.5%),Upper confidence limit (97.5%)"
)
_MONTHLY_HEADER = _ANNUAL_HEADER


def _parse_row_time(time_raw: str) -> tuple[int, int | None]:
    text = time_raw.strip()
    if "-" in text:
        year_s, month_s = text.split("-", 1)
        return int(year_s), int(month_s)
    return int(text), None


class HadCrut5AnnualFetcher(BaseFetcher):
    spec = HADCRUT5_GLOBAL_ANNUAL

    def parse(self, content: bytes) -> list[dict[str, Any]]:
        text = content.decode("utf-8")
        lines = [line for line in text.splitlines() if line.strip()]
        if not lines or lines[0].strip() != _ANNUAL_HEADER:
            raise SourceValidationError(f"hadcrut5 annual: unexpected header {lines[0]!r}")
        reader = csv.DictReader(io.StringIO("\n".join(lines)))
        rows: list[dict[str, Any]] = []
        for row in reader:
            year, _ = _parse_row_time(row["Time"])
            rows.append(
                {
                    "year": year,
                    "anomaly_c": float(row["Anomaly (deg C)"]),
                    "lower_95_c": float(row["Lower confidence limit (2.5%)"]),
                    "upper_95_c": float(row["Upper confidence limit (97.5%)"]),
                }
            )
        return rows

    def validate(self, frame: list[dict[str, Any]]) -> None:
        if len(frame) < 100:
            raise SourceValidationError("hadcrut5 annual: too few rows")
        years = [r["year"] for r in frame]
        if min(years) < 1850 or max(years) > 2100:
            raise SourceValidationError("hadcrut5 annual: year out of range")
        anomalies = [r["anomaly_c"] for r in frame]
        if min(anomalies) < -2.5 or max(anomalies) > 3.5:
            raise SourceValidationError("hadcrut5 annual: anomaly out of range")

    def compute_aggregates(self, frame: list[dict[str, Any]]) -> dict[str, Any]:
        latest = frame[-1]
        return {
            "row_count": len(frame),
            "year_min": frame[0]["year"],
            "year_max": latest["year"],
            "latest_annual": {
                "year": latest["year"],
                "anomaly_c": latest["anomaly_c"],
                "lower_95_c": latest["lower_95_c"],
                "upper_95_c": latest["upper_95_c"],
            },
            "native_baseline": "1961-1990",
        }


class HadCrut5MonthlyFetcher(BaseFetcher):
    spec = HADCRUT5_GLOBAL_MONTHLY

    def parse(self, content: bytes) -> list[dict[str, Any]]:
        text = content.decode("utf-8")
        lines = [line for line in text.splitlines() if line.strip()]
        if not lines or lines[0].strip() != _MONTHLY_HEADER:
            raise SourceValidationError(f"hadcrut5 monthly: unexpected header {lines[0]!r}")
        reader = csv.DictReader(io.StringIO("\n".join(lines)))
        rows: list[dict[str, Any]] = []
        for row in reader:
            year, month = _parse_row_time(row["Time"])
            rows.append(
                {
                    "year": year,
                    "month": month,
                    "anomaly_c": float(row["Anomaly (deg C)"]),
                    "lower_95_c": float(row["Lower confidence limit (2.5%)"]),
                    "upper_95_c": float(row["Upper confidence limit (97.5%)"]),
                }
            )
        return rows

    def validate(self, frame: list[dict[str, Any]]) -> None:
        if len(frame) < 1000:
            raise SourceValidationError("hadcrut5 monthly: too few rows")
        years = [r["year"] for r in frame]
        if min(years) < 1850 or max(years) > 2100:
            raise SourceValidationError("hadcrut5 monthly: year out of range")
        anomalies = [r["anomaly_c"] for r in frame]
        if min(anomalies) < -2.5 or max(anomalies) > 3.5:
            raise SourceValidationError("hadcrut5 monthly: anomaly out of range")
        max_year = max(years)
        recent = [r for r in frame if r["year"] >= max_year - 1]
        if len(recent) < 6:
            raise SourceValidationError("hadcrut5 monthly: too few recent months")

    def compute_aggregates(self, frame: list[dict[str, Any]]) -> dict[str, Any]:
        latest = frame[-1]
        return {
            "row_count": len(frame),
            "year_min": frame[0]["year"],
            "year_max": latest["year"],
            "latest_month": {
                "year": latest["year"],
                "month": latest["month"],
                "anomaly_c": latest["anomaly_c"],
            },
            "native_baseline": "1961-1990",
        }
