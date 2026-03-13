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
        self.active_expression = None

    def health_check(self):
        self.calls.append(("health_check",))
        return {"servo": {"available": True}}

    def move_servos(
        self,
        targets,
        speed_mode="M",
        per_servo_speeds=None,
        easing="ease_in_out_cubic",
        force=True,
    ):
        self.calls.append(("move_servos", targets, speed_mode, per_servo_speeds, easing, force))
        return True

    def display_text(self, text, **kwargs):
        self.calls.append(("display_text", text, kwargs))

    def play_sound(self, **kwargs):
        self.calls.append(("play_sound", kwargs))
        return float(kwargs.get("duration", 0.0))

    def perform_expression(self, definition):
        self.calls.append(("perform_expression", definition))
        self.active_expression = "idle" if bool(definition.get("idle_reset", False)) else None
        return {
            "name": definition.get("name"),
            "builtin": definition.get("builtin") or None,
            "display_text": (definition.get("display", {}) or {}).get("text"),
            "face_chain": definition.get("face_chain", []),
            "sound_chain": definition.get("sound_chain", []),
            "waited_for_s": float((definition.get("sound", {}) or {}).get("duration", 0.0)),
            "idle_reset": bool(definition.get("idle_reset", False)),
        }

    def read_distance(self):
        self.calls.append(("read_distance",))
        return {"distance_mm": 120}

    def stop_all(self):
        self.calls.append(("stop_all",))

    def set_idle_expression(self):
        self.active_expression = "idle"
        self.calls.append(("set_idle_expression",))
        return {
            "name": "idle",
            "builtin": "idle",
            "persistent": True,
            "waited_for_s": 0.0,
            "active_expression": "idle",
            "presence_mode": "idle",
        }

    def set_presence_mode(self, mode: str):
        self.active_expression = mode
        self.calls.append(("set_presence_mode", mode))
        return {
            "name": mode,
            "builtin": mode,
            "persistent": True,
            "waited_for_s": 0.0,
            "active_expression": mode,
            "presence_mode": mode,
        }

    def stop_expression(self):
        self.active_expression = None
        self.calls.append(("stop_expression",))

    def list_builtin_expressions(self):
        self.calls.append(("list_builtin_expressions",))
        return ["idle", "greeting", "happy"]

    def shutdown_sequence(self):
        self.active_expression = None
        self.calls.append(("shutdown_sequence",))
        return {"closed": True, "display_powered_down": True}


def test_executor_runs_movement_asset_from_store(tmp_path) -> None:
    runtime = FakeRuntime()
    store = AssetStore(NinjaClawbotConfig(root_dir=tmp_path))
    store.save_movement(
        {
            "name": "wave",
            "steps": [
                {
                    "speed": "F",
                    "moves": {"gpio12": 25},
                    "per_servo_speeds": {"gpio12": "S"},
                }
            ],
        }
    )
    executor = ActionExecutor(runtime=runtime, asset_store=store)

    result = executor.execute({"action": "perform_movement", "parameters": {"name": "wave"}})

    assert result.status.value == "success"
    assert runtime.calls[0][0] == "move_servos"
    assert runtime.calls[0][3] == {"gpio12": "S"}
    assert result.data["name"] == "wave"


def test_executor_rejects_invalid_request() -> None:
    executor = ActionExecutor(runtime=FakeRuntime())
    result = executor.execute({"action": "move_servos", "parameters": {}})

    assert result.status.value == "rejected"
    assert result.error_code == "ACTION_VALIDATION_ERROR"


def test_executor_waits_for_expression_sound(tmp_path) -> None:
    runtime = FakeRuntime()
    store = AssetStore(NinjaClawbotConfig(root_dir=tmp_path))
    store.save_expression(
        {
            "name": "hello",
            "display": {"text": "Hello", "duration": 1.0},
            "sound": {"emotion": "happy", "duration": 0.3},
        }
    )
    executor = ActionExecutor(runtime=runtime, asset_store=store)

    result = executor.execute({"action": "perform_expression", "parameters": {"name": "hello"}})

    assert result.status.value == "success"
    assert runtime.calls[0][0] == "perform_expression"
    assert runtime.calls[0][1]["display"]["text"] == "Hello"
    assert runtime.calls[0][1]["sound"]["emotion"] == "happy"
    assert result.data["waited_for_s"] == 0.3


def test_executor_builds_reply_expression_from_policy() -> None:
    runtime = FakeRuntime()
    executor = ActionExecutor(runtime=runtime)

    result = executor.execute(
        {
            "action": "perform_reply",
            "parameters": {"text": "Hello!", "reply_state": "greeting"},
        }
    )

    assert result.status.value == "success"
    assert runtime.calls[0][0] == "perform_expression"
    assert runtime.calls[0][1]["builtin"] == "greeting"
    assert runtime.calls[0][1]["display"]["text"] == "Hello!"
    assert result.data["reply_state"] == "greeting"


def test_executor_lists_capabilities(tmp_path) -> None:
    runtime = FakeRuntime()
    store = AssetStore(NinjaClawbotConfig(root_dir=tmp_path))
    store.save_movement({"name": "wave", "steps": [{"speed": "F", "moves": {"gpio12": 20}}]})
    store.save_expression({"name": "hello", "display": {"text": "HELLO"}})
    executor = ActionExecutor(runtime=runtime, asset_store=store)

    result = executor.execute({"action": "list_capabilities"})

    assert result.status.value == "success"
    assert "perform_reply" in result.data["actions"]
    assert "greeting" in result.data["reply_states"]
    assert result.data["assets"]["movements"] == ["wave"]
    assert result.data["assets"]["expressions"] == ["hello"]
    assert result.data["built_in_expressions"] == ["idle", "greeting", "happy"]


def test_executor_can_set_idle_and_stop_expression() -> None:
    runtime = FakeRuntime()
    executor = ActionExecutor(runtime=runtime)

    idle_result = executor.execute({"action": "set_idle"})
    stop_result = executor.execute({"action": "stop_expression"})

    assert idle_result.status.value == "success"
    assert stop_result.status.value == "success"
    assert runtime.calls == [("set_idle_expression",), ("stop_expression",)]


def test_executor_can_set_presence_mode() -> None:
    runtime = FakeRuntime()
    executor = ActionExecutor(runtime=runtime)

    result = executor.execute({"action": "set_presence_mode", "parameters": {"mode": "thinking"}})

    assert result.status.value == "success"
    assert runtime.calls == [("set_presence_mode", "thinking")]
    assert result.data["presence_mode"] == "thinking"


def test_executor_can_run_shutdown_sequence() -> None:
    runtime = FakeRuntime()
    executor = ActionExecutor(runtime=runtime)

    result = executor.execute({"action": "shutdown_sequence"})

    assert result.status.value == "success"
    assert runtime.calls == [("shutdown_sequence",)]
    assert result.data["closed"] is True


def test_executor_runs_builtin_expression_without_saved_asset() -> None:
    runtime = FakeRuntime()
    executor = ActionExecutor(runtime=runtime)

    result = executor.execute({"action": "perform_expression", "parameters": {"name": "idle"}})

    assert result.status.value == "success"
    assert runtime.calls[0] == ("perform_expression", {"name": "idle", "builtin": "idle"})
    assert result.data["builtin"] == "idle"


def test_executor_prefers_saved_expression_over_builtin_name(tmp_path) -> None:
    runtime = FakeRuntime()
    store = AssetStore(NinjaClawbotConfig(root_dir=tmp_path))
    store.save_expression(
        {
            "name": "happy",
            "display": {"text": "Saved wins"},
            "sound": {"emotion": "happy", "duration": 0.3},
        }
    )
    executor = ActionExecutor(runtime=runtime, asset_store=store)

    result = executor.execute({"action": "perform_expression", "parameters": {"name": "happy"}})

    assert result.status.value == "success"
    assert runtime.calls[0][0] == "perform_expression"
    assert runtime.calls[0][1]["display"]["text"] == "Saved wins"
    assert runtime.calls[0][1]["builtin"] == ""


def test_executor_rejects_unknown_expression_name() -> None:
    runtime = FakeRuntime()
    executor = ActionExecutor(runtime=runtime)

    result = executor.execute(
        {"action": "perform_expression", "parameters": {"name": "does-not-exist"}}
    )

    assert result.status.value == "failed"
    assert result.error_code == "ACTIONVALIDATIONERROR"
    assert "Unknown expression asset or built-in expression" in str(result.error_message)


def test_executor_waits_for_play_sound_action() -> None:
    runtime = FakeRuntime()
    executor = ActionExecutor(runtime=runtime)

    result = executor.execute(
        {"action": "play_sound", "parameters": {"emotion": "happy", "duration": 0.3}}
    )

    assert result.status.value == "success"
    assert runtime.calls[0] == (
        "play_sound",
        {"emotion": "happy", "frequency": None, "duration": 0.3, "wait": True},
    )
