# M4 design note — ocean heat and SST (chart c)

## Why not NetCDF in the Worker

OISST daily NetCDF and xarray/netCDF4/h5py are **not** used in the Pyodide cron Worker (bundle size, native extensions). Chart (c) uses **official ASCII/JSON** products only.

## Data sources

| Series | Source | URL | Notes |
|--------|--------|-----|--------|
| OHC 0–700 m & 0–2000 m (global) | NOAA NCEI / WOA heat content | `…/basin/yearly/h22-w0-700m.dat`, `…/h22-w0-2000m.dat` | Whitespace columns `YEAR WO WOse …`; **WO in 10²² J** (10²² Joules) |
| Global ocean SST anomaly | NOAA NCEI **Climate at a Glance** API | `…/globe/ocean/ytd/12/{start}-{end}.json` (annual); plus `…/globe/ocean/1/{month}/{year}-{year}.json` for each month of the latest complete year | Official NOAA JSON; global ocean anomalies vs **1901–2000**. Not OISST grid means; closest official global index without NetCDF. |

OISST v2.1 has no small official global-mean text series; ERDDAP/Climate Reanalyzer were **not** used so the dashboard stays on **ncei.noaa.gov** endpoints only.

## Methods

- **Complete years:** exclude the current UTC calendar year from trends and `last_complete_year`.
- **OHC trend:** OLS on annual WO (10²² J) with AR(1)-adjusted 95% CI; primary chart emphasis on **0–2000 m**; **0–700 m** shown for context.
- **Heating rate:** trend slope (J yr⁻¹) → W m⁻² over Earth area **5.10072×10¹⁴ m²** (WGS84 mean radius 6 371 km); 1 yr = **365.25×86400 s**. Same form as IPCC / Earth energy imbalance summaries (power = dE/dt).
- **Acceleration (OHC 0–2000 m):** compare recent 20-year vs full-period trend slopes (as chart a), with AR(1)-adjusted CIs.
- **SST:** annual mean from monthly keys (complete years); trend with AR(1) CI; latest calendar months reported as published anomalies vs 1901–2000.

## Architecture

Unchanged: Worker cron → R2 `aggregates/latest/chart_c_ocean_heat.json` → `GET /api/chart-c.json` + static `/ocean/`.

## Worker CPU

Parsing is O(n) text/JSON on &lt;100 KB per file; expected sub-second CPU. Local scheduled run (all sources) completed in **~5.5 s** wall time including network (dominated by GCB XLSX and NCEI fetches, not parsing).

## Operational note

NCEI Climate at a Glance may return **HTTP 429** under burst traffic. The Worker fetcher retries 429 up to three times with backoff. Weekly cron spacing is usually sufficient; sustained 429 in production is an uncertainty (see PR).
