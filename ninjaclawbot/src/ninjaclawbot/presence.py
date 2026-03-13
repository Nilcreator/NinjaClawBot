"""Shared presence-mode helpers for persistent robot states."""

from __future__ import annotations

from typing import Any

from ninjaclawbot.errors import ActionValidationError

PRESENCE_MODES: tuple[str, ...] = ("idle", "thinking", "listening")


def list_presence_modes() -> list[str]:
    """Return the supported persistent robot presence modes."""

    return list(PRESENCE_MODES)


def normalize_presence_mode(name: Any) -> str:
    """Normalize and validate a persistent presence mode name."""

    normalized = str(name).strip().lower()
    if normalized not in PRESENCE_MODES:
        supported = ", ".join(PRESENCE_MODES)
        raise ActionValidationError(
            f"Unsupported presence mode '{name}'. Supported modes: {supported}."
        )
    return normalized
