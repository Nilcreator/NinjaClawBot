"""Reusable service core for persistent OpenClaw bridge sessions."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Callable

from ninjaclawbot.cli.common import create_executor
from ninjaclawbot.executor import ActionExecutor

ExecutorFactory = Callable[[str | Path], ActionExecutor]


@dataclass(slots=True)
class OpenClawServiceCore:
    """Own a long-lived executor/runtime pair for bridge-hosted sessions."""

    root_dir: Path
    executor_factory: ExecutorFactory = create_executor
    started_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    _executor: ActionExecutor = field(init=False, repr=False)
    _requests_handled: int = field(init=False, default=0, repr=False)
    _closed: bool = field(init=False, default=False, repr=False)
    _last_error: str | None = field(init=False, default=None, repr=False)

    def __post_init__(self) -> None:
        self.root_dir = Path(self.root_dir).resolve()
        self._executor = self.executor_factory(self.root_dir)

    @property
    def executor(self) -> ActionExecutor:
        return self._executor

    def startup(self) -> dict[str, Any]:
        """Return a simple startup acknowledgement for callers."""

        return self.status()

    def execute_action(self, payload: dict[str, Any]) -> dict[str, Any]:
        """Execute one action payload through the persistent executor."""

        result = self.executor.execute(payload)
        self._requests_handled += 1
        if result.status.value == "failed":
            self._last_error = str(result.error_message)
        return result.to_dict()

    def status(self) -> dict[str, Any]:
        """Return lightweight diagnostics safe for bridge clients."""

        return {
            "running": not self._closed,
            "root_dir": str(self.root_dir),
            "started_at": self.started_at.isoformat(),
            "requests_handled": self._requests_handled,
            "last_error": self._last_error,
        }

    def shutdown(self) -> dict[str, Any]:
        """Close the persistent runtime safely and report the final status."""

        if self._closed:
            return {"running": False, "closed": True}
        self._closed = True
        self.executor.runtime.close()
        return {"running": False, "closed": True}
