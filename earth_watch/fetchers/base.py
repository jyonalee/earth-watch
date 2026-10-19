"""Uniform fetcher interface for climate sources."""

from __future__ import annotations

import hashlib
from abc import ABC, abstractmethod
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

from earth_watch.net import fetch_bytes_sync
from earth_watch.sources import SourceSpec


class SourceValidationError(ValueError):
    """Raised when downloaded data fails schema or range checks."""


BytesFetcher = Callable[[str], bytes]
AsyncBytesFetcher = Callable[[str], Awaitable[bytes]]


@dataclass(frozen=True, slots=True)
class FetchResult:
    """Raw bytes plus provenance for one source."""

    spec: SourceSpec
    content: bytes
    fetched_at: datetime
    sha256: str

    @classmethod
    def from_bytes(cls, spec: SourceSpec, content: bytes, fetched_at: datetime) -> FetchResult:
        digest = hashlib.sha256(content).hexdigest()
        return cls(spec=spec, content=content, fetched_at=fetched_at, sha256=digest)


@dataclass(frozen=True, slots=True)
class SourceRecord:
    """Parsed and validated source ready for aggregation."""

    spec: SourceSpec
    fetch: FetchResult
    frame: Any
    aggregates: dict[str, Any]


class BaseFetcher(ABC):
    """Download, parse, validate, and summarize one source."""

    spec: SourceSpec

    def fetch(self, get_bytes: BytesFetcher | None = None) -> FetchResult:
        get_bytes = get_bytes or fetch_bytes_sync
        content = get_bytes(self.spec.url)
        fetched_at = datetime.now(timezone.utc)
        return FetchResult.from_bytes(self.spec, content, fetched_at)

    async def fetch_async(self, get_bytes: AsyncBytesFetcher) -> FetchResult:
        content = await get_bytes(self.spec.url)
        fetched_at = datetime.now(timezone.utc)
        return FetchResult.from_bytes(self.spec, content, fetched_at)

    def process(self, fetch: FetchResult) -> SourceRecord:
        frame = self.parse(fetch.content)
        self.validate(frame)
        aggregates = self.compute_aggregates(frame)
        return SourceRecord(
            spec=self.spec,
            fetch=fetch,
            frame=frame,
            aggregates=aggregates,
        )

    def run(self, get_bytes: BytesFetcher | None = None) -> SourceRecord:
        fetch = self.fetch(get_bytes=get_bytes)
        return self.process(fetch)

    async def run_async(self, get_bytes: AsyncBytesFetcher) -> SourceRecord:
        fetch = await self.fetch_async(get_bytes)
        return self.process(fetch)

    @abstractmethod
    def parse(self, content: bytes) -> Any:
        """Parse raw bytes into a structured object."""

    @abstractmethod
    def validate(self, frame: Any) -> None:
        """Raise SourceValidationError if schema or values are unexpected."""

    @abstractmethod
    def compute_aggregates(self, frame: Any) -> dict[str, Any]:
        """Return small JSON-serializable summary statistics."""
