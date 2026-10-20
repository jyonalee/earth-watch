"""Shared pipeline execution for CLI and Cloudflare Worker."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from earth_watch.fetchers.base import AsyncBytesFetcher
from earth_watch.chart_a import build_chart_a_payload, chart_a_json_bytes
from earth_watch.layout import fetch_date_from_datetime, run_id_from_datetime
from earth_watch.pipeline import build_manifest, collect_records, default_fetchers
from earth_watch.storage.r2 import apply_raw_dedup, load_latest_manifest, upload_to_r2


async def run_pipeline_to_r2(
    bucket: Any,
    get_bytes: AsyncBytesFetcher,
    run_at: datetime | None = None,
) -> dict[str, Any]:
    run_at = run_at or datetime.now(timezone.utc)
    fetchers = default_fetchers()
    records = await collect_records(fetchers, get_bytes)
    manifest = build_manifest(
        records,
        run_id=run_id_from_datetime(run_at),
        fetch_date=fetch_date_from_datetime(run_at),
        run_at=run_at,
    )
    previous = await load_latest_manifest(bucket)
    manifest = apply_raw_dedup(manifest, previous)
    chart_payload = build_chart_a_payload(records)
    chart_bytes = chart_a_json_bytes(chart_payload)
    upload_result = await upload_to_r2(
        bucket,
        manifest,
        records,
        chart_a_bytes=chart_bytes,
        fetch_date=manifest["fetch_date"],
    )
    return {
        "run_id": manifest["run_id"],
        "fetch_date": manifest["fetch_date"],
        "sources": len(manifest["sources"]),
        "uploaded": upload_result.uploaded,
        "skipped": upload_result.skipped,
        "manifest_key": upload_result.manifest_run_key,
    }
