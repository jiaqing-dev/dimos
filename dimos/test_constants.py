# Copyright 2026 Dimensional Inc.
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

from pathlib import Path

import pytest

from dimos.constants import (
    DEFAULT_CAPACITY_COLOR_IMAGE,
    DEFAULT_CAPACITY_DEPTH_IMAGE,
    DIMOS_LOG_DIR,
    DIMOS_PROJECT_ROOT,
    LCM_MAX_CHANNEL_NAME_LENGTH,
)


class TestConstants:
    def test_dimos_project_root_is_path(self) -> None:
        assert isinstance(DIMOS_PROJECT_ROOT, Path)

    def test_dimos_project_root_exists(self) -> None:
        assert DIMOS_PROJECT_ROOT.exists()
        assert DIMOS_PROJECT_ROOT.is_dir()

    def test_dimos_log_dir_is_path(self) -> None:
        assert isinstance(DIMOS_LOG_DIR, Path)

    def test_dimos_log_dir_relative_to_root(self) -> None:
        assert DIMOS_LOG_DIR == DIMOS_PROJECT_ROOT / "logs"

    def test_default_capacity_color_image(self) -> None:
        assert DEFAULT_CAPACITY_COLOR_IMAGE == 1920 * 1080 * 3
        assert DEFAULT_CAPACITY_COLOR_IMAGE == 6220800
        assert isinstance(DEFAULT_CAPACITY_COLOR_IMAGE, int)

    def test_default_capacity_depth_image(self) -> None:
        assert DEFAULT_CAPACITY_DEPTH_IMAGE == 1280 * 720 * 4
        assert DEFAULT_CAPACITY_DEPTH_IMAGE == 3686400
        assert isinstance(DEFAULT_CAPACITY_DEPTH_IMAGE, int)

    def test_lcm_max_channel_name_length(self) -> None:
        assert LCM_MAX_CHANNEL_NAME_LENGTH == 63
        assert isinstance(LCM_MAX_CHANNEL_NAME_LENGTH, int)

    def test_color_image_capacity_sufficient(self) -> None:
        assert DEFAULT_CAPACITY_COLOR_IMAGE > 0
        width, height, channels = 1920, 1080, 3
        assert DEFAULT_CAPACITY_COLOR_IMAGE >= width * height * channels

    def test_depth_image_capacity_sufficient(self) -> None:
        assert DEFAULT_CAPACITY_DEPTH_IMAGE > 0
        width, height, bytes_per_pixel = 1280, 720, 4
        assert DEFAULT_CAPACITY_DEPTH_IMAGE >= width * height * bytes_per_pixel

    def test_project_root_contains_expected_files(self) -> None:
        expected_files = ["setup.py", "pyproject.toml", "README.md"]
        for file in expected_files:
            assert (DIMOS_PROJECT_ROOT / file).exists(), f"{file} should exist in project root"

    def test_project_root_contains_dimos_package(self) -> None:
        dimos_package = DIMOS_PROJECT_ROOT / "dimos"
        assert dimos_package.exists()
        assert dimos_package.is_dir()
        assert (dimos_package / "__init__.py").exists()
