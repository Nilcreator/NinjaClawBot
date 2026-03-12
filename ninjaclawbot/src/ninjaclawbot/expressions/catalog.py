"""Built-in face and sound expression catalog aligned with NinjaRobotV5."""

from __future__ import annotations

from copy import deepcopy
from typing import Any

FACE_EXPRESSIONS: tuple[str, ...] = (
    "idle",
    "happy",
    "laughing",
    "sad",
    "cry",
    "angry",
    "surprising",
    "sleepy",
    "speaking",
    "shy",
    "scary",
    "exciting",
    "confusing",
    "greeting",
    "listening",
    "thinking",
    "curious",
    "success",
    "warning",
    "error",
)

FACE_ALIASES: dict[str, str] = {
    "embarrassing": "shy",
    "embarrassed": "shy",
    "excited": "exciting",
    "surprised": "surprising",
    "crying": "cry",
}

SOUND_EMOTIONS: tuple[str, ...] = (
    "idle",
    "happy",
    "laughing",
    "sad",
    "cry",
    "angry",
    "surprising",
    "sleepy",
    "speaking",
    "shy",
    "embarrassing",
    "scary",
    "exciting",
    "confusing",
)

SOUND_ALIASES: dict[str, str] = {
    "greeting": "happy",
    "success": "exciting",
    "listening": "idle",
    "thinking": "confusing",
    "curious": "confusing",
    "warning": "surprising",
    "error": "sad",
    "surprised": "surprising",
    "excited": "exciting",
    "crying": "cry",
}

BUILTIN_EXPRESSIONS: dict[str, dict[str, Any]] = {
    "idle": {
        "name": "idle",
        "description": "Default waiting expression based on the legacy idle face.",
        "face_chain": [{"expression": "idle", "duration": 2.5}],
        "sound_chain": [],
        "idle_reset": False,
        "preview_duration": 2.5,
    },
    "greeting": {
        "name": "greeting",
        "description": "Warm greeting with a bright smile and happy tone.",
        "face_chain": [
            {"expression": "greeting", "duration": 1.0},
            {"expression": "happy", "duration": 1.1},
        ],
        "sound_chain": [{"emotion": "happy", "duration": 0.3}],
        "idle_reset": True,
        "preview_duration": 2.1,
    },
    "happy": {
        "name": "happy",
        "description": "Steady cheerful face and the legacy happy melody.",
        "face_chain": [{"expression": "happy", "duration": 1.8}],
        "sound_chain": [{"emotion": "happy", "duration": 0.3}],
        "idle_reset": True,
        "preview_duration": 1.8,
    },
    "laughing": {
        "name": "laughing",
        "description": "Animated laughing face with the legacy laughing melody.",
        "face_chain": [{"expression": "laughing", "duration": 1.8}],
        "sound_chain": [{"emotion": "laughing", "duration": 0.45}],
        "idle_reset": True,
        "preview_duration": 1.8,
    },
    "speaking": {
        "name": "speaking",
        "description": "Talking face for spoken-style replies.",
        "face_chain": [{"expression": "speaking", "duration": 1.6}],
        "sound_chain": [{"emotion": "speaking", "duration": 0.45}],
        "idle_reset": True,
        "preview_duration": 1.6,
    },
    "listening": {
        "name": "listening",
        "description": "Soft attentive face while the robot listens.",
        "face_chain": [{"expression": "listening", "duration": 1.8}],
        "sound_chain": [],
        "idle_reset": False,
        "preview_duration": 1.8,
    },
    "thinking": {
        "name": "thinking",
        "description": "Thinking expression derived from the legacy confusing face.",
        "face_chain": [{"expression": "thinking", "duration": 1.8}],
        "sound_chain": [{"emotion": "confusing", "duration": 0.4}],
        "idle_reset": True,
        "preview_duration": 1.8,
    },
    "curious": {
        "name": "curious",
        "description": "Curious expression for follow-up questions or discovery.",
        "face_chain": [{"expression": "curious", "duration": 1.8}],
        "sound_chain": [{"emotion": "confusing", "duration": 0.4}],
        "idle_reset": True,
        "preview_duration": 1.8,
    },
    "confusing": {
        "name": "confusing",
        "description": "Legacy confusing face and sound for uncertainty or questions.",
        "face_chain": [{"expression": "confusing", "duration": 1.8}],
        "sound_chain": [{"emotion": "confusing", "duration": 0.4}],
        "idle_reset": True,
        "preview_duration": 1.8,
    },
    "exciting": {
        "name": "exciting",
        "description": "Energetic star-eyed excitement.",
        "face_chain": [{"expression": "exciting", "duration": 1.8}],
        "sound_chain": [{"emotion": "exciting", "duration": 0.45}],
        "idle_reset": True,
        "preview_duration": 1.8,
    },
    "success": {
        "name": "success",
        "description": "Proud successful confirmation expression.",
        "face_chain": [
            {"expression": "success", "duration": 0.9},
            {"expression": "happy", "duration": 0.9},
        ],
        "sound_chain": [{"emotion": "exciting", "duration": 0.45}],
        "idle_reset": True,
        "preview_duration": 1.8,
    },
    "surprising": {
        "name": "surprising",
        "description": "Wide-eyed surprise from the legacy surprised design.",
        "face_chain": [{"expression": "surprising", "duration": 1.5}],
        "sound_chain": [{"emotion": "surprising", "duration": 0.35}],
        "idle_reset": True,
        "preview_duration": 1.5,
    },
    "warning": {
        "name": "warning",
        "description": "Alert warning expression for caution and attention.",
        "face_chain": [
            {"expression": "warning", "duration": 0.8},
            {"expression": "surprising", "duration": 0.8},
        ],
        "sound_chain": [{"emotion": "surprising", "duration": 0.35}],
        "idle_reset": True,
        "preview_duration": 1.6,
    },
    "sad": {
        "name": "sad",
        "description": "Legacy sad face with soft downward mouth.",
        "face_chain": [{"expression": "sad", "duration": 1.8}],
        "sound_chain": [{"emotion": "sad", "duration": 0.35}],
        "idle_reset": True,
        "preview_duration": 1.8,
    },
    "cry": {
        "name": "cry",
        "description": "Legacy crying face with animated tears.",
        "face_chain": [{"expression": "cry", "duration": 1.8}],
        "sound_chain": [{"emotion": "cry", "duration": 0.5}],
        "idle_reset": True,
        "preview_duration": 1.8,
    },
    "angry": {
        "name": "angry",
        "description": "Shaking angry expression from the legacy design.",
        "face_chain": [{"expression": "angry", "duration": 1.6}],
        "sound_chain": [{"emotion": "angry", "duration": 0.35}],
        "idle_reset": True,
        "preview_duration": 1.6,
    },
    "error": {
        "name": "error",
        "description": "Strong failure expression for errors or unavailable actions.",
        "face_chain": [
            {"expression": "error", "duration": 0.8},
            {"expression": "sad", "duration": 0.8},
        ],
        "sound_chain": [{"emotion": "sad", "duration": 0.35}],
        "idle_reset": True,
        "preview_duration": 1.6,
    },
    "shy": {
        "name": "shy",
        "description": "Blushing shy expression and soft melody.",
        "face_chain": [{"expression": "shy", "duration": 1.8}],
        "sound_chain": [{"emotion": "shy", "duration": 0.35}],
        "idle_reset": True,
        "preview_duration": 1.8,
    },
    "sleepy": {
        "name": "sleepy",
        "description": "Relaxed sleepy face and drowsy sound.",
        "face_chain": [{"expression": "sleepy", "duration": 1.8}],
        "sound_chain": [{"emotion": "sleepy", "duration": 0.4}],
        "idle_reset": True,
        "preview_duration": 1.8,
    },
    "scary": {
        "name": "scary",
        "description": "High-tension scary face with trembling pupils.",
        "face_chain": [{"expression": "scary", "duration": 1.5}],
        "sound_chain": [{"emotion": "scary", "duration": 0.4}],
        "idle_reset": True,
        "preview_duration": 1.5,
    },
}


def normalize_face_expression(name: str) -> str:
    """Return a canonical built-in face name."""

    normalized = str(name).strip().lower()
    if not normalized:
        raise ValueError("Face expression name must be a non-empty string.")
    normalized = FACE_ALIASES.get(normalized, normalized)
    if normalized not in FACE_EXPRESSIONS:
        supported = ", ".join(FACE_EXPRESSIONS)
        raise ValueError(
            f"Unsupported face expression '{name}'. Supported expressions: {supported}."
        )
    return normalized


def normalize_sound_emotion(name: str) -> str:
    """Return a canonical buzzer emotion name."""

    normalized = str(name).strip().lower()
    if not normalized:
        raise ValueError("Sound emotion name must be a non-empty string.")
    normalized = SOUND_ALIASES.get(normalized, normalized)
    if normalized not in SOUND_EMOTIONS:
        supported = ", ".join(SOUND_EMOTIONS)
        raise ValueError(f"Unsupported sound emotion '{name}'. Supported emotions: {supported}.")
    return normalized


def list_builtin_expressions() -> list[str]:
    """Return the built-in expression names in a stable order."""

    return list(BUILTIN_EXPRESSIONS)


def get_builtin_expression(name: str) -> dict[str, Any]:
    """Return a deep copy of a built-in expression definition."""

    normalized = str(name).strip().lower()
    normalized = FACE_ALIASES.get(normalized, normalized)
    if normalized not in BUILTIN_EXPRESSIONS:
        supported = ", ".join(BUILTIN_EXPRESSIONS)
        raise ValueError(
            f"Unsupported built-in expression '{name}'. Supported expressions: {supported}."
        )
    return deepcopy(BUILTIN_EXPRESSIONS[normalized])
