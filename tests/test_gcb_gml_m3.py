"""M3 fetchers: GCB XLSX and GML global growth."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from earth_watch.fetchers import GcbBudgetFetcher, GmlGlobalGrowthFetcher
from earth_watch.fetchers.base import FetchResult

FIXTURES = Path(__file__).parent / "fixtures"


def test_gcb_parse_budget_sheet():
    fetcher = GcbBudgetFetcher()
    content = (FIXTURES / "global_carbon_budget_2025.xlsx").read_bytes()
    fetch = FetchResult.from_bytes(fetcher.spec, content, datetime(2026, 1, 1, tzinfo=timezone.utc))
    record = fetcher.process(fetch)
    assert record.aggregates["year_max"] == 2024
    assert record.frame[0]["year"] == 1959
    assert "fossil_gtc" in record.frame[-1]


def test_gml_global_growth_parse():
    fetcher = GmlGlobalGrowthFetcher()
    content = (FIXTURES / "co2_gr_gl.txt").read_bytes()
    fetch = FetchResult.from_bytes(fetcher.spec, content, datetime(2026, 1, 1, tzinfo=timezone.utc))
    record = fetcher.process(fetch)
    assert record.aggregates["latest"]["growth_ppm"] > 0
