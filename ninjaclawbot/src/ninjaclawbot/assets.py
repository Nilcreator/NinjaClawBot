"""Persistent movement and expression assets used by ninjaclawbot."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from ninjaclawbot.config import NinjaClawbotConfig
from ninjaclawbot.errors import ActionValidationError

_NAME_PATTERN = re.compile(r"^[a-zA-Z0-9_-]+$")


def _validate_asset_name(name: str) -> str:
    if not isinstance(name, str) or not name.strip():
        raise ActionValidationError("Asset name must be a non-empty string.")
    if not _NAME_PATTERN.fullmatch(name):
        raise ActionValidationError(
            "Asset name may only contain letters, numbers, underscores, and hyphens."
        )
    return name


def validate_movement_asset(payload: dict[str, Any]) -> dict[str, Any]:
    name = _validate_asset_name(str(payload.get("name", "")).strip())
    steps = payload.get("steps")
    if not isinstance(steps, list) or not steps:
        raise ActionValidationError("Movement assets must contain a non-empty 'steps' list.")
    normalized_steps: list[dict[str, Any]] = []
    for index, step in enumerate(steps, start=1):
        if not isinstance(step, dict):
            raise ActionValidationError(f"Movement step {index} must be a dictionary.")
        targets = step.get("targets")
        if not isinstance(targets, dict) or not targets:
            raise ActionValidationError(f"Movement step {index} must contain non-empty targets.")
        for endpoint, angle in targets.items():
            if not isinstance(endpoint, str) or not endpoint:
                raise ActionValidationError(f"Movement step {index} has an invalid endpoint key.")
            if not isinstance(angle, (int, float)):
                raise ActionValidationError(f"Movement step {index} angles must be numeric.")
        normalized_steps.append(
            {
                "targets": {str(key): float(value) for key, value in targets.items()},
                "speed_mode": str(step.get("speed_mode", "M")),
                "easing": str(step.get("easing", "ease_in_out_cubic")),
                "pause_after_ms": int(step.get("pause_after_ms", 0)),
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
        return validate_movement_asset(json.loads(path.read_text(encoding="utf-8")))

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
        return validate_expression_asset(json.loads(path.read_text(encoding="utf-8")))

    def delete_expression(self, name: str) -> None:
        path = self.config.expression_asset_dir / f"{_validate_asset_name(name)}.json"
        path.unlink(missing_ok=True)
