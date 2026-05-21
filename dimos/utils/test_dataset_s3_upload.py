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

import json
import os
from pathlib import Path
import tarfile
from unittest.mock import patch

import pytest

from dimos.utils import dataset_manifest as dm
from dimos.utils.dataset_pack import (
    build_object_key,
    pack_dataset_tar_gz,
    sha256_file,
    write_upload_sidecar_meta,
)
from dimos.utils.dataset_s3_upload import (
    run_dataset_pack_and_upload,
    S3UploadConfig,
    upload_file_to_s3,
)


def test_build_object_key_prefix() -> None:
    from datetime import datetime, timezone

    ts = datetime(2026, 5, 8, 12, 0, 0, tzinfo=timezone.utc)
    k = build_object_key("cap", key_prefix="pre", timestamp=ts)
    assert k == "pre/cap-20260508T120000Z.tar.gz"


def test_pack_dataset_tar_gz_roundtrip(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(
        dm, "get_data_dir", lambda name=None: tmp_path / name if name else tmp_path
    )

    root = tmp_path / "ds1"
    (root / "lidar").mkdir(parents=True)
    (root / "lidar" / "000.pickle").write_bytes(b"abc")
    dm.write_go2_manifest("ds1")

    arc = tmp_path / "out.tar.gz"
    meta = pack_dataset_tar_gz("ds1", arc)
    assert arc.is_file()
    assert meta["files_packed"] >= 2
    assert meta["archive_sha256"] == sha256_file(arc)
    assert meta["includes_manifest"] is True

    with tarfile.open(arc, "r:gz") as tf:
        names = tf.getnames()
    assert any(n.endswith("dataset_manifest.json") for n in names)
    assert any("ds1/lidar/000.pickle" in n for n in names)


def test_pack_dataset_empty_raises(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(
        dm, "get_data_dir", lambda name=None: tmp_path / name if name else tmp_path
    )
    (tmp_path / "empty").mkdir()
    arc = tmp_path / "x.tar.gz"
    with pytest.raises(ValueError, match="No files"):
        pack_dataset_tar_gz("empty", arc)


@pytest.mark.parametrize("name", ["..", ".", "/etc", "nested/name", "a\\b"])
def test_pack_dataset_rejects_unsafe_dataset_names(tmp_path, monkeypatch, name: str) -> None:
    monkeypatch.setattr(
        dm, "get_data_dir", lambda name=None: tmp_path / name if name else tmp_path
    )
    with pytest.raises(ValueError, match="Dataset name"):
        pack_dataset_tar_gz(name, tmp_path / "out.tar.gz")


@pytest.mark.parametrize("name", ["..", ".", "/etc", "nested/name", "a\\b"])
def test_build_object_key_rejects_unsafe_dataset_names(name: str) -> None:
    with pytest.raises(ValueError, match="Dataset name"):
        build_object_key(name)


def test_write_upload_sidecar_meta(tmp_path) -> None:
    arc = tmp_path / "a.tar.gz"
    arc.write_bytes(b"x")
    meta = {"archive_sha256": "deadbeef", "dataset_name": "x"}
    sc = write_upload_sidecar_meta(arc, meta)
    assert sc.name == "a.tar.gz.meta.json"
    assert json.loads(sc.read_text(encoding="utf-8"))["archive_sha256"] == "deadbeef"


def test_run_dataset_pack_and_upload_dry_run(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(
        dm, "get_data_dir", lambda name=None: tmp_path / name if name else tmp_path
    )
    root = tmp_path / "dry_ds"
    (root / "video").mkdir(parents=True)
    (root / "video" / "000.pickle").write_bytes(b"v")
    dm.write_go2_manifest("dry_ds")

    msg = run_dataset_pack_and_upload("dry_ds", dry_run=True)
    assert "Dry-run:" in msg
    assert "Would upload" in msg


def test_run_dataset_pack_and_upload_calls_s3(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(
        dm, "get_data_dir", lambda name=None: tmp_path / name if name else tmp_path
    )
    root = tmp_path / "up_ds"
    (root / "odom").mkdir(parents=True)
    (root / "odom" / "000.pickle").write_bytes(b"o")
    dm.write_go2_manifest("up_ds")

    monkeypatch.setenv("DIMOS_S3_BUCKET", "testbucket")
    monkeypatch.setenv("DIMOS_S3_ACCESS_KEY_ID", "ak")
    monkeypatch.setenv("DIMOS_S3_SECRET_ACCESS_KEY", "sk")

    uploads: list[tuple[Path, str]] = []

    def fake_upload(local_path: Path, object_key: str, *, cfg: S3UploadConfig | None = None, **_: object) -> str:
        uploads.append((local_path, object_key))
        return f"s3://{cfg.bucket}/{object_key}" if cfg else ""

    with patch("dimos.utils.dataset_s3_upload._import_boto3"), patch(
        "dimos.utils.dataset_s3_upload.upload_file_to_s3", side_effect=fake_upload
    ):
        msg = run_dataset_pack_and_upload("up_ds", dry_run=False)

    assert "Uploaded s3://testbucket/" in msg
    assert len(uploads) == 2
    assert uploads[0][0].suffixes[:2] == [".tar", ".gz"]
    assert uploads[0][1].endswith(".tar.gz")
    assert uploads[1][1].endswith(".tar.gz.meta.json")


def test_upload_file_to_s3_mock_client(monkeypatch, tmp_path) -> None:
    monkeypatch.setenv("DIMOS_S3_BUCKET", "b")
    monkeypatch.setenv("DIMOS_S3_ACCESS_KEY_ID", "x")
    monkeypatch.setenv("DIMOS_S3_SECRET_ACCESS_KEY", "y")

    f = tmp_path / "blob.bin"
    f.write_bytes(b"data")

    mock_client = object.__new__(object)
    called = {}

    def upload_file(Filename: str, Bucket: str, Key: str, ExtraArgs: dict | None = None) -> None:
        called["fn"] = Filename
        called["bucket"] = Bucket
        called["key"] = Key

    mock_client.upload_file = upload_file

    with patch("dimos.utils.dataset_s3_upload.s3_client_from_config", return_value=mock_client):
        uri = upload_file_to_s3(f, "prefix/k.tar.gz")

    assert uri == "s3://b/prefix/k.tar.gz"
    assert called["bucket"] == "b"
    assert called["key"] == "prefix/k.tar.gz"


def test_maybe_upload_skips_without_env(monkeypatch) -> None:
    monkeypatch.delenv("DIMOS_DATASET_AUTO_UPLOAD", raising=False)
    from dimos.utils.dataset_s3_upload import maybe_upload_dataset_after_recording

    maybe_upload_dataset_after_recording("any")  # no-op


def test_maybe_upload_logs_when_incomplete(monkeypatch, caplog) -> None:
    import logging

    monkeypatch.setenv("DIMOS_DATASET_AUTO_UPLOAD", "1")
    monkeypatch.delenv("DIMOS_S3_BUCKET", raising=False)
    from dimos.utils.dataset_s3_upload import maybe_upload_dataset_after_recording

    with caplog.at_level(logging.WARNING):
        maybe_upload_dataset_after_recording("x")
    assert "missing" in caplog.text.lower() or "skip" in caplog.text.lower()
