"""Camera backend helpers for pi5camera."""

from __future__ import annotations

import importlib
import time
from pathlib import Path
from typing import Any

from pi5camera.environment import describe_picamera2_environment, inject_system_site_packages
from pi5camera.errors import CaptureError
from pi5camera.models import CaptureResult


def _import_picamera2_module() -> Any:
    try:
        return importlib.import_module("picamera2")
    except ImportError:
        pass  # Fall through to recovery logic below.

    # Attempt runtime recovery: inject system dist-packages into sys.path
    # so apt-installed picamera2 becomes importable even when uv recreated
    # the venv without --system-site-packages.
    if inject_system_site_packages():
        try:
            return importlib.import_module("picamera2")
        except ImportError:
            pass  # Recovery added paths but import still failed.

    # Report the final error with environment guidance.
    environment = describe_picamera2_environment()
    if not environment["available"] and environment["help_text"] is not None:
        raise CaptureError(environment["help_text"])
    raise CaptureError(
        "Picamera2 could not be imported in this environment. "
        "Check that python3-picamera2 is installed and the virtual environment "
        "has access to system packages."
    )


def _apply_autofocus(picam2: Any, autofocus_mode: str) -> None:
    normalized = str(autofocus_mode).strip().lower()
    if normalized in {"", "none"}:
        return

    try:
        controls_module = importlib.import_module("libcamera.controls")
    except ImportError:  # pragma: no cover - depends on host environment
        return

    mode_map = {
        "manual": getattr(controls_module.AfModeEnum, "Manual", None),
        "auto": getattr(controls_module.AfModeEnum, "Auto", None),
        "continuous": getattr(controls_module.AfModeEnum, "Continuous", None),
    }
    mode_value = mode_map.get(normalized)
    if mode_value is None:
        return

    try:
        picam2.set_controls({"AfMode": mode_value})
    except Exception:
        # Autofocus support varies by camera module. Best effort only.
        return


class Picamera2StillBackend:
    """Small wrapper around Picamera2 still capture."""

    def __init__(
        self,
        *,
        width: int,
        height: int,
        warmup_seconds: float,
        use_preview: bool,
        autofocus_mode: str,
    ) -> None:
        module = _import_picamera2_module()
        self._picam2 = module.Picamera2()
        self._width = int(width)
        self._height = int(height)
        self._warmup_seconds = max(0.0, float(warmup_seconds))
        self._use_preview = bool(use_preview)
        self._autofocus_mode = autofocus_mode

    def capture(self, output_path: Path) -> CaptureResult:
        """Capture one still image to the given path."""
        output_path = output_path.expanduser().resolve()
        output_path.parent.mkdir(parents=True, exist_ok=True)

        preview_module = None
        config = self._picam2.create_still_configuration(main={"size": (self._width, self._height)})
        self._picam2.configure(config)
        if self._use_preview:
            try:
                preview_module = _import_picamera2_module().Preview
                self._picam2.start_preview(preview_module.NULL)
            except Exception:
                preview_module = None

        self._picam2.start()
        try:
            _apply_autofocus(self._picam2, self._autofocus_mode)
            if self._warmup_seconds > 0:
                time.sleep(self._warmup_seconds)
            metadata = self._picam2.capture_file(str(output_path))
        except Exception as exc:
            raise CaptureError(f"Camera capture failed: {exc}") from exc
        finally:
            try:
                self._picam2.stop()
            except Exception:
                pass
            if preview_module is not None:
                try:
                    self._picam2.stop_preview()
                except Exception:
                    pass

        return CaptureResult(path=output_path, metadata=dict(metadata or {}))

    def close(self) -> None:
        """Close camera resources."""
        try:
            self._picam2.close()
        except Exception:
            return


def build_camera_backend(config: dict[str, Any]) -> Picamera2StillBackend:
    """Build the configured still-camera backend."""
    camera_config = config.get("camera", {})
    return Picamera2StillBackend(
        width=int(camera_config.get("width", 1280)),
        height=int(camera_config.get("height", 720)),
        warmup_seconds=float(camera_config.get("warmup_seconds", 1.0)),
        use_preview=bool(camera_config.get("use_preview", False)),
        autofocus_mode=str(camera_config.get("autofocus_mode", "continuous")),
    )
