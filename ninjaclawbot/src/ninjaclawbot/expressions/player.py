"""Expression orchestration and idle policy for NinjaClawBot."""

from __future__ import annotations

import threading
import time
from copy import deepcopy
from typing import Any

from ninjaclawbot.expressions.catalog import (
    get_builtin_expression,
    list_builtin_expressions,
    normalize_sound_emotion,
)
from ninjaclawbot.expressions.faces import AnimatedFaceEngine
from ninjaclawbot.expressions.sounds import normalize_sound_chain, normalize_sound_step
from ninjaclawbot.presence import normalize_presence_mode


class ExpressionPlayer:
    """Own the animated face engine and buzzer/display orchestration."""

    def __init__(self, display: Any, buzzer: Any) -> None:
        self._display = display
        self._buzzer = buzzer
        self._engine: AnimatedFaceEngine | None = None
        self._idle_active = False

    @property
    def active_expression(self) -> str | None:
        if self._engine is None:
            return None
        return self._engine.active_expression

    def list_builtins(self) -> list[str]:
        return list_builtin_expressions()

    def resolve_definition(self, definition: dict[str, Any]) -> dict[str, Any]:
        builtin_name = str(definition.get("builtin", "")).strip()
        resolved: dict[str, Any]
        if builtin_name:
            resolved = get_builtin_expression(builtin_name)
        else:
            resolved = {
                "builtin": "",
                "face_chain": [],
                "sound_chain": [],
                "idle_reset": False,
                "description": "",
                "name": definition.get("name"),
            }

        resolved["name"] = definition.get("name", resolved.get("name"))
        resolved["description"] = str(
            definition.get("description", resolved.get("description", ""))
        ).strip()
        resolved["builtin"] = builtin_name or resolved.get("builtin", "")
        resolved["display"] = {
            "text": str((definition.get("display", {}) or {}).get("text", "")).strip(),
            "scroll": bool((definition.get("display", {}) or {}).get("scroll", False)),
            "duration": float((definition.get("display", {}) or {}).get("duration", 3.0)),
            "language": str((definition.get("display", {}) or {}).get("language", "en")),
            "font_size": int((definition.get("display", {}) or {}).get("font_size", 32)),
        }

        explicit_face_chain = definition.get("face_chain", []) or []
        if explicit_face_chain:
            resolved["face_chain"] = [
                {
                    "expression": str(step["expression"]),
                    "duration": float(step.get("duration", 1.5)),
                }
                for step in explicit_face_chain
            ]
        else:
            resolved["face_chain"] = deepcopy(resolved.get("face_chain", []))

        explicit_sound_chain = definition.get("sound_chain", []) or []
        if explicit_sound_chain:
            resolved["sound_chain"] = normalize_sound_chain(explicit_sound_chain)
        else:
            resolved["sound_chain"] = normalize_sound_chain(resolved.get("sound_chain", []))

        sound = dict(definition.get("sound", {}) or {})
        if sound.get("emotion") or sound.get("frequency") is not None:
            resolved["sound_chain"].append(normalize_sound_step(sound))

        resolved["idle_reset"] = bool(
            definition.get("idle_reset", resolved.get("idle_reset", False))
        )
        return resolved

    def perform(self, definition: dict[str, Any]) -> dict[str, Any]:
        resolved = self.resolve_definition(definition)
        self.stop()

        display = resolved["display"]
        self._display.prewarm()
        text_rendered = False

        if resolved["face_chain"]:
            first_expression = str(resolved["face_chain"][0]["expression"])
            first_frame = self._engine_or_create().render_frame(first_expression, 0.0)
            self._display.show_image(first_frame)
        elif display.get("text") and not bool(display.get("scroll", False)):
            self._display.show_text(
                display["text"],
                scroll=False,
                duration=float(display.get("duration", 3.0)),
                language=str(display.get("language", "en")),
                font_size=int(display.get("font_size", 32)),
            )
            text_rendered = True

        waited_for = 0.0
        sound_done = threading.Event()

        def run_sound_chain() -> None:
            nonlocal waited_for
            waited_for = self._play_sound_chain(resolved["sound_chain"])
            sound_done.set()

        sound_thread: threading.Thread | None = None
        if resolved["sound_chain"]:
            sound_thread = threading.Thread(target=run_sound_chain, daemon=True)
            sound_thread.start()
        else:
            sound_done.set()

        if resolved["face_chain"]:
            self._play_face_chain(resolved["face_chain"])

        if display.get("text") and not text_rendered:
            self._display.show_text(
                display["text"],
                scroll=bool(display.get("scroll", False)),
                duration=float(display.get("duration", 3.0)),
                language=str(display.get("language", "en")),
                font_size=int(display.get("font_size", 32)),
            )
            text_rendered = not bool(display.get("scroll", False))

        if text_rendered and display.get("duration", 0.0) > 0:
            time.sleep(float(display["duration"]))

        if sound_thread is not None:
            sound_thread.join()
        else:
            sound_done.wait(timeout=0.1)

        if resolved["idle_reset"]:
            self.set_idle()

        return {
            "name": resolved.get("name"),
            "builtin": resolved.get("builtin") or None,
            "display_text": display.get("text") or None,
            "face_chain": deepcopy(resolved["face_chain"]),
            "sound_chain": deepcopy(resolved["sound_chain"]),
            "waited_for_s": waited_for,
            "idle_reset": bool(resolved["idle_reset"]),
        }

    def preview_builtin(self, name: str) -> dict[str, Any]:
        return self.perform({"builtin": name})

    def set_idle(self) -> None:
        self.set_presence("idle", play_sound=False)

    def set_presence(self, name: str, *, play_sound: bool = True) -> dict[str, Any]:
        mode = normalize_presence_mode(name)
        resolved = self.resolve_definition({"builtin": mode, "idle_reset": False})
        self.stop()
        self._display.prewarm()

        waited_for = 0.0
        first_expression = mode
        if resolved["face_chain"]:
            first_expression = str(resolved["face_chain"][0]["expression"])
            first_frame = self._engine_or_create().render_frame(first_expression, 0.0)
            self._display.show_image(first_frame)
        elif resolved["display"].get("text"):
            self._display.show_text(
                str(resolved["display"]["text"]),
                scroll=False,
                duration=float(resolved["display"].get("duration", 3.0)),
                language=str(resolved["display"].get("language", "en")),
                font_size=int(resolved["display"].get("font_size", 32)),
            )

        if play_sound and resolved["sound_chain"]:
            waited_for = self._play_sound_chain(resolved["sound_chain"])

        self._idle_active = mode == "idle"
        self._engine_or_create().play(first_expression, float("inf"))
        return {
            "name": resolved.get("name"),
            "builtin": resolved.get("builtin") or None,
            "persistent": True,
            "waited_for_s": waited_for,
            "active_expression": first_expression,
            "presence_mode": mode,
        }

    def stop(self) -> None:
        self._idle_active = False
        if self._engine is not None:
            self._engine.stop()

    def close(self) -> None:
        self.stop()
        if self._engine is not None:
            self._engine.close()
            self._engine = None

    def _engine_or_create(self) -> AnimatedFaceEngine:
        if self._engine is None:
            self._engine = AnimatedFaceEngine(self._display)
        return self._engine

    def _play_face_chain(self, chain: list[dict[str, Any]]) -> None:
        engine = self._engine_or_create()
        for step in chain:
            duration = max(0.05, float(step.get("duration", 1.5)))
            engine.play(str(step["expression"]), duration)
            engine.wait(timeout=duration + 0.3)

    def _play_sound_chain(self, chain: list[dict[str, Any]]) -> float:
        total_wait = 0.0
        for step in chain:
            emotion = str(step.get("emotion", "")).strip()
            frequency = step.get("frequency")
            duration = float(step.get("duration", 0.3))
            if emotion:
                emotion = normalize_sound_emotion(emotion)
                total_wait += float(
                    self._buzzer.play(emotion=emotion, duration=duration, wait=True)
                )
            elif frequency is not None:
                total_wait += float(
                    self._buzzer.play(
                        frequency=int(frequency),
                        duration=duration,
                        wait=True,
                    )
                )
            pause_after = max(0.0, float(step.get("pause_after_s", 0.0)))
            if pause_after > 0:
                time.sleep(pause_after)
                total_wait += pause_after
        return total_wait
