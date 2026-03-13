from __future__ import annotations

from types import SimpleNamespace

from PIL import Image

from ninjaclawbot.expressions.catalog import get_builtin_expression, list_builtin_expressions
from ninjaclawbot.expressions.faces import AnimatedFaceEngine
from ninjaclawbot.expressions.player import ExpressionPlayer
from ninjaclawbot.expressions.sounds import normalize_sound_chain


def test_builtin_expression_catalog_exposes_stage1_faces() -> None:
    names = list_builtin_expressions()

    assert "idle" in names
    assert "greeting" in names
    assert get_builtin_expression("greeting")["face_chain"][0]["expression"] == "greeting"


def test_animated_face_engine_renders_v5_compatible_frame() -> None:
    display = SimpleNamespace(width=240, height=240, show_image=lambda image: None)
    engine = AnimatedFaceEngine(display)

    image = engine.render_frame("confusing", 0.75)

    assert isinstance(image, Image.Image)
    assert image.size == (240, 240)


def test_normalize_sound_chain_resolves_aliases() -> None:
    chain = normalize_sound_chain([{"emotion": "success", "duration": 0.25}])

    assert chain == [
        {"emotion": "exciting", "frequency": None, "duration": 0.25, "pause_after_s": 0.0}
    ]


class _RecordingDisplay:
    def __init__(self, events: list[str]) -> None:
        self.events = events

    def prewarm(self) -> None:
        self.events.append("display.prewarm")

    def show_image(self, _image) -> None:
        self.events.append("display.show_image")

    def show_text(self, text: str, **_kwargs) -> None:
        self.events.append(f"display.show_text:{text}")

    def close(self) -> None:
        self.events.append("display.close")


class _RecordingBuzzer:
    def __init__(self, events: list[str]) -> None:
        self.events = events

    def play(self, *, emotion=None, frequency=None, duration=0.3, wait=False):
        self.events.append(
            f"buzzer.play:{emotion or frequency}:{duration}:{'wait' if wait else 'nowait'}"
        )
        return float(duration)


class _FakeEngine:
    def __init__(self, events: list[str]) -> None:
        self.events = events
        self.active_expression = None

    def render_frame(self, expression: str, _t: float):
        self.events.append(f"engine.render_frame:{expression}")
        return Image.new("RGB", (240, 240), "black")

    def play(self, expression: str, duration_s: float = 3.0) -> None:
        self.active_expression = expression
        self.events.append(f"engine.play:{expression}:{duration_s}")

    def wait(self, timeout=None) -> None:
        self.events.append(f"engine.wait:{timeout}")

    def set_idle(self) -> None:
        self.active_expression = "idle"
        self.events.append("engine.set_idle")

    def stop(self) -> None:
        self.events.append("engine.stop")

    def close(self) -> None:
        self.events.append("engine.close")


class _ImmediateThread:
    def __init__(self, target=None, args=(), kwargs=None, daemon=None) -> None:
        self._target = target
        self._args = args
        self._kwargs = kwargs or {}
        self._alive = False

    def start(self) -> None:
        self._alive = True
        if self._target is not None:
            self._target(*self._args, **self._kwargs)
        self._alive = False

    def join(self, timeout=None) -> None:
        return None

    def is_alive(self) -> bool:
        return self._alive


def test_expression_player_prewarms_and_latches_first_frame_before_sound(monkeypatch) -> None:
    events: list[str] = []
    player = ExpressionPlayer(_RecordingDisplay(events), _RecordingBuzzer(events))
    engine = _FakeEngine(events)

    monkeypatch.setattr(player, "_engine_or_create", lambda: engine)
    monkeypatch.setattr("ninjaclawbot.expressions.player.threading.Thread", _ImmediateThread)

    result = player.perform({"builtin": "greeting"})

    assert result["builtin"] == "greeting"
    assert events[:4] == [
        "display.prewarm",
        "engine.render_frame:greeting",
        "display.show_image",
        "buzzer.play:happy:0.3:wait",
    ]


def test_expression_player_prewarms_text_only_expression_before_sound(monkeypatch) -> None:
    events: list[str] = []
    player = ExpressionPlayer(_RecordingDisplay(events), _RecordingBuzzer(events))

    monkeypatch.setattr("ninjaclawbot.expressions.player.threading.Thread", _ImmediateThread)
    monkeypatch.setattr("ninjaclawbot.expressions.player.time.sleep", lambda _seconds: None)

    result = player.perform(
        {
            "name": "hello",
            "display": {"text": "HELLO", "duration": 0.1},
            "sound": {"emotion": "happy", "duration": 0.3},
        }
    )

    assert result["display_text"] == "HELLO"
    assert events[:3] == [
        "display.prewarm",
        "display.show_text:HELLO",
        "buzzer.play:happy:0.3:wait",
    ]


def test_expression_player_can_set_persistent_presence(monkeypatch) -> None:
    events: list[str] = []
    player = ExpressionPlayer(_RecordingDisplay(events), _RecordingBuzzer(events))
    engine = _FakeEngine(events)

    monkeypatch.setattr(player, "_engine_or_create", lambda: engine)

    result = player.set_presence("thinking")

    assert result["presence_mode"] == "thinking"
    assert events[:4] == [
        "display.prewarm",
        "engine.render_frame:thinking",
        "display.show_image",
        "buzzer.play:confusing:0.4:wait",
    ]
    assert events[-1] == "engine.play:thinking:inf"
