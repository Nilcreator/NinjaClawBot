"""Servo pulse backend abstractions for Raspberry Pi 5."""

from __future__ import annotations

from typing import Any, Protocol, runtime_checkable

from .backend_errors import (
    BackendConfigurationError,
    BackendError,
    BackendUnavailableError,
)
from .backends.hardware_pwm import HardwarePWMServoBackend
from .backends.pca9685 import PCA9685ServoBackend
from .backends.pwm_pio import PwmPioServoBackend


@runtime_checkable
class ServoPulseBackend(Protocol):
    """Interface for long-lived servo pulse generators."""

    def claim(self, identifier: int) -> None:
        """Claim a servo output once for long-lived use."""

    def set_pulse_us(self, identifier: int, pulse_width_us: int) -> None:
        """Set the output pulse width in microseconds."""

    def get_pulse_us(self, identifier: int) -> int:
        """Return the last known pulse width in microseconds."""

    def off(self, identifier: int) -> None:
        """Turn the servo output off for one identifier."""

    def release(self, identifier: int) -> None:
        """Release one claimed output."""

    def close(self) -> None:
        """Release all claimed outputs."""


class PigpioServoBackend:
    """Thin compatibility wrapper around a pigpio-like servo API."""

    def __init__(self, pi: Any, *, owns_pi: bool = False) -> None:
        self._pi = pi
        self._owns_pi = owns_pi
        self._claimed: set[int] = set()
        self._closed = False

    def claim(self, identifier: int) -> None:
        self._claimed.add(identifier)

    def set_pulse_us(self, identifier: int, pulse_width_us: int) -> None:
        self.claim(identifier)
        self._pi.set_servo_pulsewidth(identifier, pulse_width_us)

    def get_pulse_us(self, identifier: int) -> int:
        try:
            return int(self._pi.get_servo_pulsewidth(identifier))
        except Exception:
            return 0

    def off(self, identifier: int) -> None:
        self._pi.set_servo_pulsewidth(identifier, 0)

    def release(self, identifier: int) -> None:
        if identifier in self._claimed:
            self.off(identifier)
            self._claimed.discard(identifier)

    def close(self) -> None:
        if self._closed:
            return
        for identifier in list(self._claimed):
            self.release(identifier)
        if self._owns_pi and hasattr(self._pi, "stop"):
            self._pi.stop()
        self._closed = True


def is_servo_backend(candidate: Any | None) -> bool:
    """Return True when a value looks like a servo pulse backend.

    Pigpio-like objects expose ``set_servo_pulsewidth`` / ``get_servo_pulsewidth`` and should
    stay on the legacy compatibility path even if they are mocks.
    """
    if candidate is None or isinstance(candidate, str):
        return False

    if callable(getattr(candidate, "set_servo_pulsewidth", None)):
        return False

    required = (
        "claim",
        "set_pulse_us",
        "get_pulse_us",
        "off",
        "release",
        "close",
    )
    return all(callable(getattr(candidate, name, None)) for name in required)


def create_servo_backend(
    backend: str | ServoPulseBackend | None = None,
    *,
    pi: Any | None = None,
    pins: list[int] | None = None,
    **kwargs: Any,
) -> ServoPulseBackend:
    """Create a servo backend from a name, a backend object, or a pigpio-like pi."""
    if backend is not None and not isinstance(backend, str):
        return backend

    backend_name = (backend or ("pigpio" if pi is not None else "auto")).lower()

    if backend_name in {"pigpio", "legacy"}:
        if pi is None:
            raise BackendConfigurationError("pigpio backend requires a `pi` instance.")
        return PigpioServoBackend(pi, owns_pi=kwargs.pop("owns_pi", False))

    if backend_name in {"auto", "hardware_pwm", "rp1_hardware_pwm"}:
        return HardwarePWMServoBackend(pins=pins, **kwargs)

    if backend_name == "pwm_pio":
        return PwmPioServoBackend(pins=pins, **kwargs)

    if backend_name == "pca9685":
        return PCA9685ServoBackend(**kwargs)

    raise BackendConfigurationError(f"Unknown servo backend: {backend_name}")


__all__ = [
    "BackendConfigurationError",
    "BackendError",
    "BackendUnavailableError",
    "PigpioServoBackend",
    "ServoPulseBackend",
    "create_servo_backend",
    "is_servo_backend",
]
