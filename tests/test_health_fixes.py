"""Production health fixes: GISTEMP last month, Last-Modified, known_lag."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from earth_watch.fetch_http import normalize_http_last_modified
from earth_watch.fetchers import GistempGlobalFetcher
from earth_watch.fetchers.base import FetchResult
from earth_watch.freshness import (
    cadence_for_source,
    known_lag_for_source,
    last_data_point_from_frame,
)
from earth_watch.health import health_from_manifest

FIXTURES = Path(__file__).parent / "fixtures"


def test_normalize_http_last_modified_rejects_jsnull():
    assert normalize_http_last_modified(None) is None
    assert normalize_http_last_modified("jsnull") is None
    assert normalize_http_last_modified("JSNULL") is None
    assert normalize_http_last_modified("Wed, 01 Jan 2025 00:00:00 GMT") == (
        "Wed, 01 Jan 2025 00:00:00 GMT"
    )


def test_gistemp_last_data_point_from_monthly_columns():
    fetcher = GistempGlobalFetcher()
    content = (FIXTURES / "GLB.Ts+dSST.csv").read_bytes()
    frame = fetcher.parse(content)
    point = last_data_point_from_frame("gistemp_glb_ts_dsst", frame)
    assert point is not None
    assert point.month is not None
    assert cadence_for_source("gistemp_glb_ts_dsst") == "monthly"


def test_health_ok_when_only_known_lag_sources_stale():
    manifest = {
        "run_at_utc": "2026-10-19T12:00:00Z",
        "run_id": "r1",
        "fetch_date": "2026-10-19",
        "sources": [
            {
                "source_id": "berkeley_earth_land_ocean",
                "status": "ok",
                "error": None,
                "last_data_point": {"year": 2024},
                "http_last_modified": None,
                "stale": True,
                "known_lag": True,
                "cadence": "annual",
            },
            {
                "source_id": "gistemp_glb_ts_dsst",
                "status": "ok",
                "error": None,
                "last_data_point": {"year": 2025, "month": 8},
                "http_last_modified": None,
                "stale": False,
                "known_lag": False,
                "cadence": "monthly",
            },
        ],
    }
    health = health_from_manifest(manifest)
    assert health["status"] == "ok"
    assert health["stale"] is True
    assert health["any_failed"] is False
    assert known_lag_for_source("berkeley_earth_land_ocean") is True
    assert known_lag_for_source("gistemp_glb_ts_dsst") is False


def test_health_degraded_when_non_known_lag_stale():
    manifest = {
        "run_at_utc": "2026-10-19T12:00:00Z",
        "run_id": "r1",
        "fetch_date": "2026-10-19",
        "sources": [
            {
                "source_id": "gistemp_glb_ts_dsst",
                "status": "ok",
                "stale": True,
                "known_lag": False,
                "cadence": "monthly",
            }
        ],
    }
    health = health_from_manifest(manifest)
    assert health["status"] == "degraded"
