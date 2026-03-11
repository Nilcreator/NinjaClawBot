"""Runtime composition for the integrated NinjaClawBot control layer."""

from __future__ import annotations

import importlib
import time
from types import ModuleType
from typing import Any

from ninjaclawbot.config import NinjaClawbotConfig
from ninjaclawbot.errors import ExecutionError, UnavailableCapabilityError
from ninjaclawbot.locks import ExecutionLock


class NinjaClawbotRuntime:
    """Owns the Pi 5 driver instances used by ninjaclawbot."""

    def __init__(self, config: NinjaClawbotConfig | None = None) -> None:
        self.config = config or NinjaClawbotConfig()
        self._execution_lock = ExecutionLock()
        self._servo_group: Any | None = None
        self._servo_endpoints: list[str] = []
        self._buzzer: Any | None = None
        self._display: Any | None = None
        self._distance_sensor: Any | None = None

    @property
    def execution_lock(self) -> ExecutionLock:
        return self._execution_lock

    def _import_module(self, module_name: str) -> ModuleType:
        try:
            return importlib.import_module(module_name)
        except ImportError as exc:
            raise UnavailableCapabilityError(
                f"Required package '{module_name}' is not installed in the ninjaclawbot environment."
            ) from exc

    def _close_servo_group(self) -> None:
        if self._servo_group is not None:
            close = getattr(self._servo_group, "close", None)
            if callable(close):
                close()
        self._servo_group = None
        self._servo_endpoints = []

    def get_servo_group(self, required_endpoints: list[str] | None = None) -> Any:
        required = list(dict.fromkeys(required_endpoints or []))
        if self._servo_group is not None and all(
            endpoint in self._servo_endpoints for endpoint in required
        ):
            return self._servo_group

        servo_module = self._import_module("pi5servo")
        config_module = self._import_module("pi5servo.config.config_manager")
        manager = config_module.ConfigManager(str(self.config.servo_config_path))
        manager.load()

        known_endpoints = list(manager.get_known_endpoints())
        selected_endpoints = list(dict.fromkeys(known_endpoints + required))
        if not selected_endpoints:
            raise UnavailableCapabilityError(
                "No servo endpoints are configured. Add endpoints to servo.json or pass them explicitly."
            )

        backend_config = manager.get_backend_config()
        calibrations = manager.get_all_endpoint_calibrations()
        self._close_servo_group()
        self._servo_group = servo_module.ServoGroup(
            None,
            selected_endpoints,
            calibrations,
            backend=backend_config["name"],
            backend_kwargs=backend_config["kwargs"],
        )
        self._servo_endpoints = list(self._servo_group.pins)
        return self._servo_group

    def move_servos(
        self,
        targets: dict[str, float],
        *,
        speed_mode: str = "M",
        easing: str = "ease_in_out_cubic",
    ) -> bool:
        group = self.get_servo_group(list(targets.keys()))
        ordered_targets = [targets.get(endpoint) for endpoint in group.pins]
        return bool(group.move_all_sync(ordered_targets, speed_mode=speed_mode, easing=easing))

    def get_buzzer(self) -> Any:
        if self._buzzer is not None:
            return self._buzzer

        config_module = self._import_module("pi5buzzer.config.config_manager")
        music_module = self._import_module("pi5buzzer")
        manager = config_module.BuzzerConfigManager(str(self.config.buzzer_config_path))
        manager.load()
        self._buzzer = music_module.MusicBuzzer(
            pin=manager.get_pin(),
            volume=manager.get_volume(),
        )
        self._buzzer.initialize()
        return self._buzzer

    def play_sound(
        self,
        *,
        emotion: str | None = None,
        frequency: int | None = None,
        duration: float = 0.3,
    ) -> None:
        buzzer = self.get_buzzer()
        if emotion:
            buzzer.play_emotion(emotion)
            return
        if frequency is None:
            raise ExecutionError("Sound actions require either an emotion name or a frequency.")
        buzzer.play_sound(frequency, duration)

    def get_display(self) -> Any:
        if self._display is not None:
            return self._display

        display_module = self._import_module("pi5disp")
        config_module = self._import_module("pi5disp.config.config_manager")
        manager = config_module.ConfigManager(str(self.config.display_config_path))
        config = manager.load()
        self._display = display_module.ST7789V(
            dc_pin=int(config.get("dc_pin", 14)),
            rst_pin=int(config.get("rst_pin", 15)),
            backlight_pin=int(config.get("backlight_pin", 16)),
            speed_hz=int(config.get("spi_speed_mhz", 32)) * 1_000_000,
            width=int(config.get("width", 240)),
            height=int(config.get("height", 320)),
            rotation=int(config.get("rotation", 90)),
        )
        self._display.set_brightness(int(config.get("brightness", 100)))
        return self._display

    def display_text(
        self,
        text: str,
        *,
        scroll: bool = False,
        duration: float = 3.0,
        language: str = "en",
        font_size: int = 32,
    ) -> None:
        display = self.get_display()
        ticker_module = self._import_module("pi5disp.effects.text_ticker")
        pil_image_module = self._import_module("PIL.Image")
        pil_draw_module = self._import_module("PIL.ImageDraw")

        if scroll:
            ticker = ticker_module.TextTicker(
                display,
                text,
                font_size=font_size,
                language=language,
            )
            ticker.start()
            try:
                time.sleep(duration)
            finally:
                ticker.stop()
            return

        font = ticker_module.load_font(language, font_size)
        image = pil_image_module.new("RGB", (display.width, display.height), (0, 0, 0))
        draw = pil_draw_module.Draw(image)
        bbox = draw.textbbox((0, 0), text, font=font)
        x_pos = (display.width - (bbox[2] - bbox[0])) // 2
        y_pos = (display.height - (bbox[3] - bbox[1])) // 2
        draw.text((x_pos, y_pos), text, font=font, fill=(255, 255, 255))
        display.display(image)

    def get_distance_sensor(self) -> Any:
        if self._distance_sensor is not None:
            return self._distance_sensor

        sensor_module = self._import_module("pi5vl53l0x")
        self._distance_sensor = sensor_module.VL53L0X(
            i2c_bus=self.config.distance_bus,
            config_file_path=str(self.config.distance_config_path),
        )
        return self._distance_sensor

    def read_distance(self) -> dict[str, Any]:
        sensor = self.get_distance_sensor()
        return dict(sensor.get_data())

    def health_check(self) -> dict[str, Any]:
        health: dict[str, Any] = {}

        try:
            group = self.get_servo_group([])
            health["servo"] = {
                "available": True,
                "configured_endpoints": list(getattr(group, "pins", [])),
            }
        except Exception as exc:
            health["servo"] = {"available": False, "error": str(exc)}

        try:
            buzzer = self.get_buzzer()
            health["buzzer"] = {"available": True, "initialized": bool(buzzer.is_initialized())}
        except Exception as exc:
            health["buzzer"] = {"available": False, "error": str(exc)}

        try:
            display = self.get_display()
            health["display"] = {"available": True, **dict(display.health_check())}
        except Exception as exc:
            health["display"] = {"available": False, "error": str(exc)}

        try:
            sensor = self.get_distance_sensor()
            health["distance"] = {"available": True, **dict(sensor.health_check())}
        except Exception as exc:
            health["distance"] = {"available": False, "error": str(exc)}

        return health

    def stop_all(self) -> None:
        if self._servo_group is not None:
            abort = getattr(self._servo_group, "abort", None)
            if callable(abort):
                abort()
            off = getattr(self._servo_group, "off", None)
            if callable(off):
                off()
        if self._buzzer is not None:
            self._buzzer.off()
        if self._display is not None:
            self._display.off()

    def close(self) -> None:
        self.stop_all()
        self._close_servo_group()
        if self._buzzer is not None:
            self._buzzer = None
        if self._display is not None:
            close = getattr(self._display, "close", None)
            if callable(close):
                close()
            self._display = None
        if self._distance_sensor is not None:
            close = getattr(self._distance_sensor, "close", None)
            if callable(close):
                close()
            self._distance_sensor = None
