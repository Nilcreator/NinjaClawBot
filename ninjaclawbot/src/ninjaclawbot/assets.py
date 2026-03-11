"""Persistent movement and expression assets used by ninjaclawbot."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from pi5servo.core.endpoint import parse_servo_endpoint

from ninjaclawbot.config import NinjaClawbotConfig
from ninjaclawbot.errors import ActionValidationError

_NAME_PATTERN = re.compile(r"^[a-zA-Z0-9_-]+$")
_SPEED_CHOICES = {"S", "M", "F"}


def _validate_asset_name(name: str) -> str:
    if not isinstance(name, str) or not name.strip():
        raise ActionValidationError("Asset name must be a non-empty string.")
    if not _NAME_PATTERN.fullmatch(name):
        raise ActionValidationError(
            "Asset name may only contain letters, numbers, underscores, and hyphens."
        )
    return name


def _normalize_endpoint_key(endpoint: int | str) -> str:
    try:
        return parse_servo_endpoint(endpoint).identifier
    except ValueError as exc:
        raise ActionValidationError(str(exc)) from exc


def _normalize_move_map(targets: dict[Any, Any], *, step_index: int) -> dict[str, float]:
    if not isinstance(targets, dict) or not targets:
        raise ActionValidationError(f"Movement step {step_index} must contain non-empty moves.")
    normalized: dict[str, float] = {}
    for endpoint, angle in targets.items():
        if not isinstance(angle, (int, float)):
            raise ActionValidationError(f"Movement step {step_index} angles must be numeric.")
        normalized[_normalize_endpoint_key(endpoint)] = float(angle)
    return normalized


def _normalize_speed_map(speed_map: dict[Any, Any] | None, *, step_index: int) -> dict[str, str]:
    if not speed_map:
        return {}
    if not isinstance(speed_map, dict):
        raise ActionValidationError(
            f"Movement step {step_index} per_servo_speeds must be a dictionary."
        )
    normalized: dict[str, str] = {}
    for endpoint, speed in speed_map.items():
        speed_text = str(speed).upper()
        if speed_text not in _SPEED_CHOICES:
            raise ActionValidationError(
                f"Movement step {step_index} speed overrides must use S, M, or F values."
            )
        normalized[_normalize_endpoint_key(endpoint)] = speed_text
    return normalized


def validate_movement_asset(payload: dict[str, Any]) -> dict[str, Any]:
    name = _validate_asset_name(str(payload.get("name", "")).strip())
    steps = payload.get("steps")
    if not isinstance(steps, list) or not steps:
        raise ActionValidationError("Movement assets must contain a non-empty 'steps' list.")

    normalized_steps: list[dict[str, Any]] = []
    for index, step in enumerate(steps, start=1):
        if not isinstance(step, dict):
            raise ActionValidationError(f"Movement step {index} must be a dictionary.")

        raw_speed = step.get("speed", step.get("speed_mode", "M"))
        speed = str(raw_speed).upper()
        if speed not in _SPEED_CHOICES:
            raise ActionValidationError(f"Movement step {index} speed must be S, M, or F.")

        raw_moves = step.get("moves", step.get("targets"))
        normalized_moves = _normalize_move_map(raw_moves, step_index=index)
        per_servo_speeds = _normalize_speed_map(
            step.get("per_servo_speeds"),
            step_index=index,
        )

        normalized_steps.append(
            {
                "speed": speed,
                "moves": normalized_moves,
                "per_servo_speeds": per_servo_speeds,
                "pause_after_ms": max(0, int(step.get("pause_after_ms", 0))),
            }
        )

    return {
        "name": name,
        "description": str(payload.get("description", "")).strip(),
        "steps": normalized_steps,
    }


def validate_expression_asset(payload: dict[str, Any]) -> dict[str, Any]:
    name = _validate_asset_name(str(payload.get("name", "")).strip())
    display = payload.get("display", {}) or {}
    sound = payload.get("sound", {}) or {}
    if not isinstance(display, dict) or not isinstance(sound, dict):
        raise ActionValidationError(
            "Expression asset display and sound blocks must be dictionaries."
        )
    if not display and not sound:
        raise ActionValidationError("Expression assets must define display, sound, or both.")
    return {
        "name": name,
        "description": str(payload.get("description", "")).strip(),
        "display": {
            "text": str(display.get("text", "")).strip(),
            "scroll": bool(display.get("scroll", False)),
            "duration": float(display.get("duration", 3.0)),
            "language": str(display.get("language", "en")),
            "font_size": int(display.get("font_size", 32)),
        },
        "sound": {
            "emotion": str(sound.get("emotion", "")).strip(),
            "frequency": sound.get("frequency"),
            "duration": float(sound.get("duration", 0.3)),
        },
    }


class AssetStore:
    """Persistence layer for named movements and expressions."""

    def __init__(self, config: NinjaClawbotConfig | None = None) -> None:
        self.config = config or NinjaClawbotConfig()
        self.config.movement_asset_dir.mkdir(parents=True, exist_ok=True)
        self.config.expression_asset_dir.mkdir(parents=True, exist_ok=True)

    def list_assets(self, asset_type: str) -> list[str]:
        if asset_type == "movements":
            return sorted(path.stem for path in self.config.movement_asset_dir.glob("*.json"))
        if asset_type == "expressions":
            return sorted(path.stem for path in self.config.expression_asset_dir.glob("*.json"))
        if asset_type == "all":
            return sorted(set(self.list_assets("movements") + self.list_assets("expressions")))
        raise ActionValidationError("asset_type must be one of: all, movements, expressions.")

    def save_movement(self, payload: dict[str, Any]) -> Path:
        validated = validate_movement_asset(payload)
        path = self.config.movement_asset_dir / f"{validated['name']}.json"
        path.write_text(json.dumps(validated, indent=2), encoding="utf-8")
        return path

    def load_movement(self, name: str) -> dict[str, Any]:
        path = self.config.movement_asset_dir / f"{_validate_asset_name(name)}.json"
        if not path.exists():
            raise ActionValidationError(f"Unknown movement asset '{name}'.")
        payload = json.loads(path.read_text(encoding="utf-8"))
        validated = validate_movement_asset(payload)
        if payload != validated:
            path.write_text(json.dumps(validated, indent=2), encoding="utf-8")
        return validated

    def delete_movement(self, name: str) -> None:
        path = self.config.movement_asset_dir / f"{_validate_asset_name(name)}.json"
        path.unlink(missing_ok=True)

    def save_expression(self, payload: dict[str, Any]) -> Path:
        validated = validate_expression_asset(payload)
        path = self.config.expression_asset_dir / f"{validated['name']}.json"
        path.write_text(json.dumps(validated, indent=2), encoding="utf-8")
        return path

    def load_expression(self, name: str) -> dict[str, Any]:
        path = self.config.expression_asset_dir / f"{_validate_asset_name(name)}.json"
        if not path.exists():
            raise ActionValidationError(f"Unknown expression asset '{name}'.")
        payload = json.loads(path.read_text(encoding="utf-8"))
        validated = validate_expression_asset(payload)
        if payload != validated:
            path.write_text(json.dumps(validated, indent=2), encoding="utf-8")
        return validated

    def delete_expression(self, name: str) -> None:
        path = self.config.expression_asset_dir / f"{_validate_asset_name(name)}.json"
        path.unlink(missing_ok=True)
