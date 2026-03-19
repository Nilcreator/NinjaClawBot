"""Status reporting for pi5mic."""

from __future__ import annotations

import click

from pi5mic.core.devices import get_default_input_device, list_input_devices
from pi5mic.errors import ConfigError, DeviceError
from pi5mic.integration.delivery import describe_delivery_mode

from ._common import load_manager


@click.command("status")
@click.pass_context
def status(ctx: click.Context) -> None:
    """Show config and local microphone readiness."""
    try:
        manager = load_manager(ctx.obj.get("config_file"))
    except ConfigError as exc:
        raise click.ClickException(str(exc)) from exc

    config = manager.config
    audio_config = config["audio"]
    stt_config = config["stt"]

    click.echo("pi5mic Status")
    click.echo(f"  Config file:      {manager.path}")
    click.echo(f"  Profile:          {config.get('profile')}")
    click.echo(f"  Input device:     {audio_config.get('input_device') or 'default'}")
    click.echo(f"  Sample rate:      {audio_config.get('sample_rate')} Hz")
    click.echo(f"  Channels:         {audio_config.get('channels')}")
    click.echo(f"  STT backend:      {stt_config.get('selected')}")
    if config.get("profile") == "openclaw":
        openclaw_config = config["integration"]["openclaw"]
        click.echo(f"  OpenClaw command: {openclaw_config.get('command') or 'openclaw (PATH)'}")
        click.echo(
            f"  Gateway URL:      {openclaw_config.get('gateway_url') or 'local CLI config'}"
        )
        click.echo(f"  Agent id:         {openclaw_config.get('agent_id')}")
        click.echo(f"  Session key:      {openclaw_config.get('session_key')}")
        click.echo(
            "  Delivery mode:    "
            + describe_delivery_mode(
                str(config["integration"].get("delivery_mode", "local_only")),
                reply_channel=openclaw_config.get("reply_channel"),
                reply_to=openclaw_config.get("reply_to"),
            )
        )

    try:
        devices = list_input_devices()
        default_device = get_default_input_device()
        click.echo(f"  Input devices:    {len(devices)}")
        click.echo(
            f"  Default device:   {default_device if default_device is not None else 'none'}"
        )
    except DeviceError as exc:
        click.echo(f"  Audio backend:    unavailable ({exc})")
