"""Shared CLI helpers for pi5camera."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from pi5camera.config.config_manager import CameraConfigManager
from pi5camera.environment import (
    describe_face_recognition_environment,
    describe_picamera2_environment,
)
from pi5camera.errors import ConfigError


def load_manager(config_file: Path | str | None) -> CameraConfigManager:
    """Create and load a config manager for the given path."""
    manager = CameraConfigManager(config_file)
    manager.load()
    return manager


def describe_camera_stack(config: dict[str, Any]) -> dict[str, Any]:
    """Summarize camera and recognition backend readiness."""
    camera_config = config.get("camera")
    recognition_config = config.get("recognition")
    paths = config.get("paths")
    if not isinstance(camera_config, dict):
        raise ConfigError("Config key 'camera' must be an object.")
    if not isinstance(recognition_config, dict):
        raise ConfigError("Config key 'recognition' must be an object.")
    if not isinstance(paths, dict):
        raise ConfigError("Config key 'paths' must be an object.")

    recognition_backend = str(recognition_config.get("backend", "face_recognition"))
    picamera2_environment = describe_picamera2_environment()
    recognition_environment = describe_face_recognition_environment()
    return {
        "photo_dir": str(paths["photo_dir"]),
        "data_dir": str(paths["data_dir"]),
        "camera_backend": "picamera2",
        "camera_backend_available": picamera2_environment["available"],
        "camera_backend_state": picamera2_environment["state"],
        "camera_backend_help_text": picamera2_environment["help_text"],
        "python_executable": picamera2_environment["current_python"],
        "system_python": picamera2_environment["system_python"],
        "system_python_available": picamera2_environment["system_python_available"],
        "recognition_backend": recognition_backend,
        "recognition_backend_available": recognition_environment["available"],
        "recognition_backend_state": recognition_environment["state"],
        "recognition_backend_help_text": recognition_environment["help_text"],
        "resolution": {
            "width": int(camera_config.get("width", 1280)),
            "height": int(camera_config.get("height", 720)),
        },
        "warmup_seconds": float(camera_config.get("warmup_seconds", 1.0)),
    }
