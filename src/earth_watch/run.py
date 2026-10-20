"""Shared pipeline execution for CLI and Cloudflare Worker."""

from __future__ import annotations

import time
from datetime import datetime, timezone
from typing import Any, Callable

from earth_watch.fetchers.base import AsyncBytesFetcher, SourceRecord
from earth_watch.chart_a import build_chart_a_payload, chart_a_json_bytes
from earth_watch.chart_b import build_chart_b_payload, chart_b_json_bytes
from earth_watch.chart_c import build_chart_c_payload, chart_c_json_bytes
from earth_watch.layout import (
    chart_a_latest_key,
    chart_b_latest_key,
    chart_c_latest_key,
    fetch_date_from_datetime,
    run_id_from_datetime,
)
from earth_watch.pipeline import build_manifest, default_fetchers
from earth_watch.source_collect import chart_records, collect_source_outcomes_async
from earth_watch.storage.r2 import (
    apply_raw_dedup,
    load_latest_manifest,
    load_object_bytes,
    upload_to_r2,
)


async def _try_chart(
    bucket: Any,
    key: str,
    build_payload: Callable[..., dict[str, Any]],
    to_bytes: Callable[[dict[str, Any]], bytes],
    records: list[SourceRecord],
    run_at: datetime,
) -> bytes | None:
    try:
        return to_bytes(build_payload(records, run_at=run_at))
    except Exception:
        return await load_object_bytes(bucket, key)


async def run_pipeline_to_r2(
    bucket: Any,
    get_bytes: AsyncBytesFetcher,
    run_at: datetime | None = None,
) -> dict[str, Any]:
    started = time.perf_counter()
    run_at = run_at or datetime.now(timezone.utc)
    fetchers = default_fetchers()
    previous = await load_latest_manifest(bucket)
    outcomes = await collect_source_outcomes_async(
        fetchers,
        get_bytes,
        run_at=run_at,
        bucket=bucket,
        previous_manifest=previous,
    )
    manifest = build_manifest(
        outcomes,
        run_id=run_id_from_datetime(run_at),
        fetch_date=fetch_date_from_datetime(run_at),
        run_at=run_at,
        previous_manifest=previous,
    )
    manifest = apply_raw_dedup(manifest, previous)
    records = chart_records(outcomes)
    chart_a_bytes = await _try_chart(
        bucket,
        chart_a_latest_key(),
        build_chart_a_payload,
        chart_a_json_bytes,
        records,
        run_at,
    )
    chart_b_bytes = await _try_chart(
        bucket,
        chart_b_latest_key(),
        build_chart_b_payload,
        chart_b_json_bytes,
        records,
        run_at,
    )
    chart_c_bytes = await _try_chart(
        bucket,
        chart_c_latest_key(),
        build_chart_c_payload,
        chart_c_json_bytes,
        records,
        run_at,
    )
    upload_result = await upload_to_r2(
        bucket,
        manifest,
        [o.record for o in outcomes if o.record is not None],
        chart_a_bytes=chart_a_bytes,
        chart_b_bytes=chart_b_bytes,
        chart_c_bytes=chart_c_bytes,
        fetch_date=manifest["fetch_date"],
    )
    elapsed = time.perf_counter() - started
    failed = sum(1 for o in outcomes if o.status == "failed")
    return {
        "run_id": manifest["run_id"],
        "fetch_date": manifest["fetch_date"],
        "sources": len(manifest["sources"]),
        "sources_failed": failed,
        "uploaded": upload_result.uploaded,
        "skipped": upload_result.skipped,
        "manifest_key": upload_result.manifest_run_key,
        "wall_seconds": round(elapsed, 3),
    }
