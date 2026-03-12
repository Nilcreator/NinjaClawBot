"""CLI entrypoint for the ninjaclawbot package."""

from __future__ import annotations

import json
from typing import Any

import click

from ninjaclawbot.actions import ActionRequest
from ninjaclawbot.cli.common import create_executor, extract_movement_data, parse_movement_command
from ninjaclawbot.cli.expression_tool import expression_tool
from ninjaclawbot.cli.movement_tool import movement_tool
from ninjaclawbot.expressions.policy import list_reply_states


def _execute_and_print(root_dir: str, payload: ActionRequest | dict[str, Any]) -> None:
    executor = create_executor(root_dir)
    try:
        result = executor.execute(payload)
    finally:
        executor.runtime.close()
    click.echo(json.dumps(result.to_dict(), indent=2))


@click.group()
@click.option(
    "--root-dir", default=".", help="Project directory containing config and asset files."
)
@click.pass_context
def cli(ctx: click.Context, root_dir: str) -> None:
    """High-level robot control entrypoint for NinjaClawBot."""

    ctx.ensure_object(dict)
    ctx.obj["root_dir"] = root_dir


@cli.command("list-assets")
@click.option(
    "--asset-type",
    default="all",
    type=click.Choice(["all", "movements", "expressions"]),
    show_default=True,
)
@click.pass_context
def list_assets(ctx: click.Context, asset_type: str) -> None:
    """List saved movement and expression assets."""

    _execute_and_print(
        ctx.obj["root_dir"],
        {"action": "list_assets", "parameters": {"asset_type": asset_type}},
    )


@cli.command("health-check")
@click.pass_context
def health_check(ctx: click.Context) -> None:
    """Run an integrated hardware availability check."""

    _execute_and_print(ctx.obj["root_dir"], {"action": "health_check"})


@cli.command("list-capabilities")
@click.pass_context
def list_capabilities(ctx: click.Context) -> None:
    """List the supported actions, reply states, and expression catalog."""

    _execute_and_print(ctx.obj["root_dir"], {"action": "list_capabilities"})


@cli.command("run-action")
@click.argument("payload")
@click.pass_context
def run_action(ctx: click.Context, payload: str) -> None:
    """Execute a JSON action payload."""

    request = ActionRequest.from_dict(json.loads(payload))
    _execute_and_print(ctx.obj["root_dir"], request)


@cli.command("openclaw-action", hidden=True)
@click.argument("payload")
@click.pass_context
def openclaw_action(ctx: click.Context, payload: str) -> None:
    """Machine-facing JSON action bridge for the OpenClaw plugin."""

    request = ActionRequest.from_dict(json.loads(payload))
    _execute_and_print(ctx.obj["root_dir"], request)


@cli.command("move-servos")
@click.argument("command")
@click.pass_context
def move_servos(ctx: click.Context, command: str) -> None:
    """Move servos using movement-tool syntax like `F_gpio12:30/hat_pwm1:C`."""

    speed_mode, parsed_moves = parse_movement_command(command)
    targets, per_servo_speeds = extract_movement_data(parsed_moves)
    _execute_and_print(
        ctx.obj["root_dir"],
        {
            "action": "move_servos",
            "parameters": {
                "targets": targets,
                "speed_mode": speed_mode,
                "per_servo_speeds": per_servo_speeds,
            },
        },
    )


@cli.command("perform-movement")
@click.argument("name")
@click.pass_context
def perform_movement(ctx: click.Context, name: str) -> None:
    """Run a saved movement asset."""

    _execute_and_print(
        ctx.obj["root_dir"],
        {"action": "perform_movement", "parameters": {"name": name}},
    )


@cli.command("perform-reply")
@click.argument("text")
@click.option(
    "--reply-state",
    type=click.Choice(list_reply_states()),
    default="speaking",
    show_default=True,
)
@click.option("--display-text", default=None, help="Short text to render on the robot display.")
@click.option("--duration", default=3.0, show_default=True, type=float)
@click.option("--language", default="en", show_default=True)
@click.option("--font-size", default=32, show_default=True, type=int)
@click.pass_context
def perform_reply(
    ctx: click.Context,
    text: str,
    reply_state: str,
    display_text: str | None,
    duration: float,
    language: str,
    font_size: int,
) -> None:
    """Render a reply using the built-in reply-emotion policy."""

    _execute_and_print(
        ctx.obj["root_dir"],
        {
            "action": "perform_reply",
            "parameters": {
                "text": text,
                "reply_state": reply_state,
                "display_text": display_text,
                "duration": duration,
                "language": language,
                "font_size": font_size,
            },
        },
    )


@cli.command("perform-expression")
@click.argument("name")
@click.pass_context
def perform_expression(ctx: click.Context, name: str) -> None:
    """Run a saved expression asset or a built-in expression."""

    _execute_and_print(
        ctx.obj["root_dir"],
        {"action": "perform_expression", "parameters": {"name": name}},
    )


@cli.command("set-idle")
@click.pass_context
def set_idle(ctx: click.Context) -> None:
    """Start the persistent idle expression."""

    _execute_and_print(ctx.obj["root_dir"], {"action": "set_idle"})


@cli.command("stop-expression")
@click.pass_context
def stop_expression(ctx: click.Context) -> None:
    """Stop the active expression loop."""

    _execute_and_print(ctx.obj["root_dir"], {"action": "stop_expression"})


cli.add_command(movement_tool)
cli.add_command(expression_tool)
