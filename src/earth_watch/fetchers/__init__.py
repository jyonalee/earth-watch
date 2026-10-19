"""Climate source fetchers."""

from earth_watch.fetchers.base import BaseFetcher, FetchResult, SourceRecord, SourceValidationError
from earth_watch.fetchers.gistemp import GistempGlobalFetcher
from earth_watch.fetchers.gml_co2 import GmlCo2Fetcher, gml_fetchers

__all__ = [
    "BaseFetcher",
    "FetchResult",
    "GistempGlobalFetcher",
    "GmlCo2Fetcher",
    "SourceRecord",
    "SourceValidationError",
    "gml_fetchers",
]
