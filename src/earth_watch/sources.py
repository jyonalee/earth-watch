"""Canonical source URLs and identifiers."""

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class SourceSpec:
    """Metadata for one downloadable climate series."""

    source_id: str
    url: str
    version: str | None = None


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

M2_TEMPERATURE_SOURCES: tuple[SourceSpec, ...] = (
    GISTEMP_GLOBAL,
    HADCRUT5_GLOBAL_MONTHLY,
    HADCRUT5_GLOBAL_ANNUAL,
    BERKELEY_LAND_OCEAN,
)
