"""HTTP fetch helpers (stdlib; Worker uses js fetch via async wrapper)."""

from __future__ import annotations

import urllib.error
import urllib.request

USER_AGENT = "earth-watch/0.1 (climate data pipeline)"


def fetch_bytes_sync(url: str, timeout: float = 120.0) -> bytes:
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            status = getattr(response, "status", 200)
            if status >= 400:
                raise urllib.error.HTTPError(url, status, "HTTP error", response.headers, None)
            return response.read()
    except urllib.error.HTTPError as exc:
        raise RuntimeError(f"GET {url} failed: HTTP {exc.code}") from exc
