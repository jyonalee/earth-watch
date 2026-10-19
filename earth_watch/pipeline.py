"""End-to-end pipeline: fetch, validate, aggregate, write outputs."""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import httpx

from earth_watch import __version__
from earth_watch.fetchers import BaseFetcher, GistempGlobalFetcher, gml_fetchers
from earth_watch.fetchers.base import SourceRecord


@dataclass(frozen=True, slots=True)
class PipelineResult:
    """Paths and records produced by a pipeline run."""

    output_dir: Path
    records: list[SourceRecord]
    manifest_path: Path


def default_fetchers() -> list[BaseFetcher]:
    return [*gml_fetchers(), GistempGlobalFetcher()]


def run_pipeline(
    output_dir: Path,
    fetchers: list[BaseFetcher] | None = None,
    client: httpx.Client | None = None,
) -> PipelineResult:
    output_dir = output_dir.resolve()
    aggregates_dir = output_dir / "aggregates"
    raw_dir = output_dir / "raw"
    aggregates_dir.mkdir(parents=True, exist_ok=True)
    raw_dir.mkdir(parents=True, exist_ok=True)

    fetchers = fetchers or default_fetchers()
    records: list[SourceRecord] = []

    owns_client = client is None
    if owns_client:
        client = httpx.Client(timeout=120.0, follow_redirects=True)

    try:
        for fetcher in fetchers:
            record = fetcher.run(client=client)
            records.append(record)
            source_id = record.spec.source_id
            (raw_dir / f"{source_id}.csv").write_bytes(record.fetch.content)
            agg_path = aggregates_dir / f"{source_id}.json"
            agg_path.write_text(
                json.dumps(record.aggregates, indent=2, sort_keys=True) + "\n",
                encoding="utf-8",
            )
    finally:
        if owns_client and client is not None:
            client.close()

    manifest = build_manifest(records)
    manifest_path = output_dir / "manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    return PipelineResult(output_dir=output_dir, records=records, manifest_path=manifest_path)


def build_manifest(records: list[SourceRecord]) -> dict[str, Any]:
    run_at = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    sources = []
    for record in records:
        fetched = record.fetch.fetched_at.replace(microsecond=0).isoformat().replace("+00:00", "Z")
        sources.append(
            {
                "source_id": record.spec.source_id,
                "url": record.spec.url,
                "version": record.spec.version,
                "fetched_at_utc": fetched,
                "sha256": record.fetch.sha256,
                "aggregate_file": f"aggregates/{record.spec.source_id}.json",
                "raw_file": f"raw/{record.spec.source_id}.csv",
            }
        )
    return {
        "pipeline_version": __version__,
        "run_at_utc": run_at,
        "sources": sources,
    }
