"""Climate source fetchers."""

from earth_watch.fetchers.base import BaseFetcher, FetchResult, SourceRecord, SourceValidationError
from earth_watch.fetchers.berkeley import BerkeleyLandOceanFetcher
from earth_watch.fetchers.gistemp import GistempGlobalFetcher
from earth_watch.fetchers.gml_co2 import GmlCo2Fetcher, gml_fetchers
from earth_watch.fetchers.hadcrut5 import HadCrut5AnnualFetcher, HadCrut5MonthlyFetcher

__all__ = [
    "BaseFetcher",
    "BerkeleyLandOceanFetcher",
    "FetchResult",
    "GistempGlobalFetcher",
    "GmlCo2Fetcher",
    "HadCrut5AnnualFetcher",
    "HadCrut5MonthlyFetcher",
    "SourceRecord",
    "SourceValidationError",
    "gml_fetchers",
]
