from __future__ import annotations

from ninjaclawbot.adapters import DeviceHealth
from ninjaclawbot.config import NinjaClawbotConfig
from ninjaclawbot.runtime import NinjaClawbotRuntime


class FakeServoAdapter:
    def __init__(self) -> None:
        self.calls = []

    def move(
        self,
        targets,
        *,
        speed_mode="M",
        per_servo_speeds=None,
        easing="ease_in_out_cubic",
        force=True,
    ):
        self.calls.append((targets, speed_mode, per_servo_speeds, easing, force))
        return True

    def health_check(self) -> DeviceHealth:
        return DeviceHealth(True, {"configured_endpoints": ["gpio12", "hat_pwm1"]})

    def stop(self) -> None:
        self.calls.append(("stop",))

    def close(self) -> None:
        self.calls.append(("close",))


class FakeDeviceAdapter:
    def __init__(self, name: str) -> None:
        self.name = name
        self.closed = False

    def health_check(self) -> DeviceHealth:
        return DeviceHealth(True, {"device": self.name})

    def read_data(self) -> dict[str, int]:
        return {"distance_mm": 123}

    def play(self, **kwargs) -> None:
        self.last_play = kwargs

    def show_text(self, *args, **kwargs) -> None:
        self.last_text = (args, kwargs)

    def close(self) -> None:
        self.closed = True


class FakeExpressionPlayer:
    def __init__(self) -> None:
        self.calls: list[tuple[str, object]] = []

    def perform(self, definition):
        self.calls.append(("perform", definition))
        return {"name": definition.get("name"), "builtin": definition.get("builtin")}

    def set_idle(self) -> None:
        self.calls.append(("set_idle", None))

    def stop(self) -> None:
        self.calls.append(("stop", None))

    def close(self) -> None:
        self.calls.append(("close", None))

    def list_builtins(self) -> list[str]:
        return ["idle", "happy"]


def test_runtime_delegates_servo_moves_and_health_checks() -> None:
    runtime = NinjaClawbotRuntime(NinjaClawbotConfig())
    runtime._servo = FakeServoAdapter()
    runtime._buzzer = FakeDeviceAdapter("buzzer")
    runtime._display = FakeDeviceAdapter("display")
    runtime._distance = FakeDeviceAdapter("distance")

    assert runtime.move_servos({"gpio12": 15.0}, per_servo_speeds={"gpio12": "S"}) is True
    health = runtime.health_check()

    assert health["servo"]["configured_endpoints"] == ["gpio12", "hat_pwm1"]
    assert runtime._servo.calls[0][2] == {"gpio12": "S"}
    assert runtime.read_distance()["distance_mm"] == 123


def test_runtime_health_check_catches_adapter_errors() -> None:
    runtime = NinjaClawbotRuntime(NinjaClawbotConfig())
    runtime._servo = FakeServoAdapter()

    class BrokenAdapter:
        def health_check(self):
            raise RuntimeError("boom")

        def close(self):
            return None

    runtime._buzzer = BrokenAdapter()
    runtime._display = BrokenAdapter()
    runtime._distance = BrokenAdapter()

    health = runtime.health_check()

    assert health["buzzer"]["available"] is False
    assert "boom" in health["buzzer"]["error"]


def test_runtime_stop_all_closes_display_before_buzzer() -> None:
    runtime = NinjaClawbotRuntime(NinjaClawbotConfig())
    runtime._servo = FakeServoAdapter()
    call_order: list[str] = []

    class OrderedDeviceAdapter(FakeDeviceAdapter):
        def close(self) -> None:
            call_order.append(f"{self.name}.close")
            super().close()

    runtime._display = OrderedDeviceAdapter("display")
    runtime._buzzer = OrderedDeviceAdapter("buzzer")
    runtime._distance = OrderedDeviceAdapter("distance")

    runtime.stop_all()

    assert call_order == ["display.close", "buzzer.close"]
    assert runtime._servo.calls[-1] == ("stop",)


def test_runtime_close_swallows_cleanup_errors() -> None:
    runtime = NinjaClawbotRuntime(NinjaClawbotConfig())
    runtime._servo = FakeServoAdapter()

    class BrokenDevice:
        def __init__(self) -> None:
            self.closed = False

        def close(self) -> None:
            self.closed = True
            raise RuntimeError("cleanup failed")

    runtime._display = BrokenDevice()
    runtime._buzzer = BrokenDevice()
    runtime._distance = BrokenDevice()

    runtime.close()

    assert runtime._display.closed is True
    assert runtime._buzzer.closed is True
    assert runtime._distance.closed is True
    assert runtime._servo.calls[-2:] == [("stop",), ("close",)]


def test_runtime_expression_methods_delegate_to_player() -> None:
    runtime = NinjaClawbotRuntime(NinjaClawbotConfig())
    runtime._servo = FakeServoAdapter()
    runtime._buzzer = FakeDeviceAdapter("buzzer")
    runtime._display = FakeDeviceAdapter("display")
    runtime._distance = FakeDeviceAdapter("distance")
    runtime._expressions = FakeExpressionPlayer()

    result = runtime.perform_expression({"name": "hello", "builtin": "happy"})
    runtime.set_idle_expression()
    runtime.stop_expression()

    assert result == {"name": "hello", "builtin": "happy"}
    assert runtime.list_builtin_expressions() == ["idle", "happy"]
    assert runtime._expressions.calls == [
        ("perform", {"name": "hello", "builtin": "happy"}),
        ("set_idle", None),
        ("stop", None),
    ]
