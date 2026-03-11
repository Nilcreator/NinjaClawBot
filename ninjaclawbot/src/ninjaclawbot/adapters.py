"""Thin adapters around the standalone Pi 5 driver libraries."""

from __future__ import annotations

import importlib
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from pi5servo.core.endpoint import parse_servo_endpoint

from ninjaclawbot.config import NinjaClawbotConfig
from ninjaclawbot.errors import ExecutionError, UnavailableCapabilityError


def _import_or_raise(module_name: str):
    try:
        return importlib.import_module(module_name)
    except ImportError as exc:  # pragma: no cover - depends on environment packaging
        raise UnavailableCapabilityError(
            f"Required package '{module_name}' is not installed in the NinjaClawBot environment."
        ) from exc


def _normalize_endpoint(endpoint: int | str) -> str:
    return parse_servo_endpoint(endpoint).identifier


def _normalize_targets(targets: dict[int | str, float]) -> dict[str, float]:
    return {_normalize_endpoint(endpoint): float(angle) for endpoint, angle in targets.items()}


def _normalize_speed_map(speed_map: dict[int | str, str] | None) -> dict[str, str]:
    if not speed_map:
        return {}
    normalized: dict[str, str] = {}
    for endpoint, speed in speed_map.items():
        normalized[_normalize_endpoint(endpoint)] = str(speed).upper()
    return normalized


@dataclass(slots=True)
class DeviceHealth:
    """Structured health result from a driver adapter."""

    available: bool
    data: dict[str, Any]


class ServoAdapter:
    """Adapter for pi5servo group creation and motion execution."""

    def __init__(self, config: NinjaClawbotConfig) -> None:
        self.config = config
        self._group: Any | None = None
        self._runtime_handle: Any | None = None
        self._group_endpoints: list[str] = []
        self._backend_name = "auto"
        self._backend_kwargs: dict[str, Any] = {}

    def _manager(self) -> Any:
        config_module = _import_or_raise("pi5servo.config.config_manager")
        manager = config_module.ConfigManager(str(self.config.servo_config_path))
        manager.load()
        return manager

    def configured_endpoints(self) -> list[str]:
        manager = self._manager()
        return [_normalize_endpoint(endpoint) for endpoint in manager.get_known_endpoints()]

    def _build_group(self, required_endpoints: list[str] | None = None) -> Any:
        required = [_normalize_endpoint(endpoint) for endpoint in (required_endpoints or [])]
        if self._group is not None and all(
            endpoint in self._group_endpoints for endpoint in required
        ):
            return self._group

        manager = self._manager()
        configured = [_normalize_endpoint(endpoint) for endpoint in manager.get_known_endpoints()]
        selected = list(dict.fromkeys(configured + required))
        if not selected:
            raise UnavailableCapabilityError(
                "No servo endpoints are configured. Run `uv run pi5servo calib <endpoint>` "
                "or `uv run pi5servo servo-tool` from the project root first."
            )

        common = _import_or_raise("pi5servo.cli._common")
        self.close()
        try:
            group, _manager, runtime_handle, backend_name, backend_kwargs = (
                common.create_group_from_config(
                    pins=selected,
                    config_path=str(self.config.servo_config_path),
                )
            )
        except Exception as exc:
            raise UnavailableCapabilityError(str(exc)) from exc
        self._group = group
        self._runtime_handle = runtime_handle
        self._backend_name = backend_name
        self._backend_kwargs = dict(backend_kwargs)
        self._group_endpoints = [_normalize_endpoint(endpoint) for endpoint in group.pins]
        return group

    def move(
        self,
        targets: dict[int | str, float],
        *,
        speed_mode: str = "M",
        per_servo_speeds: dict[int | str, str] | None = None,
        easing: str = "ease_in_out_cubic",
        force: bool = True,
    ) -> bool:
        normalized_targets = _normalize_targets(targets)
        normalized_speeds = _normalize_speed_map(per_servo_speeds)
        group = self._build_group(list(normalized_targets))

        ordered_targets: list[float | None] = []
        speed_modes: list[str] = []
        for endpoint in self._group_endpoints:
            ordered_targets.append(normalized_targets.get(endpoint))
            speed_modes.append(normalized_speeds.get(endpoint, str(speed_mode).upper()))

        return bool(
            group.move_all_sync(
                ordered_targets,
                speed_mode=speed_modes,
                easing=easing,
                force=force,
            )
        )

    def current_angles(self) -> dict[str, float]:
        group = self._build_group([])
        return dict(zip(self._group_endpoints, group.get_all_angles(), strict=False))

    def center_all(self, *, speed_mode: str = "M") -> bool:
        group = self._build_group([])
        targets = [0.0 for _ in self._group_endpoints]
        speed_modes = [str(speed_mode).upper() for _ in self._group_endpoints]
        return bool(group.move_all_sync(targets, speed_mode=speed_modes, force=True))

    def health_check(self) -> DeviceHealth:
        configured = self.configured_endpoints()
        if not configured:
            return DeviceHealth(
                available=False,
                data={
                    "configured_endpoints": [],
                    "error": (
                        "No configured endpoints. Run `uv run pi5servo calib <endpoint>` or "
                        "`uv run pi5servo servo-tool` from the project root first."
                    ),
                },
            )

        self._build_group(configured)
        return DeviceHealth(
            available=True,
            data={
                "configured_endpoints": configured,
                "backend": self._backend_name,
                "backend_kwargs": dict(self._backend_kwargs),
            },
        )

    def stop(self) -> None:
        if self._group is None:
            return
        abort = getattr(self._group, "abort", None)
        if callable(abort):
            abort()
        off = getattr(self._group, "off", None)
        if callable(off):
            off()

    def close(self) -> None:
        if self._group is not None:
            close = getattr(self._group, "close", None)
            if callable(close):
                close()
        if self._runtime_handle is not None:
            common = _import_or_raise("pi5servo.cli._common")
            common.close_runtime_handle(self._runtime_handle)
        self._group = None
        self._runtime_handle = None
        self._group_endpoints = []


class BuzzerAdapter:
    """Adapter for the pi5buzzer standalone package."""

    def __init__(self, config: NinjaClawbotConfig) -> None:
        self.config = config
        self._buzzer: Any | None = None
        self._backend: Any | None = None

    def _build_buzzer(self) -> Any:
        if self._buzzer is not None:
            return self._buzzer

        config_module = _import_or_raise("pi5buzzer.config.config_manager")
        music_module = _import_or_raise("pi5buzzer")
        driver_module = _import_or_raise("pi5buzzer.core.driver")

        manager = config_module.BuzzerConfigManager(str(self.config.buzzer_config_path))
        manager.load()
        self._backend = driver_module.create_default_backend()
        self._buzzer = music_module.MusicBuzzer(
            pin=manager.get_pin(),
            pi=self._backend,
            volume=manager.get_volume(),
        )
        self._buzzer.initialize()
        return self._buzzer

    def play(
        self,
        *,
        emotion: str | None = None,
        frequency: int | None = None,
        duration: float = 0.3,
    ) -> None:
        buzzer = self._build_buzzer()
        if emotion:
            buzzer.play_emotion(emotion)
            return
        if frequency is None:
            raise ExecutionError("Sound actions require an emotion name or a frequency value.")
        buzzer.play_sound(int(frequency), float(duration))

    def health_check(self) -> DeviceHealth:
        manager_module = _import_or_raise("pi5buzzer.config.config_manager")
        manager = manager_module.BuzzerConfigManager(str(self.config.buzzer_config_path))
        config = manager.load()
        buzzer = self._build_buzzer()
        return DeviceHealth(
            available=True,
            data={
                "pin": config.get("pin"),
                "volume": config.get("volume"),
                "initialized": bool(buzzer.is_initialized),
            },
        )

    def close(self) -> None:
        if self._buzzer is not None:
            self._buzzer.off()
            self._buzzer = None
        if self._backend is not None:
            stop = getattr(self._backend, "stop", None)
            if callable(stop):
                stop()
            self._backend = None


class DisplayAdapter:
    """Adapter for the pi5disp standalone package."""

    def __init__(self, config: NinjaClawbotConfig) -> None:
        self.config = config
        self._display: Any | None = None
        self._config: dict[str, Any] | None = None

    def _build_display(self) -> Any:
        if self._display is not None:
            return self._display

        common = _import_or_raise("pi5disp.cli._common")
        _manager, config = common.load_config()
        self._config = dict(config)
        self._display = common.create_display()
        return self._display

    def show_text(
        self,
        text: str,
        *,
        scroll: bool = False,
        duration: float = 3.0,
        language: str = "en",
        font_size: int = 32,
    ) -> None:
        display = self._build_display()
        ticker_module = _import_or_raise("pi5disp.effects.text_ticker")
        image_module = _import_or_raise("PIL.Image")
        draw_module = _import_or_raise("PIL.ImageDraw")

        if scroll:
            ticker = ticker_module.TextTicker(
                display,
                text,
                font_size=int(font_size),
                language=language,
            )
            ticker.start()
            try:
                time.sleep(float(duration))
            finally:
                ticker.stop()
            return

        font = ticker_module.load_font(language, int(font_size))
        image = image_module.new("RGB", (display.width, display.height), (0, 0, 0))
        draw = draw_module.Draw(image)
        bbox = draw.textbbox((0, 0), text, font=font)
        x_pos = (display.width - (bbox[2] - bbox[0])) // 2
        y_pos = (display.height - (bbox[3] - bbox[1])) // 2
        draw.text((x_pos, y_pos), text, font=font, fill=(255, 255, 255))
        display.display(image)

    def clear(self) -> None:
        display = self._build_display()
        display.clear()

    def health_check(self) -> DeviceHealth:
        display = self._build_display()
        config = self._config or {}
        return DeviceHealth(
            available=bool(display.health_check()),
            data={
                "width": display.width,
                "height": display.height,
                "rotation": config.get("rotation", 90),
                "brightness": config.get("brightness", 100),
            },
        )

    def close(self) -> None:
        if self._display is not None:
            close = getattr(self._display, "close", None)
            if callable(close):
                close()
            self._display = None


class DistanceAdapter:
    """Adapter for the pi5vl53l0x standalone package."""

    def __init__(self, config: NinjaClawbotConfig) -> None:
        self.config = config
        self._sensor: Any | None = None

    def _build_sensor(self) -> Any:
        if self._sensor is not None:
            return self._sensor
        sensor_module = _import_or_raise("pi5vl53l0x")
        self._sensor = sensor_module.VL53L0X(
            i2c_bus=self.config.distance_bus,
            config_file_path=str(self.config.distance_config_path),
        )
        return self._sensor

    def read_data(self) -> dict[str, Any]:
        sensor = self._build_sensor()
        return dict(sensor.get_data())

    def health_check(self) -> DeviceHealth:
        sensor = self._build_sensor()
        return DeviceHealth(
            available=bool(sensor.health_check()),
            data={
                "bus": self.config.distance_bus,
                "config_file": str(Path(self.config.distance_config_path)),
            },
        )

    def close(self) -> None:
        if self._sensor is not None:
            close = getattr(self._sensor, "close", None)
            if callable(close):
                close()
            self._sensor = None
