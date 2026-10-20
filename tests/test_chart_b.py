"""Chart (b) airborne fraction aggregate."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from earth_watch.chart_b import CHART_B_LATEST_KEY, build_chart_b_payload
from earth_watch.fetchers import GcbBudgetFetcher, GmlGlobalGrowthFetcher
from earth_watch.fetchers.base import FetchResult

FIXTURES = Path(__file__).parent / "fixtures"


def _record(fetcher, filename: str):
    content = (FIXTURES / filename).read_bytes()
    fetch = FetchResult.from_bytes(
        fetcher.spec,
        content,
        datetime(2026, 1, 1, tzinfo=timezone.utc),
    )
    return fetcher.process(fetch)


def test_chart_b_complete_years_and_af():
    run_at = datetime(2026, 10, 19, 12, 0, tzinfo=timezone.utc)
    records = [
        _record(GcbBudgetFetcher(), "global_carbon_budget_2025.xlsx"),
        _record(GmlGlobalGrowthFetcher(), "co2_gr_gl.txt"),
    ]
    payload = build_chart_b_payload(records, run_at=run_at)
    assert payload["last_complete_year"] == 2024
    years = [row["year"] for row in payload["annual"]]
    assert 2025 not in years
    assert 2024 in years
    assert CHART_B_LATEST_KEY.endswith("chart_b_airborne_fraction.json")
    latest = payload["annual"][-1]
    assert 0 < latest["airborne_fraction"] < 1
    assert latest["airborne_fraction_fossil_only"] is not None
    assert any(
        row["airborne_fraction_smoothed_10y"] is not None for row in payload["annual"]
    )
    assert "through complete year 2024" in payload["facts"][0].lower()
    assert payload["trend"]["from_year"] == 1960
    assert "read" in payload
    assert payload["ppm_to_gtc_factor"] == 2.124
