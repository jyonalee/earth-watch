"""Berkeley Earth global land and ocean summary."""

from __future__ import annotations

from typing import Any

from earth_watch.fetchers.base import BaseFetcher, SourceValidationError
from earth_watch.sources import BERKELEY_LAND_OCEAN

_HEADER_MARKER = (
    "Year, Annual Anomaly, Annual Unc., Five-year Anomaly, Five-year Unc., "
    "Annual Anomaly, Annual Unc., Five-year Anomaly, Five-year Unc."
)


def _parse_float(token: str) -> float | None:
    text = token.strip()
    if not text or text.lower() == "nan":
        return None
    return float(text)


class BerkeleyLandOceanFetcher(BaseFetcher):
    """Air-temperature-above-sea-ice annual anomalies (first block in summary file)."""

    spec = BERKELEY_LAND_OCEAN

    def parse(self, content: bytes) -> list[dict[str, Any]]:
        text = content.decode("utf-8", errors="replace")
        lines = text.splitlines()
        data_start = None
        for idx, line in enumerate(lines):
            stripped = line.strip()
            if stripped.startswith("%"):
                stripped = stripped[1:].strip()
            if stripped == _HEADER_MARKER:
                data_start = idx + 1
                break
        if data_start is None:
            raise SourceValidationError("berkeley: missing data header")
        rows: list[dict[str, Any]] = []
        for line in lines[data_start:]:
            stripped = line.strip()
            if not stripped or stripped.startswith("%"):
                continue
            parts = stripped.split()
            if len(parts) < 2:
                continue
            year = int(parts[0])
            annual = _parse_float(parts[1])
            annual_unc = _parse_float(parts[2]) if len(parts) > 2 else None
            if annual is None:
                continue
            rows.append(
                {
                    "year": year,
                    "anomaly_c": annual,
                    "annual_unc_c": annual_unc,
                }
            )
        return rows

    def validate(self, frame: list[dict[str, Any]]) -> None:
        if len(frame) < 100:
            raise SourceValidationError("berkeley: too few annual rows")
        years = [r["year"] for r in frame]
        if min(years) < 1850 or max(years) > 2100:
            raise SourceValidationError("berkeley: year out of range")
        anomalies = [r["anomaly_c"] for r in frame]
        if min(anomalies) < -2.0 or max(anomalies) > 3.5:
            raise SourceValidationError("berkeley: anomaly out of range")

    def compute_aggregates(self, frame: list[dict[str, Any]]) -> dict[str, Any]:
        latest = frame[-1]
        return {
            "row_count": len(frame),
            "year_min": frame[0]["year"],
            "year_max": latest["year"],
            "latest_annual": {
                "year": latest["year"],
                "anomaly_c": latest["anomaly_c"],
                "annual_unc_c": latest.get("annual_unc_c"),
            },
            "native_baseline": "1951-1980",
        }
