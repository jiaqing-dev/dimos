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

import numpy as np
import pytest

from dimos.memory.timeseries.legacy import LegacyPickleStore
from dimos.msgs.sensor_msgs.Image import Image, ImageFormat
from dimos.utils import dataset_manifest as dm
from dimos.utils import dataset_paths as dpaths


def _patch_data_dir(monkeypatch: pytest.MonkeyPatch, tmp_path) -> None:
    monkeypatch.setattr(
        dpaths,
        "get_data_dir",
        lambda name=None: tmp_path / name if name else tmp_path,
    )


def test_stream_dir_stats_empty_dir(tmp_path) -> None:
    stream = tmp_path / "lidar"
    stream.mkdir()
    stats = dm.stream_dir_stats(stream)
    assert stats["frames"] == 0


def test_stream_dir_stats_with_frames(tmp_path) -> None:
    store = LegacyPickleStore(tmp_path)
    img = Image.from_numpy(
        np.zeros((4, 4, 3), dtype=np.uint8),
        format=ImageFormat.RGB,
        frame_id="cam",
    )
    store.save(img)
    stats = dm.stream_dir_stats(tmp_path)
    assert stats["frames"] == 1
    assert stats["first_timestamp"] == img.ts
    assert stats["last_timestamp"] == img.ts


def test_write_go2_manifest_roundtrip(tmp_path, monkeypatch) -> None:
    _patch_data_dir(monkeypatch, tmp_path)

    (tmp_path / "capture" / "lidar").mkdir(parents=True)
    store = LegacyPickleStore(tmp_path / "capture" / "lidar")
    img = Image.from_numpy(
        np.ones((2, 2, 3), dtype=np.uint8),
        format=ImageFormat.RGB,
        frame_id="cam",
    )
    store.save(img)

    manifest_path = dm.write_go2_manifest("capture")
    assert manifest_path.is_file()
    data = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert data["dataset_name"] == "capture"
    assert data["streams"]["lidar"]["frames"] == 1
    summary = dm.format_manifest_summary(data)
    assert "lidar" in summary


def test_write_go2_manifest_rejects_path_traversal(tmp_path, monkeypatch) -> None:
    _patch_data_dir(monkeypatch, tmp_path)

    with pytest.raises(ValueError, match="single directory name"):
        dm.write_go2_manifest("../outside")

    assert not (tmp_path.parent / "outside").exists()
