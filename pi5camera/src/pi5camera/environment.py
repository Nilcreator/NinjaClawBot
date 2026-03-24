"""Environment and dependency probes for pi5camera."""

from __future__ import annotations

import importlib.util
import platform
import subprocess
import sys
from pathlib import Path
from typing import Any

SYSTEM_PYTHON = Path("/usr/bin/python3")
PICAMERA2_APT_COMMAND = "sudo apt install -y python3-picamera2"
PICAMERA2_VENV_COMMAND = "rm -rf .venv && /usr/bin/python3 -m venv --system-site-packages .venv"
PICAMERA2_SYNC_COMMAND = "source .venv/bin/activate && uv sync --active --extra dev"


def is_module_available(module_name: str) -> bool:
    """Return whether a Python module can be imported in the current environment."""
    return importlib.util.find_spec(module_name) is not None


def _is_virtual_environment() -> bool:
    """Return whether the current interpreter is running inside a virtual environment."""
    base_prefix = getattr(sys, "base_prefix", sys.prefix)
    real_prefix = getattr(sys, "real_prefix", None)
    return sys.prefix != base_prefix or real_prefix is not None


def _python_can_import_module(python_executable: Path, module_name: str) -> bool:
    """Probe whether the given Python executable can import a module."""
    if not python_executable.exists():
        return False

    probe_code = "import importlib, sys; importlib.import_module(sys.argv[1]); raise SystemExit(0)"
    try:
        result = subprocess.run(
            [str(python_executable), "-c", probe_code, module_name],
            check=False,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            timeout=10,
        )
    except (OSError, subprocess.SubprocessError):
        return False
    return result.returncode == 0


def describe_picamera2_environment(system_python: Path = SYSTEM_PYTHON) -> dict[str, Any]:
    """Summarize whether Picamera2 is available in the current and system Python environments."""
    current_available = is_module_available("picamera2")
    on_linux = platform.system() == "Linux"
    system_python_available = (
        _python_can_import_module(system_python, "picamera2")
        if on_linux and not current_available
        else False
    )
    environment_mismatch = (
        not current_available and system_python_available and _is_virtual_environment()
    )

    help_text: str | None = None
    if current_available:
        state = "ready"
    elif environment_mismatch:
        state = "system-only"
        help_text = (
            "Picamera2 is available in `/usr/bin/python3` but not in this virtual environment. "
            "Run `./scripts/bootstrap-rpi-standalone.sh` to fix this, or manually: "
            f"`{PICAMERA2_VENV_COMMAND}`, then `{PICAMERA2_SYNC_COMMAND}`."
        )
    elif system_python_available:
        state = "system-only"
        help_text = (
            "Picamera2 is available in `/usr/bin/python3` but not in the current Python interpreter. "
            "Run `./scripts/bootstrap-rpi-standalone.sh`, or manually: "
            f"`{PICAMERA2_VENV_COMMAND}`, then `{PICAMERA2_SYNC_COMMAND}`."
        )
    else:
        state = "missing"
        help_text = (
            "Picamera2 is not importable. On Raspberry Pi OS install it with "
            f"`{PICAMERA2_APT_COMMAND}`, then run `./scripts/bootstrap-rpi-standalone.sh`. "
            f"Or manually: `{PICAMERA2_VENV_COMMAND}`, then `{PICAMERA2_SYNC_COMMAND}`."
        )

    return {
        "available": current_available,
        "state": state,
        "help_text": help_text,
        "current_python": sys.executable,
        "is_virtualenv": _is_virtual_environment(),
        "system_python": str(system_python) if on_linux and system_python.exists() else None,
        "system_python_available": system_python_available,
    }
