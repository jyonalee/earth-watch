"""Public HTTP route helpers (no Worker runtime)."""

from __future__ import annotations

import json

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
    text, headers = health_json_body()
    assert json.loads(text)["status"] == "ok"
