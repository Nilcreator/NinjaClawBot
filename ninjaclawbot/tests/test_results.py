from __future__ import annotations

from datetime import UTC, datetime, timedelta

from ninjaclawbot.results import ActionResult, ActionStatus


def test_action_result_success_serializes_expected_fields() -> None:
    start = datetime(2026, 3, 11, 10, 0, tzinfo=UTC)
    end = start + timedelta(milliseconds=250)

    result = ActionResult.success(
        action="health_check",
        devices_used=["servo", "display"],
        data={"servo": {"available": True}},
        request_id="req-2",
        started_at=start,
        ended_at=end,
    )

    payload = result.to_dict()

    assert payload["status"] == "success"
    assert payload["duration_ms"] == 250
    assert payload["devices_used"] == ["servo", "display"]
    assert payload["request_id"] == "req-2"


def test_action_result_failure_serializes_error_fields() -> None:
    result = ActionResult.failure(
        action="move_servos",
        error_code="SERVO_UNAVAILABLE",
        error_message="Servo driver could not be imported.",
        rollback_hint="Install pi5servo into the same virtual environment.",
        status=ActionStatus.REJECTED,
    )

    payload = result.to_dict()

    assert payload["status"] == "rejected"
    assert payload["error_code"] == "SERVO_UNAVAILABLE"
    assert payload["rollback_hint"] == "Install pi5servo into the same virtual environment."
