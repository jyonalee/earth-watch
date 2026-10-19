"""HTTP fetch for Cloudflare Python Workers (js fetch)."""

from __future__ import annotations

from earth_watch.fetchers.base import SourceValidationError


async def js_fetch_bytes(url: str) -> bytes:
    from js import Object, Uint8Array, fetch

    headers = Object.fromEntries([["User-Agent", "earth-watch/0.1 (climate data pipeline)"]])
    response = await fetch(url, {"headers": headers})
    if not response.ok:
        raise SourceValidationError(f"GET {url} failed: HTTP {response.status}")
    buffer = await response.arrayBuffer()
    view = Uint8Array.new(buffer)
    return bytes(view.to_py())
