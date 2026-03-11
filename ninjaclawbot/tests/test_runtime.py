from __future__ import annotations

from types import SimpleNamespace

from ninjaclawbot.config import NinjaClawbotConfig
from ninjaclawbot.runtime import NinjaClawbotRuntime


class FakeServoGroup:
    def __init__(self, _pi, pins, _calibrations, backend, backend_kwargs):
        self.pins = list(pins)
        self.backend = backend
        self.backend_kwargs = backend_kwargs
        self.moved = []

    def move_all_sync(self, targets, speed_mode="M", easing="ease_in_out_cubic"):
        self.moved.append((targets, speed_mode, easing))
        return True

    def off(self):
        return None

    def close(self):
        return None


class FakeServoConfigManager:
    def __init__(self, _path):
        self._loaded = False

    def load(self):
        self._loaded = True

    def get_known_endpoints(self):
        return ["gpio12"]

    def get_backend_config(self):
        return {"name": "hardware_pwm", "kwargs": {}}

    def get_all_endpoint_calibrations(self):
        return {}


def test_runtime_composes_servo_group_with_known_and_requested_endpoints() -> None:
    runtime = NinjaClawbotRuntime(NinjaClawbotConfig())

    def fake_import(module_name: str):
        if module_name == "pi5servo":
            return SimpleNamespace(ServoGroup=FakeServoGroup)
        if module_name == "pi5servo.config.config_manager":
            return SimpleNamespace(ConfigManager=FakeServoConfigManager)
        raise AssertionError(f"Unexpected import: {module_name}")

    runtime._import_module = fake_import  # type: ignore[method-assign]

    group = runtime.get_servo_group(["hat_pwm1"])

    assert group.pins == ["gpio12", "hat_pwm1"]
    assert runtime.move_servos({"hat_pwm1": 15.0}) is True
