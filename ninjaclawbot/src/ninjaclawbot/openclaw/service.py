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

_WAITING_PRESENCE_MODES = frozenset({"thinking", "listening"})


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
    _activity_epoch: int = field(init=False, default=0, repr=False)
    _last_presence_epoch: int = field(init=False, default=0, repr=False)
    _last_explicit_epoch: int = field(init=False, default=0, repr=False)
    _suppressed_lifecycle_events: int = field(init=False, default=0, repr=False)
    _last_transition_source: str | None = field(init=False, default=None, repr=False)
    _last_transition_reason: str | None = field(init=False, default=None, repr=False)
    _last_explicit_action: str | None = field(init=False, default=None, repr=False)

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

    def _next_epoch(self) -> int:
        self._activity_epoch += 1
        return self._activity_epoch

    def _mark_transition(self, *, source: str, reason: str | None = None) -> None:
        self._last_transition_source = source
        self._last_transition_reason = reason

    def _suppress_presence_update(
        self,
        *,
        mode: str,
        lifecycle_event: str | None,
        reason: str,
    ) -> dict[str, Any]:
        self._suppressed_lifecycle_events += 1
        if lifecycle_event:
            self._last_lifecycle_event = lifecycle_event
        self._mark_transition(source=lifecycle_event or f"presence:{mode}", reason=reason)
        return {
            "presence_mode": self._current_presence_mode or mode,
            "changed": False,
            "suppressed": True,
            "reason": reason,
            "activity_epoch": self._activity_epoch,
        }

    def _should_suppress_presence_update(
        self,
        *,
        mode: str,
        lifecycle_event: str | None,
    ) -> str | None:
        active_expression = self.executor.runtime.active_expression

        if (
            lifecycle_event in {"gateway_start", "boot_md", "service_start"}
            and self._startup_completed
        ):
            return "startup_already_completed"

        if lifecycle_event == "agent_end" and mode == "idle":
            waiting_state_active = (
                self._current_presence_mode in _WAITING_PRESENCE_MODES
                or active_expression in _WAITING_PRESENCE_MODES
            )
            if not waiting_state_active:
                return "idle_fallback_not_needed"
            if self._last_explicit_epoch > self._last_presence_epoch:
                return "stale_idle_after_explicit_activity"

        if lifecycle_event == "message_received" and mode == "thinking":
            if self._current_presence_mode == "thinking" and active_expression == "thinking":
                return "thinking_already_active"

        return None

    def startup(self) -> dict[str, Any]:
        """Return a simple startup acknowledgement for callers."""

        with self._service_lock:
            return self.status()

    def execute_action(self, payload: dict[str, Any]) -> dict[str, Any]:
        """Execute one action payload through the persistent executor."""

        with self._service_lock:
            action_name = str(payload.get("action", "unknown"))
            epoch = self._next_epoch()
            self._last_explicit_epoch = epoch
            self._last_explicit_action = action_name
            result = self.executor.execute(payload)
            self._requests_handled += 1
            self._refresh_presence_mode()
            if result.status.value == "failed":
                self._last_error = str(result.error_message)
                self._mark_transition(
                    source=f"execute_action:{action_name}",
                    reason=f"failed:{result.error_code or 'unknown'}",
                )
            else:
                self._last_error = None
                self._mark_transition(source=f"execute_action:{action_name}", reason="completed")
            return result.to_dict()

    def startup_sequence(self, *, lifecycle_event: str = "gateway_start") -> dict[str, Any]:
        """Run the greeting sequence once, then transition into persistent idle."""

        with self._service_lock:
            if self._closed:
                return {"started": False, "closed": True}
            if self._startup_completed:
                self._mark_transition(source=lifecycle_event, reason="startup_already_completed")
                return {
                    "started": True,
                    "already_started": True,
                    "presence_mode": self._current_presence_mode,
                    "activity_epoch": self._activity_epoch,
                }

            epoch = self._next_epoch()
            greeting_result = self.executor.runtime.perform_expression(_STARTUP_GREETING_DEFINITION)
            idle_result = self.executor.runtime.set_presence_mode("idle")
            self._startup_completed = True
            self._last_lifecycle_event = lifecycle_event
            self._current_presence_mode = "idle"
            self._last_presence_epoch = epoch
            self._last_error = None
            self._mark_transition(source=lifecycle_event, reason="startup_completed")
            return {
                "started": True,
                "already_started": False,
                "greeting_result": greeting_result,
                "idle_result": idle_result,
                "presence_mode": "idle",
                "activity_epoch": epoch,
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
            suppress_reason = self._should_suppress_presence_update(
                mode=normalized,
                lifecycle_event=lifecycle_event,
            )
            if suppress_reason is not None:
                return self._suppress_presence_update(
                    mode=normalized,
                    lifecycle_event=lifecycle_event,
                    reason=suppress_reason,
                )
            if (
                self._current_presence_mode == normalized
                and self.executor.runtime.active_expression == normalized
            ):
                return self._suppress_presence_update(
                    mode=normalized,
                    lifecycle_event=lifecycle_event,
                    reason="presence_already_active",
                )

            result = self.executor.runtime.set_presence_mode(normalized)
            self._current_presence_mode = normalized
            self._last_presence_epoch = self._activity_epoch
            self._last_lifecycle_event = lifecycle_event or f"presence:{normalized}"
            self._last_error = None
            self._mark_transition(
                source=self._last_lifecycle_event,
                reason="presence_updated",
            )
            return {**result, "changed": True, "activity_epoch": self._activity_epoch}

    def shutdown_sequence(self, *, lifecycle_event: str = "gateway_stop") -> dict[str, Any]:
        """Run sleepy shutdown, then power down the display and close hardware."""

        with self._service_lock:
            epoch = self._next_epoch()
            result = self.executor.runtime.shutdown_sequence()
            self._current_presence_mode = None
            self._last_lifecycle_event = lifecycle_event
            self._last_error = None
            self._mark_transition(source=lifecycle_event, reason="shutdown_sequence")
            return {**result, "activity_epoch": epoch}

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
            "activity_epoch": self._activity_epoch,
            "last_presence_epoch": self._last_presence_epoch,
            "last_explicit_epoch": self._last_explicit_epoch,
            "suppressed_lifecycle_events": self._suppressed_lifecycle_events,
            "last_transition_source": self._last_transition_source,
            "last_transition_reason": self._last_transition_reason,
            "last_explicit_action": self._last_explicit_action,
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
