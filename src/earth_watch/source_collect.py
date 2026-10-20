"""Resilient per-source fetch with optional R2 recovery for charts."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Sequence

from earth_watch.fetchers.base import AsyncBytesFetcher, BaseFetcher, SourceRecord, SourceValidationError
from earth_watch.freshness import (
    LastDataPoint,
    cadence_for_source,
    is_stale,
    last_data_point_from_record,
)
@dataclass(frozen=True, slots=True)
class SourceOutcome:
    spec: Any
    status: str
    error: str | None
    record: SourceRecord | None
    chart_record: SourceRecord | None
    recovered_from_previous: bool
    last_data_point: LastDataPoint | None
    http_last_modified: str | None
    stale: bool


def _outcome_from_record(record: SourceRecord, *, run_at: datetime) -> SourceOutcome:
    point = last_data_point_from_record(record)
    cadence = cadence_for_source(record.spec.source_id)
    return SourceOutcome(
        spec=record.spec,
        status="ok",
        error=None,
        record=record,
        chart_record=record,
        recovered_from_previous=False,
        last_data_point=point,
        http_last_modified=record.fetch.http_last_modified,
        stale=is_stale(point, cadence=cadence, as_of=run_at),
    )


async def _recover_record(
    bucket: Any,
    fetcher: BaseFetcher,
    previous_entry: dict[str, Any] | None,
) -> SourceRecord | None:
    if not previous_entry or not bucket:
        return None
    raw_key = (previous_entry.get("r2") or {}).get("raw")
    if not raw_key:
        return None
    from earth_watch.storage.r2 import read_object_bytes

    content = await read_object_bytes(bucket, str(raw_key))
    if content is None:
        return None
    fetched_at_raw = previous_entry.get("fetched_at_utc") or "1970-01-01T00:00:00Z"
    fetched_at = datetime.fromisoformat(fetched_at_raw.replace("Z", "+00:00"))
    from earth_watch.fetchers.base import FetchResult

    fetch = FetchResult.from_bytes(
        fetcher.spec,
        content,
        fetched_at,
        http_last_modified=previous_entry.get("http_last_modified"),
    )
    return fetcher.process(fetch)


async def collect_source_outcomes_async(
    fetchers: list[BaseFetcher],
    get_bytes: AsyncBytesFetcher,
    *,
    run_at: datetime,
    bucket: Any | None = None,
    previous_manifest: dict[str, Any] | None = None,
) -> list[SourceOutcome]:
    prev_by_id = {
        str(e["source_id"]): e for e in (previous_manifest or {}).get("sources", [])
    }
    outcomes: list[SourceOutcome] = []
    for fetcher in fetchers:
        source_id = fetcher.spec.source_id
        prev_entry = prev_by_id.get(source_id)
        try:
            record = await fetcher.run_async(get_bytes)
            outcomes.append(_outcome_from_record(record, run_at=run_at))
        except (SourceValidationError, OSError, ValueError) as exc:
            recovered = await _recover_record(bucket, fetcher, prev_entry)
            point = last_data_point_from_record(recovered) if recovered else None
            if recovered is None and prev_entry:
                ldp = prev_entry.get("last_data_point")
                if isinstance(ldp, dict) and "year" in ldp:
                    point = LastDataPoint(
                        year=int(ldp["year"]),
                        month=int(ldp["month"]) if ldp.get("month") is not None else None,
                    )
            cadence = cadence_for_source(source_id)
            outcomes.append(
                SourceOutcome(
                    spec=fetcher.spec,
                    status="failed",
                    error=str(exc),
                    record=None,
                    chart_record=recovered,
                    recovered_from_previous=recovered is not None,
                    last_data_point=point,
                    http_last_modified=prev_entry.get("http_last_modified") if prev_entry else None,
                    stale=is_stale(point, cadence=cadence, as_of=run_at),
                )
            )
    return outcomes


def collect_source_outcomes_sync(
    fetchers: list[BaseFetcher],
    get_bytes=None,
    *,
    run_at: datetime | None = None,
) -> list[SourceOutcome]:
    run_at = run_at or datetime.now(timezone.utc)
    outcomes: list[SourceOutcome] = []
    for fetcher in fetchers:
        try:
            record = fetcher.run(get_bytes=get_bytes)
            outcomes.append(_outcome_from_record(record, run_at=run_at))
        except (SourceValidationError, OSError, ValueError) as exc:
            cadence = cadence_for_source(fetcher.spec.source_id)
            outcomes.append(
                SourceOutcome(
                    spec=fetcher.spec,
                    status="failed",
                    error=str(exc),
                    record=None,
                    chart_record=None,
                    recovered_from_previous=False,
                    last_data_point=None,
                    http_last_modified=None,
                    stale=True,
                )
            )
    return outcomes


def chart_records(outcomes: Sequence[SourceOutcome]) -> list[SourceRecord]:
    return [o.chart_record for o in outcomes if o.chart_record is not None]
