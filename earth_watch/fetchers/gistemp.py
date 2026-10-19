"""NASA GISTEMP v4 global temperature table."""

from __future__ import annotations

import io

import pandas as pd

from earth_watch.fetchers.base import BaseFetcher, SourceValidationError
from earth_watch.sources import GISTEMP_GLOBAL

_MISSING = "***"
_MONTH_COLS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
_SEASON_COLS = ["J-D", "D-N", "DJF", "MAM", "JJA", "SON"]


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

    def parse(self, content: bytes) -> pd.DataFrame:
        text = content.decode("utf-8")
        lines = text.splitlines()
        if not lines or "Global Means" not in lines[0]:
            raise SourceValidationError("gistemp: missing expected title line")
        header_line = lines[1]
        expected_header = "Year," + ",".join(_MONTH_COLS + _SEASON_COLS)
        if header_line.strip() != expected_header:
            raise SourceValidationError(
                f"gistemp: unexpected header: {header_line!r} (expected {expected_header!r})"
            )
        body = "\n".join(lines[1:])
        frame = pd.read_csv(
            io.StringIO(body),
            converters={col: _parse_gistemp_value for col in _MONTH_COLS + _SEASON_COLS},
        )
        return frame

    def validate(self, frame: pd.DataFrame) -> None:
        if "Year" not in frame.columns:
            raise SourceValidationError("gistemp: missing Year column")
        years = frame["Year"]
        if years.min() < 1880 or years.max() > 2100:
            raise SourceValidationError("gistemp: year out of range")

        jd = frame["J-D"].dropna()
        if jd.empty:
            raise SourceValidationError("gistemp: no annual J-D values")
        if jd.min() < -2.0 or jd.max() > 3.0:
            raise SourceValidationError("gistemp: J-D anomaly out of expected range")

        # Require a reasonable run of recent monthly data.
        recent = frame[frame["Year"] >= frame["Year"].max() - 1]
        month_vals = recent[_MONTH_COLS].stack().dropna()
        if len(month_vals) < 6:
            raise SourceValidationError("gistemp: too few recent monthly values")

    def compute_aggregates(self, frame: pd.DataFrame) -> dict:
        latest_year = int(frame["Year"].max())
        latest_row = frame.loc[frame["Year"] == latest_year].iloc[-1]

        # Latest calendar month with data in the most recent year row.
        latest_month: dict | None = None
        for month_name, month_num in zip(_MONTH_COLS, range(1, 13), strict=True):
            value = latest_row[month_name]
            if value is not None and not pd.isna(value):
                latest_month = {
                    "year": latest_year,
                    "month": month_num,
                    "anomaly_c": float(value),
                }

        # Latest year with a complete annual mean (J-D).
        annual = frame.dropna(subset=["J-D"])
        last_annual = annual.iloc[-1]
        annual_year = int(last_annual["Year"])
        annual_anomaly = float(last_annual["J-D"])

        return {
            "row_count": len(frame),
            "year_min": int(frame["Year"].min()),
            "year_max": latest_year,
            "latest_month": latest_month,
            "latest_annual": {
                "year": annual_year,
                "j_d_anomaly_c": annual_anomaly,
            },
        }
