"""Diagnostics for pi5mic."""

from __future__ import annotations

import importlib.util

import click

from pi5mic.core.devices import list_input_devices, resolve_supported_input_settings
from pi5mic.core.system_info import (
    is_raspberry_pi,
    read_linux_mem_available_mb,
    read_raspberry_pi_model,
    read_raspberry_pi_temperature_celsius,
    read_raspberry_pi_throttled_state,
)
from pi5mic.errors import ConfigError, DeviceError, STTError, TransportError
from pi5mic.install.whisper_cpp import resolve_model_path, resolve_whisper_cpp_command
from pi5mic.integration.delivery import describe_delivery_mode
from pi5mic.stt.gemini import describe_gemini_env_help, resolve_gemini_api_key
from pi5mic.stt.whisper_cpp import describe_whisper_runtime, recommend_whisper_threads

from ._common import build_openclaw_transport, build_presence_controller, load_manager


@click.command("doctor")
@click.pass_context
def doctor(ctx: click.Context) -> None:
    """Check local config, microphone readiness, and STT prerequisites."""
    failures: list[str] = []
    warnings: list[str] = []

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
        devices = []

    if is_raspberry_pi():
        model = read_raspberry_pi_model()
        if model:
            click.echo(f"INFO Raspberry Pi: {model}")
        temperature = read_raspberry_pi_temperature_celsius()
        if temperature is not None:
            click.echo(f"INFO Raspberry Pi temp: {temperature:.1f} C")
            if temperature >= 75.0:
                warnings.append(
                    "Raspberry Pi temperature is already high. Heavy whisper.cpp runs may "
                    "throttle or become unstable without better cooling."
                )
        throttled_hex, throttled_issues = read_raspberry_pi_throttled_state()
        if throttled_hex is not None:
            click.echo(f"INFO Raspberry Pi throttled state: {throttled_hex}")
        for issue in throttled_issues:
            warnings.append(
                "Raspberry Pi firmware reported " + issue + ". "
                "If the board powered off after recording, check the power supply and cooling."
            )

    if devices:
        audio_config = config["audio"]
        try:
            resolved_device, actual_rate, device_info, warning = resolve_supported_input_settings(
                selector=audio_config.get("input_device"),
                sample_rate=int(audio_config["sample_rate"]),
                channels=int(audio_config["channels"]),
            )
            device_label = (
                f"{device_info.name} [{device_info.index}]"
                if device_info is not None
                else f"default ({resolved_device if resolved_device is not None else 'auto'})"
            )
            click.echo(f"OK   input stream settings: {device_label} @ {actual_rate} Hz")
            if warning:
                warnings.append(warning)
        except DeviceError as exc:
            failures.append(str(exc))

    selected_backend = str(config["stt"]["selected"])
    click.echo(f"INFO active STT backend: {selected_backend}")
    if selected_backend == "whisper_cpp":
        whisper_config = config["stt"]["whisper_cpp"]
        try:
            resolved_command = resolve_whisper_cpp_command(whisper_config.get("command"))
            resolved_model = resolve_model_path(whisper_config.get("model_path"))
            click.echo(f"OK   whisper.cpp command: {resolved_command}")
            click.echo(f"OK   whisper.cpp model:   {resolved_model}")
            configured_threads = (
                int(whisper_config["threads"])
                if whisper_config.get("threads") not in (None, "")
                else None
            )
            click.echo("OK   whisper.cpp runtime: " + describe_whisper_runtime(configured_threads))
            if (
                is_raspberry_pi()
                and configured_threads is None
                and recommend_whisper_threads(None) is not None
            ):
                warnings.append(
                    "whisper.cpp thread count is not explicitly configured. "
                    "pi5mic will cap it to a safer Raspberry Pi default automatically."
                )
            max_clip_seconds = float(config["audio"].get("max_clip_seconds", 12.0))
            if is_raspberry_pi() and max_clip_seconds > 12.0:
                warnings.append(
                    f"Maximum clip length is {max_clip_seconds:.0f}s. "
                    "The current preview path records the full clip before transcription, "
                    "so 8 to 12 seconds is a safer Raspberry Pi starting point."
                )
            available_mb = read_linux_mem_available_mb()
            if is_raspberry_pi() and available_mb is not None and available_mb < 1024:
                warnings.append(
                    f"Only about {available_mb} MiB of memory is currently available. "
                    "Close other apps, lower clip length, or switch to Gemini if whisper.cpp "
                    "still destabilizes the Pi."
                )
        except STTError as exc:
            failures.append(str(exc))
    elif selected_backend == "gemini":
        try:
            gemini_spec = importlib.util.find_spec("google.genai")
        except ModuleNotFoundError:
            gemini_spec = None
        if gemini_spec is None:
            failures.append(
                "The 'google-genai' package is not installed. Run 'uv sync --extra dev' "
                "from the NinjaClawBot root so pi5mic can use the Gemini backend."
            )
        try:
            credential_name, _api_key = resolve_gemini_api_key()
            click.echo(f"OK   Gemini credentials found in environment ({credential_name})")
        except STTError as exc:
            failures.append(f"{exc} {describe_gemini_env_help()}")
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

    if warnings:
        click.echo("\nWarnings:")
        for warning in warnings:
            click.echo(f"  - {warning}")
        click.echo("\npi5mic doctor passed with warnings.")
        return

    click.echo("\npi5mic doctor passed.")
