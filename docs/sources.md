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

## R2 object layout (M1 pipeline)

Bucket: **`earth-watch`** (private). The **Python Worker** writes via an **R2 binding** (`DATA` → `earth-watch`); no S3 API keys in GitHub or Wrangler.

See [deployment.md](deployment.md) and [README](../README.md).
