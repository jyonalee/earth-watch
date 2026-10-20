"""Async HTTP GET with optional Last-Modified (Worker or test double)."""

from __future__ import annotations

from earth_watch.fetch_http import HttpFetchResult
from earth_watch.fetchers.base import AsyncBytesFetcher


async def fetch_http(url: str, get_bytes: AsyncBytesFetcher) -> HttpFetchResult:
    try:
        from js import fetch as _js_fetch  # noqa: F401

        from earth_watch.worker_fetch import js_fetch_http

        return await js_fetch_http(url)
    except ImportError:
        return HttpFetchResult(content=await get_bytes(url), last_modified=None)
