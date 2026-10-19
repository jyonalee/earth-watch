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

**Production:** set `RUN_SECRET` after the first successful deploy (see [Workers Builds settings](#workers-builds-settings)). **Local dev:** `.dev.vars` or `uv run pywrangler secret put RUN_SECRET` — never commit the value.

### 3. Workers Builds (GitHub → Cloudflare)

**Prerequisite:** the GitHub app **Cloudflare Workers and Pages** must have repository access to `jyonalee/earth-watch` ([configure installations](https://github.com/settings/installations)). Without it, Cloudflare build settings show **This project is disconnected from your Git account** and pushes to **`main`** start no build.

1. **New Worker:** Cloudflare dashboard → **Workers & Pages** → **Create application** → **GitHub** → select repo `jyonalee/earth-watch`.
2. **Existing Worker:** open the Worker → **Settings** → **Builds** → **Connect** ([Workers Builds](https://developers.cloudflare.com/workers/ci-cd/builds/)).
   After connecting or reconnecting, push a commit to **`main`** to start a build (connecting alone does not build).
3. Root directory: repository root (where `wrangler.jsonc` lives).

   Application code lives under `src/` next to `entry.py` so Wrangler bundles `earth_watch` with the Worker. Do **not** copy the package into `python_modules/` — `pywrangler deploy` rebuilds that directory from `pylock.toml` and would drop vendored copies.
4. Ensure the build service account can deploy Workers and access the **`earth-watch`** R2 bucket binding (same account as the bucket).
5. Do **not** store a Cloudflare API token in GitHub; Builds uses Cloudflare’s OAuth integration.

#### Workers Builds settings

- **Build command:** `uv sync`
- **Deploy command:** `uv run pywrangler deploy`
- **Production branch:** `main`
- **Worker name:** must equal `name` in `wrangler.jsonc` (`earth-watch-pipeline`)

Keep **Builds for non-production branches** unchecked unless the **Version command** is a non-deploying preview upload. If the Version command is `uv run pywrangler deploy`, a push to any branch deploys to production.

If a PR changes the build or deploy commands, update these Workers Builds settings **before merging**.

After the **first successful deploy**, set **`RUN_SECRET`** as a **runtime secret** (Worker → **Settings** → **Variables & Secrets**). Generate with `openssl rand -hex 32`; never commit it.

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
