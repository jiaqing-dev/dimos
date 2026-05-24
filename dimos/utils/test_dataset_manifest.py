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

from dataclasses import dataclass
import json

import pytest

from dimos.memory.timeseries.legacy import LegacyPickleStore
from dimos.utils import dataset_manifest as dm


@dataclass
class SampleFrame:
    ts: float


def test_stream_dir_stats_empty_dir(tmp_path) -> None:
    stream = tmp_path / "lidar"
    stream.mkdir()
    stats = dm.stream_dir_stats(stream)
    assert stats["frames"] == 0


def test_stream_dir_stats_with_frames(tmp_path) -> None:
    store = LegacyPickleStore(tmp_path)
    frame = SampleFrame(ts=123.0)
    store.save(frame)
    stats = dm.stream_dir_stats(tmp_path)
    assert stats["frames"] == 1
    assert stats["first_timestamp"] == frame.ts
    assert stats["last_timestamp"] == frame.ts


def test_write_go2_manifest_roundtrip(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(dm, "get_data_dir", lambda name: tmp_path / name)

    (tmp_path / "capture" / "lidar").mkdir(parents=True)
    store = LegacyPickleStore(tmp_path / "capture" / "lidar")
    store.save(SampleFrame(ts=456.0))

    manifest_path = dm.write_go2_manifest("capture")
    assert manifest_path.is_file()
    data = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert data["dataset_name"] == "capture"
    assert data["streams"]["lidar"]["frames"] == 1
    summary = dm.format_manifest_summary(data)
    assert "lidar" in summary


@pytest.mark.parametrize("dataset_name", ["../capture", "capture/../../etc", "/tmp/capture", "."])
def test_validate_dataset_name_rejects_paths_outside_data(dataset_name: str) -> None:
    with pytest.raises(ValueError, match="Unsafe dataset name"):
        dm.validate_dataset_name(dataset_name)
