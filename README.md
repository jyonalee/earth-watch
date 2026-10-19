# Earth Watch

Personal climate dashboard (Phase 1). Milestone **M1** provides a small Python pipeline that fetches official NOAA GML Mauna Loa CO₂ and NASA GISTEMP v4 global temperature data, validates schemas and plausible value ranges, and writes JSON aggregates plus a `manifest.json` (URL, version, fetch time UTC, SHA-256).

Dataset URLs and GISTEMP uncertainty notes: [docs/sources.md](docs/sources.md).

## Run locally

Requirements: **Python 3.12+**.

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"

# Fetch live data and write ./output/
earth-watch-pipeline --output-dir output

# Unit tests (offline fixtures only)
pytest -q
```

Outputs:

- `output/manifest.json` — provenance for each source
- `output/aggregates/<source_id>.json` — small summaries (latest values, row counts)
- `output/raw/<source_id>.csv` — verbatim downloads (not committed)

Optional R2 upload (GitHub Actions or local): set `CLOUDFLARE_API_TOKEN` and `CLOUDFLARE_ACCOUNT_ID`; see `scripts/upload_r2.py`. The step is skipped when those variables are unset.

## CI

- **CI** — pytest on push/PR (`.github/workflows/ci.yml`)
- **Data pipeline** — scheduled + manual run; uploads `output/` as a workflow artifact (`.github/workflows/pipeline.yml`)
