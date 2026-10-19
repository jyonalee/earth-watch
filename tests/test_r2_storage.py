"""R2 layout and upload planning (mocked S3 client, no network)."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from earth_watch.layout import (
    MANIFEST_LATEST_KEY,
    aggregate_dated_key,
    aggregate_latest_key,
    manifest_run_key,
    raw_object_key,
    run_id_from_datetime,
)
from earth_watch.pipeline import build_manifest
from earth_watch.fetchers.base import FetchResult
from earth_watch.sources import GML_CO2_GROWTH
from earth_watch.storage.r2 import (
    apply_raw_dedup,
    credentials_from_env,
    plan_uploads,
    upload_pipeline_output,
)


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
    from earth_watch.fetchers.gml_co2 import GmlCo2Fetcher

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


def test_plan_uploads_skips_raw_put_when_flagged(tmp_path: Path):
    fetch = _sample_record()
    from earth_watch.fetchers.gml_co2 import GmlCo2Fetcher

    record = GmlCo2Fetcher("growth").process(fetch)
    run_at = datetime(2026, 10, 19, 12, 0, tzinfo=timezone.utc)
    manifest = build_manifest(
        [record],
        run_id="20261019T120000Z",
        fetch_date="2026-10-19",
        run_at=run_at,
    )
    manifest["sources"][0]["raw_upload_skipped"] = True
    manifest["sources"][0]["r2"]["raw"] = "raw/gml_co2_gr_mlo/2026-10-12/co2_gr_mlo.csv"

    out = tmp_path
    for entry in manifest["sources"]:
        raw_path = out / entry["local"]["raw"]
        agg_path = out / entry["local"]["aggregate"]
        raw_path.parent.mkdir(parents=True, exist_ok=True)
        agg_path.parent.mkdir(parents=True, exist_ok=True)
        raw_path.write_bytes(fetch.content)
        agg_path.write_text(json.dumps(record.aggregates) + "\n")

    (out / "manifests").mkdir()
    (out / "manifests" / "20261019T120000Z.json").write_text(json.dumps(manifest) + "\n")

    items = plan_uploads(out, manifest)
    skipped = [i for i in items if i.skip]
    assert len(skipped) == 1
    assert skipped[0].key == "raw/gml_co2_gr_mlo/2026-10-12/co2_gr_mlo.csv"


def test_upload_pipeline_output_calls_put_object(tmp_path: Path):
    fetch = _sample_record()
    from earth_watch.fetchers.gml_co2 import GmlCo2Fetcher

    record = GmlCo2Fetcher("growth").process(fetch)
    manifest = build_manifest(
        [record],
        run_id="20261019T120000Z",
        fetch_date="2026-10-19",
        run_at=datetime(2026, 10, 19, 12, 0, tzinfo=timezone.utc),
    )
    out = tmp_path
    for entry in manifest["sources"]:
        raw_path = out / entry["local"]["raw"]
        agg_path = out / entry["local"]["aggregate"]
        raw_path.parent.mkdir(parents=True, exist_ok=True)
        agg_path.parent.mkdir(parents=True, exist_ok=True)
        raw_path.write_bytes(fetch.content)
        agg_path.write_text(json.dumps(record.aggregates) + "\n")
    (out / "manifests").mkdir()
    (out / "manifests" / "20261019T120000Z.json").write_text(json.dumps(manifest) + "\n")

    client = MagicMock()
    result = upload_pipeline_output(client, "earth-watch", out, manifest)
    assert result.uploaded > 0
    assert client.put_object.call_count == result.uploaded
    keys = [call.kwargs["Key"] for call in client.put_object.call_args_list]
    assert manifest_run_key("20261019T120000Z") in keys
    assert MANIFEST_LATEST_KEY in keys


def test_credentials_from_env_missing(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.delenv("R2_ACCOUNT_ID", raising=False)
    monkeypatch.delenv("R2_ACCESS_KEY_ID", raising=False)
    monkeypatch.delenv("R2_SECRET_ACCESS_KEY", raising=False)
    assert credentials_from_env() is None
