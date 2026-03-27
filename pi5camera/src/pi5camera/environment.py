"""Environment and dependency probes for pi5camera."""

from __future__ import annotations

import importlib.util
import json
import platform
import subprocess
import sys
from pathlib import Path
from typing import Any

SYSTEM_PYTHON = Path("/usr/bin/python3")
PICAMERA2_APT_COMMAND = "sudo apt install -y python3-picamera2"
PICAMERA2_VENV_COMMAND = "rm -rf .venv && /usr/bin/python3 -m venv --system-site-packages .venv"
PICAMERA2_SYNC_COMMAND = "source .venv/bin/activate && uv sync --active --extra dev"
RECOGNITION_REPAIR_COMMAND = (
    "source .venv/bin/activate && uv sync --active --extra dev "
    "--reinstall-package dlib "
    "--reinstall-package face-recognition "
    "--reinstall-package face-recognition-models"
)
BOOTSTRAP_STANDALONE_COMMAND = "./scripts/bootstrap-rpi-standalone.sh"
BOOTSTRAP_WORKSPACE_COMMAND = "./scripts/bootstrap-rpi-workspace.sh"

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


def _probe_module_import(
    python_executable: Path,
    module_name: str,
) -> dict[str, Any]:
    """Return import diagnostics for ``module_name`` under ``python_executable``."""
    if not python_executable.exists():
        return {
            "available": False,
            "spec_found": False,
            "error_type": "MissingInterpreter",
            "error_message": f"Python interpreter not found: {python_executable}",
            "missing_module": None,
        }

    probe_code = """
import importlib
import importlib.util
import json
import sys

module_name = sys.argv[1]
result = {
    "available": False,
    "spec_found": importlib.util.find_spec(module_name) is not None,
    "error_type": None,
    "error_message": None,
    "missing_module": None,
}
try:
    importlib.import_module(module_name)
except Exception as exc:  # pragma: no cover - exercised through subprocess
    result["error_type"] = type(exc).__name__
    result["error_message"] = str(exc)
    if isinstance(exc, ModuleNotFoundError) and getattr(exc, "name", None):
        result["missing_module"] = exc.name
else:
    result["available"] = True

print(json.dumps(result))
"""
    try:
        result = subprocess.run(
            [str(python_executable), "-c", probe_code, module_name],
            check=False,
            capture_output=True,
            text=True,
            timeout=15,
        )
    except (OSError, subprocess.SubprocessError) as exc:
        return {
            "available": False,
            "spec_found": False,
            "error_type": type(exc).__name__,
            "error_message": str(exc),
            "missing_module": None,
        }

    stdout = result.stdout.strip()
    if not stdout:
        return {
            "available": False,
            "spec_found": False,
            "error_type": "ProbeError",
            "error_message": result.stderr.strip() or "Module probe returned no output.",
            "missing_module": None,
        }

    try:
        payload = json.loads(stdout)
    except json.JSONDecodeError:
        return {
            "available": False,
            "spec_found": False,
            "error_type": "ProbeError",
            "error_message": stdout,
            "missing_module": None,
        }
    return payload


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
    module_name: str = "picamera2",
    system_python: Path = SYSTEM_PYTHON,
) -> bool:
    """Add system dist-packages to ``sys.path`` so apt-installed packages are importable.

    This is necessary because ``uv run`` and ``uv sync`` can recreate the
    virtual environment without ``--system-site-packages``, making Picamera2
    invisible even when it is installed through ``apt``.

    Returns whether ``module_name`` was successfully made importable.
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
    return is_module_available(module_name)


def _bootstrap_help_text() -> str:
    return (
        "Run the Raspberry Pi bootstrap script that matches your install layout: "
        f"`{BOOTSTRAP_STANDALONE_COMMAND}` for standalone `pi5camera`, or "
        f"`{BOOTSTRAP_WORKSPACE_COMMAND}` from the NinjaClawBot workspace root."
    )


def _format_import_diagnostic(probe: dict[str, Any]) -> str | None:
    error_type = probe.get("error_type")
    error_message = probe.get("error_message")
    if not error_type and not error_message:
        return None
    if error_type and error_message:
        return f"{error_type}: {error_message}"
    return str(error_type or error_message)


def describe_picamera2_environment(system_python: Path = SYSTEM_PYTHON) -> dict[str, Any]:
    """Summarize whether Picamera2 is available in the current and system Python environments."""
    current_available = is_module_available("picamera2")
    on_linux = platform.system() == "Linux"

    # ── Auto-fix: inject system dist-packages when picamera2 is missing ──
    if not current_available and on_linux and _is_virtual_environment():
        if inject_system_site_packages(system_python=system_python):
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
            f"{_bootstrap_help_text()} Or manually: "
            f"`{PICAMERA2_VENV_COMMAND}`, then `{PICAMERA2_SYNC_COMMAND}`."
        )
    elif system_python_available:
        state = "system-only"
        help_text = (
            "Picamera2 is available in `/usr/bin/python3` but not in the current Python interpreter. "
            f"{_bootstrap_help_text()} Or manually: "
            f"`{PICAMERA2_VENV_COMMAND}`, then `{PICAMERA2_SYNC_COMMAND}`."
        )
    else:
        state = "missing"
        help_text = (
            "Picamera2 is not importable. On Raspberry Pi OS install it with "
            f"`{PICAMERA2_APT_COMMAND}`. {_bootstrap_help_text()} "
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


def describe_face_recognition_environment(
    system_python: Path = SYSTEM_PYTHON,
) -> dict[str, Any]:
    """Summarize whether ``face_recognition`` is usable in the current environment."""
    current_probe = _probe_module_import(Path(sys.executable), "face_recognition")
    current_available = bool(current_probe["available"])
    on_linux = platform.system() == "Linux"

    if not current_available and on_linux and _is_virtual_environment():
        if inject_system_site_packages("face_recognition", system_python=system_python):
            current_probe = _probe_module_import(Path(sys.executable), "face_recognition")
            current_available = bool(current_probe["available"])

    system_probe = (
        _probe_module_import(system_python, "face_recognition")
        if on_linux and not current_available and system_python.exists()
        else {
            "available": False,
            "spec_found": False,
            "error_type": None,
            "error_message": None,
            "missing_module": None,
        }
    )
    environment_mismatch = (
        not current_available and system_probe["available"] and _is_virtual_environment()
    )

    help_text: str | None = None
    if current_available:
        state = "ready"
    elif environment_mismatch:
        state = "system-only"
        help_text = (
            "face_recognition is available in `/usr/bin/python3` but not in this virtual "
            "environment. "
            f"{_bootstrap_help_text()} Or manually: `{PICAMERA2_VENV_COMMAND}`, then "
            f"`{PICAMERA2_SYNC_COMMAND}`."
        )
    elif current_probe.get("spec_found"):
        state = "broken"
        missing_module = current_probe.get("missing_module")
        detail = _format_import_diagnostic(current_probe)
        if missing_module and missing_module != "face_recognition":
            help_text = (
                "face_recognition is installed, but a dependency failed to import "
                f"(`{missing_module}`). {_bootstrap_help_text()} If the environment already exists, "
                f"repair it manually with `{RECOGNITION_REPAIR_COMMAND}`."
            )
        else:
            help_text = (
                "face_recognition is present but failed to import correctly. "
                f"{_bootstrap_help_text()} If the environment already exists, repair it manually "
                f"with `{RECOGNITION_REPAIR_COMMAND}`."
            )
        if detail:
            help_text = f"{help_text} Import detail: {detail}."
    elif system_probe["available"]:
        state = "system-only"
        help_text = (
            "face_recognition is available in `/usr/bin/python3` but not in the current Python "
            f"interpreter. {_bootstrap_help_text()} Or manually: `{PICAMERA2_VENV_COMMAND}`, then "
            f"`{PICAMERA2_SYNC_COMMAND}`."
        )
    else:
        state = "missing"
        detail = _format_import_diagnostic(current_probe)
        help_text = (
            "The face_recognition stack is not importable in this environment. "
            f"{_bootstrap_help_text()} If the environment already exists, repair it manually with "
            f"`{RECOGNITION_REPAIR_COMMAND}`."
        )
        if detail:
            help_text = f"{help_text} Import detail: {detail}."

    return {
        "available": current_available,
        "state": state,
        "help_text": help_text,
        "current_python": sys.executable,
        "is_virtualenv": _is_virtual_environment(),
        "system_python": str(system_python) if on_linux and system_python.exists() else None,
        "system_python_available": bool(system_probe["available"]),
        "diagnostic": _format_import_diagnostic(current_probe),
        "missing_module": current_probe.get("missing_module"),
    }
