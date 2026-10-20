"""NOAA NCEI global ocean heat content ASCII (10^22 J)."""

from __future__ import annotations

from typing import Any

from earth_watch.fetchers.base import BaseFetcher, SourceValidationError
from earth_watch.sources import NCEI_OHC_0_2000M_YEARLY, NCEI_OHC_0_700M_YEARLY, SourceSpec


def _parse_ohc_dat(content: bytes) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for line in content.decode("utf-8").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("YEAR"):
            continue
        parts = stripped.split()
        if len(parts) < 3:
            continue
        try:
            year_frac = float(parts[0])
        except ValueError:
            continue
        year = int(year_frac)
        rows.append(
            {
                "year": year,
                "ohc_1e22j": float(parts[1]),
                "sigma_1e22j": float(parts[2]),
            }
        )
    return rows


class NceiOhcFetcher(BaseFetcher):
    def __init__(self, depth: str) -> None:
        if depth == "0-700m":
            self.spec: SourceSpec = NCEI_OHC_0_700M_YEARLY
            self.depth_label = "0-700 m"
        elif depth == "0-2000m":
            self.spec = NCEI_OHC_0_2000M_YEARLY
            self.depth_label = "0-2000 m"
        else:
            raise ValueError("depth must be 0-700m or 0-2000m")

    def parse(self, content: bytes) -> list[dict[str, Any]]:
        return _parse_ohc_dat(content)

    def validate(self, frame: list[dict[str, Any]]) -> None:
        if len(frame) < 10:
            raise SourceValidationError(f"{self.spec.source_id}: too few rows")
        years = [r["year"] for r in frame]
        if min(years) < 1950 or max(years) > 2100:
            raise SourceValidationError(f"{self.spec.source_id}: year out of range")
        vals = [r["ohc_1e22j"] for r in frame]
        if min(vals) < -50 or max(vals) > 500:
            raise SourceValidationError(f"{self.spec.source_id}: OHC out of range")

    def compute_aggregates(self, frame: list[dict[str, Any]]) -> dict[str, Any]:
        latest = frame[-1]
        return {
            "depth": self.depth_label,
            "units": "10^22 J",
            "row_count": len(frame),
            "year_min": frame[0]["year"],
            "year_max": latest["year"],
            "latest": {
                "year": latest["year"],
                "ohc_1e22j": latest["ohc_1e22j"],
                "sigma_1e22j": latest["sigma_1e22j"],
            },
        }
