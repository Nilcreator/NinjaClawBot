from __future__ import annotations

from pathlib import Path

import pytest

from ninjaclawbot.assets import AssetStore
from ninjaclawbot.config import NinjaClawbotConfig
from ninjaclawbot.errors import ActionValidationError


def test_asset_store_round_trips_movement_and_expression_assets(tmp_path: Path) -> None:
    store = AssetStore(NinjaClawbotConfig(root_dir=tmp_path))

    store.save_movement(
        {
            "name": "wave",
            "steps": [
                {
                    "speed": "S",
                    "moves": {"gpio12": 20, 13: 0},
                    "per_servo_speeds": {"gpio12": "F"},
                    "pause_after_ms": 100,
                }
            ],
        }
    )
    store.save_expression(
        {
            "name": "happy",
            "display": {"text": "Hello"},
            "sound": {"emotion": "happy"},
        }
    )

    assert store.list_assets("movements") == ["wave"]
    movement = store.load_movement("wave")
    assert movement["steps"][0]["moves"]["gpio12"] == 20.0
    assert movement["steps"][0]["moves"]["gpio13"] == 0.0
    assert movement["steps"][0]["per_servo_speeds"]["gpio12"] == "F"
    assert store.list_assets("expressions") == ["happy"]
    assert store.load_expression("happy")["sound"]["emotion"] == "happy"


def test_asset_store_migrates_legacy_movement_step_keys(tmp_path: Path) -> None:
    store = AssetStore(NinjaClawbotConfig(root_dir=tmp_path))
    path = tmp_path / "ninjaclawbot_data" / "movements" / "legacy.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        ('{"name":"legacy","steps":[{"targets":{"12":30},"speed_mode":"F","pause_after_ms":50}]}'),
        encoding="utf-8",
    )

    movement = store.load_movement("legacy")

    assert movement["steps"][0]["speed"] == "F"
    assert movement["steps"][0]["moves"]["gpio12"] == 30.0


def test_asset_store_normalizes_builtin_expression_assets(tmp_path: Path) -> None:
    store = AssetStore(NinjaClawbotConfig(root_dir=tmp_path))

    store.save_expression(
        {
            "name": "hello",
            "builtin": "greeting",
            "display": {"text": "Hello there"},
            "face_chain": ["happy", {"expression": "speaking", "duration": 0.8}],
            "sound_chain": [{"emotion": "success", "duration": 0.25, "pause_after_s": 0.1}],
            "idle_reset": True,
        }
    )

    expression = store.load_expression("hello")

    assert expression["builtin"] == "greeting"
    assert expression["face_chain"][0]["expression"] == "happy"
    assert expression["face_chain"][1]["expression"] == "speaking"
    assert expression["sound_chain"][0]["emotion"] == "exciting"
    assert expression["idle_reset"] is True


def test_asset_store_rejects_unknown_builtin_expression(tmp_path: Path) -> None:
    store = AssetStore(NinjaClawbotConfig(root_dir=tmp_path))

    with pytest.raises(ActionValidationError, match="Unsupported built-in expression"):
        store.save_expression({"name": "bad", "builtin": "shrugging"})
