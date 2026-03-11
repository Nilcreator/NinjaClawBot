from __future__ import annotations

from ninjaclawbot.assets import AssetStore
from ninjaclawbot.config import NinjaClawbotConfig
from ninjaclawbot.executor import ActionExecutor


class FakeRuntime:
    def __init__(self):
        class _Lock:
            def acquire(self):
                class _Context:
                    def __enter__(self_inner):
                        return None

                    def __exit__(self_inner, exc_type, exc, tb):
                        return False

                return _Context()

        self.execution_lock = _Lock()
        self.config = NinjaClawbotConfig()
        self.calls = []

    def health_check(self):
        self.calls.append(("health_check",))
        return {"servo": {"available": True}}

    def move_servos(self, targets, speed_mode="M", easing="ease_in_out_cubic"):
        self.calls.append(("move_servos", targets, speed_mode, easing))
        return True

    def display_text(self, text, **kwargs):
        self.calls.append(("display_text", text, kwargs))

    def play_sound(self, **kwargs):
        self.calls.append(("play_sound", kwargs))

    def read_distance(self):
        self.calls.append(("read_distance",))
        return {"distance_mm": 120}

    def stop_all(self):
        self.calls.append(("stop_all",))


def test_executor_runs_movement_asset_from_store(tmp_path) -> None:
    runtime = FakeRuntime()
    store = AssetStore(NinjaClawbotConfig(root_dir=tmp_path))
    store.save_movement({"name": "wave", "steps": [{"targets": {"gpio12": 25}, "speed_mode": "F"}]})
    executor = ActionExecutor(runtime=runtime, asset_store=store)

    result = executor.execute({"action": "perform_movement", "parameters": {"name": "wave"}})

    assert result.status.value == "success"
    assert runtime.calls[0][0] == "move_servos"
    assert result.data["name"] == "wave"


def test_executor_rejects_invalid_request() -> None:
    executor = ActionExecutor(runtime=FakeRuntime())
    result = executor.execute({"action": "move_servos", "parameters": {}})

    assert result.status.value == "rejected"
    assert result.error_code == "ACTION_VALIDATION_ERROR"
