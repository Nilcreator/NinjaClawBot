"""Typed action executor for the ninjaclawbot integration layer."""

from __future__ import annotations

import time
from datetime import UTC, datetime
from typing import Any

from ninjaclawbot.actions import ActionRequest, ActionType
from ninjaclawbot.assets import AssetStore
from ninjaclawbot.errors import ActionValidationError, ExecutionError, NinjaClawbotError
from ninjaclawbot.expressions.catalog import get_builtin_expression
from ninjaclawbot.expressions.policy import build_reply_expression, list_reply_states
from ninjaclawbot.results import ActionResult, ActionStatus
from ninjaclawbot.runtime import NinjaClawbotRuntime


class ActionExecutor:
    """Execute validated robot actions and return structured results."""

    def __init__(
        self,
        runtime: NinjaClawbotRuntime | None = None,
        asset_store: AssetStore | None = None,
    ) -> None:
        self.runtime = runtime or NinjaClawbotRuntime()
        self.asset_store = asset_store or AssetStore(self.runtime.config)

    def execute(self, request: ActionRequest | dict[str, Any]) -> ActionResult:
        started_at = datetime.now(UTC)
        try:
            normalized = (
                request if isinstance(request, ActionRequest) else ActionRequest.from_dict(request)
            )
        except ActionValidationError as exc:
            return ActionResult.failure(
                action=str(request.get("action", "unknown"))
                if isinstance(request, dict)
                else "unknown",
                error_code="ACTION_VALIDATION_ERROR",
                error_message=str(exc),
                rollback_hint="Fix the request payload and retry the action.",
                status=ActionStatus.REJECTED,
                started_at=started_at,
                ended_at=datetime.now(UTC),
            )

        try:
            with self.runtime.execution_lock.acquire():
                data, devices_used, warnings = self._dispatch(normalized)
            return ActionResult.success(
                action=normalized.action.value,
                devices_used=devices_used,
                data=data,
                warnings=warnings,
                request_id=normalized.request_id,
                started_at=started_at,
                ended_at=datetime.now(UTC),
            )
        except NinjaClawbotError as exc:
            return ActionResult.failure(
                action=normalized.action.value,
                error_code=type(exc).__name__.upper(),
                error_message=str(exc),
                rollback_hint=(
                    "Review calibration files, connected hardware, and requested action parameters."
                ),
                request_id=normalized.request_id,
                started_at=started_at,
                ended_at=datetime.now(UTC),
            )
        except Exception as exc:  # pragma: no cover - last-resort guard
            return ActionResult.failure(
                action=normalized.action.value,
                error_code="UNEXPECTED_ERROR",
                error_message=str(exc),
                rollback_hint="Inspect the traceback and rerun the action after fixing the integration layer.",
                request_id=normalized.request_id,
                started_at=started_at,
                ended_at=datetime.now(UTC),
            )

    def _dispatch(self, request: ActionRequest) -> tuple[dict[str, Any], list[str], list[str]]:
        params = request.parameters
        if request.action == ActionType.HEALTH_CHECK:
            return self.runtime.health_check(), ["servo", "buzzer", "display", "distance"], []
        if request.action == ActionType.LIST_CAPABILITIES:
            return (
                {
                    "actions": [action.value for action in ActionType],
                    "reply_states": list_reply_states(),
                    "built_in_expressions": self.runtime.list_builtin_expressions(),
                    "assets": {
                        "movements": self.asset_store.list_assets("movements"),
                        "expressions": self.asset_store.list_assets("expressions"),
                    },
                },
                [],
                [],
            )
        if request.action == ActionType.MOVE_SERVOS:
            completed = self.runtime.move_servos(
                {key: float(value) for key, value in params["targets"].items()},
                speed_mode=str(params.get("speed_mode", "M")).upper(),
                per_servo_speeds=params.get("per_servo_speeds"),
                easing=str(params.get("easing", "ease_in_out_cubic")),
                force=bool(params.get("force", True)),
            )
            if not completed:
                raise ExecutionError("Servo movement aborted before completion.")
            return (
                {
                    "targets": params["targets"],
                    "speed_mode": str(params.get("speed_mode", "M")).upper(),
                    "per_servo_speeds": params.get("per_servo_speeds", {}),
                    "completed": True,
                },
                ["servo"],
                [],
            )
        if request.action == ActionType.PERFORM_MOVEMENT:
            asset = self.asset_store.load_movement(str(params["name"]))
            return self._execute_movement_asset(asset), ["servo"], []
        if request.action == ActionType.PERFORM_REPLY:
            definition = build_reply_expression(
                text=str(params["text"]),
                reply_state=params["reply_state"],
                display_text=params.get("display_text"),
                idle_reset=params.get("idle_reset"),
                duration=float(params.get("duration", 3.0)),
                language=str(params.get("language", "en")),
                font_size=int(params.get("font_size", 32)),
            )
            result = self._execute_expression_definition(definition)
            result["reply_state"] = definition["reply_policy"]["reply_state"]
            result["reply_text"] = str(params["text"])
            result["display_text"] = definition["reply_policy"]["display_text"]
            return result, ["display", "buzzer"], []
        if request.action == ActionType.DISPLAY_TEXT:
            self.runtime.display_text(
                str(params["text"]),
                scroll=bool(params.get("scroll", False)),
                duration=float(params.get("duration", 3.0)),
                language=str(params.get("language", "en")),
                font_size=int(params.get("font_size", 32)),
            )
            return {"text": params["text"]}, ["display"], []
        if request.action == ActionType.PLAY_SOUND:
            waited_for = self.runtime.play_sound(
                emotion=str(params.get("emotion", "")).strip() or None,
                frequency=params.get("frequency"),
                duration=float(params.get("duration", 0.3)),
                wait=True,
            )
            return (
                {
                    "emotion": params.get("emotion"),
                    "frequency": params.get("frequency"),
                    "waited_for_s": waited_for,
                },
                ["buzzer"],
                [],
            )
        if request.action == ActionType.SHOW_EXPRESSION:
            definition = {
                "display": {
                    "text": str(params.get("text", "")).strip(),
                    "scroll": bool(params.get("scroll", False)),
                    "duration": float(params.get("duration", 3.0)),
                    "language": str(params.get("language", "en")),
                    "font_size": int(params.get("font_size", 32)),
                },
                "sound": {
                    "emotion": str(params.get("emotion", "")).strip(),
                    "frequency": params.get("frequency"),
                    "duration": float(params.get("sound_duration", params.get("duration", 0.3))),
                },
            }
            return self._execute_expression_definition(definition), ["display", "buzzer"], []
        if request.action == ActionType.PERFORM_EXPRESSION:
            definition = self._resolve_expression_definition(str(params["name"]))
            return self._execute_expression_definition(definition), ["display", "buzzer"], []
        if request.action == ActionType.SET_IDLE:
            result = self.runtime.set_idle_expression()
            return result, ["display"], []
        if request.action == ActionType.SET_PRESENCE_MODE:
            result = self.runtime.set_presence_mode(str(params["mode"]))
            return result, ["display", "buzzer"], []
        if request.action == ActionType.STOP_EXPRESSION:
            self.runtime.stop_expression()
            return {"stopped": True}, ["display", "buzzer"], []
        if request.action == ActionType.SHUTDOWN_SEQUENCE:
            return self.runtime.shutdown_sequence(), ["display", "buzzer", "servo"], []
        if request.action == ActionType.READ_DISTANCE:
            return self.runtime.read_distance(), ["distance"], []
        if request.action == ActionType.LIST_ASSETS:
            asset_type = str(params.get("asset_type", "all"))
            return (
                {
                    "asset_type": asset_type,
                    "assets": self.asset_store.list_assets(asset_type),
                },
                [],
                [],
            )
        if request.action == ActionType.STOP_ALL:
            self.runtime.stop_all()
            return {"stopped": True}, ["servo", "buzzer", "display"], []
        raise ActionValidationError(f"Unsupported action '{request.action.value}'.")

    def _execute_movement_asset(self, asset: dict[str, Any]) -> dict[str, Any]:
        sequence = asset["steps"]
        total_steps = len(sequence)
        for index, step in enumerate(sequence):
            if total_steps == 1:
                easing = "ease_in_out_cubic"
            elif index == 0:
                easing = "ease_in_cubic"
            elif index == total_steps - 1:
                easing = "ease_out_cubic"
            else:
                easing = "linear"

            completed = self.runtime.move_servos(
                step["moves"],
                speed_mode=step["speed"],
                per_servo_speeds=step.get("per_servo_speeds"),
                easing=easing,
                force=True,
            )
            if not completed:
                raise ExecutionError(f"Movement '{asset['name']}' was aborted.")

            pause_after_ms = int(step.get("pause_after_ms", 0))
            if pause_after_ms > 0:
                time.sleep(pause_after_ms / 1000)
        return {"name": asset["name"], "steps_executed": len(sequence)}

    def _execute_expression_definition(self, asset: dict[str, Any]) -> dict[str, Any]:
        return self.runtime.perform_expression(asset)

    def _resolve_expression_definition(self, name: str) -> dict[str, Any]:
        try:
            return self.asset_store.load_expression(name)
        except ActionValidationError as exc:
            if str(exc) != f"Unknown expression asset '{name}'.":
                raise
        try:
            get_builtin_expression(name)
        except ValueError as builtin_exc:
            raise ActionValidationError(
                f"Unknown expression asset or built-in expression '{name}'."
            ) from builtin_exc
        return {"name": name, "builtin": name}
