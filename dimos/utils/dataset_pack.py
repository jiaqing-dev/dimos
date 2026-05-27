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

"""Pack ``data/<dataset>/`` into a tar.gz for upload (streaming write, streaming SHA-256)."""

from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import importlib.metadata
import json
import tarfile
from pathlib import Path
from typing import Any

from dimos.utils.dataset_manifest import MANIFEST_FILENAME, dataset_root_path as _dataset_root_path

_ARCHIVE_CHUNK = 1024 * 1024


def _dimos_version() -> str | None:
    try:
        return importlib.metadata.version("dimos")
    except importlib.metadata.PackageNotFoundError:
        return None


def dataset_root_path(dataset_name: str) -> Path:
    """Resolved ``data/<dataset_name>/`` root."""
    return _dataset_root_path(dataset_name)


def build_object_key(
    dataset_name: str,
    *,
    key_prefix: str = "",
    timestamp: datetime | None = None,
) -> str:
    """S3 object key: ``{prefix}{dataset}-{utc}.tar.gz``."""
    ts = timestamp or datetime.now(timezone.utc)
    stamp = ts.strftime("%Y%m%dT%H%M%SZ")
    base = f"{dataset_name}-{stamp}.tar.gz"
    p = (key_prefix or "").strip().strip("/")
    return f"{p}/{base}" if p else base


def pack_dataset_tar_gz(
    dataset_name: str,
    dest_path: Path,
) -> dict[str, Any]:
    """Write a gzip-compressed tar of ``data/<dataset_name>/`` into ``dest_path``.

    Archive members are stored under ``<dataset_name>/...`` relative paths.

    Returns upload metadata (including ``archive_sha256`` of the written file).
    """
    root = dataset_root_path(dataset_name)
    if not root.is_dir():
        raise FileNotFoundError(f"Dataset directory does not exist: {root}")

    files_added = 0
    dest_path.parent.mkdir(parents=True, exist_ok=True)

    with tarfile.open(dest_path, "w:gz", compresslevel=6) as tf:
        for path in sorted(root.rglob("*")):
            if not path.is_file():
                continue
            try:
                rel = path.relative_to(root)
            except ValueError:
                continue
            arcname = f"{dataset_name}/{rel.as_posix()}"
            tf.add(path, arcname=arcname, recursive=False)
            files_added += 1

    if files_added == 0:
        dest_path.unlink(missing_ok=True)
        raise ValueError(f"No files to pack under {root}")

    archive_sha256 = sha256_file(dest_path)
    created_at = datetime.now(timezone.utc).isoformat()
    meta: dict[str, Any] = {
        "schema_version": 1,
        "dataset_name": dataset_name,
        "archive_filename": dest_path.name,
        "archive_sha256": archive_sha256,
        "archive_size_bytes": dest_path.stat().st_size,
        "files_packed": files_added,
        "created_at": created_at,
        "dimos_version": _dimos_version(),
        "includes_manifest": (root / MANIFEST_FILENAME).is_file(),
    }
    return meta


def sha256_file(path: Path) -> str:
    """Streaming SHA-256 hex digest of a file."""
    h = hashlib.sha256()
    with path.open("rb") as f:
        while chunk := f.read(_ARCHIVE_CHUNK):
            h.update(chunk)
    return h.hexdigest()


def write_upload_sidecar_meta(dest_path: Path, meta: dict[str, Any]) -> Path:
    """Write ``<archive>.meta.json`` next to the archive."""
    sidecar = dest_path.with_name(dest_path.name + ".meta.json")
    sidecar.write_text(json.dumps(meta, indent=2), encoding="utf-8")
    return sidecar
