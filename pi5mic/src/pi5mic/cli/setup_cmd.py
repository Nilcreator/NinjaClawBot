"""Interactive setup wizard for pi5mic."""

from __future__ import annotations

from pathlib import Path

import click

from pi5mic.core.devices import get_recommended_sample_rate, list_input_devices
from pi5mic.core.system_info import is_raspberry_pi
from pi5mic.errors import ConfigError, DeviceError, IntegrationError, STTError, TransportError
from pi5mic.install.whisper_cpp import DEFAULT_MODEL_FILE, find_whisper_cpp_command
from pi5mic.integration.openclaw_setup import (
    approve_latest_openclaw_pairing,
    discover_openclaw_auto_config,
    explain_openclaw_error,
    is_pairing_required_error,
    probe_openclaw_voice_ready,
    summarize_openclaw_auto_config,
)
from pi5mic.stt.gemini import describe_gemini_env_help
from pi5mic.stt.whisper_cpp import recommend_whisper_threads
from pi5mic.transport.openclaw_cli import find_openclaw_command

from ._common import build_stt_backend, load_manager


def _set_local_only_delivery(integration_config: dict, openclaw_config: dict) -> None:
    integration_config["delivery_mode"] = "local_only"
    openclaw_config["reply_channel"] = None
    openclaw_config["reply_to"] = None
    openclaw_config["reply_account"] = None


def _configure_openclaw_delivery(
    *,
    integration_config: dict,
    openclaw_config: dict,
    discovery,
) -> None:
    if discovery.telegram_reply_target is not None:
        click.echo("\nOpenClaw reply delivery")
        click.echo(
            "pi5mic found a Telegram conversation target that OpenClaw can reuse for voice turns."
        )
        click.echo(f"Detected Telegram target: {discovery.telegram_reply_target.describe()}")
        use_telegram = click.confirm(
            "Ask OpenClaw to reply both here and in Telegram?",
            default=True,
        )
        if use_telegram:
            integration_config["delivery_mode"] = "local_plus_explicit_channel_target"
            openclaw_config["reply_channel"] = discovery.telegram_reply_target.channel
            openclaw_config["reply_to"] = discovery.telegram_reply_target.target
            openclaw_config["reply_account"] = discovery.telegram_reply_target.account_id
            click.echo(
                "pi5mic will keep showing the OpenClaw reply locally and will also ask "
                "OpenClaw to deliver the same reply to Telegram."
            )
            return

        _set_local_only_delivery(integration_config, openclaw_config)
        click.echo("pi5mic will keep replies local only for now.")
        return

    if discovery.telegram_enabled:
        click.echo("\nOpenClaw reply delivery")
        click.echo(
            "OpenClaw Telegram is enabled, but pi5mic could not find a recent Telegram "
            "conversation target to mirror voice replies automatically."
        )
        if discovery.telegram_reply_target_error:
            click.echo(discovery.telegram_reply_target_error)
        click.echo(
            "Fastest fix: send one short message to your OpenClaw Telegram bot from the chat "
            "or topic where you want replies, then rerun `uv run pi5mic setup`."
        )
        if click.confirm("Enter a Telegram target manually now?", default=False):
            target = click.prompt(
                "Telegram target (chat id or -100...:topic:123)",
            ).strip()
            account_default = (
                discovery.telegram_default_account
                or str(openclaw_config.get("reply_account") or "").strip()
            )
            account = click.prompt(
                "Telegram account id (leave blank for default account)",
                default=account_default,
                show_default=bool(account_default),
            ).strip()
            integration_config["delivery_mode"] = "local_plus_explicit_channel_target"
            openclaw_config["reply_channel"] = "telegram"
            openclaw_config["reply_to"] = target
            openclaw_config["reply_account"] = account or None
            click.echo(
                "pi5mic saved the manual Telegram target. Test it with `uv run pi5mic doctor` "
                "before relying on it."
            )
            return

    _set_local_only_delivery(integration_config, openclaw_config)
    if not discovery.telegram_enabled:
        click.echo(
            "Replies will stay local because OpenClaw Telegram is not enabled in its config yet."
        )
    else:
        click.echo("Replies will stay local until pi5mic can discover or save a Telegram target.")


def _configure_openclaw_profile(config: dict) -> None:
    """Auto-discover the local OpenClaw settings and apply them to the config."""
    integration_config = config["integration"]
    openclaw_config = integration_config["openclaw"]
    click.echo("\nOpenClaw auto-setup")
    click.echo("pi5mic will look for your local OpenClaw configuration and reuse it automatically.")
    click.echo(
        "This avoids typing gateway settings by hand and prepares the profile for "
        "`Run one capture cycle` or `uv run pi5mic run --once`."
    )

    try:
        discovery = discover_openclaw_auto_config(
            command=openclaw_config.get("command"),
            saved_gateway_url=openclaw_config.get("gateway_url"),
            saved_agent_id=openclaw_config.get("agent_id"),
            saved_session_key=openclaw_config.get("session_key"),
            saved_reply_channel=openclaw_config.get("reply_channel"),
            saved_reply_to=openclaw_config.get("reply_to"),
            saved_reply_account=openclaw_config.get("reply_account"),
        )
    except TransportError as exc:
        detected_openclaw = find_openclaw_command(openclaw_config.get("command"))
        if detected_openclaw is not None:
            openclaw_config["command"] = str(detected_openclaw)
        click.echo("WARNING: pi5mic could not finish automatic OpenClaw discovery.")
        click.echo(explain_openclaw_error(str(exc)))
        click.echo(
            "pi5mic kept the saved OpenClaw values for now. After fixing OpenClaw, rerun "
            "`uv run pi5mic setup` or `uv run pi5mic doctor`."
        )
        return

    openclaw_config["command"] = str(discovery.command)
    openclaw_config["gateway_url"] = discovery.gateway_url
    openclaw_config["agent_id"] = discovery.agent_id
    openclaw_config["session_key"] = discovery.session_key

    click.echo("\nDetected OpenClaw settings:")
    for line in summarize_openclaw_auto_config(discovery):
        click.echo(f"  - {line}")

    _configure_openclaw_delivery(
        integration_config=integration_config,
        openclaw_config=openclaw_config,
        discovery=discovery,
    )

    if discovery.plugin_ready:
        return

    click.echo(
        "WARNING: The local OpenClaw config does not yet look fully ready for the "
        "NinjaClawBot plugin."
    )
    if not discovery.plugin_install_found:
        click.echo("  - OpenClaw does not show a NinjaClawBot plugin install/load path yet.")
    if not discovery.plugin_allowlisted:
        click.echo("  - The plugin is not listed in `plugins.allow`.")
    if not discovery.plugin_enabled:
        click.echo("  - The plugin entry does not look enabled.")
    click.echo(
        "pi5mic can still save the profile now, but OpenClaw may reject presence updates or "
        "voice handoff until the plugin is installed, allowlisted, and enabled. After fixing "
        "that, restart the gateway and run `uv run pi5mic doctor`."
    )


def _run_openclaw_readiness_check(config: dict) -> None:
    """Run a post-save OpenClaw preflight and guide the user through pairing if needed."""
    integration_config = config["integration"]
    openclaw_config = integration_config["openclaw"]
    check_presence = bool(integration_config.get("presence_enabled", True))

    click.echo("\nOpenClaw readiness check")
    click.echo(
        "pi5mic will make a safe local call to OpenClaw to confirm the voice handoff path is ready."
    )

    try:
        lines = probe_openclaw_voice_ready(
            command=openclaw_config.get("command"),
            gateway_url=openclaw_config.get("gateway_url"),
            check_presence=check_presence,
        )
        for line in lines:
            click.echo(f"OK   {line}")
        click.echo(
            "OpenClaw voice handoff is ready. You can now use `5. Run one capture cycle` or "
            "`uv run pi5mic run --once`."
        )
        return
    except (IntegrationError, TransportError) as exc:
        message = explain_openclaw_error(str(exc))
        click.echo("WARNING: OpenClaw is not fully ready yet.")
        click.echo(message)

    if not is_pairing_required_error(message):
        click.echo(
            "After fixing the issue above, rerun `uv run pi5mic doctor` to verify the "
            "OpenClaw path."
        )
        return

    click.echo(
        "This usually means OpenClaw created a local device request that still needs a "
        "one-time approval."
    )
    should_approve = click.confirm(
        "Approve the newest local OpenClaw device request now?",
        default=True,
    )
    if not should_approve:
        click.echo(
            "OpenClaw was not approved yet. When you're ready, run "
            "`openclaw devices approve --latest` and then `uv run pi5mic doctor`."
        )
        return

    try:
        approval_message = approve_latest_openclaw_pairing(openclaw_config.get("command"))
        click.echo(f"OK   {approval_message}")
        lines = probe_openclaw_voice_ready(
            command=openclaw_config.get("command"),
            gateway_url=openclaw_config.get("gateway_url"),
            check_presence=check_presence,
        )
    except (IntegrationError, TransportError) as exc:
        click.echo("WARNING: Automatic OpenClaw approval did not finish cleanly.")
        click.echo(explain_openclaw_error(str(exc)))
        click.echo(
            "If needed, run `openclaw devices list`, approve the pending local request, "
            "then rerun `uv run pi5mic doctor`."
        )
        return

    for line in lines:
        click.echo(f"OK   {line}")
    click.echo(
        "OpenClaw voice handoff is ready. You can now use `5. Run one capture cycle` or "
        "`uv run pi5mic run --once`."
    )


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

    recommended_sample_rate = get_recommended_sample_rate(
        config["audio"]["input_device"],
        fallback_rate=int(config["audio"]["sample_rate"]),
    )
    if recommended_sample_rate != int(config["audio"]["sample_rate"]):
        click.echo(
            f"Recommended sample rate for this microphone: {recommended_sample_rate} Hz "
            "(using the device default reported by PortAudio/ALSA)."
        )
    config["audio"]["sample_rate"] = click.prompt(
        "Sample rate (Hz)",
        type=int,
        default=recommended_sample_rate,
    )

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
        configured_threads = (
            int(whisper_config["threads"])
            if whisper_config.get("threads") not in (None, "")
            else None
        )
        recommended_threads = recommend_whisper_threads(configured_threads)
        if recommended_threads is not None and configured_threads is None:
            click.echo(
                "Recommended whisper.cpp thread limit on this device: "
                f"{recommended_threads} (safer on Raspberry Pi)."
            )
        thread_default = (
            str(configured_threads)
            if configured_threads is not None
            else (str(recommended_threads) if recommended_threads is not None else "")
        )
        thread_prompt = click.prompt(
            "whisper.cpp threads (leave blank for automatic)",
            default=thread_default,
            show_default=bool(thread_default),
        ).strip()
        whisper_config["threads"] = int(thread_prompt) if thread_prompt else None
        whisper_config["timeout_seconds"] = click.prompt(
            "whisper.cpp timeout (seconds)",
            type=int,
            default=int(whisper_config.get("timeout_seconds", 120)),
        )
    else:
        gemini_config = config["stt"]["gemini"]
        gemini_config["model"] = click.prompt(
            "Gemini model id",
            default=str(gemini_config.get("model", "gemini-2.5-flash")),
        ).strip()
        gemini_config["timeout_seconds"] = click.prompt(
            "Gemini request timeout (seconds)",
            type=int,
            default=int(gemini_config.get("timeout_seconds", 60)),
        )
        gemini_config["retry_limit"] = click.prompt(
            "Gemini retry limit",
            type=int,
            default=int(gemini_config.get("retry_limit", 2)),
        )
        click.echo(
            "Gemini requires GOOGLE_API_KEY or GEMINI_API_KEY in the environment before use."
        )
        click.echo(describe_gemini_env_help())

    max_clip_default = float(config["audio"]["max_clip_seconds"])
    if backend == "whisper_cpp" and is_raspberry_pi() and max_clip_default > 12.0:
        click.echo(
            "The current preview path records a fixed-length clip before transcription. "
            "On Raspberry Pi, 8 to 12 seconds is a safer starting point."
        )
        max_clip_default = 12.0
    max_clip_seconds = click.prompt(
        "Maximum clip length (seconds)",
        type=float,
        default=max_clip_default,
    )
    config["audio"]["max_clip_seconds"] = max_clip_seconds

    if profile == "openclaw":
        _configure_openclaw_profile(config)

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

    if profile == "openclaw":
        _run_openclaw_readiness_check(config)
