"""NCEI OHC and CAG fetchers."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from earth_watch.fetchers import NceiCagOceanSstFetcher, NceiOhcFetcher
from earth_watch.fetchers.base import FetchResult

FIXTURES = Path(__file__).parent / "fixtures"


def test_ncei_ohc_parse():
    fetcher = NceiOhcFetcher("0-2000m")
    content = (FIXTURES / "ncei_ohc_0_2000m_yearly.dat").read_bytes()
    fetch = FetchResult.from_bytes(fetcher.spec, content, datetime(2026, 1, 1, tzinfo=timezone.utc))
    record = fetcher.process(fetch)
    assert record.aggregates["units"] == "10^22 J"
    assert record.frame[-1]["year"] >= 2024


def test_cag_annual_parse():
    fetcher = NceiCagOceanSstFetcher()
    content = (FIXTURES / "ncei_cag_ocean_annual.json").read_bytes()
    fetch = FetchResult.from_bytes(fetcher.spec, content, datetime(2026, 1, 1, tzinfo=timezone.utc))
    frame = fetcher.parse(content)
    fetcher.validate(frame)
    assert frame["annual"][-1]["year"] >= 2020
