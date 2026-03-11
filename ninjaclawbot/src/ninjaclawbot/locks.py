"""Lock helpers for serializing hardware actions."""

from __future__ import annotations

from contextlib import contextmanager
from threading import Lock
from typing import Iterator

from ninjaclawbot.errors import ExecutionError


class ExecutionLock:
    """A non-reentrant lock used to prevent overlapping robot actions."""

    def __init__(self) -> None:
        self._lock = Lock()

    @contextmanager
    def acquire(self) -> Iterator[None]:
        acquired = self._lock.acquire(blocking=False)
        if not acquired:
            raise ExecutionError("Another robot action is already running.")
        try:
            yield
        finally:
            self._lock.release()
