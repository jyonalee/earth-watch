#!/usr/bin/env python3
"""Upload pipeline output to Cloudflare R2 (skipped when credentials are absent)."""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path


def main() -> int:
    token = os.environ.get("CLOUDFLARE_API_TOKEN")
    account_id = os.environ.get("CLOUDFLARE_ACCOUNT_ID")
    bucket = os.environ.get("R2_BUCKET", "earth-watch")
    output_dir = Path(os.environ.get("OUTPUT_DIR", "output"))

    if not token or not account_id:
        print(
            "Skipping R2 upload: CLOUDFLARE_API_TOKEN and/or CLOUDFLARE_ACCOUNT_ID not set.",
            file=sys.stderr,
        )
        return 0

    if not output_dir.is_dir():
        print(f"R2 upload failed: output directory missing: {output_dir}", file=sys.stderr)
        return 1

    env = os.environ.copy()
    env["CLOUDFLARE_API_TOKEN"] = token
    env["CLOUDFLARE_ACCOUNT_ID"] = account_id

    uploaded = 0
    for path in sorted(output_dir.rglob("*")):
        if not path.is_file():
            continue
        key = path.relative_to(output_dir).as_posix()
        object_name = f"{bucket}/{key}"
        result = subprocess.run(
            [
                "npx",
                "--yes",
                "wrangler@3",
                "r2",
                "object",
                "put",
                object_name,
                f"--file={path}",
            ],
            env=env,
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            print(result.stdout, file=sys.stderr)
            print(result.stderr, file=sys.stderr)
            print(f"R2 upload failed for {key}", file=sys.stderr)
            return result.returncode
        uploaded += 1

    print(f"Uploaded {uploaded} files to R2 bucket {bucket}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
