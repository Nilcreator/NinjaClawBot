"""Line-delimited JSON bridge for persistent OpenClaw sessions."""

from __future__ import annotations

import json
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, TextIO

from ninjaclawbot.openclaw.service import OpenClawServiceCore


@dataclass(slots=True)
class BridgeRequest:
    """One line-delimited bridge request."""

    type: str
    request_id: str | None = None
    payload: dict[str, Any] | None = None

    @classmethod
    def from_line(cls, line: str) -> "BridgeRequest":
        raw = json.loads(line)
        if not isinstance(raw, dict):
            raise ValueError("Bridge request must be a JSON object.")

        request_type = str(raw.get("type", "")).strip()
        if not request_type:
            raise ValueError("Bridge request must include a non-empty 'type'.")

        request_id = raw.get("request_id")
        if request_id is not None and not isinstance(request_id, str):
            raise ValueError("Bridge request 'request_id' must be a string when provided.")

        payload = raw.get("payload")
        if payload is not None and not isinstance(payload, dict):
            raise ValueError("Bridge request 'payload' must be an object when provided.")

        return cls(type=request_type, request_id=request_id, payload=payload)


@dataclass(slots=True)
class BridgeResponse:
    """One line-delimited bridge response."""

    ok: bool
    request_id: str | None = None
    data: dict[str, Any] | None = None
    error: str | None = None

    def to_line(self) -> str:
        return json.dumps(
            {
                "ok": self.ok,
                "request_id": self.request_id,
                "data": self.data,
                "error": self.error,
            },
            separators=(",", ":"),
        )


def _response_error(request_id: str | None, message: str) -> BridgeResponse:
    return BridgeResponse(ok=False, request_id=request_id, error=message)


def _handle_request(
    service: OpenClawServiceCore,
    request: BridgeRequest,
) -> tuple[BridgeResponse, bool]:
    if request.type == "health_ping":
        return BridgeResponse(ok=True, request_id=request.request_id, data={"alive": True}), False
    if request.type == "status":
        return BridgeResponse(ok=True, request_id=request.request_id, data=service.status()), False
    if request.type == "execute_action":
        if request.payload is None:
            return _response_error(request.request_id, "execute_action requires a payload."), False
        return (
            BridgeResponse(
                ok=True,
                request_id=request.request_id,
                data=service.execute_action(request.payload),
            ),
            False,
        )
    if request.type == "shutdown":
        return (
            BridgeResponse(ok=True, request_id=request.request_id, data=service.shutdown()),
            True,
        )
    return _response_error(
        request.request_id, f"Unsupported bridge request type '{request.type}'."
    ), False


def serve_stdio(
    root_dir: str | Path,
    *,
    input_stream: TextIO | None = None,
    output_stream: TextIO | None = None,
) -> None:
    """Serve bridge requests over stdin/stdout using line-delimited JSON."""

    reader = input_stream or sys.stdin
    writer = output_stream or sys.stdout
    service = OpenClawServiceCore(Path(root_dir))

    try:
        service.startup()
        for raw_line in reader:
            line = raw_line.strip()
            if not line:
                continue

            request_id: str | None = None
            try:
                request = BridgeRequest.from_line(line)
                request_id = request.request_id
                response, should_stop = _handle_request(service, request)
            except Exception as exc:  # pragma: no cover - exercised through tests
                response = _response_error(request_id, str(exc))
                should_stop = False

            writer.write(f"{response.to_line()}\n")
            writer.flush()

            if should_stop:
                return
    finally:
        service.shutdown()
