"""Tests for OpenClaw auto-discovery helpers."""

from __future__ import annotations

import importlib
import json

openclaw_setup_module = importlib.import_module("pi5mic.integration.openclaw_setup")


def test_discover_openclaw_auto_config_reads_local_config(monkeypatch, tmp_path) -> None:
    command_path = tmp_path / "openclaw"
    command_path.write_text("", encoding="utf-8")
    config_path = tmp_path / "openclaw.json"
    config_path.write_text(
        json.dumps(
            {
                "gateway": {
                    "mode": "local",
                    "bind": "loopback",
                    "port": 18789,
                },
                "agents": {
                    "list": [
                        {"id": "main"},
                    ]
                },
                "plugins": {
                    "allow": ["ninjaclawbot"],
                    "entries": {"ninjaclawbot": {"enabled": True}},
                    "load": {"paths": ["/tmp/ninjaclawbot-plugin"]},
                },
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(
        openclaw_setup_module,
        "DEFAULT_OPENCLAW_CONFIG_PATH",
        config_path,
    )
    monkeypatch.setattr(
        openclaw_setup_module,
        "resolve_openclaw_command",
        lambda command=None: command_path,
    )

    discovery = openclaw_setup_module.discover_openclaw_auto_config(command=None)

    assert discovery.command == command_path
    assert discovery.config_path == config_path
    assert discovery.gateway_url == "ws://127.0.0.1:18789"
    assert discovery.agent_id == "main"
    assert discovery.session_key == "voice:local-mic"
    assert discovery.plugin_ready is True
    assert discovery.used_defaults == ("session_key",)
