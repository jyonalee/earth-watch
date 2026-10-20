# M3 design note — airborne fraction (chart b)

## Architecture

Same as M1/M2: Python Worker cron + `POST /run` → private R2 `earth-watch` → public `GET /api/chart-b.json` and static `/airborne/` dashboard (`ASSETS`, `run_worker_first`).

## Data sources

| Role | Source | URL | Format |
|------|--------|-----|--------|
| Fossil + land-use emissions | Global Carbon Budget **2025** (Friedlingstein et al.) | `https://globalcarbonbudget.org/download/2341/` | XLSX (Excel 2007+; GET returns the workbook bytes) |
| Atmospheric CO₂ growth | NOAA GML **global** annual increase | `https://gml.noaa.gov/webdata/ccgg/trends/co2/co2_gr_gl.txt` | Whitespace table after `#` header lines |

**GML choice:** `co2_gr_gl.txt` is the global marine-boundary-layer annual growth used in carbon-budget studies. Mauna Loa `co2_gr_mlo.csv` (already in M1) is station-local; chart (b) uses the global series so AF matches GCB’s atmospheric growth definition.

**ppm → GtC:** multiply annual growth (ppm/yr) by **2.124 GtC per ppm**, the standard conversion for the total atmospheric CO₂ inventory (1 ppm ≈ 2.124 PgC). GCB tab text and carbon-budget methods use this factor; see Friedlingstein et al. 2025 / GCB methods and NOAA GML global trends documentation.

## GCB parsing (Pyodide)

We parse the official XLSX with **openpyxl** (pure Python; vendored via `uv` / Pywrangler). Sheet **`Global Carbon Budget`**, header row `Year | fossil emissions excluding carbonation | land-use change emissions | …`, values in **GtC/yr**. Land-use σ = **±0.7 GtC/yr** (1σ, from sheet notes); fossil σ = **±5%** (1σ).

**Pyodide check:** `openpyxl` is listed in `pyproject.toml` and imported only inside `GcbBudgetFetcher.parse`; local `pywrangler dev` scheduled run must complete without import errors (recorded in PR test notes).

## Methods

- **Airborne fraction (AF):** `(growth_ppm × 2.124) / (fossil + land_use)`; also **fossil-only** AF using fossil denominator only.
- **Uncertainty (1σ, visual):** growth from GML `unc` column × 2.124; emissions σ from fossil 5% and LUC 0.7 GtC/yr combined in quadrature; AF σ via propagation. LUC band shown explicitly on chart.
- **Smoothing:** centered **10-year** mean of annual AF where the full window exists.
- **Trend:** OLS on annual AF since **1960** with AR(1)-adjusted 95% slope CI (same module as chart a).
- **Complete years:** AF years limited to **GCB budget years** (inventory lag; 2025 release through **2024**) intersected with GML; exclude calendar years ≥ current UTC year.

## Read text

Plain-language `read` uses **only** the AF trend 95% CI: if it includes zero → sinks absorb a roughly constant share of emissions; if entirely above zero → rising airborne fraction; if entirely below → declining share.
