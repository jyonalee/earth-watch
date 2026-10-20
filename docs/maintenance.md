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
| `monthly` | 4 months | GML Mauna Loa monthly, HadCRUT5 monthly |
| `annual` | 20 months | GISTEMP, Berkeley, NCEI OHC, CAG ocean |
| `gcb` | 24 months | Global Carbon Budget XLSX |

Thresholds are defined in `src/earth_watch/freshness.py` (`STALE_THRESHOLD_MONTHS`). A failed fetch in the latest run sets `status: failed`; aggregates for that source are not overwritten.

## External monitoring

No alerting is built into the Worker. Poll `GET /api/health` on a schedule outside this repo; treat `stale: true`, `any_failed: true`, or `status: degraded` as signals to investigate.

## After a bump

1. `uv run pytest -q`
2. Optional: `uv run pywrangler dev --test-scheduled`
3. `uv run pywrangler deploy` (see [deployment.md](deployment.md))
