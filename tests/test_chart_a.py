"""Chart (a) aggregate: common baseline and trends."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from earth_watch.chart_a import CHART_A_LATEST_KEY, build_chart_a_payload
from earth_watch.fetchers import (
    BerkeleyLandOceanFetcher,
    GistempGlobalFetcher,
    HadCrut5AnnualFetcher,
)
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


def test_build_chart_a_three_series_common_baseline():
    records = [
        _record(GistempGlobalFetcher(), "GLB.Ts+dSST.csv"),
        _record(HadCrut5AnnualFetcher(), "hadcrut5_global_annual.csv"),
        _record(BerkeleyLandOceanFetcher(), "berkeley_land_ocean_summary.txt"),
    ]
    payload = build_chart_a_payload(records)
    assert payload["baseline"]["label"] == "1951-1980"
    assert len(payload["series"]) == 3
    ids = {s["source_id"] for s in payload["series"]}
    assert ids == {
        "gistemp_glb_ts_dsst",
        "hadcrut5_global_annual",
        "berkeley_earth_land_ocean",
    }
    for series in payload["series"]:
        assert series["annual"]
        assert series["trends"]["from_1970"]
        assert series["trends"]["recent_20y"]
    assert (
        payload["acceleration"]["gistemp_glb_ts_dsst"]["recent_minus_long_slope_per_decade_c"]
        is not None
    )
    assert CHART_A_LATEST_KEY == "aggregates/latest/chart_a_warming.json"
