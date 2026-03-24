"""Doctor command for pi5camera."""

from __future__ import annotations

from pathlib import Path

import click

from pi5camera.cli._common import describe_camera_stack, load_manager
from pi5camera.errors import ConfigError


def _is_writable_directory(path: str) -> bool:
    target = Path(path)
    try:
        target.mkdir(parents=True, exist_ok=True)
        probe = target / ".pi5camera-write-test"
        probe.write_text("ok", encoding="utf-8")
        probe.unlink()
    except OSError:
        return False
    return True


@click.command("doctor")
@click.pass_context
def doctor(ctx: click.Context) -> None:
    """Check config, directories, and local backend readiness."""
    try:
        manager = load_manager(ctx.obj.get("config_file"))
        summary = describe_camera_stack(manager.config)
    except ConfigError as exc:
        raise click.ClickException(str(exc)) from exc

    warnings: list[str] = []

    if not _is_writable_directory(summary["photo_dir"]):
        warnings.append(f"Photo directory is not writable: {summary['photo_dir']}")
    if not _is_writable_directory(summary["data_dir"]):
        warnings.append(f"Camera data directory is not writable: {summary['data_dir']}")
    if not summary["camera_backend_available"]:
        warnings.append(summary["camera_backend_help_text"])
    if not summary["recognition_backend_available"]:
        warnings.append(
            "The face_recognition Python package is not importable in this environment."
        )

    click.echo("pi5camera doctor")
    click.echo("----------------")
    click.echo(f"Config path: {manager.path}")
    click.echo(f"Python:      {summary['python_executable']}")
    click.echo(f"Photo dir:   {summary['photo_dir']}")
    click.echo(f"Data dir:    {summary['data_dir']}")
    if summary["system_python"] is not None:
        click.echo(
            f"System Py:   {summary['system_python']} "
            f"({'ok' if summary['system_python_available'] else 'missing'})"
        )
    click.echo(f"Camera backend: {summary['camera_backend']} ({summary['camera_backend_state']})")
    click.echo(
        f"Recognition backend: {summary['recognition_backend']} "
        f"({'ok' if summary['recognition_backend_available'] else 'missing'})"
    )

    if warnings:
        click.echo("\nWarnings:")
        for warning in warnings:
            click.echo(f"- {warning}")
        click.echo("\npi5camera doctor passed with warnings.")
        return

    click.echo("\npi5camera doctor passed.")
