# Earth Watch

Personal climate dashboard (Phase 1). Milestone **M1** fetches NOAA GML Mauna Loa CO₂ and NASA GISTEMP v4 global temperature; **M2** adds HadCRUT5, Berkeley Earth, warming trends, and chart (a) (`GET /api/chart-a.json`, `/warming/`). **M3** adds Global Carbon Budget + global CO₂ growth, airborne fraction, and chart (b) (`GET /api/chart-b.json`, `/airborne/`). **M4** adds NCEI ocean heat + global SST and chart (c) (`GET /api/chart-c.json`, `/ocean/`).

**Runtime:** Python **Worker** on a weekly cron (and optional authenticated `POST /run`). See [docs/deployment.md](docs/deployment.md) for Workers Builds and secrets. M2 design: [docs/m2-design.md](docs/m2-design.md).

Dataset URLs: [docs/sources.md](docs/sources.md). M3: [docs/m3-design.md](docs/m3-design.md). M4: [docs/m4-design.md](docs/m4-design.md).

## Repository layout

| Path | Role |
|------|------|
| `src/earth_watch/` | Shared pipeline (fetch, validate, aggregate, R2 layout) — stdlib only |
| `src/entry.py` | Cloudflare Worker entry (`scheduled`, public reads, `/run`) |
| `public/` | Static dashboard assets (Workers `ASSETS` binding) |
| `wrangler.jsonc` | Worker name, cron, R2 binding, CPU limit |
| `tests/` | Offline pytest (fixtures + mocked R2 binding) |

## Run locally (CLI, optional)

Writes under `./output/` with the same key layout as R2 (for debugging without deploying).

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
earth-watch-pipeline --output-dir output
pytest -q
```

## Run locally (Worker)

```bash
uv sync
cp .dev.vars.example .dev.vars          # set RUN_SECRET for POST /run
uv run pywrangler dev --test-scheduled
curl "http://localhost:8787/cdn-cgi/local/scheduled?cron=0+6+*+*+1"
curl -X POST "http://127.0.0.1:8787/run" -H "Authorization: Bearer $RUN_SECRET"
```

Package / Pyodide notes: [docs/packages.md](docs/packages.md).

## R2 object layout

| Prefix | Purpose |
|--------|---------|
| `raw/<source_id>/<fetch-date>/<original-filename>` | Exact bytes per run |
| `aggregates/latest/*.json` | Dashboard reads these |
| `aggregates/<fetch-date>/*.json` | Dated snapshots |
| `manifests/<run_id>.json` | Per-run provenance |
| `manifests/latest.json` | Latest run manifest |

Unchanged raw SHA-256 vs `manifests/latest.json` → skip re-uploading the raw object (manifest still records the run).

## CI

GitHub Actions **CI** (`.github/workflows/ci.yml`) runs **pytest only**. Production refresh is **not** on GitHub Actions; Joseph may remove CI later if desired.

Deployment is via **Cloudflare Workers Builds** connected to this repo (no Cloudflare token in GitHub). See [docs/deployment.md](docs/deployment.md).
