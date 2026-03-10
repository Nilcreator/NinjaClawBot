"""Shared CLI helpers for backend-aware standalone servo commands."""

from __future__ import annotations

import sys
from typing import Any, Callable

import click

from ..config import ConfigManager
from ..core import Servo, ServoGroup

BACKEND_CHOICES = (
    "auto",
    "hardware_pwm",
    "rp1_hardware_pwm",
    "pwm_pio",
    "pca9685",
    "pigpio",
)
LEGACY_BACKENDS = {"pigpio", "legacy"}


def _parse_int(value: str | int) -> int:
    """Parse a decimal or ``0x``-prefixed integer value."""
    if isinstance(value, int):
        return value
    return int(value, 0)


def parse_pin_list(pins: str) -> list[int]:
    """Parse a comma-separated pin list."""
    try:
        return [_parse_int(pin.strip()) for pin in pins.split(",") if pin.strip()]
    except ValueError as exc:
        raise click.BadParameter(f"Invalid pins format: {exc}") from exc


def parse_mapping_option(value: str | None, option_name: str) -> dict[int, int] | None:
    """Parse ``PIN:CHANNEL`` mappings from a comma-separated option string."""
    if not value:
        return None

    mapping: dict[int, int] = {}
    for item in value.split(","):
        candidate = item.strip()
        if not candidate:
            continue
        try:
            left, right = candidate.split(":", 1)
            mapping[_parse_int(left.strip())] = _parse_int(right.strip())
        except (TypeError, ValueError) as exc:
            raise click.BadParameter(
                f"Invalid {option_name} entry '{candidate}'. Use the form LEFT:RIGHT."
            ) from exc
    return mapping or None


def normalize_mapping(mapping: dict[Any, Any] | None) -> dict[int, int]:
    """Normalize mapping keys and values to integers."""
    if not mapping:
        return {}
    return {_parse_int(key): _parse_int(value) for key, value in mapping.items()}


def backend_options(command: Callable[..., Any]) -> Callable[..., Any]:
    """Apply common backend-selection options to a Click command."""
    options = [
        click.option(
            "--channel-map",
            default=None,
            help="Map servo identifiers to PCA9685 channels, for example '12:0,13:1'.",
        ),
        click.option(
            "--pin-channel-map",
            default=None,
            help="Override the Pi 5 header PWM pin mapping, for example '12:0,13:1'.",
        ),
        click.option(
            "--address",
            default=None,
            help="PCA9685 I2C address. Decimal or hex values such as '0x40' are accepted.",
        ),
        click.option(
            "--frequency-hz",
            type=int,
            default=None,
            help="Servo pulse frequency in Hz. The default is 50.",
        ),
        click.option(
            "--chip",
            type=int,
            default=None,
            help="RP1 PWM chip index for the hardware PWM backend.",
        ),
        click.option(
            "--backend",
            "backend_name",
            type=click.Choice(BACKEND_CHOICES, case_sensitive=False),
            default=None,
            help="Pulse backend. Defaults to the value stored in servo.json or 'auto'.",
        ),
    ]

    for option in reversed(options):
        command = option(command)
    return command


def create_pigpio_runtime() -> Any:
    """Create the legacy pigpio runtime when explicitly requested."""
    try:
        import pigpio

        pi = pigpio.pi()
    except ImportError as exc:
        click.echo("Error: pigpio is not installed for the requested backend.", err=True)
        raise click.Abort() from exc

    if not pi.connected:
        click.echo("Error: Could not connect to the pigpio daemon.", err=True)
        click.echo("Run 'sudo pigpiod' to start the daemon.", err=True)
        raise click.Abort()
    return pi


def close_runtime_handle(handle: Any | None) -> None:
    """Stop a legacy pigpio runtime if one was created."""
    if handle is not None and hasattr(handle, "stop"):
        handle.stop()


def resolve_backend_settings(
    manager: ConfigManager,
    *,
    backend_name: str | None = None,
    chip: int | None = None,
    frequency_hz: int | None = None,
    address: str | None = None,
    pin_channel_map: str | None = None,
    channel_map: str | None = None,
) -> tuple[str, dict[str, Any]]:
    """Merge backend settings from config metadata with CLI overrides."""
    stored = manager.get_backend_config()
    resolved_name = str(backend_name or stored.get("name") or "auto").lower()
    kwargs = dict(stored.get("kwargs", {}))

    if "pin_channel_map" in kwargs:
        kwargs["pin_channel_map"] = normalize_mapping(kwargs["pin_channel_map"])
    if "channel_map" in kwargs:
        kwargs["channel_map"] = normalize_mapping(kwargs["channel_map"])

    if chip is not None:
        kwargs["chip"] = int(chip)
    if frequency_hz is not None:
        kwargs["frequency_hz"] = int(frequency_hz)
    if address is not None:
        kwargs["address"] = _parse_int(address)

    parsed_pin_channel_map = parse_mapping_option(pin_channel_map, "pin-channel-map")
    if parsed_pin_channel_map is not None:
        kwargs["pin_channel_map"] = parsed_pin_channel_map

    parsed_channel_map = parse_mapping_option(channel_map, "channel-map")
    if parsed_channel_map is not None:
        kwargs["channel_map"] = parsed_channel_map

    return resolved_name, kwargs


def create_servo_from_config(
    *,
    pin: int,
    config_path: str,
    backend_name: str | None = None,
    chip: int | None = None,
    frequency_hz: int | None = None,
    address: str | None = None,
    pin_channel_map: str | None = None,
    channel_map: str | None = None,
) -> tuple[Servo, ConfigManager, Any | None, str, dict[str, Any]]:
    """Create a single Servo using config-backed calibration and backend settings."""
    manager = ConfigManager(config_path)
    manager.load()

    resolved_backend, backend_kwargs = resolve_backend_settings(
        manager,
        backend_name=backend_name,
        chip=chip,
        frequency_hz=frequency_hz,
        address=address,
        pin_channel_map=pin_channel_map,
        channel_map=channel_map,
    )

    runtime = create_pigpio_runtime() if resolved_backend in LEGACY_BACKENDS else None
    servo = Servo(
        runtime,
        pin,
        manager.get_calibration(pin),
        backend=None if resolved_backend in LEGACY_BACKENDS else resolved_backend,
        backend_kwargs=backend_kwargs,
    )
    return servo, manager, runtime, resolved_backend, backend_kwargs


def create_group_from_config(
    *,
    pins: list[int],
    config_path: str,
    backend_name: str | None = None,
    chip: int | None = None,
    frequency_hz: int | None = None,
    address: str | None = None,
    pin_channel_map: str | None = None,
    channel_map: str | None = None,
) -> tuple[ServoGroup, ConfigManager, Any | None, str, dict[str, Any]]:
    """Create a ServoGroup using config-backed calibration and backend settings."""
    manager = ConfigManager(config_path)
    manager.load()

    resolved_backend, backend_kwargs = resolve_backend_settings(
        manager,
        backend_name=backend_name,
        chip=chip,
        frequency_hz=frequency_hz,
        address=address,
        pin_channel_map=pin_channel_map,
        channel_map=channel_map,
    )

    runtime = create_pigpio_runtime() if resolved_backend in LEGACY_BACKENDS else None
    calibrations = {pin: manager.get_calibration(pin) for pin in pins}
    group = ServoGroup(
        runtime,
        pins=pins,
        calibrations=calibrations,
        backend=None if resolved_backend in LEGACY_BACKENDS else resolved_backend,
        backend_kwargs=backend_kwargs,
    )
    return group, manager, runtime, resolved_backend, backend_kwargs


def fail_with_error(message: str) -> None:
    """Print a CLI error message and abort."""
    click.echo(message, err=True)
    sys.exit(1)
