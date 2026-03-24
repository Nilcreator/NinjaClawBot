from __future__ import annotations

import importlib

import pytest

from pi5camera.core.camera_backend import _import_picamera2_module
from pi5camera.environment import describe_picamera2_environment
from pi5camera.errors import CaptureError


def test_describe_picamera2_environment_detects_virtualenv_mismatch(monkeypatch) -> None:
    monkeypatch.setattr("pi5camera.environment.is_module_available", lambda module_name: False)
    monkeypatch.setattr("pi5camera.environment.platform.system", lambda: "Linux")
    monkeypatch.setattr("pi5camera.environment._is_virtual_environment", lambda: True)
    monkeypatch.setattr(
        "pi5camera.environment._python_can_import_module",
        lambda python_executable, module_name: True,
    )

    result = describe_picamera2_environment()

    assert result["state"] == "system-only"
    assert result["available"] is False
    assert "uv venv --python /usr/bin/python3 --system-site-packages" in result["help_text"]
    assert "uv sync --extra dev" in result["help_text"]


def test_describe_picamera2_environment_reports_missing_install(monkeypatch) -> None:
    monkeypatch.setattr("pi5camera.environment.is_module_available", lambda module_name: False)
    monkeypatch.setattr("pi5camera.environment.platform.system", lambda: "Linux")
    monkeypatch.setattr("pi5camera.environment._is_virtual_environment", lambda: True)
    monkeypatch.setattr(
        "pi5camera.environment._python_can_import_module",
        lambda python_executable, module_name: False,
    )

    result = describe_picamera2_environment()

    assert result["state"] == "missing"
    assert "sudo apt install -y python3-picamera2" in result["help_text"]
    assert "uv venv --python /usr/bin/python3 --system-site-packages" in result["help_text"]


def test_import_picamera2_module_raises_environment_guidance(monkeypatch) -> None:
    real_import_module = importlib.import_module

    def fake_import_module(name: str):
        if name == "picamera2":
            raise ImportError("No module named 'picamera2'")
        return real_import_module(name)

    monkeypatch.setattr("pi5camera.core.camera_backend.importlib.import_module", fake_import_module)
    monkeypatch.setattr(
        "pi5camera.core.camera_backend.describe_picamera2_environment",
        lambda: {
            "available": False,
            "help_text": (
                "Picamera2 is available in `/usr/bin/python3` but not in this virtual environment. "
                "Recreate the environment with "
                "`uv venv --python /usr/bin/python3 --system-site-packages`, "
                "then run `uv sync --extra dev`."
            ),
        },
    )

    with pytest.raises(CaptureError, match="system-site-packages"):
        _import_picamera2_module()
