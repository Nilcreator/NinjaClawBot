from __future__ import annotations

import io
import json
from pathlib import Path

from ninjaclawbot.openclaw.bridge import BridgeRequest, serve_stdio
from ninjaclawbot.openclaw.service import OpenClawServiceCore
from ninjaclawbot.results import ActionResult


class _FakeRuntime:
    def __init__(self) -> None:
        self.closed = False
        self.active_expression = None

    def close(self) -> None:
        self.closed = True


class _FakeExecutor:
    def __init__(self) -> None:
        self.runtime = _FakeRuntime()
        self.calls: list[dict[str, object]] = []

    def execute(self, payload):
        self.calls.append(payload)
        return ActionResult.success(action=str(payload.get("action", "unknown")))


def test_bridge_request_requires_object_payload() -> None:
    request = BridgeRequest.from_line(
        json.dumps(
            {
                "type": "execute_action",
                "request_id": "req-1",
                "payload": {"action": "health_check"},
            }
        )
    )

    assert request.type == "execute_action"
    assert request.request_id == "req-1"
    assert request.payload == {"action": "health_check"}


def test_service_core_reuses_executor_and_tracks_status(tmp_path: Path) -> None:
    created: list[_FakeExecutor] = []

    def factory(_root_dir: str | Path) -> _FakeExecutor:
        executor = _FakeExecutor()
        created.append(executor)
        return executor

    service = OpenClawServiceCore(tmp_path, executor_factory=factory)

    first = service.execute_action({"action": "health_check"})
    second = service.execute_action({"action": "list_capabilities"})

    assert len(created) == 1
    assert first["action"] == "health_check"
    assert second["action"] == "list_capabilities"
    assert service.status()["requests_handled"] == 2

    shutdown = service.shutdown()
    assert shutdown == {"running": False, "closed": True}
    assert created[0].runtime.closed is True


def test_service_core_can_run_presence_and_startup_sequences(tmp_path: Path) -> None:
    created: list[_FakeExecutor] = []

    class PresenceRuntime(_FakeRuntime):
        def __init__(self) -> None:
            super().__init__()
            self.active_expression = None
            self.greeting_runs = 0
            self.presence_calls: list[str] = []

        def perform_expression(self, definition):
            self.greeting_runs += 1
            self.active_expression = "greeting"
            return {"builtin": definition.get("builtin")}

        def set_presence_mode(self, mode: str):
            self.presence_calls.append(mode)
            self.active_expression = mode
            return {"presence_mode": mode, "active_expression": mode}

    class PresenceExecutor(_FakeExecutor):
        def __init__(self) -> None:
            super().__init__()
            self.runtime = PresenceRuntime()

    def factory(_root_dir: str | Path) -> PresenceExecutor:
        executor = PresenceExecutor()
        created.append(executor)
        return executor

    service = OpenClawServiceCore(tmp_path, executor_factory=factory)

    startup = service.startup_sequence()
    startup_again = service.startup_sequence(lifecycle_event="boot_md")
    thinking = service.set_presence_mode("thinking", lifecycle_event="message_received")
    status = service.status()

    assert startup["presence_mode"] == "idle"
    assert startup_again["already_started"] is True
    assert thinking["presence_mode"] == "thinking"
    assert status["current_presence_mode"] == "thinking"
    assert status["last_lifecycle_event"] == "message_received"
    assert status["suppressed_lifecycle_events"] == 0
    assert created[0].runtime.greeting_runs == 1
    assert created[0].runtime.presence_calls == ["idle", "thinking"]


def test_service_core_suppresses_stale_idle_after_explicit_activity(tmp_path: Path) -> None:
    class PresenceRuntime(_FakeRuntime):
        def set_presence_mode(self, mode: str):
            self.active_expression = mode
            return {"presence_mode": mode, "active_expression": mode}

    class PresenceExecutor(_FakeExecutor):
        def __init__(self) -> None:
            super().__init__()
            self.runtime = PresenceRuntime()

        def execute(self, payload):
            self.calls.append(payload)
            self.runtime.active_expression = "idle"
            return ActionResult.success(action=str(payload.get("action", "unknown")))

    service = OpenClawServiceCore(tmp_path, executor_factory=lambda _root: PresenceExecutor())

    thinking = service.set_presence_mode("thinking", lifecycle_event="message_received")
    reply = service.execute_action({"action": "perform_reply"})
    fallback_idle = service.set_presence_mode("idle", lifecycle_event="agent_end")
    status = service.status()

    assert thinking["changed"] is True
    assert reply["status"] == "success"
    assert fallback_idle["changed"] is False
    assert fallback_idle["suppressed"] is True
    assert fallback_idle["reason"] == "idle_fallback_not_needed"
    assert status["suppressed_lifecycle_events"] == 1
    assert status["last_transition_reason"] == "idle_fallback_not_needed"


def test_service_core_coalesces_repeated_thinking_updates(tmp_path: Path) -> None:
    class PresenceRuntime(_FakeRuntime):
        def __init__(self) -> None:
            super().__init__()
            self.presence_calls: list[str] = []

        def set_presence_mode(self, mode: str):
            self.presence_calls.append(mode)
            self.active_expression = mode
            return {"presence_mode": mode, "active_expression": mode}

    class PresenceExecutor(_FakeExecutor):
        def __init__(self) -> None:
            super().__init__()
            self.runtime = PresenceRuntime()

    executor = PresenceExecutor()
    service = OpenClawServiceCore(tmp_path, executor_factory=lambda _root: executor)

    first = service.set_presence_mode("thinking", lifecycle_event="message_received")
    second = service.set_presence_mode("thinking", lifecycle_event="message_received")

    assert first["changed"] is True
    assert second["changed"] is False
    assert second["suppressed"] is True
    assert second["reason"] == "thinking_already_active"
    assert executor.runtime.presence_calls == ["thinking"]


def test_serve_stdio_handles_status_action_and_shutdown(monkeypatch, tmp_path: Path) -> None:
    class FakeService:
        def __init__(self, _root_dir: Path) -> None:
            self.shutdown_calls = 0

        def startup(self):
            return {"running": True}

        def status(self):
            return {"running": True, "requests_handled": 0}

        def startup_sequence(self):
            return {"started": True, "presence_mode": "idle"}

        def set_presence_mode(self, mode: str, *, lifecycle_event: str | None = None):
            return {"presence_mode": mode, "lifecycle_event": lifecycle_event}

        def execute_action(self, payload):
            return {"status": "success", "action": payload["action"]}

        def shutdown_sequence(self, *, lifecycle_event: str = "gateway_stop"):
            return {"closed": True, "lifecycle_event": lifecycle_event}

        def shutdown(self):
            self.shutdown_calls += 1
            return {"running": False, "closed": True}

    monkeypatch.setattr("ninjaclawbot.openclaw.bridge.OpenClawServiceCore", FakeService)

    reader = io.StringIO(
        "\n".join(
            [
                json.dumps({"type": "status", "request_id": "status-1"}),
                json.dumps({"type": "startup_sequence", "request_id": "startup-1"}),
                json.dumps(
                    {
                        "type": "set_presence_mode",
                        "request_id": "presence-1",
                        "payload": {"mode": "thinking", "lifecycle_event": "message_received"},
                    }
                ),
                json.dumps(
                    {
                        "type": "execute_action",
                        "request_id": "action-1",
                        "payload": {"action": "health_check"},
                    }
                ),
                json.dumps(
                    {
                        "type": "shutdown_sequence",
                        "request_id": "shutdown-seq-1",
                        "payload": {"lifecycle_event": "gateway_stop"},
                    }
                ),
                json.dumps({"type": "shutdown", "request_id": "shutdown-1"}),
            ]
        )
        + "\n"
    )
    writer = io.StringIO()

    serve_stdio(tmp_path, input_stream=reader, output_stream=writer)

    responses = [json.loads(line) for line in writer.getvalue().splitlines() if line.strip()]
    assert responses[0]["ok"] is True
    assert responses[0]["request_id"] == "status-1"
    assert responses[0]["data"]["running"] is True
    assert responses[1]["ok"] is True
    assert responses[1]["data"]["presence_mode"] == "idle"
    assert responses[2]["ok"] is True
    assert responses[2]["data"]["presence_mode"] == "thinking"
    assert responses[3]["ok"] is True
    assert responses[3]["data"]["action"] == "health_check"
    assert responses[4]["ok"] is True
    assert responses[4]["data"]["closed"] is True
    assert responses[5]["ok"] is True
    assert responses[5]["data"]["closed"] is True


def test_serve_stdio_returns_protocol_error_for_invalid_line(tmp_path: Path) -> None:
    reader = io.StringIO("not-json\n")
    writer = io.StringIO()

    serve_stdio(tmp_path, input_stream=reader, output_stream=writer)

    responses = [json.loads(line) for line in writer.getvalue().splitlines() if line.strip()]
    assert responses[0]["ok"] is False
    assert "Expecting value" in responses[0]["error"]
