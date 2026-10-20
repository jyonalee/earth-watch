"""HTTP helpers for the Worker (public reads + JSON responses)."""

from __future__ import annotations

import json
from typing import Any

CHART_A_API_PATH = "/api/chart-a.json"
CHART_B_API_PATH = "/api/chart-b.json"
CHART_C_API_PATH = "/api/chart-c.json"
HEALTH_API_PATH = "/api/health"


def is_public_api_path(path: str) -> bool:
    return path in {CHART_A_API_PATH, CHART_B_API_PATH, CHART_C_API_PATH, HEALTH_API_PATH}


def chart_json_body(payload: dict[str, Any]) -> tuple[str, dict[str, str]]:
    body = json.dumps(payload, separators=(",", ":"))
    headers = {
        "Content-Type": "application/json; charset=utf-8",
        "Cache-Control": "public, max-age=3600",
    }
    return body, headers


def chart_a_json_body(payload: dict[str, Any]) -> tuple[str, dict[str, str]]:
    return chart_json_body(payload)


def chart_b_json_body(payload: dict[str, Any]) -> tuple[str, dict[str, str]]:
    return chart_json_body(payload)


def chart_c_json_body(payload: dict[str, Any]) -> tuple[str, dict[str, str]]:
    return chart_json_body(payload)


def health_json_body(summary: dict[str, Any] | None = None) -> tuple[str, dict[str, str]]:
    payload = summary if summary is not None else {"status": "no_data", "stale": True, "sources": []}
    return json.dumps(payload, separators=(",", ":")), {
        "Content-Type": "application/json; charset=utf-8",
        "Cache-Control": "public, max-age=300",
    }


def chart_a_json_response(payload: dict[str, Any]):
    from workers import Response

    body, headers = chart_a_json_body(payload)
    return Response(body, status=200, headers=headers)


def health_json_response(summary: dict[str, Any] | None = None):
    from workers import Response

    body, headers = health_json_body(summary)
    return Response(body, status=200, headers=headers)


def chart_b_json_response(payload: dict[str, Any]):
    from workers import Response

    body, headers = chart_b_json_body(payload)
    return Response(body, status=200, headers=headers)


def chart_c_json_response(payload: dict[str, Any]):
    from workers import Response

    body, headers = chart_c_json_body(payload)
    return Response(body, status=200, headers=headers)
