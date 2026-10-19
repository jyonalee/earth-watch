"""NOAA GML Mauna Loa CO2 trend tables."""

from __future__ import annotations

import io
from typing import Literal

import pandas as pd

from earth_watch.fetchers.base import BaseFetcher, SourceValidationError
from earth_watch.sources import GML_CO2_ANNMEAN, GML_CO2_GROWTH, GML_CO2_MONTHLY, SourceSpec

GmlKind = Literal["annmean", "growth", "monthly"]

_EXPECTED_COLUMNS: dict[GmlKind, list[str]] = {
    "annmean": ["year", "mean", "unc"],
    "growth": ["year", "ann inc", "unc"],
    "monthly": [
        "year",
        "month",
        "decimal date",
        "average",
        "deseasonalized",
        "ndays",
        "sdev",
        "unc",
    ],
}


class GmlCo2Fetcher(BaseFetcher):
    """Fetcher for one NOAA GML Mauna Loa CO2 CSV."""

    def __init__(self, kind: GmlKind, spec: SourceSpec | None = None) -> None:
        self.kind = kind
        if spec is None:
            spec = {
                "annmean": GML_CO2_ANNMEAN,
                "growth": GML_CO2_GROWTH,
                "monthly": GML_CO2_MONTHLY,
            }[kind]
        self.spec = spec

    def parse(self, content: bytes) -> pd.DataFrame:
        text = content.decode("utf-8")
        lines = [line for line in text.splitlines() if not line.startswith("#")]
        body = "\n".join(lines)
        frame = pd.read_csv(io.StringIO(body))
        frame.columns = [str(c).strip().lower() for c in frame.columns]
        return frame

    def validate(self, frame: pd.DataFrame) -> None:
        expected = _EXPECTED_COLUMNS[self.kind]
        if list(frame.columns) != expected:
            raise SourceValidationError(
                f"{self.spec.source_id}: expected columns {expected}, got {list(frame.columns)}"
            )
        if frame.empty:
            raise SourceValidationError(f"{self.spec.source_id}: empty table")

        years = frame["year"]
        if years.min() < 1950 or years.max() > 2100:
            raise SourceValidationError(f"{self.spec.source_id}: year out of range")

        if self.kind == "annmean":
            means = frame["mean"]
            if means.min() < 300 or means.max() > 550:
                raise SourceValidationError(f"{self.spec.source_id}: mean CO2 out of range")
        elif self.kind == "growth":
            growth = frame["ann inc"]
            if growth.min() < -5 or growth.max() > 15:
                raise SourceValidationError(f"{self.spec.source_id}: growth out of range")
        else:
            avg = frame["average"]
            if avg.min() < 300 or avg.max() > 550:
                raise SourceValidationError(f"{self.spec.source_id}: monthly average out of range")
            months = frame["month"]
            if months.min() < 1 or months.max() > 12:
                raise SourceValidationError(f"{self.spec.source_id}: month out of range")

    def compute_aggregates(self, frame: pd.DataFrame) -> dict:
        if self.kind == "annmean":
            last = frame.iloc[-1]
            return {
                "kind": self.kind,
                "row_count": len(frame),
                "year_min": int(frame["year"].min()),
                "year_max": int(frame["year"].max()),
                "latest": {
                    "year": int(last["year"]),
                    "mean_ppm": float(last["mean"]),
                    "unc_ppm": float(last["unc"]),
                },
            }
        if self.kind == "growth":
            last = frame.iloc[-1]
            return {
                "kind": self.kind,
                "row_count": len(frame),
                "year_min": int(frame["year"].min()),
                "year_max": int(frame["year"].max()),
                "latest": {
                    "year": int(last["year"]),
                    "annual_growth_ppm": float(last["ann inc"]),
                    "unc_ppm": float(last["unc"]),
                },
            }
        last = frame.iloc[-1]
        return {
            "kind": self.kind,
            "row_count": len(frame),
            "year_min": int(frame["year"].min()),
            "year_max": int(frame["year"].max()),
            "latest": {
                "year": int(last["year"]),
                "month": int(last["month"]),
                "average_ppm": float(last["average"]),
                "deseasonalized_ppm": float(last["deseasonalized"]),
                "unc_ppm": float(last["unc"]),
            },
        }


def gml_fetchers() -> list[GmlCo2Fetcher]:
    return [
        GmlCo2Fetcher("annmean"),
        GmlCo2Fetcher("growth"),
        GmlCo2Fetcher("monthly"),
    ]
