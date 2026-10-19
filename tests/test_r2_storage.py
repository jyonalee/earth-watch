"""R2 layout and upload planning (mocked binding, no network)."""

from __future__ import annotations

import asyncio
import json
from datetime import datetime, timezone

from earth_watch.layout import (
    MANIFEST_LATEST_KEY,
    aggregate_dated_key,
    aggregate_latest_key,
    manifest_run_key,
    raw_object_key,
    run_id_from_datetime,
)
from earth_watch.pipeline import aggregate_json_bytes, build_manifest
from earth_watch.fetchers.base import FetchResult
from earth_watch.fetchers.gml_co2 import GmlCo2Fetcher
from earth_watch.sources import GML_CO2_GROWTH
from earth_watch.storage.r2 import (
    apply_raw_dedup,
    load_latest_manifest,
    plan_r2_uploads,
    upload_to_r2,
)


class _MockObject:
    def __init__(self, text: str) -> None:
        self._text = text

    async def text(self) -> str:
        return self._text


class MockBucket:
    def __init__(self) -> None:
        self.store: dict[str, bytes] = {}
        self.put_calls: list[str] = []

    async def get(self, key: str):
        if key not in self.store:
            return None
        body = self.store[key]
        return _MockObject(body.decode("utf-8"))

    async def put(self, key: str, value: bytes | str, *, http_metadata=None):
        if isinstance(value, str):
            self.store[key] = value.encode("utf-8")
        else:
            self.store[key] = value
        self.put_calls.append(key)


def test_layout_keys():
    assert raw_object_key("gml_co2_gr_mlo", "2026-10-19", "co2_gr_mlo.csv") == (
        "raw/gml_co2_gr_mlo/2026-10-19/co2_gr_mlo.csv"
    )
    assert aggregate_latest_key("gistemp_glb_ts_dsst") == "aggregates/latest/gistemp_glb_ts_dsst.json"
    assert aggregate_dated_key("gistemp_glb_ts_dsst", "2026-10-19") == (
        "aggregates/2026-10-19/gistemp_glb_ts_dsst.json"
    )
    when = datetime(2026, 10, 19, 12, 30, tzinfo=timezone.utc)
    assert run_id_from_datetime(when) == "20261019T123000Z"
    assert manifest_run_key("20261019T123000Z") == "manifests/20261019T123000Z.json"


def _sample_record() -> FetchResult:
    return FetchResult.from_bytes(
        GML_CO2_GROWTH,
        b"year,ann inc,unc\n2025,2.23,0.11\n",
        datetime(2026, 10, 19, 12, 0, tzinfo=timezone.utc),
    )


def test_apply_raw_dedup_reuses_key_when_sha_matches():
    fetch = _sample_record()
    record = GmlCo2Fetcher("growth").process(fetch)
    manifest = build_manifest(
        [record],
        run_id="20261019T120000Z",
        fetch_date="2026-10-19",
        run_at=datetime(2026, 10, 19, 12, 0, tzinfo=timezone.utc),
    )
    previous = {
        "sources": [
            {
                "source_id": GML_CO2_GROWTH.source_id,
                "sha256": fetch.sha256,
                "r2": {"raw": "raw/gml_co2_gr_mlo/2026-10-12/co2_gr_mlo.csv"},
            }
        ]
    }
    updated = apply_raw_dedup(manifest, previous)
    src = updated["sources"][0]
    assert src["raw_upload_skipped"] is True
    assert src["r2"]["raw"] == "raw/gml_co2_gr_mlo/2026-10-12/co2_gr_mlo.csv"


def test_plan_r2_uploads_skips_raw_put_when_flagged():
    fetch = _sample_record()
    record = GmlCo2Fetcher("growth").process(fetch)
    manifest = build_manifest(
        [record],
        run_id="20261019T120000Z",
        fetch_date="2026-10-19",
        run_at=datetime(2026, 10, 19, 12, 0, tzinfo=timezone.utc),
    )
    manifest["sources"][0]["raw_upload_skipped"] = True
    manifest["sources"][0]["r2"]["raw"] = "raw/gml_co2_gr_mlo/2026-10-12/co2_gr_mlo.csv"

    items = plan_r2_uploads(manifest, [record])
    skipped = [i for i in items if i.skip]
    assert len(skipped) == 1
    assert skipped[0].key == "raw/gml_co2_gr_mlo/2026-10-12/co2_gr_mlo.csv"
    assert aggregate_json_bytes(record) in [i.body for i in items if not i.skip]


def test_upload_to_r2_binding():
    asyncio.run(_test_upload_to_r2_binding())


async def _test_upload_to_r2_binding():
    fetch = _sample_record()
    record = GmlCo2Fetcher("growth").process(fetch)
    manifest = build_manifest(
        [record],
        run_id="20261019T120000Z",
        fetch_date="2026-10-19",
        run_at=datetime(2026, 10, 19, 12, 0, tzinfo=timezone.utc),
    )
    bucket = MockBucket()
    result = await upload_to_r2(bucket, manifest, [record])
    assert result.uploaded > 0
    assert manifest_run_key("20261019T120000Z") in bucket.put_calls
    assert MANIFEST_LATEST_KEY in bucket.put_calls


def test_load_latest_manifest_from_binding():
    asyncio.run(_test_load_latest_manifest_from_binding())


async def _test_load_latest_manifest_from_binding():
    bucket = MockBucket()
    payload = {"run_id": "x"}
    bucket.store[MANIFEST_LATEST_KEY] = json.dumps(payload).encode("utf-8")
    loaded = await load_latest_manifest(bucket)
    assert loaded == payload
