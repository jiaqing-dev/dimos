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
from typing import Any

from dimos.core.stream import Out
from dimos.robot.unitree.go2 import connection as go2_connection


@dataclass
class _Frame:
    ts: float


class _ExplodingConnection:
    def lidar_stream(self) -> None:
        raise AssertionError("recording should not subscribe to lidar upstream")

    def odom_stream(self) -> None:
        raise AssertionError("recording should not subscribe to odom upstream")

    def video_stream(self) -> None:
        raise AssertionError("recording should not subscribe to video upstream")


class _FakeStore:
    def __init__(self, name: str) -> None:
        self.name = name
        self.saved: list[Any] = []

    def save(self, *data: Any) -> None:
        self.saved.extend(data)


def test_start_recording_records_from_published_outputs(monkeypatch) -> None:
    stores: list[_FakeStore] = []

    def fake_storage(name: str) -> _FakeStore:
        store = _FakeStore(name)
        stores.append(store)
        return store

    monkeypatch.setattr(go2_connection, "TimedSensorStorage", fake_storage)

    module = go2_connection.GO2Connection.__new__(go2_connection.GO2Connection)
    module.connection = _ExplodingConnection()
    module.lidar = Out(_Frame, "lidar", module)
    module.odom = Out(_Frame, "odom", module)
    module.color_image = Out(_Frame, "color_image", module)
    module._recording_disposables = None
    module._active_recording_name = None

    assert "Recording started" in module.start_recording("capture")

    lidar_frame = _Frame(1.0)
    odom_frame = _Frame(2.0)
    video_frame = _Frame(3.0)
    module.lidar.publish(lidar_frame)
    module.odom.publish(odom_frame)
    module.color_image.publish(video_frame)

    assert [store.name for store in stores] == [
        "capture/lidar",
        "capture/odom",
        "capture/video",
    ]
    assert stores[0].saved == [lidar_frame]
    assert stores[1].saved == [odom_frame]
    assert stores[2].saved == [video_frame]

    module._recording_disposables.dispose()
