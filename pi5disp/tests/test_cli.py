"""CLI smoke tests for pi5disp."""

from __future__ import annotations

from click.testing import CliRunner

from pi5disp.__main__ import cli


def test_cli_help_shows_commands() -> None:
    """Help output should include the migrated commands."""
    runner = CliRunner()
    result = runner.invoke(cli, ["--help"])
    assert result.exit_code == 0
    assert "display-tool" in result.output
    assert "brightness" in result.output
    assert "config" in result.output


def test_config_show_works() -> None:
    """Config show should print the saved display settings."""
    runner = CliRunner()
    result = runner.invoke(cli, ["config", "show"])
    assert result.exit_code == 0
    assert "Display Configuration" in result.output
