"""Command-line entry points."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from earth_watch.pipeline import run_pipeline


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Earth Watch M1 data pipeline")
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("output"),
        help="Directory for manifest, aggregates, and raw CSV copies",
    )
    args = parser.parse_args(argv)
    result = run_pipeline(args.output_dir)
    print(f"Wrote manifest to {result.manifest_path}")
    print(f"Processed {len(result.records)} sources")
    return 0


if __name__ == "__main__":
    sys.exit(main())
