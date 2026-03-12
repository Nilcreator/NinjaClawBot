from __future__ import annotations

from ninjaclawbot.expressions.policy import build_reply_expression, list_reply_states


def test_reply_policy_builds_greeting_expression() -> None:
    definition = build_reply_expression(text="Hello!", reply_state="greeting")

    assert definition["builtin"] == "greeting"
    assert definition["display"]["text"] == "Hello!"
    assert definition["reply_policy"]["reply_state"] == "greeting"


def test_reply_policy_uses_default_display_label_for_long_text() -> None:
    definition = build_reply_expression(
        text="I need to ask a much longer clarifying question now.",
        reply_state="asking_clarification",
    )

    assert definition["builtin"] == "confusing"
    assert definition["display"]["text"] == "?"


def test_reply_policy_lists_supported_states() -> None:
    states = list_reply_states()

    assert "greeting" in states
    assert "asking_clarification" in states
