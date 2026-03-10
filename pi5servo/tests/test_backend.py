"""Unit tests for servo pulse backends."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from pi5servo.core.backend import (
    BackendConfigurationError,
    PigpioServoBackend,
    create_servo_backend,
)
from pi5servo.core.backends.hardware_pwm import HardwarePWMServoBackend
from pi5servo.core.backends.pca9685 import PCA9685ServoBackend


class FakeHardwarePWM:
    """Simple fake for rpi_hardware_pwm.HardwarePWM."""

    def __init__(self, pwm_channel: int, hz: int, chip: int) -> None:
        self.pwm_channel = pwm_channel
        self.hz = hz
        self.chip = chip
        self.started_with: list[float] = []
        self.duty_history: list[float] = []
        self.frequency_history: list[int] = []
        self.stop_calls = 0

    def start(self, duty_cycle: float) -> None:
        self.started_with.append(duty_cycle)

    def change_duty_cycle(self, duty_cycle: float) -> None:
        self.duty_history.append(duty_cycle)

    def change_frequency(self, hz: int) -> None:
        self.frequency_history.append(hz)

    def stop(self) -> None:
        self.stop_calls += 1


class FakeChannel:
    """Simple PWM channel fake."""

    def __init__(self) -> None:
        self.duty_cycle = 0


class FakePCA9685:
    """Simple fake for adafruit_pca9685.PCA9685."""

    def __init__(self, i2c_bus, **kwargs) -> None:
        self.i2c_bus = i2c_bus
        self.kwargs = kwargs
        self.frequency = 0
        self.channels = [FakeChannel() for _ in range(16)]
        self.deinit_called = False

    def deinit(self) -> None:
        self.deinit_called = True


def test_pigpio_backend_pass_through(mock_pigpio) -> None:
    """Pigpio backend should proxy set/get/off calls."""
    backend = PigpioServoBackend(mock_pigpio)

    backend.claim(20)
    backend.set_pulse_us(20, 1500)
    assert backend.get_pulse_us(20) == 1500
    backend.off(20)

    mock_pigpio.set_servo_pulsewidth.assert_any_call(20, 1500)
    mock_pigpio.set_servo_pulsewidth.assert_any_call(20, 0)


def test_hardware_pwm_backend_rejects_unsupported_pin() -> None:
    """Only Pi 5 PWM-capable header pins should be accepted."""
    backend = HardwarePWMServoBackend(pwm_cls=FakeHardwarePWM)

    with pytest.raises(BackendConfigurationError, match="GPIO20"):
        backend.claim(20)


def test_hardware_pwm_backend_sets_pulse_and_off() -> None:
    """Hardware PWM backend should keep long-lived PWM objects per pin."""
    backend = HardwarePWMServoBackend(pwm_cls=FakeHardwarePWM)

    backend.set_pulse_us(12, 1500)
    pwm = backend._pwms[12]
    assert pwm.pwm_channel == 0
    assert pytest.approx(pwm.started_with[-1], rel=0.01) == 7.5
    assert backend.get_pulse_us(12) == 1500

    backend.set_pulse_us(12, 2000)
    assert pytest.approx(pwm.duty_history[-1], rel=0.01) == 10.0
    assert pwm.frequency_history[-1] == 50

    backend.off(12)
    assert pwm.stop_calls == 1
    assert backend.get_pulse_us(12) == 0


def test_pca9685_backend_sets_frequency_and_duty() -> None:
    """PCA9685 backend should convert pulse widths to duty-cycle values."""
    backend = PCA9685ServoBackend(
        pca9685_cls=FakePCA9685,
        i2c_bus=object(),
        channel_map={20: 3},
    )

    assert backend._controller.frequency == 50

    backend.set_pulse_us(20, 1500)
    assert backend.get_pulse_us(20) == 1500
    assert backend._controller.channels[3].duty_cycle > 0

    backend.off(20)
    assert backend._controller.channels[3].duty_cycle == 0

    backend.close()
    assert backend._controller.deinit_called is True


def test_create_servo_backend_wraps_pigpio(mock_pigpio) -> None:
    """Passing a pigpio-like `pi` should create the legacy wrapper backend."""
    backend = create_servo_backend(pi=mock_pigpio)

    backend.set_pulse_us(20, 1700)
    mock_pigpio.set_servo_pulsewidth.assert_called_with(20, 1700)


def test_create_servo_backend_accepts_backend_object() -> None:
    """A prebuilt backend object should pass straight through."""
    backend = MagicMock()

    assert create_servo_backend(backend) is backend
