"""RP1 hardware PWM backend for header-connected servos on Raspberry Pi 5."""

from __future__ import annotations

from importlib import import_module
from typing import Any

from ..backend_errors import BackendConfigurationError, BackendUnavailableError

DEFAULT_SERVO_FREQUENCY_HZ = 50
DEFAULT_PWM_CHIP = 0
PI5_HEADER_PWM_CHANNELS = {
    12: 0,
    13: 1,
    18: 2,
    19: 3,
}


class HardwarePWMServoBackend:
    """Long-lived servo backend using `rpi-hardware-pwm`."""

    def __init__(
        self,
        *,
        pins: list[int] | None = None,
        pin_channel_map: dict[int, int] | None = None,
        frequency_hz: int = DEFAULT_SERVO_FREQUENCY_HZ,
        chip: int = DEFAULT_PWM_CHIP,
        pwm_cls: type[Any] | None = None,
    ) -> None:
        if pwm_cls is None:
            try:
                pwm_module = import_module("rpi_hardware_pwm")
                pwm_cls = pwm_module.HardwarePWM
            except ImportError as exc:
                raise BackendUnavailableError(
                    "rpi-hardware-pwm is not installed. Install the `pi` extra on Raspberry Pi 5."
                ) from exc

        self._pwm_cls = pwm_cls
        self._frequency_hz = int(frequency_hz)
        self._chip = int(chip)
        self._pin_channel_map = dict(pin_channel_map or PI5_HEADER_PWM_CHANNELS)
        self._pwms: dict[int, Any] = {}
        self._active: set[int] = set()
        self._current_pulses: dict[int, int] = {}

        if pins:
            for pin in pins:
                self._validate_pin(pin)

    def _validate_pin(self, pin: int) -> int:
        try:
            return self._pin_channel_map[pin]
        except KeyError as exc:
            supported = ", ".join(str(candidate) for candidate in sorted(self._pin_channel_map))
            raise BackendConfigurationError(
                f"GPIO{pin} is not supported by the RP1 hardware PWM backend. "
                f"Supported header pins: {supported}."
            ) from exc

    def _period_us(self) -> float:
        return 1_000_000.0 / float(self._frequency_hz)

    def _pulse_to_duty_cycle(self, pulse_width_us: int) -> float:
        pulse_width_us = max(0, pulse_width_us)
        duty = (pulse_width_us / self._period_us()) * 100.0
        return max(0.0, min(100.0, duty))

    def claim(self, identifier: int) -> None:
        if identifier in self._pwms:
            return
        pwm_channel = self._validate_pin(identifier)
        self._pwms[identifier] = self._pwm_cls(
            pwm_channel=pwm_channel,
            hz=self._frequency_hz,
            chip=self._chip,
        )
        self._current_pulses.setdefault(identifier, 0)

    def set_pulse_us(self, identifier: int, pulse_width_us: int) -> None:
        if pulse_width_us <= 0:
            self.off(identifier)
            return

        self.claim(identifier)
        pwm = self._pwms[identifier]
        duty_cycle = self._pulse_to_duty_cycle(int(pulse_width_us))

        if identifier in self._active:
            pwm.change_frequency(self._frequency_hz)
            pwm.change_duty_cycle(duty_cycle)
        else:
            pwm.start(duty_cycle)
            self._active.add(identifier)

        self._current_pulses[identifier] = int(pulse_width_us)

    def get_pulse_us(self, identifier: int) -> int:
        return int(self._current_pulses.get(identifier, 0))

    def off(self, identifier: int) -> None:
        self.claim(identifier)
        pwm = self._pwms[identifier]
        if identifier in self._active:
            pwm.stop()
            self._active.discard(identifier)
        self._current_pulses[identifier] = 0

    def release(self, identifier: int) -> None:
        if identifier not in self._pwms:
            return
        self.off(identifier)
        self._pwms.pop(identifier, None)
        self._current_pulses.pop(identifier, None)

    def close(self) -> None:
        for identifier in list(self._pwms):
            self.release(identifier)
