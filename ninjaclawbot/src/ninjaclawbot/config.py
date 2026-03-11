"""Configuration helpers for the ninjaclawbot runtime."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path


@dataclass(slots=True)
class NinjaClawbotConfig:
    """Runtime configuration for the integrated robot layer."""

    root_dir: Path = field(default_factory=Path.cwd)
    servo_config_file: str = "servo.json"
    buzzer_config_file: str = "buzzer.json"
    display_config_file: str = "display.json"
    distance_config_file: str = "vl53l0x.json"
    asset_dir_name: str = "ninjaclawbot_data"
    distance_bus: int = 1

    @property
    def servo_config_path(self) -> Path:
        return self.root_dir / self.servo_config_file

    @property
    def buzzer_config_path(self) -> Path:
        return self.root_dir / self.buzzer_config_file

    @property
    def display_config_path(self) -> Path:
        return self.root_dir / self.display_config_file

    @property
    def distance_config_path(self) -> Path:
        return self.root_dir / self.distance_config_file

    @property
    def asset_root(self) -> Path:
        return self.root_dir / self.asset_dir_name

    @property
    def movement_asset_dir(self) -> Path:
        return self.asset_root / "movements"

    @property
    def expression_asset_dir(self) -> Path:
        return self.asset_root / "expressions"
