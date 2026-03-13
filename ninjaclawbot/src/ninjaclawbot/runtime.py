"""Runtime composition for the rebuilt NinjaClawBot integration layer."""

from __future__ import annotations

import logging
from typing import Any

from ninjaclawbot.adapters import (
    BuzzerAdapter,
    DeviceHealth,
    DisplayAdapter,
    DistanceAdapter,
    ServoAdapter,
)
from ninjaclawbot.config import NinjaClawbotConfig
from ninjaclawbot.expressions.player import ExpressionPlayer
from ninjaclawbot.locks import ExecutionLock
from ninjaclawbot.presence import normalize_presence_mode

log = logging.getLogger(__name__)


class NinjaClawbotRuntime:
    """Owns the Pi 5 driver adapters used by ninjaclawbot."""

    def __init__(self, config: NinjaClawbotConfig | None = None) -> None:
        self.config = config or NinjaClawbotConfig()
        self._execution_lock = ExecutionLock()
        self._servo = ServoAdapter(self.config)
        self._buzzer = BuzzerAdapter(self.config)
        self._display = DisplayAdapter(self.config)
        self._distance = DistanceAdapter(self.config)
        self._expressions: ExpressionPlayer | None = None
        self._closed = False

    @property
    def execution_lock(self) -> ExecutionLock:
        return self._execution_lock

    @property
    def servo(self) -> ServoAdapter:
        return self._servo

    @property
    def buzzer(self) -> BuzzerAdapter:
        return self._buzzer

    @property
    def display(self) -> DisplayAdapter:
        return self._display

    @property
    def distance(self) -> DistanceAdapter:
        return self._distance

    @property
    def expressions(self) -> ExpressionPlayer:
        if self._expressions is None:
            self._expressions = ExpressionPlayer(self.display, self.buzzer)
        return self._expressions

    @property
    def active_expression(self) -> str | None:
        if self._expressions is None:
            return None
        return self._expressions.active_expression

    def move_servos(
        self,
        targets: dict[int | str, float],
        *,
        speed_mode: str = "M",
        per_servo_speeds: dict[int | str, str] | None = None,
        easing: str = "ease_in_out_cubic",
        force: bool = True,
    ) -> bool:
        return self.servo.move(
            targets,
            speed_mode=speed_mode,
            per_servo_speeds=per_servo_speeds,
            easing=easing,
            force=force,
        )

    def play_sound(
        self,
        *,
        emotion: str | None = None,
        frequency: int | None = None,
        duration: float = 0.3,
        wait: bool = False,
    ) -> float:
        return self.buzzer.play(
            emotion=emotion,
            frequency=frequency,
            duration=duration,
            wait=wait,
        )

    def display_text(
        self,
        text: str,
        *,
        scroll: bool = False,
        duration: float = 3.0,
        language: str = "en",
        font_size: int = 32,
    ) -> None:
        self.display.show_text(
            text,
            scroll=scroll,
            duration=duration,
            language=language,
            font_size=font_size,
        )

    def read_distance(self) -> dict[str, Any]:
        return self.distance.read_data()

    def perform_expression(self, definition: dict[str, Any]) -> dict[str, Any]:
        return self.expressions.perform(definition)

    def set_idle_expression(self) -> dict[str, Any]:
        return self.set_presence_mode("idle")

    def set_presence_mode(self, mode: str) -> dict[str, Any]:
        normalized = normalize_presence_mode(mode)
        result = self.expressions.set_presence(normalized, play_sound=normalized != "idle")
        result["presence_mode"] = normalized
        return result

    def stop_expression(self) -> None:
        self.expressions.stop()

    def list_builtin_expressions(self) -> list[str]:
        return self.expressions.list_builtins()

    def health_check(self) -> dict[str, Any]:
        health: dict[str, Any] = {}
        checks: dict[str, tuple[str, callable]] = {
            "servo": ("servo", self.servo.health_check),
            "buzzer": ("buzzer", self.buzzer.health_check),
            "display": ("display", self.display.health_check),
            "distance": ("distance", self.distance.health_check),
        }
        for name, (_device, callback) in checks.items():
            try:
                result = callback()
                if isinstance(result, DeviceHealth):
                    health[name] = {"available": result.available, **result.data}
                else:  # pragma: no cover - adapter contract guard
                    health[name] = {"available": False, "error": "Invalid health result"}
            except Exception as exc:
                health[name] = {"available": False, "error": str(exc)}
        return health

    def _safe_cleanup(self, label: str, callback: Any) -> None:
        try:
            callback()
        except Exception as exc:  # pragma: no cover - defensive cleanup guard
            log.warning("Cleanup step '%s' failed: %s", label, exc)

    def _finalize_close(self, *, power_down_display: bool) -> None:
        self._safe_cleanup("expressions.stop", self.stop_expression)
        if power_down_display:
            self._safe_cleanup("display.power_down", self.display.power_down)
        else:
            self._safe_cleanup("display.close", self.display.close)
        self._safe_cleanup("buzzer.close", self.buzzer.close)
        self._safe_cleanup("servo.stop", self.servo.stop)
        if self._expressions is not None:
            self._safe_cleanup("expressions.close", self._expressions.close)
        self._safe_cleanup("servo.close", self.servo.close)
        self._safe_cleanup("distance.close", self.distance.close)

    def stop_all(self) -> None:
        # Display cleanup must run before buzzer backend shutdown because both
        # libraries ultimately share the global RPi.GPIO / rpi-lgpio state.
        self._safe_cleanup("expressions.stop", self.stop_expression)
        self._safe_cleanup("display.close", self.display.close)
        self._safe_cleanup("buzzer.close", self.buzzer.close)
        self._safe_cleanup("servo.stop", self.servo.stop)

    def shutdown_sequence(self) -> dict[str, Any]:
        if self._closed:
            return {"closed": True, "sleepy_result": None, "display_powered_down": True}

        sleepy_result: dict[str, Any] | None = None
        try:
            sleepy_result = self.perform_expression({"builtin": "sleepy", "idle_reset": False})
        except Exception as exc:  # pragma: no cover - defensive cleanup guard
            log.warning("Sleepy shutdown expression failed: %s", exc)

        self._closed = True
        self._finalize_close(power_down_display=True)
        return {
            "closed": True,
            "sleepy_result": sleepy_result,
            "display_powered_down": True,
        }

    def close(self) -> None:
        if self._closed:
            return
        self._closed = True
        self._finalize_close(power_down_display=False)
