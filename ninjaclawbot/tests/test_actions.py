from __future__ import annotations

import pytest

from ninjaclawbot.actions import ActionRequest, ActionType
from ninjaclawbot.errors import ActionValidationError


def test_action_request_from_dict_validates_move_targets() -> None:
    request = ActionRequest.from_dict(
        {
            "action": "move_servos",
            "parameters": {
                "targets": {"gpio12": 10, "hat_pwm1": -15},
                "per_servo_speeds": {"hat_pwm1": "S"},
            },
            "request_id": "req-1",
        }
    )

    assert request.action is ActionType.MOVE_SERVOS
    assert request.parameters["targets"]["gpio12"] == 10
    assert request.parameters["per_servo_speeds"]["hat_pwm1"] == "S"
    assert request.request_id == "req-1"


def test_action_request_rejects_unknown_action() -> None:
    with pytest.raises(ActionValidationError, match="Unsupported action"):
        ActionRequest.from_dict({"action": "launch_missiles"})


def test_action_request_rejects_empty_targets() -> None:
    with pytest.raises(ActionValidationError, match="non-empty dictionary"):
        ActionRequest.from_dict({"action": "move_servos", "parameters": {"targets": {}}})


def test_action_request_rejects_invalid_endpoint_name() -> None:
    with pytest.raises(ActionValidationError, match="Unsupported servo endpoint"):
        ActionRequest.from_dict({"action": "move_servos", "parameters": {"targets": {"S12": 0}}})


def test_action_request_requires_name_for_movement() -> None:
    with pytest.raises(ActionValidationError, match="missing required parameters: name"):
        ActionRequest.from_dict({"action": "perform_movement", "parameters": {}})


def test_action_request_requires_non_empty_text() -> None:
    with pytest.raises(ActionValidationError, match="Display text"):
        ActionRequest.from_dict({"action": "display_text", "parameters": {"text": "  "}})
