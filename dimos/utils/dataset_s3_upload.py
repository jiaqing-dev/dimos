# Copyright 2025-2026 Dimensional Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Upload dataset archives to S3-compatible object storage (optional boto3 extra)."""

from __future__ import annotations

import logging
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

_BOTO3_MISSING = (
    "boto3 is required for S3 upload. Install with: uv sync --extra s3"
)


def _import_boto3():  # type: ignore[no-untyped-def]
    try:
        import boto3

        return boto3
    except ImportError as e:
        raise ImportError(_BOTO3_MISSING) from e


@dataclass(frozen=True)
class S3UploadConfig:
    bucket: str
    endpoint_url: str | None
    region: str | None
    access_key_id: str | None
    secret_access_key: str | None
    key_prefix: str

    @classmethod
    def from_env(cls) -> S3UploadConfig:
        return cls(
            bucket=os.environ.get("DIMOS_S3_BUCKET", "").strip(),
            endpoint_url=os.environ.get("DIMOS_S3_ENDPOINT") or None,
            region=os.environ.get("DIMOS_S3_REGION") or None,
            access_key_id=(
                os.environ.get("DIMOS_S3_ACCESS_KEY_ID")
                or os.environ.get("AWS_ACCESS_KEY_ID")
            ),
            secret_access_key=(
                os.environ.get("DIMOS_S3_SECRET_ACCESS_KEY")
                or os.environ.get("AWS_SECRET_ACCESS_KEY")
            ),
            key_prefix=(os.environ.get("DIMOS_S3_KEY_PREFIX") or "").strip().strip("/"),
        )

    def is_complete(self) -> bool:
        return bool(self.bucket and self.access_key_id and self.secret_access_key)


def s3_client_from_config(cfg: S3UploadConfig):  # type: ignore[no-untyped-def]
    _import_boto3()
    import boto3

    session = boto3.session.Session(
        aws_access_key_id=cfg.access_key_id,
        aws_secret_access_key=cfg.secret_access_key,
        region_name=cfg.region or None,
    )
    kw: dict[str, Any] = {}
    if cfg.endpoint_url:
        kw["endpoint_url"] = cfg.endpoint_url
    return session.client("s3", **kw)


def upload_file_to_s3(
    local_path: Path,
    object_key: str,
    *,
    cfg: S3UploadConfig | None = None,
    extra_args: dict[str, Any] | None = None,
) -> str:
    """Upload a single file to ``s3://bucket/object_key``."""
    cfg = cfg or S3UploadConfig.from_env()
    if not cfg.is_complete():
        raise ValueError(
            "Incomplete S3 configuration: set DIMOS_S3_BUCKET, "
            "DIMOS_S3_ACCESS_KEY_ID (or AWS_ACCESS_KEY_ID), "
            "and DIMOS_S3_SECRET_ACCESS_KEY (or AWS_SECRET_ACCESS_KEY)"
        )
    client = s3_client_from_config(cfg)
    if extra_args:
        client.upload_file(str(local_path), cfg.bucket, object_key, ExtraArgs=extra_args)
    else:
        client.upload_file(str(local_path), cfg.bucket, object_key)
    return f"s3://{cfg.bucket}/{object_key}"


def dataset_auto_upload_enabled() -> bool:
    v = os.environ.get("DIMOS_DATASET_AUTO_UPLOAD", "").strip().lower()
    return v in ("1", "true", "yes", "on")


def run_dataset_pack_and_upload(
    dataset_name: str,
    *,
    key_prefix_cli: str | None = None,
    dry_run: bool = False,
) -> str:
    """Pack ``data/<dataset_name>/`` and upload to S3 (or dry-run). Returns a status line."""
    import tempfile

    from dimos.utils.dataset_pack import (
        build_object_key,
        pack_dataset_tar_gz,
        write_upload_sidecar_meta,
    )

    cfg = S3UploadConfig.from_env()
    eff_prefix = (
        key_prefix_cli.strip().strip("/")
        if key_prefix_cli is not None and key_prefix_cli.strip()
        else cfg.key_prefix
    )
    cfg_eff = S3UploadConfig(
        bucket=cfg.bucket,
        endpoint_url=cfg.endpoint_url,
        region=cfg.region,
        access_key_id=cfg.access_key_id,
        secret_access_key=cfg.secret_access_key,
        key_prefix=eff_prefix,
    )

    with tempfile.TemporaryDirectory(prefix="dimos-dataset-upload-") as tmp:
        arc = Path(tmp) / f"{dataset_name}.tar.gz"
        meta = pack_dataset_tar_gz(dataset_name, arc)
        object_key = build_object_key(
            dataset_name,
            key_prefix=cfg_eff.key_prefix or "",
            content_hash=meta["archive_sha256"],
        )
        sidecar = write_upload_sidecar_meta(arc, meta)
        meta_key = f"{object_key}.meta.json"

        if dry_run:
            bucket = cfg_eff.bucket or "(set DIMOS_S3_BUCKET)"
            return (
                f"Dry-run: packed {arc} ({meta['files_packed']} files, "
                f"sha256={meta['archive_sha256'][:16]}…)\n"
                f"  Sidecar: {sidecar}\n"
                f"  Would upload to s3://{bucket}/{object_key}\n"
                f"  Would upload to s3://{bucket}/{meta_key}"
            )

        _import_boto3()
        if not cfg_eff.is_complete():
            raise ValueError(
                "S3 upload requires DIMOS_S3_BUCKET and credentials "
                "(DIMOS_S3_ACCESS_KEY_ID / DIMOS_S3_SECRET_ACCESS_KEY or AWS_*)."
            )

        uri = upload_file_to_s3(arc, object_key, cfg=cfg_eff)
        meta_uri = upload_file_to_s3(sidecar, meta_key, cfg=cfg_eff)
        return f"Uploaded {uri}\n{meta_uri}"


def maybe_upload_dataset_after_recording(dataset_name: str) -> None:
    """If auto-upload is enabled and S3 is configured, pack and upload (logs errors only)."""
    if not dataset_auto_upload_enabled():
        return

    cfg = S3UploadConfig.from_env()
    if not cfg.is_complete():
        logger.warning(
            "DIMOS_DATASET_AUTO_UPLOAD is set but S3 bucket or credentials are missing; skip upload."
        )
        return

    try:
        msg = run_dataset_pack_and_upload(dataset_name, dry_run=False)
        logger.info("%s", msg.replace("\n", " | "))
    except ImportError:
        logger.error(_BOTO3_MISSING)
    except Exception:
        logger.exception("Dataset auto-upload failed for %s", dataset_name)
