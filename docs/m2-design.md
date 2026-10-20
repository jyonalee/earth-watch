# M2 design note — warming chart (a)

## Architecture (Cloudflare-only)

| Piece | Choice |
|-------|--------|
| Ingest | Existing Python Worker `earth-watch-pipeline` (`src/entry.py`, Pyodide), weekly cron + `POST /run` |
| Storage | Private R2 `earth-watch` via `DATA` binding; chart JSON at `aggregates/latest/chart_a_warming.json` |
| Public read | Same Worker: `GET /api/chart-a.json` reads chart JSON from R2; static dashboard under `public/` via Workers **static assets** (`ASSETS`, `run_worker_first: true`) |
| Deploy | `uv sync` + `uv run pywrangler deploy` on push to `main` (Workers Builds) |

GitHub Actions in the Phase 1 plan is **not** used for ingest. CI here remains pytest-only.

### Why static assets on the same Worker

Python Workers support the `ASSETS` binding with `run_worker_first`, so API routes stay in Python while HTML/JS/CSS are served from the asset store without a separate Pages project or public R2 bucket. No third-party scripts; the chart uses canvas + `fetch('/api/chart-a.json')`.

## Data

| Series | Official URL | Notes |
|--------|--------------|--------|
| GISTEMP v4 global | `https://data.giss.nasa.gov/gistemp/tabledata_v4/GLB.Ts+dSST.csv` | Native baseline 1951–1980 (`J-D` annual) |
| HadCRUT5 global annual | Met Office diagnostics CSV (5.1.0.0) | Native baseline 1961–1990; re-baselined to 1951–1980 for the chart |
| HadCRUT5 global monthly | Same diagnostics path (monthly) | Stored for parity with M1 raw/aggregate layout; chart uses annual file |
| Berkeley Earth land+ocean | `Land_and_Ocean_summary.txt` on official S3 | Air-above-sea-ice annual column; native 1951–1980 |

## Methods

- **Re-baseline:** for series not already on 1951–1980, subtract the mean of native anomalies over 1951–1980 (equivalent shift for anomaly products).
- **Trends:** OLS on annual anomalies; 95% CI on slope with AR(1)-inflated standard error (`n_eff = n(1−ρ)/(1+ρ)`).
- **Windows:** 1970–present (through latest year per series) and trailing 20 years.
- **Acceleration:** compare recent vs long-window slopes (intervals treated as separate if 95% CIs on the difference exclude zero); quadratic coefficient reported with CI on 1970–present window.
- **Facts vs read:** numeric statements in `facts`; `read` is plain-language interpretation.

## Tests

Offline pytest on fixtures; local Worker check with `pywrangler dev` (scheduled handler, `GET /api/chart-a.json`, `/warming/`).
