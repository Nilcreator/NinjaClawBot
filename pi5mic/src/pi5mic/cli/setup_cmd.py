"""Interactive setup wizard for pi5mic."""

from __future__ import annotations

from pathlib import Path

import click

from pi5mic.core.devices import list_input_devices
from pi5mic.errors import ConfigError, DeviceError, STTError
from pi5mic.install.whisper_cpp import DEFAULT_MODEL_FILE, find_whisper_cpp_command
from pi5mic.integration.delivery import SUPPORTED_DELIVERY_MODES
from pi5mic.transport.openclaw_cli import find_openclaw_command

from ._common import build_stt_backend, load_manager


@click.command("setup")
@click.pass_context
def setup_cmd(ctx: click.Context) -> None:
    """Run the guided first-run setup wizard."""
    try:
        manager = load_manager(ctx.obj.get("config_file"))
    except ConfigError as exc:
        raise click.ClickException(str(exc)) from exc

    config = manager.config
    click.echo("pi5mic setup wizard")
    click.echo("------------------")

    profile = click.prompt(
        "Profile",
        type=click.Choice(["standalone", "openclaw"]),
        default=str(config["profile"]),
        show_choices=True,
    )
    config["profile"] = profile

    try:
        devices = list_input_devices()
        if devices:
            click.echo("\nDetected input devices:")
            for device in devices:
                click.echo(f"  [{device.index}] {device.name}")
    except DeviceError as exc:
        click.echo(f"\nWARNING: Could not list audio devices yet: {exc}")

    current_device = config["audio"].get("input_device")
    current_device_display = "default" if current_device in (None, "") else str(current_device)
    device_choice = click.prompt(
        "\nInput device index/name or 'default'",
        default=current_device_display,
    ).strip()
    config["audio"]["input_device"] = None if device_choice.lower() == "default" else device_choice

    backend = click.prompt(
        "STT backend",
        type=click.Choice(["whisper_cpp", "gemini"]),
        default=str(config["stt"]["selected"]),
        show_choices=True,
    )
    config["stt"]["selected"] = backend

    if backend == "whisper_cpp":
        whisper_config = config["stt"]["whisper_cpp"]
        detected_command = find_whisper_cpp_command(whisper_config.get("command"))
        default_command = str(detected_command or whisper_config.get("command") or "whisper-cli")
        command_value = click.prompt("whisper.cpp command path", default=default_command).strip()
        default_model_path = whisper_config.get("model_path") or str(
            Path.home() / ".local" / "share" / "pi5mic" / "models" / DEFAULT_MODEL_FILE
        )
        model_value = click.prompt("whisper.cpp model path", default=default_model_path).strip()
        whisper_config["command"] = command_value
        whisper_config["model_path"] = model_value
    else:
        gemini_config = config["stt"]["gemini"]
        gemini_config["model"] = click.prompt(
            "Gemini model id",
            default=str(gemini_config.get("model", "gemini-3-flash-preview")),
        ).strip()
        click.echo(
            "Gemini requires GOOGLE_API_KEY or GEMINI_API_KEY in the environment before use."
        )

    max_clip_seconds = click.prompt(
        "Maximum clip length (seconds)",
        type=float,
        default=float(config["audio"]["max_clip_seconds"]),
    )
    config["audio"]["max_clip_seconds"] = max_clip_seconds

    if profile == "openclaw":
        integration_config = config["integration"]
        openclaw_config = config["integration"]["openclaw"]
        detected_openclaw = find_openclaw_command(openclaw_config.get("command"))
        default_openclaw_command = str(
            detected_openclaw or openclaw_config.get("command") or "openclaw"
        )
        openclaw_config["command"] = click.prompt(
            "OpenClaw CLI command",
            default=default_openclaw_command,
        ).strip()
        openclaw_config["gateway_url"] = click.prompt(
            "OpenClaw gateway URL",
            default=str(openclaw_config["gateway_url"]),
        ).strip()
        openclaw_config["agent_id"] = click.prompt(
            "OpenClaw agent id",
            default=str(openclaw_config["agent_id"]),
        ).strip()
        openclaw_config["session_key"] = click.prompt(
            "OpenClaw session key",
            default=str(openclaw_config["session_key"]),
        ).strip()
        delivery_mode = click.prompt(
            "Delivery mode",
            type=click.Choice(list(SUPPORTED_DELIVERY_MODES)),
            default=str(integration_config.get("delivery_mode", "local_only")),
            show_choices=True,
        )
        integration_config["delivery_mode"] = delivery_mode
        if delivery_mode == "local_plus_explicit_channel_target":
            openclaw_config["reply_channel"] = click.prompt(
                "Reply channel",
                default=str(openclaw_config.get("reply_channel") or ""),
            ).strip()
            openclaw_config["reply_to"] = click.prompt(
                "Reply target",
                default=str(openclaw_config.get("reply_to") or ""),
            ).strip()
            openclaw_config["reply_account"] = (
                click.prompt(
                    "Reply account (optional)",
                    default=str(openclaw_config.get("reply_account") or ""),
                    show_default=False,
                ).strip()
                or None
            )
        else:
            openclaw_config["reply_channel"] = None
            openclaw_config["reply_to"] = None
            openclaw_config["reply_account"] = None

    try:
        manager.replace(config)
        manager.save()
    except ConfigError as exc:
        raise click.ClickException(str(exc)) from exc

    click.echo(f"\nSaved config to {manager.path}")
    try:
        build_stt_backend(config)
        click.echo("Configured STT backend looks ready.")
    except (ConfigError, STTError) as exc:
        click.echo(f"WARNING: STT backend still needs attention: {exc}")
