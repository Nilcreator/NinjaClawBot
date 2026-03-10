"""Unit tests for backend-aware CLI commands."""

from __future__ import annotations

import importlib
from unittest.mock import MagicMock

from click.testing import CliRunner

from pi5servo.cli._common import resolve_backend_settings
from pi5servo.config import ConfigManager

cmd_module = importlib.import_module("pi5servo.cli.cmd")
move_module = importlib.import_module("pi5servo.cli.move")


class FakeServo:
    """Simple fake servo for CLI tests."""

    def __init__(self) -> None:
        self.angles: list[float] = []
        self.closed = False

    def set_angle(self, angle: float) -> None:
        self.angles.append(angle)

    def close(self) -> None:
        self.closed = True


class FakeGroup:
    """Simple fake servo group for CLI tests."""

    def __init__(self, success: bool = True) -> None:
        self.success = success
        self.commands: list[str] = []
        self.closed = False

    def execute_command(self, command: str) -> bool:
        self.commands.append(command)
        return self.success

    def close(self) -> None:
        self.closed = True


def test_resolve_backend_settings_normalizes_config_mappings(tmp_path) -> None:
    """Backend settings should normalize JSON-loaded mapping keys."""
    config_path = tmp_path / "servo.json"
    manager = ConfigManager(config_path)
    manager.set_backend_config(
        "pca9685",
        {
            "address": 64,
            "channel_map": {"12": 0, "13": 1},
        },
    )
    manager.save()
    manager.load()

    backend_name, kwargs = resolve_backend_settings(manager)

    assert backend_name == "pca9685"
    assert kwargs["channel_map"] == {12: 0, 13: 1}


def test_move_command_uses_backend_aware_creation(monkeypatch) -> None:
    """`move` should operate through the shared backend-aware helper."""
    runner = CliRunner()
    servo = FakeServo()
    manager = MagicMock()

    def fake_create_servo_from_config(**kwargs):
        del kwargs
        return servo, manager, None, "hardware_pwm", {"chip": 0}

    monkeypatch.setattr(move_module, "create_servo_from_config", fake_create_servo_from_config)
    monkeypatch.setattr(move_module.time, "sleep", lambda _: None)

    result = runner.invoke(move_module.move, ["12", "center", "--config", "servo.json"])

    assert result.exit_code == 0, result.output
    assert servo.angles == [0.0]
    assert servo.closed is True


def test_cmd_command_executes_and_closes_group(monkeypatch) -> None:
    """`cmd` should execute through ServoGroup and release resources on exit."""
    runner = CliRunner()
    group = FakeGroup(success=True)
    manager = MagicMock()
    manager.get_all_calibrations.return_value = {}

    def fake_create_group_from_config(**kwargs):
        del kwargs
        return group, manager, None, "hardware_pwm", {"chip": 0}

    monkeypatch.setattr(cmd_module, "create_group_from_config", fake_create_group_from_config)

    result = runner.invoke(cmd_module.cmd, ["12:45", "--pins", "12,13"])

    assert result.exit_code == 0, result.output
    assert group.commands == ["12:45"]
    assert group.closed is True
