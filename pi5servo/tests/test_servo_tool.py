"""Regression tests for the interactive servo tool."""

from __future__ import annotations

import importlib
from contextlib import nullcontext

from click.testing import CliRunner

from pi5servo.config import ConfigManager
from pi5servo.core import ServoCalibration
from pi5servo.core.backend_errors import BackendConfigurationError

servo_tool_module = importlib.import_module("pi5servo.cli.servo_tool")


class FakeTerminal:
    """Minimal blessed.Terminal stand-in for menu tests."""

    def clear(self) -> str:
        return ""

    def bold(self, text: str) -> str:
        return text

    def cyan(self, text: str) -> str:
        return text

    def green(self, text: str) -> str:
        return text

    def red(self, text: str) -> str:
        return text

    def yellow(self, text: str) -> str:
        return text

    def cbreak(self):
        return nullcontext()

    def hidden_cursor(self):
        return nullcontext()


class FakePersistentGroup:
    """Simple persistent group stub used by the interactive tool."""

    def __init__(self, *, pins: list[int | str], backend: object) -> None:
        self.pins = pins
        self.backend = backend
        self.centered = False
        self.closed = False
        self.off_called = False
        self.move_calls: list[tuple[list[float], str, bool]] = []

    def center_all(self) -> None:
        self.centered = True

    def move_all_sync(
        self,
        angles: list[float],
        *,
        speed_mode: str,
        force: bool,
    ) -> None:
        self.move_calls.append((angles, speed_mode, force))

    def off(self) -> None:
        self.off_called = True

    def close(self) -> None:
        self.closed = True


class FakeTransientServo:
    """Simple temporary servo stub for calibration flow tests."""

    def __init__(
        self,
        _runtime,
        pin,
        _calibration,
        *,
        backend=None,
        backend_kwargs=None,
        owns_backend=None,
    ) -> None:
        self.pin = pin
        self.backend = backend
        self.backend_kwargs = backend_kwargs
        self.owns_backend = owns_backend
        self.closed = False
        self.off_called = False

    def close(self) -> None:
        self.closed = True

    def off(self) -> None:
        self.off_called = True


class FakeCalibApp:
    """Calibration app stub that avoids interactive TUI behavior."""

    def __init__(self, servo, *_args, **_kwargs) -> None:
        self.servo = servo

    def main(self) -> None:
        return None

    def end(self) -> None:
        return None


def test_servo_tool_uses_auto_backend_for_hat_calibration(monkeypatch, tmp_path) -> None:
    """Calibrating a new HAT endpoint should not reuse the persistent GPIO backend."""
    config_path = tmp_path / "servo.json"
    manager = ConfigManager(config_path)
    manager.set_calibration(12, ServoCalibration())
    manager.save()
    manager.load()

    persistent_group = FakePersistentGroup(pins=[12], backend=object())
    captured: dict[str, object] = {}

    class CapturingServo(FakeTransientServo):
        def __init__(self, *args, **kwargs) -> None:
            super().__init__(*args, **kwargs)
            captured["pin"] = self.pin
            captured["backend"] = self.backend
            captured["backend_kwargs"] = self.backend_kwargs

    monkeypatch.setattr(servo_tool_module, "HAS_BLESSED", True)
    monkeypatch.setattr(servo_tool_module, "Terminal", FakeTerminal)
    monkeypatch.setattr(servo_tool_module, "CalibApp", FakeCalibApp)
    monkeypatch.setattr(servo_tool_module, "Servo", CapturingServo)
    monkeypatch.setattr(servo_tool_module.time, "sleep", lambda _: None)
    monkeypatch.setattr(
        servo_tool_module,
        "create_group_from_config",
        lambda **_kwargs: (persistent_group, manager, None, "auto", {}),
    )

    runner = CliRunner()
    result = runner.invoke(
        servo_tool_module.servo_tool, ["--config", str(config_path)], input="3\nhat_pwm1\nq\n"
    )

    assert result.exit_code == 0, result.output
    assert captured["pin"] == "hat_pwm1"
    assert captured["backend"] == "auto"
    assert captured["backend_kwargs"] == {}
    assert "✓ Config reloaded" in result.output


def test_servo_tool_skips_persistent_group_when_config_is_empty(monkeypatch, tmp_path) -> None:
    """Empty configs should no longer default the interactive tool to GPIO12/GPIO13."""
    config_path = tmp_path / "servo.json"
    ConfigManager(config_path).save()

    monkeypatch.setattr(servo_tool_module, "HAS_BLESSED", True)
    monkeypatch.setattr(servo_tool_module, "Terminal", FakeTerminal)
    monkeypatch.setattr(
        servo_tool_module,
        "create_group_from_config",
        lambda **_kwargs: (_ for _ in ()).throw(
            AssertionError("should not build a persistent group")
        ),
    )

    runner = CliRunner()
    result = runner.invoke(
        servo_tool_module.servo_tool, ["--config", str(config_path)], input="q\n"
    )

    assert result.exit_code == 0, result.output
    assert "No configured endpoints found." in result.output


def test_servo_tool_recovers_from_endpoint_error(monkeypatch, tmp_path) -> None:
    """Calibration errors should stay inside the menu instead of crashing the whole tool."""
    config_path = tmp_path / "servo.json"
    ConfigManager(config_path).save()

    class RaisingServo(FakeTransientServo):
        def __init__(self, *args, **kwargs) -> None:
            super().__init__(*args, **kwargs)
            raise BackendConfigurationError("RP1 hardware PWM only supports native GPIO endpoints.")

    monkeypatch.setattr(servo_tool_module, "HAS_BLESSED", True)
    monkeypatch.setattr(servo_tool_module, "Terminal", FakeTerminal)
    monkeypatch.setattr(servo_tool_module, "Servo", RaisingServo)

    runner = CliRunner()
    result = runner.invoke(
        servo_tool_module.servo_tool,
        ["--config", str(config_path)],
        input="3\nhat_pwm1\n\nq\n",
    )

    assert result.exit_code == 0, result.output
    assert "✗ Error: RP1 hardware PWM only supports native GPIO endpoints." in result.output
    assert "Goodbye!" in result.output
