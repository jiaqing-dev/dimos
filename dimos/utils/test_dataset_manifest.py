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


def _tmp_data_dir(tmp_path):
    def _get_data_dir(name: str | None = None):
        return tmp_path / name if name else tmp_path

    return _get_data_dir


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
    monkeypatch.setattr(dm, "get_data_dir", _tmp_data_dir(tmp_path))

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


def test_dataset_root_path_allows_nested_relative_names(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(dm, "get_data_dir", _tmp_data_dir(tmp_path))

    assert dm.dataset_root_path("capture/session-1") == tmp_path / "capture" / "session-1"


@pytest.mark.parametrize(
    "dataset_name",
    ["", " ", ".", "/etc", "../outside", "capture/../outside", "C:\\tmp\\capture"],
)
def test_dataset_root_path_rejects_unsafe_names(dataset_name: str) -> None:
    with pytest.raises(ValueError):
        dm.dataset_root_path(dataset_name)
