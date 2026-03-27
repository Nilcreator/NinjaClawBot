from __future__ import annotations

import importlib
import sys
from pathlib import Path

import pytest

from pi5camera.core.camera_backend import _import_picamera2_module
from pi5camera.environment import (
    _PTH_FILE_NAME,
    _STARTUP_HELPER_FILE_NAME,
    describe_face_recognition_environment,
    describe_picamera2_environment,
    inject_system_site_packages,
    install_startup_import_hook,
)
from pi5camera.errors import CaptureError


def test_describe_picamera2_environment_detects_virtualenv_mismatch(monkeypatch) -> None:
    """When system python has picamera2 but the venv does NOT and injection
    fails, the environment should report system-only with correct guidance."""
    monkeypatch.setattr("pi5camera.environment.platform.system", lambda: "Linux")
    monkeypatch.setattr("pi5camera.environment._is_virtual_environment", lambda: True)
    monkeypatch.setattr(
        "pi5camera.environment._probe_module_import",
        lambda python_executable, module_name: {
            "available": str(python_executable) == "/usr/bin/python3",
            "spec_found": str(python_executable) == "/usr/bin/python3",
            "error_type": None if str(python_executable) == "/usr/bin/python3" else "ImportError",
            "error_message": None
            if str(python_executable) == "/usr/bin/python3"
            else "No module named 'picamera2'",
            "missing_module": None if str(python_executable) == "/usr/bin/python3" else "picamera2",
        },
    )
    # Prevent actual sys.path injection and .pth writes during tests.
    monkeypatch.setattr(
        "pi5camera.environment._get_system_site_package_paths",
        lambda system_python: [],
    )

    result = describe_picamera2_environment()

    assert result["state"] == "system-only"
    assert result["available"] is False
    assert "/usr/bin/python3 -m venv --system-site-packages" in result["help_text"]
    assert "uv sync --active --extra dev" in result["help_text"]


def test_describe_picamera2_environment_reports_missing_install(monkeypatch) -> None:
    monkeypatch.setattr("pi5camera.environment.platform.system", lambda: "Linux")
    monkeypatch.setattr("pi5camera.environment._is_virtual_environment", lambda: True)
    monkeypatch.setattr(
        "pi5camera.environment._probe_module_import",
        lambda python_executable, module_name: {
            "available": False,
            "spec_found": False,
            "error_type": "ImportError",
            "error_message": "No module named 'picamera2'",
            "missing_module": "picamera2",
        },
    )
    monkeypatch.setattr(
        "pi5camera.environment._get_system_site_package_paths",
        lambda system_python: [],
    )

    result = describe_picamera2_environment()

    assert result["state"] == "missing"
    assert "sudo apt install -y python3-picamera2" in result["help_text"]
    assert "/usr/bin/python3 -m venv --system-site-packages" in result["help_text"]


def test_describe_picamera2_environment_reports_broken_dependency(monkeypatch) -> None:
    monkeypatch.setattr("pi5camera.environment.platform.system", lambda: "Linux")
    monkeypatch.setattr("pi5camera.environment._is_virtual_environment", lambda: True)
    monkeypatch.setattr(
        "pi5camera.environment.inject_system_site_packages",
        lambda module_name="picamera2", system_python=Path("/usr/bin/python3"): False,
    )

    def fake_probe(python_executable: Path, module_name: str) -> dict[str, object]:
        if str(python_executable) == str(Path(sys.executable)):
            return {
                "available": False,
                "spec_found": True,
                "error_type": "ModuleNotFoundError",
                "error_message": "No module named 'libcamera._libcamera'",
                "missing_module": "libcamera._libcamera",
            }
        return {
            "available": True,
            "spec_found": True,
            "error_type": None,
            "error_message": None,
            "missing_module": None,
        }

    monkeypatch.setattr("pi5camera.environment._probe_module_import", fake_probe)

    result = describe_picamera2_environment()

    assert result["state"] == "broken"
    assert result["available"] is False
    assert "broken Picamera2 import" in result["help_text"]
    assert (
        "Import detail: ModuleNotFoundError: No module named 'libcamera._libcamera'"
        in result["help_text"]
    )


def test_import_picamera2_module_raises_environment_guidance(monkeypatch) -> None:
    real_import_module = importlib.import_module

    def fake_import_module(name: str):
        if name == "picamera2":
            raise ImportError("No module named 'picamera2'")
        return real_import_module(name)

    monkeypatch.setattr("pi5camera.core.camera_backend.importlib.import_module", fake_import_module)
    monkeypatch.setattr(
        "pi5camera.core.camera_backend.inject_system_site_packages",
        lambda: False,
    )
    monkeypatch.setattr(
        "pi5camera.core.camera_backend.describe_picamera2_environment",
        lambda: {
            "available": False,
            "help_text": (
                "Picamera2 is available in `/usr/bin/python3` but not in this virtual environment. "
                "Run `./scripts/bootstrap-rpi-standalone.sh` to fix this, or manually: "
                "`rm -rf .venv && /usr/bin/python3 -m venv --system-site-packages .venv`, "
                "then `source .venv/bin/activate && uv sync --active --extra dev`."
            ),
        },
    )

    with pytest.raises(CaptureError, match="system-site-packages"):
        _import_picamera2_module()


def test_inject_system_site_packages_adds_paths_and_writes_pth(
    tmp_path: Path,
    monkeypatch,
) -> None:
    """When injection is called with fake system paths, sys.path is extended
    and a .pth file is written for persistence."""
    fake_dist = str(tmp_path / "fake-dist-packages")
    monkeypatch.setattr("pi5camera.environment._is_virtual_environment", lambda: True)
    monkeypatch.setattr("pi5camera.environment.platform.system", lambda: "Linux")
    monkeypatch.setattr(
        "pi5camera.environment._get_system_site_package_paths",
        lambda system_python: [fake_dist],
    )

    # Create a fake venv site-packages so _write_pth_file can write.
    version = f"python{sys.version_info.major}.{sys.version_info.minor}"
    site_packages = tmp_path / "venv" / "lib" / version / "site-packages"
    site_packages.mkdir(parents=True)
    monkeypatch.setattr(
        "pi5camera.environment._venv_site_packages_dir",
        lambda: site_packages,
    )

    real_import_module = importlib.import_module

    def fake_import_module(name: str):
        if name == "picamera2":
            return object()
        return real_import_module(name)

    monkeypatch.setattr("pi5camera.environment.importlib.import_module", fake_import_module)
    # Create a fake system python so the exists() check passes on macOS.
    fake_system_python = tmp_path / "fake-python3"
    fake_system_python.touch()
    monkeypatch.setattr("pi5camera.environment.SYSTEM_PYTHON", fake_system_python)

    result = inject_system_site_packages(system_python=fake_system_python)

    assert result is True
    assert sys.path.index(fake_dist) <= 1
    while fake_dist in sys.path:
        sys.path.remove(fake_dist)

    pth_file = site_packages / _PTH_FILE_NAME
    assert pth_file.exists()
    assert "import _pi5camera_rpi_startup" in pth_file.read_text(encoding="utf-8")

    startup_file = site_packages / _STARTUP_HELPER_FILE_NAME
    assert startup_file.exists()
    startup_body = startup_file.read_text(encoding="utf-8")
    assert fake_dist in startup_body


def test_install_startup_import_hook_writes_helper_module(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr("pi5camera.environment._is_virtual_environment", lambda: True)
    monkeypatch.setattr("pi5camera.environment.platform.system", lambda: "Linux")
    monkeypatch.setattr(
        "pi5camera.environment._get_system_site_package_paths",
        lambda system_python: ["/usr/lib/python3/dist-packages"],
    )

    version = f"python{sys.version_info.major}.{sys.version_info.minor}"
    site_packages = tmp_path / "venv" / "lib" / version / "site-packages"
    site_packages.mkdir(parents=True)
    monkeypatch.setattr(
        "pi5camera.environment._venv_site_packages_dir",
        lambda: site_packages,
    )

    fake_system_python = tmp_path / "fake-python3"
    fake_system_python.touch()

    assert install_startup_import_hook(system_python=fake_system_python) is True
    assert (site_packages / _PTH_FILE_NAME).exists()
    helper_path = site_packages / _STARTUP_HELPER_FILE_NAME
    assert helper_path.exists()
    assert "/usr/lib/python3/dist-packages" in helper_path.read_text(encoding="utf-8")


def test_describe_face_recognition_environment_reports_missing_dependency(monkeypatch) -> None:
    monkeypatch.setattr("pi5camera.environment.platform.system", lambda: "Linux")
    monkeypatch.setattr("pi5camera.environment._is_virtual_environment", lambda: True)
    monkeypatch.setattr(
        "pi5camera.environment.inject_system_site_packages",
        lambda module_name="face_recognition", system_python=Path("/usr/bin/python3"): False,
    )

    def fake_probe(python_executable: Path, module_name: str) -> dict[str, object]:
        if str(python_executable) == str(Path(sys.executable)):
            return {
                "available": False,
                "spec_found": True,
                "error_type": "ModuleNotFoundError",
                "error_message": "No module named 'dlib'",
                "missing_module": "dlib",
            }
        return {
            "available": False,
            "spec_found": False,
            "error_type": None,
            "error_message": None,
            "missing_module": None,
        }

    monkeypatch.setattr("pi5camera.environment._probe_module_import", fake_probe)

    result = describe_face_recognition_environment()

    assert result["state"] == "broken"
    assert result["available"] is False
    assert "`dlib`" in result["help_text"]
    assert "uv pip install --python .venv/bin/python" in result["help_text"]
