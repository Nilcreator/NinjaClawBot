from __future__ import annotations

from pathlib import Path

from click.testing import CliRunner

from ninjaclawbot.__main__ import cli
from ninjaclawbot.cli.common import parse_step_command


def test_parse_step_command_supports_speed_prefix_and_angle_aliases() -> None:
    speed_mode, targets = parse_step_command("F_gpio12:X/hat_pwm1:C/gpio13:M")

    assert speed_mode == "F"
    assert targets == {"gpio12": 90.0, "hat_pwm1": 0.0, "gpio13": -90.0}


def test_movement_tool_can_create_asset(tmp_path: Path) -> None:
    runner = CliRunner()
    result = runner.invoke(
        cli,
        ["--root-dir", str(tmp_path), "movement-tool"],
        input="2\nwave\nFriendly wave\nM_gpio12:20/hat_pwm1:0\n100\nn\n6\n",
    )

    assert result.exit_code == 0
    assert (tmp_path / "ninjaclawbot_data" / "movements" / "wave.json").exists()


def test_expression_tool_can_create_asset(tmp_path: Path) -> None:
    runner = CliRunner()
    result = runner.invoke(
        cli,
        ["--root-dir", str(tmp_path), "expression-tool"],
        input="2\nhappy\nHappy face\nHello\nn\n3\nen\n32\nhappy\n\n0.3\n6\n",
    )

    assert result.exit_code == 0
    assert (tmp_path / "ninjaclawbot_data" / "expressions" / "happy.json").exists()
