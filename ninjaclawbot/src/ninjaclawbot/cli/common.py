"""Shared CLI helpers for ninjaclawbot."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import click

from ninjaclawbot.config import NinjaClawbotConfig
from ninjaclawbot.executor import ActionExecutor


def build_executor(root_dir: str | Path) -> ActionExecutor:
    """Build an executor scoped to a working directory."""

    config = NinjaClawbotConfig(root_dir=Path(root_dir).resolve())
    return ActionExecutor(asset_store=None, runtime=None if config else None)  # pragma: no cover


def create_executor(root_dir: str | Path) -> ActionExecutor:
    config = NinjaClawbotConfig(root_dir=Path(root_dir).resolve())
    from ninjaclawbot.assets import AssetStore
    from ninjaclawbot.runtime import NinjaClawbotRuntime

    runtime = NinjaClawbotRuntime(config)
    store = AssetStore(config)
    return ActionExecutor(runtime=runtime, asset_store=store)


def print_json(payload: dict[str, Any]) -> None:
    click.echo(json.dumps(payload, indent=2))


def parse_step_command(command: str) -> tuple[str, dict[str, float]]:
    """Parse a movement-tool style command using endpoint names."""

    raw = command.strip()
    if not raw:
        raise click.ClickException("Movement command cannot be empty.")

    global_speed = "M"
    if raw.startswith(("S_", "M_", "F_")):
        global_speed = raw[0]
        raw = raw[2:]

    targets: dict[str, float] = {}
    for part in raw.split("/"):
        try:
            endpoint, angle_text = part.split(":", 1)
        except ValueError as exc:
            raise click.ClickException(
                f"Invalid movement part '{part}'. Use endpoint:angle."
            ) from exc

        endpoint = endpoint.strip()
        if not endpoint:
            raise click.ClickException("Movement command contains an empty endpoint name.")

        angle_text = angle_text.strip().upper()
        if angle_text == "C":
            angle = 0.0
        elif angle_text == "X":
            angle = 90.0
        elif angle_text == "M":
            angle = -90.0
        else:
            try:
                angle = float(angle_text)
            except ValueError as exc:
                raise click.ClickException(
                    f"Invalid angle '{angle_text}' for endpoint '{endpoint}'."
                ) from exc
        targets[endpoint] = angle

    return global_speed, targets
