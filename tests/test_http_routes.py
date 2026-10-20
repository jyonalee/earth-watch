"""Public HTTP route helpers (no Worker runtime)."""

from __future__ import annotations

import json

from earth_watch.health import health_from_manifest
from earth_watch.http_routes import chart_a_json_body, health_json_body, is_public_api_path


def test_public_api_paths():
    assert is_public_api_path("/api/chart-a.json")
    assert is_public_api_path("/api/chart-b.json")
    assert is_public_api_path("/api/chart-c.json")
    assert is_public_api_path("/api/health")
    assert not is_public_api_path("/run")


def test_chart_a_response_headers():
    body = {"series": []}
    text, headers = chart_a_json_body(body)
    assert "application/json" in headers["Content-Type"]
    assert json.loads(text) == body


def test_health_body():
    summary = health_from_manifest(
        {
            "run_at_utc": "2026-10-19T12:00:00Z",
            "run_id": "r1",
            "fetch_date": "2026-10-19",
            "sources": [
                {
                    "source_id": "gistemp_glb_ts_dsst",
                    "status": "ok",
                    "error": None,
                    "last_data_point": {"year": 2024},
                    "http_last_modified": None,
                    "stale": False,
                    "cadence": "annual",
                }
            ],
        }
    )
    text, headers = health_json_body(summary)
    payload = json.loads(text)
    assert payload["status"] == "ok"
    assert payload["stale"] is False
    assert len(payload["sources"]) == 1
