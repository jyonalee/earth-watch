"""Canonical source URLs and identifiers."""

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class SourceSpec:
    """Metadata for one downloadable climate series."""

    source_id: str
    url: str
    version: str | None = None
    storage_filename: str | None = None


GML_CO2_ANNMEAN = SourceSpec(
    source_id="gml_co2_annmean_mlo",
    url="https://gml.noaa.gov/webdata/ccgg/trends/co2/co2_annmean_mlo.csv",
)

GML_CO2_GROWTH = SourceSpec(
    source_id="gml_co2_gr_mlo",
    url="https://gml.noaa.gov/webdata/ccgg/trends/co2/co2_gr_mlo.csv",
)

GML_CO2_MONTHLY = SourceSpec(
    source_id="gml_co2_mm_mlo",
    url="https://gml.noaa.gov/webdata/ccgg/trends/co2/co2_mm_mlo.csv",
)

GISTEMP_GLOBAL = SourceSpec(
    source_id="gistemp_glb_ts_dsst",
    url="https://data.giss.nasa.gov/gistemp/tabledata_v4/GLB.Ts+dSST.csv",
    version="GISTEMP v4",
)

HADCRUT5_GLOBAL_MONTHLY = SourceSpec(
    source_id="hadcrut5_global_monthly",
    url=(
        "https://www.metoffice.gov.uk/hadobs/hadcrut5/data/HadCRUT.5.1.0.0/analysis/"
        "diagnostics/HadCRUT.5.1.0.0.analysis.summary_series.global.monthly.csv"
    ),
    version="HadCRUT.5.1.0.0",
)

HADCRUT5_GLOBAL_ANNUAL = SourceSpec(
    source_id="hadcrut5_global_annual",
    url=(
        "https://www.metoffice.gov.uk/hadobs/hadcrut5/data/HadCRUT.5.1.0.0/analysis/"
        "diagnostics/HadCRUT.5.1.0.0.analysis.summary_series.global.annual.csv"
    ),
    version="HadCRUT.5.1.0.0",
)

BERKELEY_LAND_OCEAN = SourceSpec(
    source_id="berkeley_earth_land_ocean",
    url="https://berkeley-earth-temperature.s3.us-west-1.amazonaws.com/Global/Land_and_Ocean_summary.txt",
    version="Berkeley Earth land+ocean (HadSST4)",
)

M1_SOURCES: tuple[SourceSpec, ...] = (
    GML_CO2_ANNMEAN,
    GML_CO2_GROWTH,
    GML_CO2_MONTHLY,
    GISTEMP_GLOBAL,
)

GML_CO2_GR_GLOBAL = SourceSpec(
    source_id="gml_co2_gr_global",
    url="https://gml.noaa.gov/webdata/ccgg/trends/co2/co2_gr_gl.txt",
    version="NOAA GML global annual CO2 increase",
)

GCB_GLOBAL_BUDGET_2025 = SourceSpec(
    source_id="gcb_global_budget_2025",
    url="https://globalcarbonbudget.org/download/2341/",
    version="Global Carbon Budget 2025",
    storage_filename="Global_Carbon_Budget_2025.xlsx",
)

NCEI_OHC_0_700M_YEARLY = SourceSpec(
    source_id="ncei_ohc_0_700m_yearly",
    url=(
        "https://www.ncei.noaa.gov/data/oceans/woa/DATA_ANALYSIS/3M_HEAT_CONTENT/DATA/"
        "basin/yearly/h22-w0-700m.dat"
    ),
    version="NCEI global OHC 0-700 m",
)

NCEI_OHC_0_2000M_YEARLY = SourceSpec(
    source_id="ncei_ohc_0_2000m_yearly",
    url=(
        "https://www.ncei.noaa.gov/data/oceans/woa/DATA_ANALYSIS/3M_HEAT_CONTENT/DATA/"
        "basin/yearly/h22-w0-2000m.dat"
    ),
    version="NCEI global OHC 0-2000 m",
)

CAG_OCEAN_ANNUAL_START_YEAR = 1980


def cag_annual_end_years_to_try(utc_year: int) -> tuple[int, ...]:
    """Try current UTC year first, then previous (NCEI may lag the annual endpoint)."""
    return (utc_year, utc_year - 1)


def cag_ocean_annual_url(end_year: int) -> str:
    """Official NCEI Climate at a Glance annual global ocean JSON (YTD month 12)."""
    return (
        "https://www.ncei.noaa.gov/access/monitoring/climate-at-a-glance/global/"
        f"time-series/globe/ocean/ytd/12/{CAG_OCEAN_ANNUAL_START_YEAR}-{end_year}.json"
    )


NCEI_CAG_OCEAN_ANNUAL = SourceSpec(
    source_id="ncei_cag_ocean_sst",
    url=cag_ocean_annual_url(2000),
    version="NCEI Climate at a Glance global ocean (annual)",
    storage_filename="ncei_cag_ocean_annual.json",
)

M2_TEMPERATURE_SOURCES: tuple[SourceSpec, ...] = (
    GISTEMP_GLOBAL,
    HADCRUT5_GLOBAL_MONTHLY,
    HADCRUT5_GLOBAL_ANNUAL,
    BERKELEY_LAND_OCEAN,
)
