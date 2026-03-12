"""Built-in expression catalogs and playback helpers for NinjaClawBot."""

from .catalog import (
    BUILTIN_EXPRESSIONS,
    FACE_ALIASES,
    FACE_EXPRESSIONS,
    SOUND_ALIASES,
    SOUND_EMOTIONS,
    get_builtin_expression,
    list_builtin_expressions,
    normalize_face_expression,
    normalize_sound_emotion,
)
from .faces import AnimatedFaceEngine
from .player import ExpressionPlayer
from .sounds import normalize_sound_chain, normalize_sound_step, resolve_emotion_alias

__all__ = [
    "AnimatedFaceEngine",
    "BUILTIN_EXPRESSIONS",
    "ExpressionPlayer",
    "FACE_ALIASES",
    "FACE_EXPRESSIONS",
    "SOUND_ALIASES",
    "SOUND_EMOTIONS",
    "get_builtin_expression",
    "list_builtin_expressions",
    "normalize_face_expression",
    "normalize_sound_chain",
    "normalize_sound_emotion",
    "normalize_sound_step",
    "resolve_emotion_alias",
]
