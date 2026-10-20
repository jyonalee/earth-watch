"""Health summary from the latest pipeline manifest."""

from __future__ import annotations

from typing import Any


def health_from_manifest(manifest: dict[str, Any] | None) -> dict[str, Any]:
    if manifest is None:
        return {
            "status": "no_data",
            "stale": True,
            "any_failed": True,
            "run_at_utc": None,
            "run_id": None,
            "fetch_date": None,
            "sources": [],
        }

    sources_out: list[dict[str, Any]] = []
    any_stale = False
    any_failed = False
    actionable_stale = False
    for entry in manifest.get("sources", []):
        status = entry.get("status", "ok")
        stale = bool(entry.get("stale", False))
        known_lag = bool(entry.get("known_lag", False))
        if status == "failed":
            any_failed = True
        if stale:
            any_stale = True
            if not known_lag:
                actionable_stale = True
        sources_out.append(
            {
                "source_id": entry.get("source_id"),
                "status": status,
                "error": entry.get("error"),
                "last_data_point": entry.get("last_data_point"),
                "http_last_modified": entry.get("http_last_modified"),
                "stale": stale,
                "known_lag": known_lag,
                "cadence": entry.get("cadence"),
            }
        )

    overall = "ok"
    if any_failed or actionable_stale:
        overall = "degraded"

    return {
        "status": overall,
        "stale": any_stale,
        "any_failed": any_failed,
        "run_at_utc": manifest.get("run_at_utc"),
        "run_id": manifest.get("run_id"),
        "fetch_date": manifest.get("fetch_date"),
        "pipeline_version": manifest.get("pipeline_version"),
        "sources": sources_out,
    }
