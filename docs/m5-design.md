# M5 design note — unattended Phase 1 operations

## Goals

Make the weekly Worker pipeline **resilient**, **observable** via `/api/health`, and **honest** about data age—without in-Worker alerting (external pollers use health).

## CAG ocean annual URL

`NCEI_CAG_OCEAN_ANNUAL` no longer hardcodes `1980-2026`. At fetch time:

- End year = current UTC calendar year (NCEI often publishes through the current year on the annual YTD endpoint).
- On HTTP 4xx, retry with `end_year - 1`.
- Raw bytes stored under stable name `ncei_cag_ocean_annual.json` (not the URL filename).

## Manifest and health

Each run’s `manifests/latest.json` lists every source with:

| Field | Meaning |
|--------|---------|
| `status` | `ok` or `failed` |
| `error` | Error text when failed, else `null` |
| `last_data_point` | `{year}` or `{year, month}` — latest observation in the parsed frame |
| `http_last_modified` | HTTP `Last-Modified` when the fetch returned it |
| `stale` | Computed against cadence thresholds (see `freshness.py`) |

**Stale thresholds** (months since last data point, evaluated at `run_at_utc`):

| Cadence | Sources | Threshold |
|---------|---------|-----------|
| `monthly` | GML monthly, HadCRUT monthly | 4 |
| `annual` | Most annual series | 20 |
| `gcb` | Global Carbon Budget XLSX | 24 |

Pinned URLs (GCB download id, HadCRUT 5.1.0.0 paths) are **not** auto-discovered; when upstream releases lag beyond thresholds, health marks them `stale`. See [maintenance.md](maintenance.md).

## Partial failure

One failed fetch does **not** abort the run:

1. Manifest records `failed` + error.
2. Chart builders reuse **last good raw** from R2 (previous manifest `r2.raw`) for that source when available.
3. R2 uploads skip updating raw/aggregate for failed sources (last good objects remain).
4. If a chart build still fails, the previous `chart_*.json` in R2 is left unchanged (not overwritten).

## Health API

`GET /api/health` reads `manifests/latest.json` from R2 and returns:

- `run_at_utc`, `run_id`, `fetch_date`
- `sources[]`: `source_id`, `status`, `error`, `last_data_point`, `http_last_modified`, `stale`, `cadence`
- Top-level `stale`: true if any source is stale or failed

No alert hooks in the Worker.

## Dashboard

- Each chart page shows **Data as of** from aggregate fields (`last_complete_year` / `data_as_of`).
- `/` landing: three questions, one-line `read` from each chart API, links to charts and `/methods/`.
- `/methods/`: datasets, baselines, trend method, complete-years rule, AF definition, OHC→W/m², limitations (CAG vs OISST, Berkeley lag).

## CPU

Parsing unchanged; resilience adds manifest fields and optional R2 reads on failure. Expect wall time dominated by HTTP as today.
