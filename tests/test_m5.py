"""M5: resilience, health, CAG URL, freshness."""

from __future__ import annotations

import asyncio
from datetime import datetime, timezone
from pathlib import Path

from earth_watch.fetchers import GmlCo2Fetcher
from earth_watch.fetchers.base import FetchResult, SourceValidationError
from earth_watch.fetchers.ncei_cag_ocean import NceiCagOceanSstFetcher
from earth_watch.freshness import LastDataPoint, is_stale, stale_threshold_months
from earth_watch.health import health_from_manifest
from earth_watch.pipeline import build_manifest, outcomes_from_records
from earth_watch.source_collect import collect_source_outcomes_async
from earth_watch.layout import storage_filename_for_spec
from earth_watch.sources import NCEI_CAG_OCEAN_ANNUAL, cag_ocean_annual_url

FIXTURES = Path(__file__).parent / "fixtures"


def test_cag_ocean_annual_url_builds_end_year():
    url = cag_ocean_annual_url(2028)
    assert url.endswith("1980-2028.json")
    assert "ytd/12/" in url


def test_cag_storage_filename_stable():
    assert storage_filename_for_spec(NCEI_CAG_OCEAN_ANNUAL) == "ncei_cag_ocean_annual.json"


def test_stale_annual_threshold():
    run_at = datetime(2026, 10, 1, tzinfo=timezone.utc)
    point = LastDataPoint(year=2025)
    assert not is_stale(point, cadence="annual", as_of=run_at)
    old = LastDataPoint(year=2020)
    assert is_stale(old, cadence="annual", as_of=run_at)
    assert stale_threshold_months("gcb") == 24


def test_manifest_records_source_status_and_stale():
    fetch = FetchResult.from_bytes(
        GmlCo2Fetcher("growth").spec,
        b"year,ann inc,unc\n2025,2.23,0.11\n",
        datetime(2026, 10, 19, 12, 0, tzinfo=timezone.utc),
    )
    record = GmlCo2Fetcher("growth").process(fetch)
    run_at = datetime(2026, 10, 19, 12, 0, tzinfo=timezone.utc)
    manifest = build_manifest(
        outcomes_from_records([record], run_at=run_at),
        run_id="x",
        fetch_date="2026-10-19",
        run_at=run_at,
    )
    src = manifest["sources"][0]
    assert src["status"] == "ok"
    assert src["error"] is None
    assert "last_data_point" in src
    assert "stale" in src
    assert src["cadence"] == "annual"


def test_health_from_manifest_degraded_on_failure():
    manifest = {
        "run_at_utc": "2026-10-19T12:00:00Z",
        "run_id": "r1",
        "fetch_date": "2026-10-19",
        "pipeline_version": "0.5.0",
        "sources": [
            {
                "source_id": "gistemp_glb_ts_dsst",
                "status": "failed",
                "error": "timeout",
                "last_data_point": {"year": 2024},
                "http_last_modified": None,
                "stale": False,
                "cadence": "annual",
            }
        ],
    }
    health = health_from_manifest(manifest)
    assert health["any_failed"] is True
    assert health["status"] == "degraded"
    assert health["sources"][0]["status"] == "failed"


_CAG_FETCHED_URLS: list[str] = []


async def _cag_fallback_fetch(url: str) -> bytes:
    _CAG_FETCHED_URLS.append(url)
    if url.endswith("1980-2028.json"):
        raise SourceValidationError("GET failed: HTTP 404")
    if url.endswith("1980-2027.json"):
        return (FIXTURES / "ncei_cag_ocean_annual.json").read_bytes()
    raise SourceValidationError(f"unexpected url {url}")


def test_cag_annual_fetch_falls_back_to_previous_year():
    from unittest.mock import patch

    async def run():
        fetcher = NceiCagOceanSstFetcher()
        with patch(
            "earth_watch.fetchers.ncei_cag_ocean.cag_annual_end_years_to_try",
            return_value=(2028, 2027),
        ):
            record = await fetcher.run_async(_cag_fallback_fetch)
        assert record.frame["annual"]
        assert any("1980-2027.json" in u for u in _CAG_FETCHED_URLS)

    _CAG_FETCHED_URLS.clear()
    asyncio.run(run())


class _FailingFetcher(GmlCo2Fetcher):
    async def run_async(self, get_bytes):
        raise SourceValidationError("boom")


def test_collect_continues_after_source_failure():
    ok_fetch = FetchResult.from_bytes(
        GmlCo2Fetcher("growth").spec,
        b"year,ann inc,unc\n2025,2.23,0.11\n",
        datetime(2026, 1, 1, tzinfo=timezone.utc),
    )

    class OkFetcher(GmlCo2Fetcher):
        async def run_async(self, get_bytes):
            return self.process(ok_fetch)

    async def run():
        outcomes = await collect_source_outcomes_async(
            [_FailingFetcher("annmean"), OkFetcher("growth")],
            _cag_fallback_fetch,
            run_at=datetime(2026, 10, 19, tzinfo=timezone.utc),
            bucket=None,
        )
        assert outcomes[0].status == "failed"
        assert outcomes[1].status == "ok"

    asyncio.run(run())
