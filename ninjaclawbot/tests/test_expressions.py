from __future__ import annotations

from types import SimpleNamespace

from PIL import Image

from ninjaclawbot.expressions.catalog import get_builtin_expression, list_builtin_expressions
from ninjaclawbot.expressions.faces import AnimatedFaceEngine
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
