"""OpenClaw autodiscovery and readiness helpers for pi5mic."""

from __future__ import annotations

import json
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from pi5mic.errors import IntegrationError, TransportError
from pi5mic.integration.presence import OpenClawPresenceController
from pi5mic.transport.openclaw_cli import (
    build_gateway_cli_args,
    resolve_openclaw_command,
)

DEFAULT_OPENCLAW_CONFIG_PATH = Path.home() / ".openclaw" / "openclaw.json"
DEFAULT_GATEWAY_URL = "ws://127.0.0.1:18789"
DEFAULT_AGENT_ID = "main"
DEFAULT_SESSION_KEY = "voice:local-mic"


@dataclass(frozen=True, slots=True)
class OpenClawAutoConfig:
    """Detected OpenClaw settings that pi5mic can reuse."""

    command: Path
    config_path: Path | None
    gateway_url: str
    agent_id: str
    session_key: str
    gateway_mode: str
    gateway_bind: str | None
    plugin_enabled: bool
    plugin_allowlisted: bool
    plugin_install_found: bool
    used_defaults: tuple[str, ...] = ()

    @property
    def plugin_ready(self) -> bool:
        """Return True when the NinjaClawBot plugin looks configured."""
        return self.plugin_enabled and self.plugin_allowlisted and self.plugin_install_found


def get_openclaw_config_path(command: str | Path | None = None) -> Path | None:
    """Return the local OpenClaw config file path when it can be located."""
    if DEFAULT_OPENCLAW_CONFIG_PATH.is_file():
        return DEFAULT_OPENCLAW_CONFIG_PATH

    resolved_command = resolve_openclaw_command(command)
    try:
        result = subprocess.run(
            [str(resolved_command), "config", "file"],
            check=False,
            capture_output=True,
            text=True,
            timeout=10,
        )
    except (OSError, subprocess.SubprocessError):
        return None

    if result.returncode != 0:
        return None

    candidate = Path(result.stdout.strip()).expanduser()
    return candidate if candidate.is_file() else None


def discover_openclaw_auto_config(
    *,
    command: str | Path | None,
    saved_gateway_url: str | None = None,
    saved_agent_id: str | None = None,
    saved_session_key: str | None = None,
) -> OpenClawAutoConfig:
    """Read the local OpenClaw config and derive a ready-to-use pi5mic profile."""
    resolved_command = resolve_openclaw_command(command)
    config_path = get_openclaw_config_path(resolved_command)
    payload: dict[str, Any] = {}
    used_defaults: list[str] = []

    if config_path is not None:
        try:
            with config_path.open("r", encoding="utf-8") as handle:
                loaded = json.load(handle)
        except json.JSONDecodeError as exc:
            raise TransportError(f"OpenClaw config file is not valid JSON: {config_path}") from exc
        except OSError as exc:
            raise TransportError(f"Could not read OpenClaw config file: {config_path}") from exc
        if isinstance(loaded, dict):
            payload = loaded
        else:
            raise TransportError(f"OpenClaw config file must contain an object: {config_path}")
    else:
        used_defaults.append("config_path")

    gateway = payload.get("gateway")
    gateway_config = gateway if isinstance(gateway, dict) else {}
    gateway_mode = str(gateway_config.get("mode", "local"))
    gateway_bind = gateway_config.get("bind")
    gateway_url = _detect_gateway_url(
        gateway_config,
        fallback=saved_gateway_url or DEFAULT_GATEWAY_URL,
    )
    if not gateway_config:
        used_defaults.append("gateway_url")

    agent_id = _detect_agent_id(payload) or saved_agent_id or DEFAULT_AGENT_ID
    if _detect_agent_id(payload) is None:
        used_defaults.append("agent_id")

    session_key = (saved_session_key or DEFAULT_SESSION_KEY).strip() or DEFAULT_SESSION_KEY
    if not saved_session_key:
        used_defaults.append("session_key")

    plugin_enabled, plugin_allowlisted, plugin_install_found = _detect_plugin_state(payload)

    return OpenClawAutoConfig(
        command=resolved_command,
        config_path=config_path,
        gateway_url=gateway_url,
        agent_id=agent_id,
        session_key=session_key,
        gateway_mode=gateway_mode,
        gateway_bind=str(gateway_bind).strip() if gateway_bind is not None else None,
        plugin_enabled=plugin_enabled,
        plugin_allowlisted=plugin_allowlisted,
        plugin_install_found=plugin_install_found,
        used_defaults=tuple(dict.fromkeys(used_defaults)),
    )


def summarize_openclaw_auto_config(discovery: OpenClawAutoConfig) -> list[str]:
    """Return concise user-facing lines describing detected OpenClaw settings."""
    config_display = (
        str(discovery.config_path) if discovery.config_path is not None else "not found"
    )
    plugin_state = "ready" if discovery.plugin_ready else "needs attention"
    lines = [
        f"OpenClaw CLI: {discovery.command}",
        f"OpenClaw config file: {config_display}",
        f"Gateway URL: {discovery.gateway_url}",
        f"Agent id: {discovery.agent_id}",
        f"Session key: {discovery.session_key}",
        f"Gateway mode: {discovery.gateway_mode}",
        f"NinjaClawBot plugin: {plugin_state}",
    ]
    if discovery.used_defaults:
        lines.append("Defaults used for: " + ", ".join(discovery.used_defaults))
    return lines


def is_pairing_required_error(message: str) -> bool:
    """Return True when the error text clearly indicates OpenClaw pairing is required."""
    return "pairing required" in message.lower()


def explain_openclaw_error(message: str) -> str:
    """Add user-facing recovery guidance for common OpenClaw failures."""
    normalized = message.lower()
    if is_pairing_required_error(message):
        return (
            f"{message} OpenClaw is asking for a one-time local device approval. "
            "Run `openclaw devices approve --latest`, or rerun `uv run pi5mic setup` "
            "and let pi5mic approve the newest local request for you."
        )

    if "method not found" in normalized or "unknown method" in normalized:
        return (
            f"{message} The NinjaClawBot plugin presence method is not available. "
            "Confirm the `ninjaclawbot` plugin is installed and enabled, then run "
            "`openclaw gateway restart` and rerun `uv run pi5mic setup`."
        )

    if "connection refused" in normalized or "econnrefused" in normalized:
        return (
            f"{message} The OpenClaw gateway does not appear to be running. Start it with "
            "`openclaw gateway start`, then rerun `uv run pi5mic setup` or "
            "`uv run pi5mic doctor`."
        )

    if "gateway connect failed" in normalized or "gateway closed" in normalized:
        return (
            f"{message} The OpenClaw gateway accepted the CLI but did not complete the "
            "request successfully. Check `openclaw gateway status`, then rerun "
            "`uv run pi5mic setup`."
        )

    if "agent" in normalized and "not found" in normalized:
        return (
            f"{message} The configured OpenClaw agent id does not exist. Check "
            "`openclaw config get agents.list` and rerun `uv run pi5mic setup`."
        )

    return message


def approve_latest_openclaw_pairing(command: str | Path | None) -> str:
    """Approve the newest pending OpenClaw device request for the local gateway."""
    resolved_command = resolve_openclaw_command(command)
    try:
        result = subprocess.run(
            [str(resolved_command), "devices", "approve", "--latest"],
            check=False,
            capture_output=True,
            text=True,
            timeout=20,
        )
    except subprocess.TimeoutExpired as exc:
        raise IntegrationError(
            "Timed out while approving the latest OpenClaw device request."
        ) from exc
    except OSError as exc:
        raise IntegrationError(f"Could not start the OpenClaw CLI: {exc}") from exc

    if result.returncode != 0:
        stderr = result.stderr.strip() or result.stdout.strip() or "unknown error"
        raise IntegrationError("Could not approve the latest OpenClaw device request: " + stderr)
    return result.stdout.strip() or "Approved the latest OpenClaw device request."


def probe_openclaw_voice_ready(
    *,
    command: str | Path | None,
    gateway_url: str | None,
    check_presence: bool = True,
) -> list[str]:
    """Verify that the gateway is reachable and optionally probe the presence method."""
    resolved_command = resolve_openclaw_command(command)
    health_command = [str(resolved_command), "gateway", "health", "--json"]
    health_command.extend(build_gateway_cli_args(gateway_url))

    try:
        result = subprocess.run(
            health_command,
            check=False,
            capture_output=True,
            text=True,
            timeout=20,
        )
    except subprocess.TimeoutExpired as exc:
        raise TransportError("OpenClaw gateway health check timed out.") from exc
    except OSError as exc:
        raise TransportError(f"Could not start the OpenClaw CLI: {exc}") from exc

    if result.returncode != 0:
        stderr = result.stderr.strip() or result.stdout.strip() or "unknown error"
        raise TransportError(
            explain_openclaw_error("OpenClaw gateway health check failed: " + stderr)
        )

    lines = ["OpenClaw gateway responded."]
    if not check_presence:
        return lines

    controller = OpenClawPresenceController(command=resolved_command, gateway_url=gateway_url)
    try:
        controller.set_mode("idle", reason="pi5mic.openclaw.check")
    except IntegrationError as exc:
        raise IntegrationError(explain_openclaw_error(str(exc))) from exc

    lines.append("NinjaClawBot presence method responded.")
    return lines


def _detect_gateway_url(gateway_config: dict[str, Any], *, fallback: str) -> str:
    remote = gateway_config.get("remote")
    remote_config = remote if isinstance(remote, dict) else {}
    gateway_mode = str(gateway_config.get("mode", "local")).strip().lower()

    if gateway_mode == "remote":
        remote_url = remote_config.get("url")
        if isinstance(remote_url, str) and remote_url.strip():
            return remote_url.strip()

    port = gateway_config.get("port", 18789)
    try:
        port_value = int(port)
    except (TypeError, ValueError):
        return fallback
    return f"ws://127.0.0.1:{port_value}"


def _detect_agent_id(payload: dict[str, Any]) -> str | None:
    agents = payload.get("agents")
    agents_config = agents if isinstance(agents, dict) else {}
    agent_list = agents_config.get("list")
    if not isinstance(agent_list, list):
        return None

    explicit_main = next(
        (
            item
            for item in agent_list
            if isinstance(item, dict) and str(item.get("id", "")).strip() == "main"
        ),
        None,
    )
    if explicit_main is not None:
        return "main"

    first_agent = next(
        (
            str(item.get("id", "")).strip()
            for item in agent_list
            if isinstance(item, dict) and str(item.get("id", "")).strip()
        ),
        None,
    )
    return first_agent or None


def _detect_plugin_state(payload: dict[str, Any]) -> tuple[bool, bool, bool]:
    plugins = payload.get("plugins")
    plugins_config = plugins if isinstance(plugins, dict) else {}

    allow = plugins_config.get("allow")
    allowlist = allow if isinstance(allow, list) else []
    plugin_allowlisted = "ninjaclawbot" in allowlist

    entries = plugins_config.get("entries")
    entries_config = entries if isinstance(entries, dict) else {}
    entry = entries_config.get("ninjaclawbot")
    entry_config = entry if isinstance(entry, dict) else {}
    plugin_enabled = bool(entry_config.get("enabled", False))

    load = plugins_config.get("load")
    load_config = load if isinstance(load, dict) else {}
    paths = load_config.get("paths")
    load_paths = paths if isinstance(paths, list) else []
    path_found = any("ninjaclawbot" in str(item).lower() for item in load_paths)

    installs = plugins_config.get("installs")
    install_config = installs if isinstance(installs, dict) else {}
    plugin_install_found = path_found or "ninjaclawbot" in install_config

    return plugin_enabled, plugin_allowlisted, plugin_install_found
