"""Helpers for built-in sound expression chains."""

from __future__ import annotations

from typing import Any

from ninjaclawbot.expressions.catalog import SOUND_ALIASES, normalize_sound_emotion


def normalize_sound_step(step: dict[str, Any]) -> dict[str, Any]:
    """Normalize a sound step for sequential playback."""

    emotion = str(step.get("emotion", "")).strip()
    frequency = step.get("frequency")
    if emotion:
        emotion = normalize_sound_emotion(emotion)
    elif frequency is not None:
        frequency = int(frequency)
    else:
        raise ValueError("Sound steps must define an emotion or frequency.")
    return {
        "emotion": emotion,
        "frequency": frequency,
        "duration": max(0.0, float(step.get("duration", 0.3))),
        "pause_after_s": max(0.0, float(step.get("pause_after_s", 0.0))),
    }


def normalize_sound_chain(steps: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Normalize a sound chain definition."""

    return [normalize_sound_step(step) for step in steps]


def resolve_emotion_alias(name: str) -> str:
    """Expose alias lookup for UI and planner code."""

    normalized = str(name).strip().lower()
    return SOUND_ALIASES.get(normalized, normalized)
