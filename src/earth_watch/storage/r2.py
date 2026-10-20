"""R2 object layout and uploads (binding or test double)."""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any, Protocol

from earth_watch.layout import MANIFEST_LATEST_KEY, chart_a_dated_key, chart_a_latest_key, manifest_run_key
from earth_watch.pipeline import aggregate_json_bytes
from earth_watch.fetchers.base import SourceRecord


class R2BucketBinding(Protocol):
    async def get(self, key: str) -> Any: ...

    async def put(
        self,
        key: str,
        value: bytes | str,
        *,
        http_metadata: dict[str, str] | None = None,
    ) -> Any: ...


@dataclass(frozen=True, slots=True)
class UploadItem:
    key: str
    body: bytes
    content_type: str
    skip: bool = False


@dataclass(frozen=True, slots=True)
class UploadResult:
    uploaded: int
    skipped: int
    manifest_run_key: str
    manifest_latest_key: str


async def load_latest_manifest(bucket: R2BucketBinding) -> dict[str, Any] | None:
    obj = await bucket.get(MANIFEST_LATEST_KEY)
    if obj is None:
        return None
    text = await obj.text()
    return json.loads(text)


def previous_raw_key_by_source(manifest: dict[str, Any] | None) -> dict[str, str]:
    if not manifest:
        return {}
    mapping: dict[str, str] = {}
    for entry in manifest.get("sources", []):
        source_id = entry.get("source_id")
        r2 = entry.get("r2") or {}
        raw_key = r2.get("raw")
        if source_id and raw_key:
            mapping[str(source_id)] = str(raw_key)
    return mapping


def previous_sha256_by_source(manifest: dict[str, Any] | None) -> dict[str, str]:
    if not manifest:
        return {}
    mapping: dict[str, str] = {}
    for entry in manifest.get("sources", []):
        source_id = entry.get("source_id")
        digest = entry.get("sha256")
        if source_id and digest:
            mapping[str(source_id)] = str(digest)
    return mapping


def apply_raw_dedup(manifest: dict[str, Any], previous: dict[str, Any] | None) -> dict[str, Any]:
    """Mark raw uploads skipped when SHA-256 matches the previous latest manifest."""
    prev_sha = previous_sha256_by_source(previous)
    prev_raw = previous_raw_key_by_source(previous)
    sources = []
    for entry in manifest["sources"]:
        updated = dict(entry)
        source_id = entry["source_id"]
        digest = entry["sha256"]
        if prev_sha.get(source_id) == digest and source_id in prev_raw:
            updated["raw_upload_skipped"] = True
            updated["r2"] = dict(entry["r2"])
            updated["r2"]["raw"] = prev_raw[source_id]
        else:
            updated["raw_upload_skipped"] = False
        sources.append(updated)
    result = dict(manifest)
    result["sources"] = sources
    return result


def plan_r2_uploads(
    manifest: dict[str, Any],
    records: list[SourceRecord],
    *,
    chart_a_bytes: bytes | None = None,
    fetch_date: str | None = None,
) -> list[UploadItem]:
    by_id = {record.spec.source_id: record for record in records}
    items: list[UploadItem] = []

    for entry in manifest["sources"]:
        source_id = entry["source_id"]
        record = by_id[source_id]
        agg_bytes = aggregate_json_bytes(record)
        skip_raw = bool(entry.get("raw_upload_skipped"))
        items.append(
            UploadItem(
                key=entry["r2"]["raw"],
                body=record.fetch.content,
                content_type="text/csv",
                skip=skip_raw,
            )
        )
        items.append(
            UploadItem(
                key=entry["r2"]["aggregate_latest"],
                body=agg_bytes,
                content_type="application/json",
            )
        )
        items.append(
            UploadItem(
                key=entry["r2"]["aggregate_dated"],
                body=agg_bytes,
                content_type="application/json",
            )
        )

    manifest_bytes = (json.dumps(manifest, indent=2, sort_keys=True) + "\n").encode("utf-8")
    items.append(
        UploadItem(
            key=manifest_run_key(manifest["run_id"]),
            body=manifest_bytes,
            content_type="application/json",
        )
    )
    items.append(
        UploadItem(
            key=MANIFEST_LATEST_KEY,
            body=manifest_bytes,
            content_type="application/json",
        )
    )
    if chart_a_bytes is not None:
        dated = fetch_date or manifest.get("fetch_date", "")
        items.append(
            UploadItem(
                key=chart_a_latest_key(),
                body=chart_a_bytes,
                content_type="application/json",
            )
        )
        if dated:
            items.append(
                UploadItem(
                    key=chart_a_dated_key(dated),
                    body=chart_a_bytes,
                    content_type="application/json",
                )
            )
    return items


async def upload_to_r2(
    bucket: R2BucketBinding,
    manifest: dict[str, Any],
    records: list[SourceRecord],
    *,
    chart_a_bytes: bytes | None = None,
    fetch_date: str | None = None,
) -> UploadResult:
    items = plan_r2_uploads(
        manifest,
        records,
        chart_a_bytes=chart_a_bytes,
        fetch_date=fetch_date,
    )
    uploaded = 0
    skipped = 0
    for item in items:
        if item.skip:
            skipped += 1
            continue
        await bucket.put(
            item.key,
            item.body,
            http_metadata={"contentType": item.content_type},
        )
        uploaded += 1

    run_key = manifest_run_key(manifest["run_id"])
    return UploadResult(
        uploaded=uploaded,
        skipped=skipped,
        manifest_run_key=run_key,
        manifest_latest_key=MANIFEST_LATEST_KEY,
    )
