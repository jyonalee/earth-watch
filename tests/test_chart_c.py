"""Chart (c) ocean heat and SST."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from earth_watch.chart_c import CHART_C_LATEST_KEY, build_chart_c_payload
from earth_watch.fetchers import NceiCagOceanSstFetcher, NceiOhcFetcher
from earth_watch.fetchers.base import FetchResult, SourceRecord

FIXTURES = Path(__file__).parent / "fixtures"


def _ohc_record(fetcher, filename: str):
    content = (FIXTURES / filename).read_bytes()
    fetch = FetchResult.from_bytes(
        fetcher.spec,
        content,
        datetime(2026, 1, 1, tzinfo=timezone.utc),
    )
    return fetcher.process(fetch)


def _sst_record():
    fetcher = NceiCagOceanSstFetcher()
    content = (FIXTURES / "ncei_cag_ocean_annual.json").read_bytes()
    fetch = FetchResult.from_bytes(
        fetcher.spec,
        content,
        datetime(2026, 1, 1, tzinfo=timezone.utc),
    )
    frame = fetcher.parse(content)
    monthly = []
    for key, value in json_load_monthly_fixture().items():
        year = int(key[:4])
        month = int(key[4:6])
        monthly.append({"year": year, "month": month, "anomaly_c": float(value)})
    frame["monthly"] = sorted(monthly, key=lambda r: (r["year"], r["month"]))
    fetcher.validate(frame)
    return SourceRecord(
        spec=fetcher.spec,
        fetch=fetch,
        frame=frame,
        aggregates=fetcher.compute_aggregates(frame),
    )


def json_load_monthly_fixture():
    import json

    return json.loads((FIXTURES / "ncei_cag_ocean_monthly.json").read_text())["data"]


def test_build_chart_c_payload():
    run_at = datetime(2026, 10, 19, 12, 0, tzinfo=timezone.utc)
    records = [
        _ohc_record(NceiOhcFetcher("0-700m"), "ncei_ohc_0_700m_yearly.dat"),
        _ohc_record(NceiOhcFetcher("0-2000m"), "ncei_ohc_0_2000m_yearly.dat"),
        _sst_record(),
    ]
    payload = build_chart_c_payload(records, run_at=run_at)
    assert payload["last_complete_year"] == 2024
    assert CHART_C_LATEST_KEY.endswith("chart_c_ocean_heat.json")
    ohc2000 = payload["ohc"]["0_2000m"]["annual"]
    assert all(row["year"] != 2025 for row in ohc2000)
    assert payload["ohc"]["0_2000m"]["trends"]["long"]["heating_rate_w_m2"] > 0
    assert payload["sst"]["annual"]
    assert payload["facts"]
    assert payload["read"]
    assert "through complete year 2024" in payload["facts"][0].lower()
    ohc_trend_fact = payload["facts"][1]
    assert "zj yr" in ohc_trend_fact.lower()
    assert "95% ci" in ohc_trend_fact.lower()
    assert "10²² j decade" not in ohc_trend_fact.lower()
    assert "w m⁻²" in ohc_trend_fact.lower() or "w m" in ohc_trend_fact.lower()
    long_trend = payload["ohc"]["0_2000m"]["trends"]["long"]
    assert "ci95_low_zj_per_year" in long_trend
    assert long_trend["ci95_low_zj_per_year"] <= long_trend["slope_zj_per_year"]
    assert long_trend["ci95_high_zj_per_year"] >= long_trend["slope_zj_per_year"]
