"""Cloudflare R2 uploads via the S3-compatible API."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Protocol

from earth_watch.layout import MANIFEST_LATEST_KEY, manifest_run_key


class S3Client(Protocol):
    def put_object(self, *, Bucket: str, Key: str, Body: bytes, ContentType: str) -> Any: ...

    def get_object(self, *, Bucket: str, Key: str) -> Any: ...


@dataclass(frozen=True, slots=True)
class R2Credentials:
    account_id: str
    access_key_id: str
    secret_access_key: str


@dataclass(frozen=True, slots=True)
class R2Config:
    bucket: str
    credentials: R2Credentials


@dataclass(frozen=True, slots=True)
class UploadItem:
    key: str
    body: bytes
    content_type: str
    skip: bool = False


@dataclass(frozen=True, slots=True)
class UploadResult:
    uploaded: int
    skipped: int
    manifest_run_key: str
    manifest_latest_key: str


def credentials_from_env() -> R2Credentials | None:
    account_id = os.environ.get("R2_ACCOUNT_ID", "").strip()
    access_key_id = os.environ.get("R2_ACCESS_KEY_ID", "").strip()
    secret_access_key = os.environ.get("R2_SECRET_ACCESS_KEY", "").strip()
    if not account_id or not access_key_id or not secret_access_key:
        return None
    return R2Credentials(
        account_id=account_id,
        access_key_id=access_key_id,
        secret_access_key=secret_access_key,
    )


def r2_endpoint_url(account_id: str) -> str:
    """S3 API endpoint for Cloudflare R2 (see Cloudflare R2 docs)."""
    return f"https://{account_id}.r2.cloudflarestorage.com"


def create_s3_client(credentials: R2Credentials) -> Any:
    import boto3

    return boto3.client(
        "s3",
        endpoint_url=r2_endpoint_url(credentials.account_id),
        aws_access_key_id=credentials.access_key_id,
        aws_secret_access_key=credentials.secret_access_key,
        region_name="auto",
    )


def load_latest_manifest(client: S3Client, bucket: str) -> dict[str, Any] | None:
    try:
        response = client.get_object(Bucket=bucket, Key=MANIFEST_LATEST_KEY)
    except Exception as exc:
        code = getattr(exc, "response", {}).get("Error", {}).get("Code")
        if code in {"NoSuchKey", "404", "NotFound"}:
            return None
        raise
    body = response["Body"].read()
    return json.loads(body.decode("utf-8"))


def previous_raw_key_by_source(manifest: dict[str, Any] | None) -> dict[str, str]:
    if not manifest:
        return {}
    mapping: dict[str, str] = {}
    for entry in manifest.get("sources", []):
        source_id = entry.get("source_id")
        r2 = entry.get("r2") or {}
        raw_key = r2.get("raw")
        if source_id and raw_key:
            mapping[str(source_id)] = str(raw_key)
    return mapping


def previous_sha256_by_source(manifest: dict[str, Any] | None) -> dict[str, str]:
    if not manifest:
        return {}
    mapping: dict[str, str] = {}
    for entry in manifest.get("sources", []):
        source_id = entry.get("source_id")
        digest = entry.get("sha256")
        if source_id and digest:
            mapping[str(source_id)] = str(digest)
    return mapping


def plan_uploads(output_dir: Path, manifest: dict[str, Any]) -> list[UploadItem]:
    """Build upload plan from local pipeline output and manifest JSON."""
    output_dir = output_dir.resolve()
    manifest_path = output_dir / "manifests" / f"{manifest['run_id']}.json"
    if not manifest_path.is_file():
        raise FileNotFoundError(f"Run manifest not found: {manifest_path}")

    items: list[UploadItem] = []

    for entry in manifest["sources"]:
        source_id = entry["source_id"]
        rel_raw = Path(entry["local"]["raw"])
        rel_agg = Path(entry["local"]["aggregate"])
        raw_bytes = (output_dir / rel_raw).read_bytes()
        agg_bytes = (output_dir / rel_agg).read_bytes()

        skip_raw = bool(entry.get("raw_upload_skipped"))
        items.append(
            UploadItem(
                key=entry["r2"]["raw"],
                body=raw_bytes,
                content_type="text/csv",
                skip=skip_raw,
            )
        )
        items.append(
            UploadItem(
                key=entry["r2"]["aggregate_latest"],
                body=agg_bytes,
                content_type="application/json",
            )
        )
        items.append(
            UploadItem(
                key=entry["r2"]["aggregate_dated"],
                body=agg_bytes,
                content_type="application/json",
            )
        )

    run_manifest_bytes = manifest_path.read_bytes()
    items.append(
        UploadItem(
            key=manifest_run_key(manifest["run_id"]),
            body=run_manifest_bytes,
            content_type="application/json",
        )
    )
    items.append(
        UploadItem(
            key=MANIFEST_LATEST_KEY,
            body=run_manifest_bytes,
            content_type="application/json",
        )
    )
    return items


def upload_pipeline_output(
    client: S3Client,
    bucket: str,
    output_dir: Path,
    manifest: dict[str, Any],
) -> UploadResult:
    items = plan_uploads(output_dir, manifest)
    uploaded = 0
    skipped = 0
    for item in items:
        if item.skip:
            skipped += 1
            continue
        client.put_object(
            Bucket=bucket,
            Key=item.key,
            Body=item.body,
            ContentType=item.content_type,
        )
        uploaded += 1

    run_key = manifest_run_key(manifest["run_id"])
    return UploadResult(
        uploaded=uploaded,
        skipped=skipped,
        manifest_run_key=run_key,
        manifest_latest_key=MANIFEST_LATEST_KEY,
    )


def apply_raw_dedup(manifest: dict[str, Any], previous: dict[str, Any] | None) -> dict[str, Any]:
    """Mark raw uploads skipped when SHA-256 matches the previous latest manifest."""
    prev_sha = previous_sha256_by_source(previous)
    prev_raw = previous_raw_key_by_source(previous)
    sources = []
    for entry in manifest["sources"]:
        updated = dict(entry)
        source_id = entry["source_id"]
        digest = entry["sha256"]
        if prev_sha.get(source_id) == digest and source_id in prev_raw:
            updated["raw_upload_skipped"] = True
            updated["r2"] = dict(entry["r2"])
            updated["r2"]["raw"] = prev_raw[source_id]
        else:
            updated["raw_upload_skipped"] = False
        sources.append(updated)
    result = dict(manifest)
    result["sources"] = sources
    return result
