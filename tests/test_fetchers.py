"""Unit tests for source fetchers (offline fixtures)."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

import pytest

from earth_watch.fetchers import GistempGlobalFetcher, GmlCo2Fetcher, SourceValidationError
from earth_watch.fetchers.base import FetchResult
from earth_watch.sources import GML_CO2_ANNMEAN, GML_CO2_GROWTH, GML_CO2_MONTHLY

FIXTURES = Path(__file__).parent / "fixtures"


def _fetch_result(spec, filename: str) -> FetchResult:
    content = (FIXTURES / filename).read_bytes()
    return FetchResult.from_bytes(
        spec,
        content,
        datetime(2026, 1, 1, tzinfo=timezone.utc),
    )


class TestGmlCo2:
    def test_annmean_parse_and_aggregate(self):
        fetcher = GmlCo2Fetcher("annmean")
        record = fetcher.process(_fetch_result(GML_CO2_ANNMEAN, "co2_annmean_mlo.csv"))
        assert record.aggregates["latest"]["year"] == 2025
        assert record.aggregates["latest"]["mean_ppm"] == pytest.approx(427.35)

    def test_growth_parse_and_aggregate(self):
        fetcher = GmlCo2Fetcher("growth")
        record = fetcher.process(_fetch_result(GML_CO2_GROWTH, "co2_gr_mlo.csv"))
        assert record.aggregates["latest"]["year"] == 2025
        assert record.aggregates["latest"]["annual_growth_ppm"] == pytest.approx(2.23)

    def test_monthly_parse_and_aggregate(self):
        fetcher = GmlCo2Fetcher("monthly")
        record = fetcher.process(_fetch_result(GML_CO2_MONTHLY, "co2_mm_mlo.csv"))
        latest = record.aggregates["latest"]
        assert latest["year"] == 2026
        assert latest["month"] == 9

    def test_annmean_rejects_bad_columns(self):
        fetcher = GmlCo2Fetcher("annmean")
        bad = FetchResult.from_bytes(
            GML_CO2_ANNMEAN,
            b"year,foo\n2020,1\n",
            datetime(2026, 1, 1, tzinfo=timezone.utc),
        )
        with pytest.raises(SourceValidationError, match="expected columns"):
            fetcher.process(bad)


class TestGistemp:
    def test_parse_and_aggregate(self):
        fetcher = GistempGlobalFetcher()
        record = fetcher.process(_fetch_result(fetcher.spec, "GLB.Ts+dSST.csv"))
        assert record.aggregates["latest_annual"]["year"] >= 2024
        assert "j_d_anomaly_c" in record.aggregates["latest_annual"]
        assert record.aggregates["latest_month"] is not None

    def test_rejects_missing_title(self):
        fetcher = GistempGlobalFetcher()
        bad = FetchResult.from_bytes(
            fetcher.spec,
            b"not a title\nYear,Jan\n",
            datetime(2026, 1, 1, tzinfo=timezone.utc),
        )
        with pytest.raises(SourceValidationError, match="title"):
            fetcher.process(bad)
