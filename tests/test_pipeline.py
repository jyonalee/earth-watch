"""Pipeline orchestration tests."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from earth_watch.fetchers import GistempGlobalFetcher, GmlCo2Fetcher
from earth_watch.fetchers.base import FetchResult
from earth_watch.pipeline import build_manifest, run_pipeline
from earth_watch.sources import GML_CO2_ANNMEAN, GML_CO2_GROWTH, GML_CO2_MONTHLY

FIXTURES = Path(__file__).parent / "fixtures"


class FixtureFetcher:
    """Wrap a real fetcher but inject fixture bytes instead of HTTP."""

    def __init__(self, inner, fixture_name: str) -> None:
        self.inner = inner
        self.fixture_name = fixture_name
        self.spec = inner.spec

    def run(self, client=None, get_bytes=None):
        content = (FIXTURES / self.fixture_name).read_bytes()
        fetch = FetchResult.from_bytes(
            self.spec,
            content,
            datetime(2026, 10, 19, 12, 0, tzinfo=timezone.utc),
        )
        return self.inner.process(fetch)


def test_run_pipeline_writes_manifest_and_aggregates(tmp_path: Path):
    fetchers = [
        FixtureFetcher(GmlCo2Fetcher("annmean"), "co2_annmean_mlo.csv"),
        FixtureFetcher(GmlCo2Fetcher("growth"), "co2_gr_mlo.csv"),
        FixtureFetcher(GmlCo2Fetcher("monthly"), "co2_mm_mlo.csv"),
        FixtureFetcher(GistempGlobalFetcher(), "GLB.Ts+dSST.csv"),
    ]
    run_at = datetime(2026, 10, 19, 12, 0, tzinfo=timezone.utc)
    result = run_pipeline(tmp_path, fetchers=fetchers, run_at=run_at)
    assert result.manifest_path.is_file()
    manifest = json.loads(result.manifest_path.read_text())
    assert len(manifest["sources"]) == 4
    assert all(s["sha256"] for s in manifest["sources"])
    assert manifest["run_id"]
    assert manifest["fetch_date"] == "2026-10-19"
    assert (tmp_path / "aggregates" / "latest" / f"{GML_CO2_GROWTH.source_id}.json").is_file()
    assert (
        tmp_path / "raw" / GML_CO2_ANNMEAN.source_id / "2026-10-19" / "co2_annmean_mlo.csv"
    ).is_file()
    assert (tmp_path / "manifests" / "latest.json").is_file()


def test_build_manifest_shape(tmp_path: Path):
    fetchers = [
        FixtureFetcher(GmlCo2Fetcher("growth"), "co2_gr_mlo.csv"),
    ]
    run_at = datetime(2026, 10, 19, 12, 0, tzinfo=timezone.utc)
    result = run_pipeline(tmp_path, fetchers=fetchers, run_at=run_at)
    manifest = json.loads(result.manifest_path.read_text())
    assert manifest["pipeline_version"]
    assert manifest["sources"][0]["url"].startswith("https://")
