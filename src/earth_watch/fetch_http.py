"""HTTP fetch result with optional response metadata."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True, slots=True)
class HttpFetchResult:
    content: bytes
    last_modified: str | None = None


def normalize_http_last_modified(value: Any) -> str | None:
    """Map Pyodide/js missing headers to JSON null, not the string 'jsnull'."""
    if value is None:
        return None
    text = value if isinstance(value, str) else str(value)
    text = text.strip()
    if not text or text.lower() in ("jsnull", "null", "none", "undefined"):
        return None
    return text
