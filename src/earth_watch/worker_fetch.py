"""HTTP fetch for Cloudflare Python Workers (js fetch)."""

from __future__ import annotations

from earth_watch.fetchers.base import SourceValidationError


async def js_fetch_bytes(url: str) -> bytes:
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
            return bytes(view.to_py())
        if last_status == 429 and attempt < 3:
            await sleep(2.0 * (attempt + 1))
            continue
        break
    raise SourceValidationError(f"GET {url} failed: HTTP {last_status}")
