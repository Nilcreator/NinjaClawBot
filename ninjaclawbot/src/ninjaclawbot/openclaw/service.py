"""Reusable service core for persistent OpenClaw bridge sessions."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from threading import RLock
from typing import Any, Callable

from ninjaclawbot.cli.common import create_executor
from ninjaclawbot.executor import ActionExecutor
from ninjaclawbot.presence import normalize_presence_mode

ExecutorFactory = Callable[[str | Path], ActionExecutor]

_STARTUP_GREETING_DEFINITION: dict[str, Any] = {
    "builtin": "greeting",
    "display": {
        "text": "HELLO",
        "scroll": False,
        "duration": 2.1,
        "language": "en",
        "font_size": 32,
    },
    "idle_reset": False,
}


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
    _service_lock: RLock = field(init=False, repr=False)
    _current_presence_mode: str | None = field(init=False, default=None, repr=False)
    _last_lifecycle_event: str | None = field(init=False, default=None, repr=False)
    _startup_completed: bool = field(init=False, default=False, repr=False)

    def __post_init__(self) -> None:
        self.root_dir = Path(self.root_dir).resolve()
        self._executor = self.executor_factory(self.root_dir)
        self._service_lock = RLock()

    @property
    def executor(self) -> ActionExecutor:
        return self._executor

    def _refresh_presence_mode(self) -> str | None:
        self._current_presence_mode = self.executor.runtime.active_expression
        return self._current_presence_mode

    def startup(self) -> dict[str, Any]:
        """Return a simple startup acknowledgement for callers."""

        with self._service_lock:
            return self.status()

    def execute_action(self, payload: dict[str, Any]) -> dict[str, Any]:
        """Execute one action payload through the persistent executor."""

        with self._service_lock:
            result = self.executor.execute(payload)
            self._requests_handled += 1
            self._refresh_presence_mode()
            if result.status.value == "failed":
                self._last_error = str(result.error_message)
            else:
                self._last_error = None
            return result.to_dict()

    def startup_sequence(self) -> dict[str, Any]:
        """Run the greeting sequence once, then transition into persistent idle."""

        with self._service_lock:
            if self._closed:
                return {"started": False, "closed": True}
            if self._startup_completed:
                return {
                    "started": True,
                    "already_started": True,
                    "presence_mode": self._current_presence_mode,
                }

            greeting_result = self.executor.runtime.perform_expression(_STARTUP_GREETING_DEFINITION)
            idle_result = self.executor.runtime.set_presence_mode("idle")
            self._startup_completed = True
            self._last_lifecycle_event = "gateway_start"
            self._current_presence_mode = "idle"
            self._last_error = None
            return {
                "started": True,
                "already_started": False,
                "greeting_result": greeting_result,
                "idle_result": idle_result,
                "presence_mode": "idle",
            }

    def set_presence_mode(
        self,
        mode: str,
        *,
        lifecycle_event: str | None = None,
    ) -> dict[str, Any]:
        """Update the robot into a persistent presence mode."""

        normalized = normalize_presence_mode(mode)
        with self._service_lock:
            if self._closed:
                return {"presence_mode": normalized, "changed": False, "closed": True}
            if (
                self._current_presence_mode == normalized
                and self.executor.runtime.active_expression == normalized
            ):
                if lifecycle_event:
                    self._last_lifecycle_event = lifecycle_event
                return {"presence_mode": normalized, "changed": False}

            result = self.executor.runtime.set_presence_mode(normalized)
            self._current_presence_mode = normalized
            self._last_lifecycle_event = lifecycle_event or f"presence:{normalized}"
            self._last_error = None
            return {**result, "changed": True}

    def shutdown_sequence(self, *, lifecycle_event: str = "gateway_stop") -> dict[str, Any]:
        """Run sleepy shutdown, then power down the display and close hardware."""

        with self._service_lock:
            result = self.executor.runtime.shutdown_sequence()
            self._current_presence_mode = None
            self._last_lifecycle_event = lifecycle_event
            self._last_error = None
            return result

    def status(self) -> dict[str, Any]:
        """Return lightweight diagnostics safe for bridge clients."""

        return {
            "running": not self._closed,
            "root_dir": str(self.root_dir),
            "started_at": self.started_at.isoformat(),
            "requests_handled": self._requests_handled,
            "last_error": self._last_error,
            "current_presence_mode": self._current_presence_mode,
            "last_lifecycle_event": self._last_lifecycle_event,
            "startup_completed": self._startup_completed,
        }

    def shutdown(self) -> dict[str, Any]:
        """Close the persistent runtime safely and report the final status."""

        with self._service_lock:
            if self._closed:
                return {"running": False, "closed": True}
            self._closed = True
            self.executor.runtime.close()
            self._current_presence_mode = None
            return {"running": False, "closed": True}
