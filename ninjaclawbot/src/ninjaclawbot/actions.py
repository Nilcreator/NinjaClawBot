"""Typed action requests accepted by the ninjaclawbot executor."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any

from pi5servo.core.endpoint import parse_servo_endpoint

from ninjaclawbot.errors import ActionValidationError


class ActionType(StrEnum):
    """Stable action names for robot control."""

    HEALTH_CHECK = "health_check"
    MOVE_SERVOS = "move_servos"
    PERFORM_MOVEMENT = "perform_movement"
    DISPLAY_TEXT = "display_text"
    PLAY_SOUND = "play_sound"
    SHOW_EXPRESSION = "show_expression"
    PERFORM_EXPRESSION = "perform_expression"
    READ_DISTANCE = "read_distance"
    LIST_ASSETS = "list_assets"
    STOP_ALL = "stop_all"


_REQUIRED_PARAMETERS: dict[ActionType, tuple[str, ...]] = {
    ActionType.HEALTH_CHECK: (),
    ActionType.MOVE_SERVOS: ("targets",),
    ActionType.PERFORM_MOVEMENT: ("name",),
    ActionType.DISPLAY_TEXT: ("text",),
    ActionType.PLAY_SOUND: (),
    ActionType.SHOW_EXPRESSION: (),
    ActionType.PERFORM_EXPRESSION: ("name",),
    ActionType.READ_DISTANCE: (),
    ActionType.LIST_ASSETS: (),
    ActionType.STOP_ALL: (),
}


@dataclass(slots=True)
class ActionRequest:
    """A validated robot action request."""

    action: ActionType
    parameters: dict[str, Any] = field(default_factory=dict)
    request_id: str | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.parameters, dict):
            raise ActionValidationError("Action parameters must be a dictionary.")

        missing = [key for key in _REQUIRED_PARAMETERS[self.action] if key not in self.parameters]
        if missing:
            raise ActionValidationError(
                f"Action '{self.action}' is missing required parameters: {', '.join(missing)}."
            )

        if self.action == ActionType.MOVE_SERVOS:
            self._validate_targets()
        elif self.action in {ActionType.PERFORM_MOVEMENT, ActionType.PERFORM_EXPRESSION}:
            self._validate_named_asset()
        elif self.action == ActionType.DISPLAY_TEXT:
            self._validate_text()
        elif self.action == ActionType.LIST_ASSETS:
            self._validate_asset_type()

    def _validate_targets(self) -> None:
        targets = self.parameters.get("targets")
        if not isinstance(targets, dict) or not targets:
            raise ActionValidationError("The 'targets' parameter must be a non-empty dictionary.")
        for endpoint, angle in targets.items():
            try:
                parse_servo_endpoint(endpoint)
            except ValueError as exc:
                raise ActionValidationError(str(exc)) from exc
            if not isinstance(angle, (int, float)):
                raise ActionValidationError("Servo target angles must be numeric.")
        per_servo_speeds = self.parameters.get("per_servo_speeds", {})
        if per_servo_speeds is None:
            return
        if not isinstance(per_servo_speeds, dict):
            raise ActionValidationError("per_servo_speeds must be a dictionary when provided.")
        for endpoint, speed in per_servo_speeds.items():
            try:
                parse_servo_endpoint(endpoint)
            except ValueError as exc:
                raise ActionValidationError(str(exc)) from exc
            if str(speed).upper() not in {"S", "M", "F"}:
                raise ActionValidationError("Per-servo speeds must use S, M, or F values.")

    def _validate_named_asset(self) -> None:
        name = self.parameters.get("name")
        if not isinstance(name, str) or not name.strip():
            raise ActionValidationError("Asset name must be a non-empty string.")

    def _validate_text(self) -> None:
        text = self.parameters.get("text")
        if not isinstance(text, str) or not text.strip():
            raise ActionValidationError("Display text must be a non-empty string.")

    def _validate_asset_type(self) -> None:
        asset_type = self.parameters.get("asset_type", "all")
        if asset_type not in {"all", "movements", "expressions"}:
            raise ActionValidationError("asset_type must be one of: all, movements, expressions.")

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "ActionRequest":
        """Create and validate an action request from plain data."""

        if not isinstance(payload, dict):
            raise ActionValidationError("Action payload must be a dictionary.")

        raw_action = payload.get("action")
        if not isinstance(raw_action, str) or not raw_action.strip():
            raise ActionValidationError("Action payload must include a non-empty 'action' field.")

        try:
            action = ActionType(raw_action)
        except ValueError as exc:
            supported = ", ".join(action.value for action in ActionType)
            raise ActionValidationError(
                f"Unsupported action '{raw_action}'. Supported actions: {supported}."
            ) from exc

        parameters = payload.get("parameters", {})
        request_id = payload.get("request_id")
        if request_id is not None and not isinstance(request_id, str):
            raise ActionValidationError("request_id must be a string when provided.")

        return cls(action=action, parameters=parameters, request_id=request_id)

    def to_dict(self) -> dict[str, Any]:
        """Serialize the action request for logging or transport."""

        return {
            "action": self.action.value,
            "parameters": self.parameters,
            "request_id": self.request_id,
        }
