"""Object storage backends."""

from earth_watch.storage.r2 import (
    R2Config,
    R2Credentials,
    credentials_from_env,
    create_s3_client,
    load_latest_manifest,
    upload_pipeline_output,
)

__all__ = [
    "R2Config",
    "R2Credentials",
    "credentials_from_env",
    "create_s3_client",
    "load_latest_manifest",
    "upload_pipeline_output",
]
