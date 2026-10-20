"""NOAA GML global annual CO2 growth (co2_gr_gl.txt)."""

from __future__ import annotations

from typing import Any

from earth_watch.fetchers.base import BaseFetcher, SourceValidationError
from earth_watch.sources import GML_CO2_GR_GLOBAL


class GmlGlobalGrowthFetcher(BaseFetcher):
    spec = GML_CO2_GR_GLOBAL

    def parse(self, content: bytes) -> list[dict[str, Any]]:
        rows: list[dict[str, Any]] = []
        for line in content.decode("utf-8").splitlines():
            if line.startswith("#") or not line.strip():
                continue
            parts = line.split()
            if len(parts) < 3:
                continue
            try:
                year = int(parts[0])
            except ValueError:
                continue
            rows.append(
                {
                    "year": year,
                    "growth_ppm": float(parts[1]),
                    "unc_ppm": float(parts[2]),
                }
            )
        return rows

    def validate(self, frame: list[dict[str, Any]]) -> None:
        if len(frame) < 50:
            raise SourceValidationError("gml global growth: too few rows")
        years = [r["year"] for r in frame]
        if min(years) < 1950 or max(years) > 2100:
            raise SourceValidationError("gml global growth: year out of range")
        growth = [r["growth_ppm"] for r in frame]
        if min(growth) < -5 or max(growth) > 15:
            raise SourceValidationError("gml global growth: value out of range")

    def compute_aggregates(self, frame: list[dict[str, Any]]) -> dict[str, Any]:
        latest = frame[-1]
        return {
            "row_count": len(frame),
            "year_min": frame[0]["year"],
            "year_max": latest["year"],
            "latest": {
                "year": latest["year"],
                "growth_ppm": latest["growth_ppm"],
                "unc_ppm": latest["unc_ppm"],
            },
        }
