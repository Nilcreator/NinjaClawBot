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

_PTH_FILE_NAME = "_pi5camera_system_packages.pth"


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


def _get_system_site_package_paths(system_python: Path) -> list[str]:
    """Ask `system_python` for its dist-packages directories."""
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
    return [p.strip() for p in result.stdout.strip().splitlines() if p.strip()]


def _venv_site_packages_dir() -> Path | None:
    """Return this virtual environment's site-packages directory, if discoverable."""
    if not _is_virtual_environment():
        return None
    version = f"python{sys.version_info.major}.{sys.version_info.minor}"
    candidate = Path(sys.prefix) / "lib" / version / "site-packages"
    if candidate.is_dir():
        return candidate
    return None


def _write_pth_file(site_packages: Path, system_paths: list[str]) -> bool:
    """Write a .pth file into the venv so system packages survive future runs."""
    pth_path = site_packages / _PTH_FILE_NAME
    try:
        pth_path.write_text("\n".join(system_paths) + "\n", encoding="utf-8")
    except OSError:
        return False
    return True


def inject_system_site_packages(
    system_python: Path = SYSTEM_PYTHON,
) -> bool:
    """Add system dist-packages to ``sys.path`` so apt-installed packages are importable.

    This is necessary because ``uv run`` and ``uv sync`` can recreate the
    virtual environment without ``--system-site-packages``, making Picamera2
    invisible even when it is installed through ``apt``.

    Returns whether picamera2 was successfully made importable.
    """
    if not _is_virtual_environment():
        return False
    if platform.system() != "Linux":
        return False
    if not system_python.exists():
        return False

    system_paths = _get_system_site_package_paths(system_python)
    if not system_paths:
        return False

    for path in system_paths:
        if path not in sys.path:
            sys.path.append(path)

    # Persist the fix so subsequent runs also work even if the .pth file
    # was wiped by a prior uv sync.
    site_packages = _venv_site_packages_dir()
    if site_packages is not None:
        _write_pth_file(site_packages, system_paths)

    # Force importlib to clear cached module lookups after path change.
    importlib.invalidate_caches()
    return is_module_available("picamera2")


def describe_picamera2_environment(system_python: Path = SYSTEM_PYTHON) -> dict[str, Any]:
    """Summarize whether Picamera2 is available in the current and system Python environments."""
    current_available = is_module_available("picamera2")
    on_linux = platform.system() == "Linux"

    # ── Auto-fix: inject system dist-packages when picamera2 is missing ──
    if not current_available and on_linux and _is_virtual_environment():
        if inject_system_site_packages(system_python):
            current_available = True

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
