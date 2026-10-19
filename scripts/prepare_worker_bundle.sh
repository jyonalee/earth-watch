#!/usr/bin/env bash
# Vendor the in-repo earth_watch package for Pyodide (python_modules/).
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
mkdir -p "${ROOT}/python_modules"
rm -rf "${ROOT}/python_modules/earth_watch"
cp -a "${ROOT}/earth_watch" "${ROOT}/python_modules/earth_watch"
