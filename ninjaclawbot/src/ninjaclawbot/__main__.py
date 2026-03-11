"""CLI entrypoint for the ninjaclawbot package."""

from __future__ import annotations

import json

import click

from ninjaclawbot.actions import ActionRequest
from ninjaclawbot.cli.common import create_executor, extract_movement_data, parse_movement_command
from ninjaclawbot.cli.expression_tool import expression_tool
from ninjaclawbot.cli.movement_tool import movement_tool


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

    result = create_executor(ctx.obj["root_dir"]).execute(
        {"action": "list_assets", "parameters": {"asset_type": asset_type}}
    )
    click.echo(json.dumps(result.to_dict(), indent=2))


@cli.command("health-check")
@click.pass_context
def health_check(ctx: click.Context) -> None:
    """Run an integrated hardware availability check."""

    result = create_executor(ctx.obj["root_dir"]).execute({"action": "health_check"})
    click.echo(json.dumps(result.to_dict(), indent=2))


@cli.command("run-action")
@click.argument("payload")
@click.pass_context
def run_action(ctx: click.Context, payload: str) -> None:
    """Execute a JSON action payload."""

    request = ActionRequest.from_dict(json.loads(payload))
    result = create_executor(ctx.obj["root_dir"]).execute(request)
    click.echo(json.dumps(result.to_dict(), indent=2))


@cli.command("move-servos")
@click.argument("command")
@click.pass_context
def move_servos(ctx: click.Context, command: str) -> None:
    """Move servos using movement-tool syntax like `F_gpio12:30/hat_pwm1:C`."""

    speed_mode, parsed_moves = parse_movement_command(command)
    targets, per_servo_speeds = extract_movement_data(parsed_moves)
    result = create_executor(ctx.obj["root_dir"]).execute(
        {
            "action": "move_servos",
            "parameters": {
                "targets": targets,
                "speed_mode": speed_mode,
                "per_servo_speeds": per_servo_speeds,
            },
        }
    )
    click.echo(json.dumps(result.to_dict(), indent=2))


@cli.command("perform-movement")
@click.argument("name")
@click.pass_context
def perform_movement(ctx: click.Context, name: str) -> None:
    """Run a saved movement asset."""

    result = create_executor(ctx.obj["root_dir"]).execute(
        {"action": "perform_movement", "parameters": {"name": name}}
    )
    click.echo(json.dumps(result.to_dict(), indent=2))


@cli.command("perform-expression")
@click.argument("name")
@click.pass_context
def perform_expression(ctx: click.Context, name: str) -> None:
    """Run a saved expression asset."""

    result = create_executor(ctx.obj["root_dir"]).execute(
        {"action": "perform_expression", "parameters": {"name": name}}
    )
    click.echo(json.dumps(result.to_dict(), indent=2))


cli.add_command(movement_tool)
cli.add_command(expression_tool)
