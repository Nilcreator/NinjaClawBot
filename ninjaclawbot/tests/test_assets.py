from __future__ import annotations

from pathlib import Path

from ninjaclawbot.assets import AssetStore
from ninjaclawbot.config import NinjaClawbotConfig


def test_asset_store_round_trips_movement_and_expression_assets(tmp_path: Path) -> None:
    store = AssetStore(NinjaClawbotConfig(root_dir=tmp_path))

    store.save_movement(
        {
            "name": "wave",
            "steps": [{"targets": {"gpio12": 20}, "speed_mode": "S", "pause_after_ms": 100}],
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
    assert store.load_movement("wave")["steps"][0]["targets"]["gpio12"] == 20.0
    assert store.list_assets("expressions") == ["happy"]
    assert store.load_expression("happy")["sound"]["emotion"] == "happy"
