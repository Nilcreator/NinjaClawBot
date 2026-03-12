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

    def set_idle_expression(self) -> None:
        self.expressions.set_idle()

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

    def stop_all(self) -> None:
        # Display cleanup must run before buzzer backend shutdown because both
        # libraries ultimately share the global RPi.GPIO / rpi-lgpio state.
        self._safe_cleanup("expressions.stop", self.stop_expression)
        self._safe_cleanup("display.close", self.display.close)
        self._safe_cleanup("buzzer.close", self.buzzer.close)
        self._safe_cleanup("servo.stop", self.servo.stop)

    def close(self) -> None:
        if self._closed:
            return
        self._closed = True
        self.stop_all()
        if self._expressions is not None:
            self._safe_cleanup("expressions.close", self._expressions.close)
        self._safe_cleanup("servo.close", self.servo.close)
        self._safe_cleanup("distance.close", self.distance.close)
