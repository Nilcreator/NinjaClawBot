"""Startup hook for Raspberry Pi system package visibility.

This module is imported automatically by Python's ``site`` machinery when it is
present on ``sys.path``. For copied standalone ``pi5camera`` installs, that lets
plain ``uv run python`` invocations see Raspberry Pi system packages such as
``libcamera`` and ``picamera2`` before any ``pi5camera`` code is imported.
"""

from __future__ import annotations

import importlib
import platform
import subprocess
import sys
from pathlib import Path

SYSTEM_PYTHON = Path("/usr/bin/python3")
SYSTEM_MODULES = ("libcamera", "picamera2", "face_recognition")


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


def _needs_system_paths(module_names: tuple[str, ...] = SYSTEM_MODULES) -> bool:
    if platform.system() != "Linux" or not _is_virtual_environment():
        return False
    for module_name in module_names:
        try:
            importlib.import_module(module_name)
        except Exception:
            sys.modules.pop(module_name, None)
            return True
    return False


def _prepend_system_paths(paths: list[str]) -> None:
    if not paths:
        return
    insertion_index = 1 if sys.path else 0
    for path in reversed(paths):
        if not path:
            continue
        if path in sys.path:
            sys.path.remove(path)
        sys.path.insert(insertion_index, path)


def ensure_rpi_system_packages_visible() -> None:
    if not _needs_system_paths():
        return
    _prepend_system_paths(_get_system_site_packages())


ensure_rpi_system_packages_visible()
