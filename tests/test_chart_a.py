"""Chart (a) aggregate: common baseline and trends."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from earth_watch.chart_a import CHART_A_LATEST_KEY, build_chart_a_payload
from earth_watch.fetchers import (
    BerkeleyLandOceanFetcher,
    GistempGlobalFetcher,
    HadCrut5AnnualFetcher,
    HadCrut5MonthlyFetcher,
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
    run_at = datetime(2026, 10, 19, 12, 0, tzinfo=timezone.utc)
    records = [
        _record(GistempGlobalFetcher(), "GLB.Ts+dSST.csv"),
        _record(HadCrut5MonthlyFetcher(), "hadcrut5_global_monthly.csv"),
        _record(HadCrut5AnnualFetcher(), "hadcrut5_global_annual.csv"),
        _record(BerkeleyLandOceanFetcher(), "berkeley_land_ocean_summary.txt"),
    ]
    payload = build_chart_a_payload(records, run_at=run_at)
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

    hadcrut = next(s for s in payload["series"] if s["source_id"] == "hadcrut5_global_annual")
    assert hadcrut["last_complete_year"] == 2025
    assert hadcrut["data_as_of_year"] == 2025
    assert all(p["year"] != 2026 for p in hadcrut["annual"])
    assert "through complete year 2025" in payload["facts"][1]

    gistemp = next(s for s in payload["series"] if s["source_id"] == "gistemp_glb_ts_dsst")
    assert gistemp["last_complete_year"] < 2026
    assert all(p["year"] != 2026 for p in gistemp["annual"])
