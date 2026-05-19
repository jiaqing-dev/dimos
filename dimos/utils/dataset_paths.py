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

"""Safe path helpers for datasets stored under ``data/``."""

from __future__ import annotations

from pathlib import Path

from dimos.utils.data import get_data_dir


def validate_dataset_name(dataset_name: str) -> str:
    """Return a normalized dataset name that cannot escape the data directory."""
    name = dataset_name.strip()
    if not name:
        raise ValueError("Dataset name must not be empty")

    path = Path(name)
    if path.is_absolute():
        raise ValueError("Dataset name must be relative to the data directory")
    if ".." in path.parts:
        raise ValueError("Dataset name must not contain '..'")

    base = get_data_dir().resolve()
    target = (base / path).resolve(strict=False)
    try:
        target.relative_to(base)
    except ValueError as exc:
        raise ValueError("Dataset path must stay within the data directory") from exc
    if target == base:
        raise ValueError("Dataset name must identify a subdirectory under data/")

    return path.as_posix()


def safe_dataset_dir(dataset_name: str) -> Path:
    """Resolve a validated dataset directory under ``data/``."""
    safe_name = validate_dataset_name(dataset_name)
    return (get_data_dir().resolve() / safe_name).resolve(strict=False)


def dataset_has_pickles(dataset_root: Path, streams: tuple[str, ...]) -> bool:
    """Return whether any stream directory already contains recorded pickle frames."""
    for stream in streams:
        if next((dataset_root / stream).glob("*.pickle"), None) is not None:
            return True
    return False
