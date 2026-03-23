"""Status command for pi5camera."""

from __future__ import annotations

import click

from pi5camera.cli._common import describe_camera_stack, load_manager
from pi5camera.errors import ConfigError


@click.command("status")
@click.pass_context
def status(ctx: click.Context) -> None:
    """Show the current config and local readiness summary."""
    try:
        manager = load_manager(ctx.obj.get("config_file"))
        summary = describe_camera_stack(manager.config)
    except ConfigError as exc:
        raise click.ClickException(str(exc)) from exc

    click.echo("pi5camera status")
    click.echo("----------------")
    click.echo(f"Config path: {manager.path}")
    click.echo(f"Active root: {manager.active_root}")
    click.echo(f"Photo dir:   {summary['photo_dir']}")
    click.echo(f"Data dir:    {summary['data_dir']}")
    click.echo(f"Resolution: {summary['resolution']['width']}x{summary['resolution']['height']}")
    click.echo(f"Warm-up:     {summary['warmup_seconds']:.1f}s")
    click.echo(
        "Camera:      "
        f"{summary['camera_backend']} "
        f"({'ready' if summary['camera_backend_available'] else 'missing'})"
    )
    click.echo(
        "Recognition: "
        f"{summary['recognition_backend']} "
        f"({'ready' if summary['recognition_backend_available'] else 'missing'})"
    )
