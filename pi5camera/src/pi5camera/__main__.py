"""CLI entry point for pi5camera."""

from __future__ import annotations

from pathlib import Path

import click

from pi5camera.cli import (
    camera_tool,
    capture_cmd,
    doctor,
    enroll_cmd,
    manage_faces,
    recognize_cmd,
    setup_cmd,
    status,
)


@click.group()
@click.option(
    "--config-file",
    "-C",
    type=click.Path(path_type=Path),
    default=None,
    help="Path to camera config file (default: ./camera.json).",
)
@click.pass_context
def cli(ctx: click.Context, config_file: Path | None) -> None:
    """pi5camera - Standalone-first Raspberry Pi 5 camera tools."""
    ctx.ensure_object(dict)
    ctx.obj["config_file"] = config_file


cli.add_command(camera_tool)
cli.add_command(capture_cmd)
cli.add_command(doctor)
cli.add_command(enroll_cmd)
cli.add_command(manage_faces)
cli.add_command(recognize_cmd)
cli.add_command(setup_cmd)
cli.add_command(status)


if __name__ == "__main__":
    cli()
