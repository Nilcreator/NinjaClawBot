"""CLI smoke tests for pi5vl53l0x."""

from __future__ import annotations

from click.testing import CliRunner

from pi5vl53l0x.cli.sensor_tool import cli


def test_cli_help_shows_commands() -> None:
    """The main help output should expose the migrated commands."""
    runner = CliRunner()
    result = runner.invoke(cli, ["--help"])
    assert result.exit_code == 0
    assert "sensor-tool" in result.output
    assert "performance" in result.output


def test_config_show_works_with_defaults(tmp_path) -> None:
    """Config show should work even when the config file does not exist yet."""
    runner = CliRunner()
    config_path = tmp_path / "missing.json"
    result = runner.invoke(cli, ["-C", str(config_path), "config", "show"])
    assert result.exit_code == 0
    assert "Config file:" in result.output
