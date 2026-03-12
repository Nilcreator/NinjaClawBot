from __future__ import annotations

from pathlib import Path

from click.testing import CliRunner

from ninjaclawbot.__main__ import cli
from ninjaclawbot.assets import AssetStore
from ninjaclawbot.cli.common import extract_movement_data, parse_movement_command
from ninjaclawbot.config import NinjaClawbotConfig
from ninjaclawbot.results import ActionResult


class FakeServoInterface:
    def configured_endpoints(self) -> list[str]:
        return ["gpio12", "gpio13"]

    def current_angles(self) -> dict[str, float]:
        return {"gpio12": 0.0, "gpio13": 0.0}

    def center_all(self) -> bool:
        return True


class FakeRuntime:
    def __init__(self) -> None:
        self.servo = FakeServoInterface()
        self.closed = False
        self.expression_calls: list[tuple[str, object]] = []

    def close(self) -> None:
        self.closed = True

    def move_servos(self, *args, **kwargs) -> bool:
        return True

    def perform_expression(self, definition):
        self.expression_calls.append(("perform_expression", definition))
        return {"builtin": definition.get("builtin")}

    def set_idle_expression(self) -> None:
        self.expression_calls.append(("set_idle_expression", None))

    def stop_expression(self) -> None:
        self.expression_calls.append(("stop_expression", None))


class FakeExecutor:
    def __init__(self, root_dir: Path) -> None:
        self.runtime = FakeRuntime()
        self.asset_store = AssetStore(NinjaClawbotConfig(root_dir=root_dir))

    def execute(self, payload):
        return ActionResult.success(action=str(payload["action"]))


def test_parse_movement_command_supports_speed_prefix_aliases_and_per_servo_speeds() -> None:
    speed_mode, parsed = parse_movement_command("F_12:X/hat_pwm1:CF/gpio13:M")
    targets, per_servo_speeds = extract_movement_data(parsed)

    assert speed_mode == "F"
    assert targets == {"gpio12": 90.0, "hat_pwm1": 0.0, "gpio13": -90.0}
    assert per_servo_speeds == {"hat_pwm1": "F"}


def test_movement_tool_can_create_asset(tmp_path: Path, monkeypatch) -> None:
    runner = CliRunner()
    monkeypatch.setattr(
        "ninjaclawbot.cli.movement_tool.create_executor",
        lambda root_dir: FakeExecutor(Path(root_dir)),
    )
    result = runner.invoke(
        cli,
        ["--root-dir", str(tmp_path), "movement-tool"],
        input="2\nF_12:20/13:-20\n3\nwave\nFriendly wave\n7\n",
    )

    assert result.exit_code == 0
    movement = AssetStore(NinjaClawbotConfig(root_dir=tmp_path)).load_movement("wave")
    assert movement["steps"][0]["moves"]["gpio12"] == 20.0


def test_expression_tool_can_create_asset(tmp_path: Path, monkeypatch) -> None:
    runner = CliRunner()
    monkeypatch.setattr(
        "ninjaclawbot.cli.expression_tool.create_executor",
        lambda root_dir: FakeExecutor(Path(root_dir)),
    )
    result = runner.invoke(
        cli,
        ["--root-dir", str(tmp_path), "expression-tool"],
        input="4\nhappy\nHappy face\nhappy\nHello\nn\n3\nen\n32\nhappy\n\n0.3\n\nY\n10\n",
    )

    assert result.exit_code == 0
    expression = AssetStore(NinjaClawbotConfig(root_dir=tmp_path)).load_expression("happy")
    assert expression["display"]["text"] == "Hello"
    assert expression["builtin"] == "happy"
    assert expression["idle_reset"] is True


def test_expression_tool_can_preview_builtin_and_set_idle(tmp_path: Path, monkeypatch) -> None:
    runner = CliRunner()
    created: list[FakeExecutor] = []

    def factory(root_dir: Path) -> FakeExecutor:
        executor = FakeExecutor(Path(root_dir))
        created.append(executor)
        return executor

    monkeypatch.setattr("ninjaclawbot.cli.expression_tool.create_executor", factory)
    result = runner.invoke(
        cli,
        ["--root-dir", str(tmp_path), "expression-tool"],
        input="3\ngreeting\n7\n8\n10\n",
    )

    assert result.exit_code == 0
    assert len(created) == 1
    assert created[0].runtime.expression_calls == [
        ("perform_expression", {"builtin": "greeting"}),
        ("set_idle_expression", None),
        ("stop_expression", None),
    ]


def test_perform_expression_closes_executor_runtime(tmp_path: Path, monkeypatch) -> None:
    runner = CliRunner()
    created: list[FakeExecutor] = []

    def factory(root_dir: Path) -> FakeExecutor:
        executor = FakeExecutor(Path(root_dir))
        created.append(executor)
        return executor

    monkeypatch.setattr("ninjaclawbot.__main__.create_executor", factory)
    result = runner.invoke(
        cli,
        ["--root-dir", str(tmp_path), "perform-expression", "hello"],
    )

    assert result.exit_code == 0
    assert len(created) == 1
    assert created[0].runtime.closed is True
