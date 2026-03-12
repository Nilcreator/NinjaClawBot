"""Reply-emotion policy for OpenClaw-facing NinjaClawBot actions."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True, slots=True)
class ReplyPolicy:
    """Declarative mapping from reply state to built-in expression behavior."""

    reply_state: str
    builtin: str
    display_label: str
    idle_reset: bool = True


_REPLY_POLICIES: dict[str, ReplyPolicy] = {
    "greeting": ReplyPolicy("greeting", "greeting", "HELLO"),
    "confirmation": ReplyPolicy("confirmation", "happy", "OK"),
    "success": ReplyPolicy("success", "success", "DONE"),
    "speaking": ReplyPolicy("speaking", "speaking", ""),
    "listening": ReplyPolicy("listening", "listening", "LISTEN", idle_reset=False),
    "thinking": ReplyPolicy("thinking", "thinking", "...", idle_reset=False),
    "confusing": ReplyPolicy("confusing", "confusing", "?"),
    "asking_clarification": ReplyPolicy("asking_clarification", "confusing", "?"),
    "cannot_answer": ReplyPolicy("cannot_answer", "confusing", "?"),
    "warning": ReplyPolicy("warning", "warning", "WAIT"),
    "error": ReplyPolicy("error", "error", "ERROR"),
    "sad": ReplyPolicy("sad", "sad", "SORRY"),
    "sleepy": ReplyPolicy("sleepy", "sleepy", "Zzz"),
    "curious": ReplyPolicy("curious", "curious", "HMM"),
}

_REPLY_ALIASES: dict[str, str] = {
    "answer": "speaking",
    "ask": "asking_clarification",
    "clarification": "asking_clarification",
    "clarify": "asking_clarification",
    "complete": "success",
    "completed": "success",
    "done": "success",
    "fail": "error",
    "failure": "error",
    "goodbye": "sad",
    "greet": "greeting",
    "hello": "greeting",
    "neutral": "speaking",
    "question": "asking_clarification",
    "reply": "speaking",
    "uncertain": "confusing",
}


def list_reply_states() -> list[str]:
    """Return the supported reply states for machine callers."""

    return sorted(_REPLY_POLICIES)


def normalize_reply_state(name: Any) -> str:
    """Normalize and validate a reply state name."""

    normalized = str(name).strip().lower()
    if not normalized:
        raise ValueError("reply_state must be a non-empty string.")
    normalized = _REPLY_ALIASES.get(normalized, normalized)
    if normalized not in _REPLY_POLICIES:
        supported = ", ".join(list_reply_states())
        raise ValueError(f"Unsupported reply_state '{name}'. Supported states: {supported}.")
    return normalized


def get_reply_policy(name: Any) -> ReplyPolicy:
    """Return the canonical reply policy for a given state."""

    return _REPLY_POLICIES[normalize_reply_state(name)]


def _derive_display_text(text: str, explicit_text: str | None, policy: ReplyPolicy) -> str:
    if explicit_text is not None:
        return explicit_text.strip()
    compact = " ".join(str(text).split())
    if compact and len(compact) <= 14:
        return compact
    return policy.display_label


def build_reply_expression(
    *,
    text: str,
    reply_state: Any,
    display_text: str | None = None,
    idle_reset: bool | None = None,
    duration: float = 3.0,
    language: str = "en",
    font_size: int = 32,
) -> dict[str, Any]:
    """Build an expression definition from a reply-state policy."""

    policy = get_reply_policy(reply_state)
    rendered_text = _derive_display_text(text, display_text, policy)
    expression: dict[str, Any] = {
        "name": f"reply_{policy.reply_state}",
        "builtin": policy.builtin,
        "display": {
            "text": rendered_text,
            "scroll": False,
            "duration": duration,
            "language": language,
            "font_size": font_size,
        },
        "idle_reset": policy.idle_reset if idle_reset is None else bool(idle_reset),
        "reply_policy": {
            "reply_state": policy.reply_state,
            "builtin": policy.builtin,
            "display_text": rendered_text,
        },
    }
    return expression
