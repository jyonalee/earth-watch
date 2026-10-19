# Deployment (Cloudflare Workers)

Earth Watch M1 runs as a **Python Worker** with a weekly **Cron Trigger**. It fetches NOAA GML and NASA GISTEMP data, validates it, and writes JSON + manifests to the private R2 bucket **`earth-watch`** through an **R2 binding** (no S3 API keys).

## Architecture

```
Cron (weekly) ──► Python Worker (earth-watch-pipeline)
                      │ fetch() to NOAA / NASA
                      ▼
                 R2 binding DATA → bucket earth-watch
                      ├── raw/<source>/<YYYY-MM-DD>/<file>
                      ├── aggregates/latest/*.json
                      ├── aggregates/<YYYY-MM-DD>/*.json
                      └── manifests/<run_id>.json + manifests/latest.json

Manual: POST /run with Authorization: Bearer <RUN_SECRET> (Worker secret)
```

- **CPU:** `limits.cpu_ms` = 120000 (2 minutes) in `wrangler.jsonc`. On Workers Paid, cron schedules at **≥ 1 hour** may use up to **15 minutes** of CPU per invocation ([Workers limits](https://developers.cloudflare.com/workers/platform/limits/)).
- **Memory:** Python Workers use the standard **128 MB** isolate limit.
- **No GitHub Actions** for production data refresh. Optional **CI** workflow runs pytest only.

## One-time setup (Joseph)

### 1. R2 bucket

Bucket **`earth-watch`** already exists (ENAM). No API token is required for the Worker when using an R2 binding.

### 2. Worker secrets

Set a manual-run shared secret (not in git):

```bash
cd /path/to/earth-watch
uv run pywrangler secret put RUN_SECRET
```

### 3. Workers Builds (GitHub → Cloudflare)

1. Cloudflare dashboard → **Workers & Pages** → **Workers Builds** (or your account’s Builds UI).
2. **Create build** → connect GitHub repo `jyonalee/earth-watch`.
3. Production branch: **`main`** (or merge PR #1 first).
4. Build settings (typical for Python Workers):
   - **Install command:** `uv sync && bash scripts/prepare_worker_bundle.sh`
   - **Deploy command:** `uv run pywrangler deploy`
   - Root directory: repository root (where `wrangler.jsonc` lives).
5. Ensure the build service account can deploy Workers and access the **`earth-watch`** R2 bucket binding (same account as the bucket).
6. Do **not** store a Cloudflare API token in GitHub; Builds uses Cloudflare’s OAuth integration.

### 4. Verify

After deploy:

```bash
# Manual run (replace URL and secret)
curl -sS -X POST "https://earth-watch-pipeline.<your-subdomain>.workers.dev/run" \
  -H "Authorization: Bearer YOUR_RUN_SECRET"
```

Cron runs **Mondays 06:00 UTC** (`0 6 * * 1` in `wrangler.jsonc`).

## Local development

Requires [uv](https://docs.astral.sh/uv/) and Node.js (for Wrangler).

```bash
uv sync
uv run pywrangler dev --test-scheduled
```

Trigger scheduled handler locally:

```bash
curl "http://localhost:8787/cdn-cgi/local/scheduled?cron=0+6+*+*+1"
```

Local R2 uses Miniflare simulation under `.wrangler/state` unless you enable [remote bindings](https://developers.cloudflare.com/workers/local-development/#remote-bindings).

Manual `/run` in dev still requires `RUN_SECRET` via `wrangler secret put RUN_SECRET` or `.dev.vars` (never commit):

```
RUN_SECRET=dev-only-secret
```
