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

import pytest

from dimos.utils.colors import blue, cyan, green, orange, red, yellow


class TestColors:
    def test_green(self) -> None:
        result = green("test")
        assert result == "\033[92mtest\033[0m"
        assert result.startswith("\033[92m")
        assert result.endswith("\033[0m")

    def test_blue(self) -> None:
        result = blue("test")
        assert result == "\033[94mtest\033[0m"
        assert result.startswith("\033[94m")
        assert result.endswith("\033[0m")

    def test_red(self) -> None:
        result = red("test")
        assert result == "\033[91mtest\033[0m"
        assert result.startswith("\033[91m")
        assert result.endswith("\033[0m")

    def test_yellow(self) -> None:
        result = yellow("test")
        assert result == "\033[93mtest\033[0m"
        assert result.startswith("\033[93m")
        assert result.endswith("\033[0m")

    def test_cyan(self) -> None:
        result = cyan("test")
        assert result == "\033[96mtest\033[0m"
        assert result.startswith("\033[96m")
        assert result.endswith("\033[0m")

    def test_orange(self) -> None:
        result = orange("test")
        assert result == "\033[38;5;208mtest\033[0m"
        assert result.startswith("\033[38;5;208m")
        assert result.endswith("\033[0m")

    def test_empty_string(self) -> None:
        assert green("") == "\033[92m\033[0m"
        assert blue("") == "\033[94m\033[0m"
        assert red("") == "\033[91m\033[0m"

    def test_multiline_string(self) -> None:
        text = "line1\nline2\nline3"
        result = green(text)
        assert result == f"\033[92m{text}\033[0m"
        assert "line1\nline2\nline3" in result

    def test_special_characters(self) -> None:
        text = "test!@#$%^&*()"
        result = red(text)
        assert result == f"\033[91m{text}\033[0m"

    def test_unicode_characters(self) -> None:
        text = "测试文本"
        result = blue(text)
        assert result == f"\033[94m{text}\033[0m"
