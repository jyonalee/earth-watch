"""Uniform fetcher interface for climate sources."""

from __future__ import annotations

import hashlib
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

import httpx

from earth_watch.sources import SourceSpec


class SourceValidationError(ValueError):
    """Raised when downloaded data fails schema or range checks."""


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

    def fetch(self, client: httpx.Client | None = None) -> FetchResult:
        owns_client = client is None
        if owns_client:
            client = httpx.Client(timeout=120.0, follow_redirects=True)
        try:
            response = client.get(self.spec.url)
            response.raise_for_status()
            fetched_at = datetime.now(timezone.utc)
            return FetchResult.from_bytes(self.spec, response.content, fetched_at)
        finally:
            if owns_client:
                client.close()

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

    def run(self, client: httpx.Client | None = None) -> SourceRecord:
        fetch = self.fetch(client=client)
        return self.process(fetch)

    @abstractmethod
    def parse(self, content: bytes) -> Any:
        """Parse raw bytes into a structured object (typically a DataFrame)."""

    @abstractmethod
    def validate(self, frame: Any) -> None:
        """Raise SourceValidationError if schema or values are unexpected."""

    @abstractmethod
    def compute_aggregates(self, frame: Any) -> dict[str, Any]:
        """Return small JSON-serializable summary statistics."""
