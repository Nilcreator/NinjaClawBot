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


def test_serve_stdio_handles_status_action_and_shutdown(monkeypatch, tmp_path: Path) -> None:
    class FakeService:
        def __init__(self, _root_dir: Path) -> None:
            self.shutdown_calls = 0

        def startup(self):
            return {"running": True}

        def status(self):
            return {"running": True, "requests_handled": 0}

        def execute_action(self, payload):
            return {"status": "success", "action": payload["action"]}

        def shutdown(self):
            self.shutdown_calls += 1
            return {"running": False, "closed": True}

    monkeypatch.setattr("ninjaclawbot.openclaw.bridge.OpenClawServiceCore", FakeService)

    reader = io.StringIO(
        "\n".join(
            [
                json.dumps({"type": "status", "request_id": "status-1"}),
                json.dumps(
                    {
                        "type": "execute_action",
                        "request_id": "action-1",
                        "payload": {"action": "health_check"},
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
    assert responses[1]["data"]["action"] == "health_check"
    assert responses[2]["ok"] is True
    assert responses[2]["data"]["closed"] is True


def test_serve_stdio_returns_protocol_error_for_invalid_line(tmp_path: Path) -> None:
    reader = io.StringIO("not-json\n")
    writer = io.StringIO()

    serve_stdio(tmp_path, input_stream=reader, output_stream=writer)

    responses = [json.loads(line) for line in writer.getvalue().splitlines() if line.strip()]
    assert responses[0]["ok"] is False
    assert "Expecting value" in responses[0]["error"]
