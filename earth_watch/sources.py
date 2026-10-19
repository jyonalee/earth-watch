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

M1_SOURCES: tuple[SourceSpec, ...] = (
    GML_CO2_ANNMEAN,
    GML_CO2_GROWTH,
    GML_CO2_MONTHLY,
    GISTEMP_GLOBAL,
)
