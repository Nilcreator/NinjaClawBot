"""Shared CLI helpers for ninjaclawbot."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import click
from pi5servo.core.endpoint import parse_servo_endpoint

from ninjaclawbot.config import NinjaClawbotConfig
from ninjaclawbot.executor import ActionExecutor
from ninjaclawbot.runtime import NinjaClawbotRuntime

_SPEED_CHOICES = {"S", "M", "F"}


def create_executor(root_dir: str | Path) -> ActionExecutor:
    """Build an executor scoped to a working directory."""

    config = NinjaClawbotConfig(root_dir=Path(root_dir).resolve())
    from ninjaclawbot.assets import AssetStore

    runtime = NinjaClawbotRuntime(config)
    store = AssetStore(config)
    return ActionExecutor(runtime=runtime, asset_store=store)


def print_json(payload: dict[str, Any]) -> None:
    click.echo(json.dumps(payload, indent=2))


def normalize_endpoint_label(endpoint: int | str) -> str:
    """Normalize servo endpoint labels to stable config identifiers."""

    try:
        return parse_servo_endpoint(endpoint).identifier
    except ValueError as exc:
        raise click.ClickException(str(exc)) from exc


def parse_movement_command(
    command: str,
) -> tuple[str, dict[str, dict[str, float | str | None]]]:
    """Parse a legacy-style movement command with optional per-servo speeds."""

    raw = command.strip()
    if not raw:
        raise click.ClickException("Movement command cannot be empty.")

    global_speed = "M"
    if raw.startswith(("S_", "M_", "F_")):
        global_speed = raw[0]
        raw = raw[2:]

    movements: dict[str, dict[str, float | str | None]] = {}
    for part in raw.split("/"):
        part = part.strip()
        if not part:
            continue
        try:
            endpoint_text, value_text = part.split(":", 1)
        except ValueError as exc:
            raise click.ClickException(
                f"Invalid movement part '{part}'. Use endpoint:angle."
            ) from exc

        endpoint = normalize_endpoint_label(endpoint_text.strip())
        value_text = value_text.strip().upper()
        per_servo_speed: str | None = None

        if value_text and value_text[-1] in _SPEED_CHOICES:
            candidate_value = value_text[:-1]
            if candidate_value in {"C", "X", "M"} or (
                candidate_value and not candidate_value[-1].isalpha()
            ):
                per_servo_speed = value_text[-1]
                value_text = candidate_value

        if value_text == "C":
            angle = 0.0
        elif value_text == "X":
            angle = 90.0
        elif value_text == "M":
            angle = -90.0
        else:
            try:
                angle = float(value_text)
            except ValueError as exc:
                raise click.ClickException(
                    f"Invalid angle '{value_text}' for endpoint '{endpoint_text}'."
                ) from exc

        movements[endpoint] = {"angle": angle, "speed": per_servo_speed}

    if not movements:
        raise click.ClickException("Movement command did not contain any servo targets.")
    return global_speed, movements


def extract_movement_data(
    movements: dict[str, dict[str, float | str | None]],
) -> tuple[dict[str, float], dict[str, str]]:
    """Split parsed movement command data into angle and per-servo speed mappings."""

    angles = {endpoint: float(data["angle"]) for endpoint, data in movements.items()}
    per_servo_speeds = {
        endpoint: str(data["speed"])
        for endpoint, data in movements.items()
        if data.get("speed") is not None
    }
    return angles, per_servo_speeds
