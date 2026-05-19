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

"""Dataset manifest helpers for pickle-based recordings (e.g. Go2 lidar/odom/video)."""

from __future__ import annotations

from datetime import datetime, timezone
import importlib.metadata
import json
from pathlib import Path
from typing import Any

from dimos.memory.timeseries.legacy import LegacyPickleStore
from dimos.utils.dataset_paths import safe_dataset_dir

MANIFEST_FILENAME = "dataset_manifest.json"
DEFAULT_GO2_STREAMS = ("lidar", "odom", "video")


def _dimos_version() -> str | None:
    try:
        return importlib.metadata.version("dimos")
    except importlib.metadata.PackageNotFoundError:
        return None


def stream_dir_stats(stream_path: Path) -> dict[str, Any]:
    """Summarize one stream directory without loading every frame."""
    if not stream_path.is_dir():
        return {"frames": 0, "path": str(stream_path)}

    pickles = sorted(stream_path.glob("*.pickle"))
    n = len(pickles)
    out: dict[str, Any] = {"frames": n, "path": str(stream_path)}
    if n == 0:
        return out

    store = LegacyPickleStore(stream_path)
    first_ts = store.first_timestamp()
    last_ts = store.last_timestamp()
    out["first_timestamp"] = first_ts
    out["last_timestamp"] = last_ts
    if first_ts is not None and last_ts is not None:
        out["duration_seconds"] = last_ts - first_ts
    return out


def build_go2_manifest_payload(
    dataset_name: str,
    *,
    streams: tuple[str, ...] = DEFAULT_GO2_STREAMS,
    extra: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Build manifest dict for a dataset rooted at ``data/<dataset_name>/``."""
    root = safe_dataset_dir(dataset_name)
    stream_entries: dict[str, Any] = {}
    for sub in streams:
        stream_entries[sub] = stream_dir_stats(root / sub)

    payload: dict[str, Any] = {
        "schema_version": 1,
        "dataset_name": dataset_name,
        "root_path": str(root),
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "dimos_version": _dimos_version(),
        "streams": stream_entries,
    }
    if extra:
        payload["extra"] = extra
    return payload


def write_go2_manifest(
    dataset_name: str,
    *,
    streams: tuple[str, ...] = DEFAULT_GO2_STREAMS,
    extra: dict[str, Any] | None = None,
) -> Path:
    """Write ``dataset_manifest.json`` under the dataset root."""
    root = safe_dataset_dir(dataset_name)
    root.mkdir(parents=True, exist_ok=True)
    payload = build_go2_manifest_payload(dataset_name, streams=streams, extra=extra)
    manifest_path = root / MANIFEST_FILENAME
    manifest_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return manifest_path


def read_manifest(path: Path | str) -> dict[str, Any]:
    """Load manifest JSON."""
    p = Path(path)
    if p.is_dir():
        p = p / MANIFEST_FILENAME
    return json.loads(p.read_text(encoding="utf-8"))


def format_manifest_summary(data: dict[str, Any]) -> str:
    """Human-readable summary for CLI."""
    lines = [
        f"dataset: {data.get('dataset_name', '?')}",
        f"updated: {data.get('updated_at', '?')}",
        f"dimos:   {data.get('dimos_version', '?')}",
        "streams:",
    ]
    streams = data.get("streams") or {}
    for name, info in streams.items():
        frames = info.get("frames", "?")
        dur = info.get("duration_seconds")
        dur_s = f"{dur:.3f}s" if isinstance(dur, (int, float)) else "?"
        lines.append(f"  - {name}: frames={frames} duration={dur_s}")
    return "\n".join(lines)
