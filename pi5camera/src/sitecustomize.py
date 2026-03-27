"""Startup hook for Raspberry Pi system package visibility.

This module is imported automatically by Python's ``site`` machinery when it is
present on ``sys.path``. For copied standalone ``pi5camera`` installs, that lets
plain ``uv run python`` invocations resolve Raspberry Pi system packages such as
``libcamera`` and ``picamera2`` without globally overriding unrelated venv
packages like ``Pillow``.
"""

from __future__ import annotations

import importlib.abc
import importlib.machinery
import platform
import subprocess
import sys
from pathlib import Path

SYSTEM_PYTHON = Path("/usr/bin/python3")
SYSTEM_MODULES = (
    "libcamera",
    "picamera2",
    "face_recognition",
    "face_recognition_models",
    "dlib",
)
SYSTEM_FINDER_MARKER = "pi5camera-rpi-system-finder"


def _is_virtual_environment() -> bool:
    base_prefix = getattr(sys, "base_prefix", sys.prefix)
    real_prefix = getattr(sys, "real_prefix", None)
    return sys.prefix != base_prefix or real_prefix is not None


def _get_system_site_packages(system_python: Path = SYSTEM_PYTHON) -> list[str]:
    if platform.system() != "Linux" or not system_python.exists():
        return []
    try:
        result = subprocess.run(
            [str(system_python), "-c", "import site; print('\\n'.join(site.getsitepackages()))"],
            check=False,
            capture_output=True,
            text=True,
            timeout=10,
        )
    except (OSError, subprocess.SubprocessError):
        return []
    if result.returncode != 0:
        return []
    return [path.strip() for path in result.stdout.splitlines() if path.strip()]


def _matches_target(fullname: str, module_names: tuple[str, ...] = SYSTEM_MODULES) -> bool:
    return any(fullname == name or fullname.startswith(f"{name}.") for name in module_names)


class _Pi5CameraSystemFinder(importlib.abc.MetaPathFinder):
    marker = SYSTEM_FINDER_MARKER

    def __init__(self, system_paths: list[str]) -> None:
        self.system_paths = tuple(dict.fromkeys(path for path in system_paths if path))

    def find_spec(self, fullname, path=None, target=None):  # type: ignore[override]
        if not _matches_target(fullname):
            return None
        search_path = path if path is not None else list(self.system_paths)
        return importlib.machinery.PathFinder.find_spec(fullname, search_path)


def ensure_rpi_system_packages_visible() -> None:
    if platform.system() != "Linux" or not _is_virtual_environment():
        return
    if any(getattr(finder, "marker", None) == SYSTEM_FINDER_MARKER for finder in sys.meta_path):
        return

    system_paths = _get_system_site_packages()
    if not system_paths:
        return
    sys.meta_path.insert(0, _Pi5CameraSystemFinder(system_paths))


ensure_rpi_system_packages_visible()
