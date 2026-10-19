# Python package support (Workers / Pyodide)

M1 uses **stdlib only** (`csv`, `json`, `urllib` in CLI; `fetch` in the Worker). No pandas, httpx, or boto3 in the production bundle.

Per [Cloudflare Python packages](https://developers.cloudflare.com/workers/languages/python/packages/):

- Supported: pure-Python and **PyEmscripten** wheels on PyPI, plus packages shipped in [Pyodide](https://pyodide.org/en/stable/usage/packages-in-pyodide.html).
- Not all PyPI packages have PyEmscripten builds; availability must be checked per package before adding a dependency.

## Milestone outlook

| Need | Package | M1 | Notes |
|------|---------|-----|--------|
| CSV tables | stdlib `csv` | Yes | GML, GISTEMP |
| GCB XLSX (M3) | `openpyxl` | Not yet | Verify PyEmscripten wheel via `uv run pywrangler` before relying on it; fallback is pre-convert XLSX to CSV in a separate step |
| Trends / stats (M2+) | `numpy`, `pandas` | Not used | Pyodide includes numpy/pandas builds but they are **large** and increase cold-start/bundle size; prefer stdlib or small pure-Python for aggregates |
| OISST NetCDF (M4) | `xarray`, `netCDF4`, `h5py` | **High risk** | NetCDF/HDF5 C extensions are unlikely to run in Pyodide; expect **M4 to need a different runtime** (e.g. TypeScript Worker with a WASM/JS NetCDF reader, Cloudflare Workflow with external compute, or pre-aggregated NOAA products) |

Joseph should treat **M4 OISST** as an architecture decision, not a drop-in dependency for this Python cron Worker.
