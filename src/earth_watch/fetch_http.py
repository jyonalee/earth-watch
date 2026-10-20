"""HTTP fetch result with optional response metadata."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class HttpFetchResult:
    content: bytes
    last_modified: str | None = None
