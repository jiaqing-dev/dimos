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
    """Validate that ``dataset_name`` is a single directory name under ``data/``."""
    if not dataset_name:
        raise ValueError("Dataset name must not be empty")
    if dataset_name in {".", ".."}:
        raise ValueError(
            f"Dataset name must be a single directory name: {dataset_name!r}"
        )
    if "\x00" in dataset_name or "/" in dataset_name or "\\" in dataset_name:
        raise ValueError(
            f"Dataset name must be a single directory name: {dataset_name!r}"
        )
    if Path(dataset_name).is_absolute():
        raise ValueError(f"Dataset name must be relative to data/: {dataset_name!r}")
    return dataset_name


def safe_dataset_root(dataset_name: str) -> Path:
    """Return ``data/<dataset_name>`` after rejecting traversal and symlink escapes."""
    root = get_data_dir(validate_dataset_name(dataset_name))
    data_root = get_data_dir().resolve()
    resolved_root = root.resolve(strict=False)
    try:
        resolved_root.relative_to(data_root)
    except ValueError as exc:
        raise ValueError(
            f"Dataset directory must stay under {data_root}: {dataset_name!r}"
        ) from exc
    return root
