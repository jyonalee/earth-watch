"""Earth Watch pipeline Worker (cron + authenticated manual run)."""

from __future__ import annotations

import hmac
from urllib.parse import urlparse

from workers import Response, WorkerEntrypoint

from earth_watch.run import run_pipeline_to_r2
from earth_watch.worker_fetch import js_fetch_bytes


class Default(WorkerEntrypoint):
    async def scheduled(self, controller, env, ctx):
        await run_pipeline_to_r2(self.env.DATA, js_fetch_bytes)

    async def fetch(self, request):
        path = urlparse(request.url).path
        if path != "/run":
            return Response("Not found", status=404)

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
