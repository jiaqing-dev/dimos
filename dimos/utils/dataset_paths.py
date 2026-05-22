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

"""Safe path helpers for user-named datasets under ``data/``."""

from pathlib import Path

from dimos.utils.data import get_data_dir


def validate_dataset_name(dataset_name: str) -> str:
    """Return a normalized dataset name that cannot escape ``data/``."""
    name = str(dataset_name).strip()
    path = Path(name)
    if not name or path.is_absolute() or path == Path("."):
        raise ValueError("Dataset name must be a relative path under data/")
    if any(part == ".." for part in path.parts):
        raise ValueError("Dataset name must not contain '..' path segments")
    return path.as_posix()


def dataset_root_path(dataset_name: str) -> Path:
    """Resolve ``data/<dataset_name>/`` and verify it remains inside ``data/``."""
    safe_name = validate_dataset_name(dataset_name)
    data_root = get_data_dir().resolve()
    root = (data_root / safe_name).resolve(strict=False)
    try:
        root.relative_to(data_root)
    except ValueError as e:
        raise ValueError("Dataset path must stay under data/") from e
    return root
