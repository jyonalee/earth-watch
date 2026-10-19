"""NASA GISTEMP v4 global temperature table."""

from __future__ import annotations

import csv
import io
from typing import Any

from earth_watch.fetchers.base import BaseFetcher, SourceValidationError
from earth_watch.sources import GISTEMP_GLOBAL

_MISSING = "***"
_MONTH_COLS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
_SEASON_COLS = ["J-D", "D-N", "DJF", "MAM", "JJA", "SON"]
_ALL_VALUE_COLS = _MONTH_COLS + _SEASON_COLS


def _parse_gistemp_value(raw: str) -> float | None:
    text = str(raw).strip()
    if text == _MISSING or text == "":
        return None
    if text.startswith("."):
        text = "0" + text
    return float(text)


class GistempGlobalFetcher(BaseFetcher):
    """Fetcher for GLB.Ts+dSST.csv global means."""

    spec = GISTEMP_GLOBAL

    def parse(self, content: bytes) -> list[dict[str, Any]]:
        text = content.decode("utf-8")
        lines = text.splitlines()
        if not lines or "Global Means" not in lines[0]:
            raise SourceValidationError("gistemp: missing expected title line")
        header_line = lines[1]
        expected_header = "Year," + ",".join(_ALL_VALUE_COLS)
        if header_line.strip() != expected_header:
            raise SourceValidationError(
                f"gistemp: unexpected header: {header_line!r} (expected {expected_header!r})"
            )
        reader = csv.DictReader(io.StringIO("\n".join(lines[1:])))
        rows: list[dict[str, Any]] = []
        for row in reader:
            parsed: dict[str, Any] = {"Year": int(row["Year"])}
            for col in _ALL_VALUE_COLS:
                parsed[col] = _parse_gistemp_value(row[col])
            rows.append(parsed)
        return rows

    def validate(self, frame: list[dict[str, Any]]) -> None:
        if not frame:
            raise SourceValidationError("gistemp: empty table")

        years = [row["Year"] for row in frame]
        if min(years) < 1880 or max(years) > 2100:
            raise SourceValidationError("gistemp: year out of range")

        jd_values = [row["J-D"] for row in frame if row["J-D"] is not None]
        if not jd_values:
            raise SourceValidationError("gistemp: no annual J-D values")
        if min(jd_values) < -2.0 or max(jd_values) > 3.0:
            raise SourceValidationError("gistemp: J-D anomaly out of expected range")

        max_year = max(years)
        recent = [row for row in frame if row["Year"] >= max_year - 1]
        month_count = 0
        for row in recent:
            for col in _MONTH_COLS:
                if row[col] is not None:
                    month_count += 1
        if month_count < 6:
            raise SourceValidationError("gistemp: too few recent monthly values")

    def compute_aggregates(self, frame: list[dict[str, Any]]) -> dict:
        latest_year = max(row["Year"] for row in frame)
        latest_row = next(row for row in reversed(frame) if row["Year"] == latest_year)

        latest_month: dict | None = None
        for month_name, month_num in zip(_MONTH_COLS, range(1, 13), strict=True):
            value = latest_row[month_name]
            if value is not None:
                latest_month = {
                    "year": latest_year,
                    "month": month_num,
                    "anomaly_c": float(value),
                }

        annual_rows = [row for row in frame if row["J-D"] is not None]
        last_annual = annual_rows[-1]
        return {
            "row_count": len(frame),
            "year_min": min(row["Year"] for row in frame),
            "year_max": latest_year,
            "latest_month": latest_month,
            "latest_annual": {
                "year": int(last_annual["Year"]),
                "j_d_anomaly_c": float(last_annual["J-D"]),
            },
        }
