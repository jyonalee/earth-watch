# Earth Watch

Personal climate dashboard (Phase 1). Milestone **M1** provides a small Python pipeline that fetches official NOAA GML Mauna Loa CO₂ and NASA GISTEMP v4 global temperature data, validates schemas and plausible value ranges, and writes JSON aggregates plus run manifests (URL, version, fetch time UTC, SHA-256).

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

Local output mirrors the R2 layout (see below):

- `output/raw/<source_id>/<YYYY-MM-DD>/<original-filename>` — verbatim downloads
- `output/aggregates/latest/<source_id>.json` — dashboard-shaped summaries
- `output/aggregates/<YYYY-MM-DD>/<source_id>.json` — dated aggregate copies
- `output/manifests/<run_id>.json` and `output/manifests/latest.json`

Optional R2 upload: set `R2_ACCOUNT_ID`, `R2_ACCESS_KEY_ID`, and `R2_SECRET_ACCESS_KEY`, then `python scripts/upload_r2.py`. The step is skipped when any of those variables are unset.

## Cloudflare R2 storage

Permanent store: private bucket **`earth-watch`** (S3-compatible API, endpoint `https://<R2_ACCOUNT_ID>.r2.cloudflarestorage.com`).

| Prefix | Purpose |
|--------|---------|
| `raw/<source_id>/<fetch-date>/<original-filename>` | Exact downloaded bytes for each run (dated for reproducibility) |
| `aggregates/latest/*.json` | What the dashboard reads |
| `aggregates/<fetch-date>/*.json` | Dated aggregate snapshots |
| `manifests/<run_id>.json` | Per-run provenance |
| `manifests/latest.json` | Pointer to the most recent run manifest |

If a source’s SHA-256 matches the previous `manifests/latest.json`, the pipeline may **skip re-uploading** the raw object and reuse the existing `r2.raw` key; the new manifest still records the fetch.

### GitHub Actions secrets (Joseph)

Create a **bucket-scoped** R2 API token (not an account-wide Cloudflare API token):

1. Cloudflare dashboard → **R2** → **Manage R2 API Tokens**.
2. **Create API token** → permission **Object Read & Write**, scope to bucket **`earth-watch`** only.
3. Copy the **Access Key ID**, **Secret Access Key**, and **Account ID** shown for S3 clients.
4. In the GitHub repo → **Settings** → **Secrets and variables** → **Actions**, add:

| Secret | Value |
|--------|--------|
| `R2_ACCOUNT_ID` | Cloudflare account ID |
| `R2_ACCESS_KEY_ID` | R2 access key ID |
| `R2_SECRET_ACCESS_KEY` | R2 secret access key |

Bucket name `earth-watch` is configured in the workflow (not a secret). R2 upload runs on **push to `main`**, **`workflow_dispatch`**, and the **weekly schedule** — not on pull requests.

## CI

- **CI** — pytest on push/PR (`.github/workflows/ci.yml`)
- **Data pipeline** — fetch, artifact upload, optional R2 (`.github/workflows/pipeline.yml`)
