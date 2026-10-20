# Data sources (M1)

Verified 2026-10-19 unless noted.

## NOAA GML — Mauna Loa CO2

| Series | URL | Format |
|--------|-----|--------|
| Annual mean | https://gml.noaa.gov/webdata/ccgg/trends/co2/co2_annmean_mlo.csv | CSV: `year,mean,unc` (comment header lines start with `#`) |
| Annual growth | https://gml.noaa.gov/webdata/ccgg/trends/co2/co2_gr_mlo.csv | CSV: `year,ann inc,unc` |
| Monthly | https://gml.noaa.gov/webdata/ccgg/trends/co2/co2_mm_mlo.csv | CSV: `year,month,decimal date,average,deseasonalized,ndays,sdev,unc` |

Citation and use terms are in the file headers. Updates are roughly monthly.

## NASA GISTEMP v4 — global temperature

| Series | URL | Format |
|--------|-----|--------|
| Global LOTI | https://data.giss.nasa.gov/gistemp/tabledata_v4/GLB.Ts+dSST.csv | CSV: title line `Land-Ocean: Global Means`, then monthly and seasonal columns; missing values are `***` |

Version label: **GISTEMP v4** (tabledata_v4 path). Anomalies are vs. 1951–1980.

### Published uncertainty (open question resolved)

GISTEMP’s main temperature table does **not** ship per-month uncertainty columns. NASA publishes uncertainty separately:

1. **Observational uncertainty ensemble (recommended for Phase 2 trends)**  
   - Documentation: https://data.giss.nasa.gov/gistemp/uncertainty/  
   - **Key series (200-member global / hemispheric / zonal monthly ensembles):**  
     https://data.giss.nasa.gov/gistemp/uncertainty/v2.0/KeySeries.zip  
   - **Gridded ensemble summary statistics (netCDF inside ZIP):**  
     https://data.giss.nasa.gov/gistemp/uncertainty/v2.0/GriddedSummary.zip  
   - **Format:** ZIP archives; KeySeries and GriddedSummary contain netCDF (time dimension labeling updated 2024-10-01 per NASA note). HTTP basic auth when prompted: user `uncertainty`, password `analysis`.  
   - **Zenodo mirror (Lenssen et al. 2024, 1880–2020):** https://doi.org/10.5281/zenodo.13343335 — `FinalEnsembleOutput/` with `FullEnsemble/`, `GriddedSummary/`, and `KeySeries/` (very large full download).

2. **Legacy 95% CI table for annual global means (older analysis)**  
   - https://data.giss.nasa.gov/gistemp/uncertainty/v1.2.1/totalCI_ERA.csv  
   - **Format:** CSV columns `year`, `gistemp`, `ci95` (half-width of 95% interval, not a full ensemble).  
   - NASA states this table was created in **2019** and is not the same as the v2.0 ensemble; use for historical reference only.

For Earth Watch chart (a) in M2+, plan to use **KeySeries** (or HadCRUT’s built-in limits) rather than the stale `totalCI_ERA.csv` alone.

## Met Office HadCRUT5 — global temperature (M2)

| Series | URL | Format |
|--------|-----|--------|
| Global monthly (with 95% limits) | https://www.metoffice.gov.uk/hadobs/hadcrut5/data/HadCRUT.5.1.0.0/analysis/diagnostics/HadCRUT.5.1.0.0.analysis.summary_series.global.monthly.csv | CSV: `Time` (`YYYY-MM`), anomaly °C, lower/upper 95% |
| Global annual | https://www.metoffice.gov.uk/hadobs/hadcrut5/data/HadCRUT.5.1.0.0/analysis/diagnostics/HadCRUT.5.1.0.0.analysis.summary_series.global.annual.csv | CSV: `Time` (year), anomaly °C, lower/upper 95% |

Version label: **HadCRUT.5.1.0.0**. Native anomalies vs **1961–1990**; chart (a) re-baselines to **1951–1980**. Licence: [Open Government Licence v3.0](https://www.nationalarchives.gov.uk/doc/open-government-licence/version/3/).

## Berkeley Earth — land + ocean (M2)

| Series | URL | Format |
|--------|-----|--------|
| Global summary | https://berkeley-earth-temperature.s3.us-west-1.amazonaws.com/Global/Land_and_Ocean_summary.txt | Comment header (`%`), then whitespace table; annual anomaly vs **1951–1980** (air above sea ice column) |

Citation: Rohde & Hausfather, ESSD 2020 (see file header). Data use terms: https://berkeleyearth.org/data/

## Global Carbon Budget 2025 (M3)

| Series | URL | Format |
|--------|-----|--------|
| Global budget workbook | https://globalcarbonbudget.org/download/2341/ | XLSX; sheet **Global Carbon Budget** (fossil and land-use emissions in GtC/yr) |

Design: [m3-design.md](m3-design.md).

## NOAA GML — global CO₂ growth (M3)

| Series | URL | Format |
|--------|-----|--------|
| Global annual increase | https://gml.noaa.gov/webdata/ccgg/trends/co2/co2_gr_gl.txt | Whitespace columns: `year`, `growth_ppm`, `unc_ppm` (after `#` headers) |

Chart (b) uses this global series (not Mauna Loa `co2_gr_mlo.csv`) for airborne fraction vs GCB emissions.

## NOAA NCEI — ocean heat & global SST (M4)

| Series | URL | Format |
|--------|-----|--------|
| Global OHC 0–700 m (yearly) | https://www.ncei.noaa.gov/data/oceans/woa/DATA_ANALYSIS/3M_HEAT_CONTENT/DATA/basin/yearly/h22-w0-700m.dat | ASCII: `YEAR WO WOse …` (10²² J) |
| Global OHC 0–2000 m (yearly) | https://www.ncei.noaa.gov/data/oceans/woa/DATA_ANALYSIS/3M_HEAT_CONTENT/DATA/basin/yearly/h22-w0-2000m.dat | Same |
| Global ocean SST anomaly (annual) | https://www.ncei.noaa.gov/access/monitoring/climate-at-a-glance/global/time-series/globe/ocean/ytd/12/1980-2030.json | NCEI Climate at a Glance JSON (`data` keys `YYYY`) |

Design: [m4-design.md](m4-design.md). Chart (c) uses monthly CAG JSON and derives annual SST; anomalies vs **1901–2000** for global ocean.

## R2 object layout (M1 pipeline)

Bucket: **`earth-watch`** (private). The **Python Worker** writes via an **R2 binding** (`DATA` → `earth-watch`); no S3 API keys in GitHub or Wrangler.

See [deployment.md](deployment.md) and [README](../README.md).
