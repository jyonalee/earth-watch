"""NOAA GML Mauna Loa CO2 trend tables."""

from __future__ import annotations

import csv
import io
from typing import Any, Literal

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


def _read_csv_rows(content: bytes) -> list[dict[str, str]]:
    text = content.decode("utf-8")
    lines = [line for line in text.splitlines() if not line.startswith("#")]
    reader = csv.DictReader(io.StringIO("\n".join(lines)))
    if reader.fieldnames is None:
        return []
    rows: list[dict[str, str]] = []
    for row in reader:
        normalized = {str(k).strip().lower(): v for k, v in row.items() if k}
        rows.append(normalized)
    return rows


def _float(value: str) -> float:
    return float(value.strip())


def _int(value: str) -> int:
    return int(float(value.strip()))


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

    def parse(self, content: bytes) -> list[dict[str, Any]]:
        return _read_csv_rows(content)

    def validate(self, frame: list[dict[str, Any]]) -> None:
        expected = _EXPECTED_COLUMNS[self.kind]
        if not frame:
            raise SourceValidationError(f"{self.spec.source_id}: empty table")
        if list(frame[0].keys()) != expected:
            raise SourceValidationError(
                f"{self.spec.source_id}: expected columns {expected}, got {list(frame[0].keys())}"
            )

        years = [_int(row["year"]) for row in frame]
        if min(years) < 1950 or max(years) > 2100:
            raise SourceValidationError(f"{self.spec.source_id}: year out of range")

        if self.kind == "annmean":
            means = [_float(row["mean"]) for row in frame]
            if min(means) < 300 or max(means) > 550:
                raise SourceValidationError(f"{self.spec.source_id}: mean CO2 out of range")
        elif self.kind == "growth":
            growth = [_float(row["ann inc"]) for row in frame]
            if min(growth) < -5 or max(growth) > 15:
                raise SourceValidationError(f"{self.spec.source_id}: growth out of range")
        else:
            avg = [_float(row["average"]) for row in frame]
            if min(avg) < 300 or max(avg) > 550:
                raise SourceValidationError(f"{self.spec.source_id}: monthly average out of range")
            months = [_int(row["month"]) for row in frame]
            if min(months) < 1 or max(months) > 12:
                raise SourceValidationError(f"{self.spec.source_id}: month out of range")

    def compute_aggregates(self, frame: list[dict[str, Any]]) -> dict:
        last = frame[-1]
        if self.kind == "annmean":
            return {
                "kind": self.kind,
                "row_count": len(frame),
                "year_min": _int(frame[0]["year"]),
                "year_max": _int(last["year"]),
                "latest": {
                    "year": _int(last["year"]),
                    "mean_ppm": _float(last["mean"]),
                    "unc_ppm": _float(last["unc"]),
                },
            }
        if self.kind == "growth":
            return {
                "kind": self.kind,
                "row_count": len(frame),
                "year_min": _int(frame[0]["year"]),
                "year_max": _int(last["year"]),
                "latest": {
                    "year": _int(last["year"]),
                    "annual_growth_ppm": _float(last["ann inc"]),
                    "unc_ppm": _float(last["unc"]),
                },
            }
        return {
            "kind": self.kind,
            "row_count": len(frame),
            "year_min": _int(frame[0]["year"]),
            "year_max": _int(last["year"]),
            "latest": {
                "year": _int(last["year"]),
                "month": _int(last["month"]),
                "average_ppm": _float(last["average"]),
                "deseasonalized_ppm": _float(last["deseasonalized"]),
                "unc_ppm": _float(last["unc"]),
            },
        }


def gml_fetchers() -> list[GmlCo2Fetcher]:
    return [
        GmlCo2Fetcher("annmean"),
        GmlCo2Fetcher("growth"),
        GmlCo2Fetcher("monthly"),
    ]
