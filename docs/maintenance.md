# Maintenance — pinned releases and health

Earth Watch does **not** auto-discover new dataset versions. When upstream publishes a new release, update the pinned URL in `src/earth_watch/sources.py`, run the test suite, and deploy.

## Pinned URLs to bump manually

| Dataset | Current pin | Where to change |
|---------|-------------|-----------------|
| Global Carbon Budget | `https://globalcarbonbudget.org/download/2341/` (GCB 2025) | `GCB_GLOBAL_BUDGET_2025` — new year → new download id and `storage_filename` |
| HadCRUT5 | `HadCRUT.5.1.0.0` paths on metoffice.gov.uk | `HADCRUT5_GLOBAL_MONTHLY`, `HADCRUT5_GLOBAL_ANNUAL` |

Other sources use stable canonical URLs (NOAA GML, GISTEMP, NCEI OHC `.dat`, NCEI Climate at a Glance with **dynamic end year** for ocean annual JSON).

## Stale detection

`GET /api/health` reads `manifests/latest.json` and marks each source `stale` when the last data point is older than:

| Cadence | Threshold | Examples |
|---------|-----------|----------|
| `monthly` | 4 months | GML Mauna Loa monthly, HadCRUT5 monthly, GISTEMP (last month from table) |
| `annual` | 20 months | Berkeley, NCEI OHC, CAG ocean |
| `gcb` | 24 months | Global Carbon Budget XLSX |

Thresholds and per-source flags are defined in `src/earth_watch/freshness.py` (`STALE_THRESHOLD_MONTHS`, `SOURCE_KNOWN_LAG`). A failed fetch in the latest run sets `status: failed`; aggregates for that source are not overwritten.

### Known lag (`known_lag`)

Some public files update slowly even when the pipeline is healthy. Set `known_lag: true` in `SOURCE_KNOWN_LAG` for those sources (currently **Berkeley Earth land+ocean** — the summary file often lags by months). They may still appear with `stale: true` in health, but overall `status` stays **`ok`** when nothing failed and every stale source is `known_lag`. External monitors should alert on `status: degraded` or `any_failed: true`, not on `stale` alone.

## External monitoring

No alerting is built into the Worker. Poll `GET /api/health` on a schedule outside this repo; treat `any_failed: true` or `status: degraded` as signals to investigate. `stale: true` with `status: ok` usually means only known-lag sources are behind.

## After a bump

1. `uv run pytest -q`
2. Optional: `uv run pywrangler dev --test-scheduled`
3. `uv run pywrangler deploy` (see [deployment.md](deployment.md))
