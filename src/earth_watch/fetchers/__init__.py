"""Climate source fetchers."""

from earth_watch.fetchers.base import BaseFetcher, FetchResult, SourceRecord, SourceValidationError
from earth_watch.fetchers.berkeley import BerkeleyLandOceanFetcher
from earth_watch.fetchers.gcb import GcbBudgetFetcher
from earth_watch.fetchers.gistemp import GistempGlobalFetcher
from earth_watch.fetchers.gml_co2 import GmlCo2Fetcher, gml_fetchers
from earth_watch.fetchers.gml_global_growth import GmlGlobalGrowthFetcher
from earth_watch.fetchers.hadcrut5 import HadCrut5AnnualFetcher, HadCrut5MonthlyFetcher
from earth_watch.fetchers.ncei_cag_ocean import NceiCagOceanSstFetcher
from earth_watch.fetchers.ncei_ohc import NceiOhcFetcher

__all__ = [
    "BaseFetcher",
    "BerkeleyLandOceanFetcher",
    "FetchResult",
    "GcbBudgetFetcher",
    "GistempGlobalFetcher",
    "GmlCo2Fetcher",
    "GmlGlobalGrowthFetcher",
    "HadCrut5AnnualFetcher",
    "HadCrut5MonthlyFetcher",
    "NceiCagOceanSstFetcher",
    "NceiOhcFetcher",
    "SourceRecord",
    "SourceValidationError",
    "gml_fetchers",
]
