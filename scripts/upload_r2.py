#!/usr/bin/env python3
"""Upload pipeline output to Cloudflare R2 (skipped when credentials are absent)."""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

from earth_watch.storage.r2 import (
    apply_raw_dedup,
    credentials_from_env,
    create_s3_client,
    load_latest_manifest,
    upload_pipeline_output,
)


def main() -> int:
    bucket = os.environ.get("R2_BUCKET", "earth-watch").strip()
    output_dir = Path(os.environ.get("OUTPUT_DIR", "output"))

    credentials = credentials_from_env()
    if credentials is None:
        print(
            "Skipping R2 upload: R2_ACCOUNT_ID, R2_ACCESS_KEY_ID, and/or "
            "R2_SECRET_ACCESS_KEY not set.",
            file=sys.stderr,
        )
        return 0

    if not output_dir.is_dir():
        print(f"R2 upload failed: output directory missing: {output_dir}", file=sys.stderr)
        return 1

    manifests_dir = output_dir / "manifests"
    latest_local = manifests_dir / "latest.json"
    if not latest_local.is_file():
        print(f"R2 upload failed: missing local manifest {latest_local}", file=sys.stderr)
        return 1

    manifest = json.loads(latest_local.read_text(encoding="utf-8"))
    client = create_s3_client(credentials)
    previous = load_latest_manifest(client, bucket)
    manifest = apply_raw_dedup(manifest, previous)

    run_id = manifest["run_id"]
    run_path = manifests_dir / f"{run_id}.json"
    payload = json.dumps(manifest, indent=2, sort_keys=True) + "\n"
    run_path.write_text(payload, encoding="utf-8")
    latest_local.write_text(payload, encoding="utf-8")

    result = upload_pipeline_output(client, bucket, output_dir, manifest)
    print(
        f"R2 upload complete: bucket={bucket} uploaded={result.uploaded} "
        f"skipped={result.skipped} manifest={result.manifest_run_key}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
