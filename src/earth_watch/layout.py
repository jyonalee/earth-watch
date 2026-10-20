"""R2 object key layout for Earth Watch."""

from __future__ import annotations

from datetime import datetime, timezone


def run_id_from_datetime(when: datetime) -> str:
    """UTC run identifier used in manifest object keys."""
    utc = when.astimezone(timezone.utc).replace(microsecond=0)
    return utc.strftime("%Y%m%dT%H%M%SZ")


def fetch_date_from_datetime(when: datetime) -> str:
    """Calendar date (UTC) for dated raw and aggregate copies."""
    utc = when.astimezone(timezone.utc)
    return utc.strftime("%Y-%m-%d")


def original_filename_from_url(url: str) -> str:
    return url.rstrip("/").split("/")[-1]


def raw_object_key(source_id: str, fetch_date: str, original_filename: str) -> str:
    return f"raw/{source_id}/{fetch_date}/{original_filename}"


def aggregate_latest_key(source_id: str) -> str:
    return f"aggregates/latest/{source_id}.json"


def aggregate_dated_key(source_id: str, fetch_date: str) -> str:
    return f"aggregates/{fetch_date}/{source_id}.json"


def manifest_run_key(run_id: str) -> str:
    return f"manifests/{run_id}.json"


MANIFEST_LATEST_KEY = "manifests/latest.json"


def chart_a_latest_key() -> str:
    return "aggregates/latest/chart_a_warming.json"


def chart_a_dated_key(fetch_date: str) -> str:
    return f"aggregates/{fetch_date}/chart_a_warming.json"
