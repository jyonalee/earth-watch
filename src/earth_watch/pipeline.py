"""End-to-end pipeline: fetch, validate, aggregate, write outputs."""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from earth_watch import __version__
from earth_watch.fetchers import (
    BaseFetcher,
    BerkeleyLandOceanFetcher,
    GcbBudgetFetcher,
    GistempGlobalFetcher,
    GmlGlobalGrowthFetcher,
    HadCrut5AnnualFetcher,
    HadCrut5MonthlyFetcher,
    gml_fetchers,
)
from earth_watch.fetchers.base import AsyncBytesFetcher, BytesFetcher, SourceRecord
from earth_watch.layout import (
    aggregate_dated_key,
    aggregate_latest_key,
    fetch_date_from_datetime,
    manifest_run_key,
    storage_filename_for_spec,
    raw_object_key,
    run_id_from_datetime,
)


@dataclass(frozen=True, slots=True)
class PipelineResult:
    """Paths and records produced by a pipeline run."""

    output_dir: Path
    records: list[SourceRecord]
    manifest_path: Path
    manifest: dict[str, Any]
    run_id: str
    fetch_date: str


def default_fetchers() -> list[BaseFetcher]:
    return [
        *gml_fetchers(),
        GistempGlobalFetcher(),
        HadCrut5MonthlyFetcher(),
        HadCrut5AnnualFetcher(),
        BerkeleyLandOceanFetcher(),
        GcbBudgetFetcher(),
        GmlGlobalGrowthFetcher(),
    ]


async def collect_records(
    fetchers: list[BaseFetcher],
    get_bytes: AsyncBytesFetcher,
) -> list[SourceRecord]:
    records: list[SourceRecord] = []
    for fetcher in fetchers:
        records.append(await fetcher.run_async(get_bytes))
    return records


def collect_records_sync(
    fetchers: list[BaseFetcher],
    get_bytes: BytesFetcher | None = None,
) -> list[SourceRecord]:
    return [fetcher.run(get_bytes=get_bytes) for fetcher in fetchers]


def run_pipeline(
    output_dir: Path,
    fetchers: list[BaseFetcher] | None = None,
    get_bytes: BytesFetcher | None = None,
    run_at: datetime | None = None,
) -> PipelineResult:
    output_dir = output_dir.resolve()
    run_at = run_at or datetime.now(timezone.utc)
    run_id = run_id_from_datetime(run_at)
    fetch_date = fetch_date_from_datetime(run_at)

    fetchers = fetchers or default_fetchers()
    records = collect_records_sync(fetchers, get_bytes=get_bytes)

    for record in records:
        _write_source_outputs(output_dir, record, fetch_date)

    manifest = build_manifest(records, run_id=run_id, fetch_date=fetch_date, run_at=run_at)
    manifests_dir = output_dir / "manifests"
    manifests_dir.mkdir(parents=True, exist_ok=True)
    manifest_path = manifests_dir / f"{run_id}.json"
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (manifests_dir / "latest.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    return PipelineResult(
        output_dir=output_dir,
        records=records,
        manifest_path=manifest_path,
        manifest=manifest,
        run_id=run_id,
        fetch_date=fetch_date,
    )


def _write_source_outputs(output_dir: Path, record: SourceRecord, fetch_date: str) -> None:
    source_id = record.spec.source_id
    original_name = storage_filename_for_spec(record.spec)
    raw_rel = Path("raw") / source_id / fetch_date / original_name
    agg_rel = Path("aggregates") / fetch_date / f"{source_id}.json"
    agg_latest_rel = Path("aggregates") / "latest" / f"{source_id}.json"

    raw_path = output_dir / raw_rel
    agg_path = output_dir / agg_rel
    agg_latest_path = output_dir / agg_latest_rel
    raw_path.parent.mkdir(parents=True, exist_ok=True)
    agg_path.parent.mkdir(parents=True, exist_ok=True)
    agg_latest_path.parent.mkdir(parents=True, exist_ok=True)

    raw_path.write_bytes(record.fetch.content)
    payload = json.dumps(record.aggregates, indent=2, sort_keys=True) + "\n"
    agg_path.write_text(payload, encoding="utf-8")
    agg_latest_path.write_text(payload, encoding="utf-8")


def build_manifest(
    records: list[SourceRecord],
    *,
    run_id: str,
    fetch_date: str,
    run_at: datetime,
) -> dict[str, Any]:
    run_at_iso = run_at.astimezone(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    sources = []
    for record in records:
        source_id = record.spec.source_id
        original_name = storage_filename_for_spec(record.spec)
        fetched = record.fetch.fetched_at.replace(microsecond=0).isoformat().replace("+00:00", "Z")
        raw_rel = f"raw/{source_id}/{fetch_date}/{original_name}"
        agg_rel = f"aggregates/{fetch_date}/{source_id}.json"
        sources.append(
            {
                "source_id": source_id,
                "url": record.spec.url,
                "version": record.spec.version,
                "original_filename": original_name,
                "fetched_at_utc": fetched,
                "sha256": record.fetch.sha256,
                "raw_upload_skipped": False,
                "local": {
                    "raw": raw_rel,
                    "aggregate": agg_rel,
                },
                "r2": {
                    "raw": raw_object_key(source_id, fetch_date, original_name),
                    "aggregate_latest": aggregate_latest_key(source_id),
                    "aggregate_dated": aggregate_dated_key(source_id, fetch_date),
                },
            }
        )
    return {
        "pipeline_version": __version__,
        "run_id": run_id,
        "fetch_date": fetch_date,
        "run_at_utc": run_at_iso,
        "sources": sources,
    }


def aggregate_json_bytes(record: SourceRecord) -> bytes:
    return (json.dumps(record.aggregates, indent=2, sort_keys=True) + "\n").encode("utf-8")
