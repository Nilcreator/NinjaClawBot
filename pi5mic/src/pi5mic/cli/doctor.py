"""Diagnostics for pi5mic."""

from __future__ import annotations

import os

import click

from pi5mic.core.devices import list_input_devices
from pi5mic.errors import ConfigError, DeviceError, STTError, TransportError
from pi5mic.install.whisper_cpp import resolve_model_path, resolve_whisper_cpp_command
from pi5mic.integration.delivery import describe_delivery_mode

from ._common import build_openclaw_transport, build_presence_controller, load_manager


@click.command("doctor")
@click.pass_context
def doctor(ctx: click.Context) -> None:
    """Check local config, microphone readiness, and STT prerequisites."""
    failures: list[str] = []

    try:
        manager = load_manager(ctx.obj.get("config_file"))
        config = manager.config
        click.echo(f"OK   config loaded: {manager.path}")
    except ConfigError as exc:
        raise click.ClickException(str(exc)) from exc

    try:
        devices = list_input_devices()
        click.echo(f"OK   audio devices discovered: {len(devices)}")
    except DeviceError as exc:
        failures.append(f"audio devices unavailable: {exc}")

    selected_backend = str(config["stt"]["selected"])
    click.echo(f"INFO active STT backend: {selected_backend}")
    if selected_backend == "whisper_cpp":
        whisper_config = config["stt"]["whisper_cpp"]
        try:
            resolved_command = resolve_whisper_cpp_command(whisper_config.get("command"))
            resolved_model = resolve_model_path(whisper_config.get("model_path"))
            click.echo(f"OK   whisper.cpp command: {resolved_command}")
            click.echo(f"OK   whisper.cpp model:   {resolved_model}")
        except STTError as exc:
            failures.append(str(exc))
    elif selected_backend == "gemini":
        if os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY"):
            click.echo("OK   Gemini credentials found in environment")
        else:
            failures.append("Gemini credentials are not configured in the environment.")
    else:
        failures.append(f"Unsupported STT backend configured: {selected_backend}")

    if config["profile"] == "openclaw":
        openclaw_config = config["integration"]["openclaw"]
        try:
            transport = build_openclaw_transport(config)
            click.echo(f"OK   OpenClaw command:  {transport.command}")
            click.echo(
                "OK   OpenClaw delivery: "
                + describe_delivery_mode(
                    str(config["integration"].get("delivery_mode", "local_only")),
                    reply_channel=openclaw_config.get("reply_channel"),
                    reply_to=openclaw_config.get("reply_to"),
                )
            )
            if bool(config["integration"].get("presence_enabled", True)):
                build_presence_controller(config)
                click.echo("OK   OpenClaw presence control is configured")
        except (ConfigError, TransportError) as exc:
            failures.append(str(exc))

    if failures:
        click.echo("\nFailures:")
        for failure in failures:
            click.echo(f"  - {failure}")
        raise click.ClickException("pi5mic doctor detected configuration problems.")

    click.echo("\npi5mic doctor passed.")
