"""Earth Watch pipeline Worker (cron, public chart reads, authenticated manual run)."""

from __future__ import annotations

import hmac
import json
from urllib.parse import urlparse

from workers import Response, WorkerEntrypoint

from earth_watch.http_routes import (
    CHART_A_API_PATH,
    CHART_B_API_PATH,
    CHART_C_API_PATH,
    HEALTH_API_PATH,
    chart_a_json_response,
    chart_b_json_response,
    chart_c_json_response,
    health_json_response,
    is_public_api_path,
)
from earth_watch.layout import chart_a_latest_key, chart_b_latest_key, chart_c_latest_key
from earth_watch.run import run_pipeline_to_r2
from earth_watch.worker_fetch import js_fetch_bytes


class Default(WorkerEntrypoint):
    async def scheduled(self, controller, env, ctx):
        await run_pipeline_to_r2(self.env.DATA, js_fetch_bytes)

    async def fetch(self, request):
        path = urlparse(request.url).path

        if path == HEALTH_API_PATH:
            return health_json_response()

        if path == CHART_A_API_PATH:
            obj = await self.env.DATA.get(chart_a_latest_key())
            if obj is None:
                return Response("Chart data not available yet", status=404)
            text = await obj.text()
            return chart_a_json_response(json.loads(text))

        if path == CHART_B_API_PATH:
            obj = await self.env.DATA.get(chart_b_latest_key())
            if obj is None:
                return Response("Chart data not available yet", status=404)
            text = await obj.text()
            return chart_b_json_response(json.loads(text))

        if path == CHART_C_API_PATH:
            obj = await self.env.DATA.get(chart_c_latest_key())
            if obj is None:
                return Response("Chart data not available yet", status=404)
            text = await obj.text()
            return chart_c_json_response(json.loads(text))

        if path == "/run":
            if request.method != "POST":
                return Response("Method not allowed", status=405, headers={"Allow": "POST"})

            secret = getattr(self.env, "RUN_SECRET", None)
            if not secret:
                return Response("RUN_SECRET not configured", status=503)

            auth = request.headers.get("Authorization") or ""
            prefix = "Bearer "
            if not auth.startswith(prefix):
                return Response("Unauthorized", status=401)
            token = auth[len(prefix) :]
            if not hmac.compare_digest(token, secret):
                return Response("Unauthorized", status=401)

            summary = await run_pipeline_to_r2(self.env.DATA, js_fetch_bytes)
            return Response.json(summary)

        assets = getattr(self.env, "ASSETS", None)
        if assets is not None and not is_public_api_path(path):
            return await assets.fetch(request)

        return Response("Not found", status=404)
