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

import threading

import pytest

from dimos.utils.sequential_ids import SequentialIds


class TestSequentialIds:
    def test_initial_value(self) -> None:
        seq = SequentialIds()
        assert seq.next() == 0

    def test_sequential_increment(self) -> None:
        seq = SequentialIds()
        assert seq.next() == 0
        assert seq.next() == 1
        assert seq.next() == 2
        assert seq.next() == 3

    def test_multiple_instances(self) -> None:
        seq1 = SequentialIds()
        seq2 = SequentialIds()

        assert seq1.next() == 0
        assert seq2.next() == 0
        assert seq1.next() == 1
        assert seq2.next() == 1

    def test_thread_safety(self) -> None:
        seq = SequentialIds()
        results: list[int] = []
        lock = threading.Lock()

        def get_ids(count: int) -> None:
            local_results = []
            for _ in range(count):
                local_results.append(seq.next())
            with lock:
                results.extend(local_results)

        threads = []
        num_threads = 10
        ids_per_thread = 100

        for _ in range(num_threads):
            thread = threading.Thread(target=get_ids, args=(ids_per_thread,))
            threads.append(thread)
            thread.start()

        for thread in threads:
            thread.join()

        assert len(results) == num_threads * ids_per_thread
        assert len(set(results)) == len(results)
        assert sorted(results) == list(range(num_threads * ids_per_thread))

    def test_large_sequence(self) -> None:
        seq = SequentialIds()
        for i in range(10000):
            assert seq.next() == i

    def test_concurrent_access(self) -> None:
        seq = SequentialIds()
        barrier = threading.Barrier(5)
        results: list[int] = []
        lock = threading.Lock()

        def concurrent_next() -> None:
            barrier.wait()
            value = seq.next()
            with lock:
                results.append(value)

        threads = [threading.Thread(target=concurrent_next) for _ in range(5)]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()

        assert len(results) == 5
        assert len(set(results)) == 5
        assert set(results) == {0, 1, 2, 3, 4}
