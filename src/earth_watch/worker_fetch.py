"""HTTP fetch for Cloudflare Python Workers (js fetch)."""

from __future__ import annotations

from earth_watch.fetch_http import HttpFetchResult, normalize_http_last_modified
from earth_watch.fetchers.base import SourceValidationError


async def js_fetch_http(url: str) -> HttpFetchResult:
    from asyncio import sleep
    from js import Object, Uint8Array, fetch

    headers = Object.fromEntries([["User-Agent", "earth-watch/0.1 (climate data pipeline)"]])
    last_status = 0
    for attempt in range(4):
        response = await fetch(url, {"headers": headers})
        last_status = int(response.status)
        if response.ok:
            buffer = await response.arrayBuffer()
            view = Uint8Array.new(buffer)
            last_modified = None
            try:
                raw_lm = response.headers.get("Last-Modified")
                last_modified = normalize_http_last_modified(raw_lm)
            except Exception:
                last_modified = None
            return HttpFetchResult(content=bytes(view.to_py()), last_modified=last_modified)
        if last_status == 429 and attempt < 3:
            await sleep(2.0 * (attempt + 1))
            continue
        break
    raise SourceValidationError(f"GET {url} failed: HTTP {last_status}")


async def js_fetch_bytes(url: str) -> bytes:
    return (await js_fetch_http(url)).content
