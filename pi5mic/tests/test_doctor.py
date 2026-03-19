"""Tests for pi5mic doctor and install commands."""

from __future__ import annotations

import importlib
from pathlib import Path

from click.testing import CliRunner

from pi5mic.__main__ import cli

doctor_module = importlib.import_module("pi5mic.cli.doctor")
install_cmd_module = importlib.import_module("pi5mic.cli.install_cmd")


def test_doctor_passes_for_valid_whisper_configuration(monkeypatch, tmp_path) -> None:
    runner = CliRunner()
    config_path = tmp_path / "mic.json"
    config_path.write_text(
        """
{
  "stt": {
    "selected": "whisper_cpp",
    "whisper_cpp": {
      "command": "/usr/local/bin/whisper-cli",
      "model_path": "/models/ggml-base.bin"
    }
  }
}
""".strip(),
        encoding="utf-8",
    )
    monkeypatch.setattr(doctor_module, "list_input_devices", lambda: [object()])
    monkeypatch.setattr(
        doctor_module,
        "resolve_whisper_cpp_command",
        lambda command: Path("/usr/local/bin/whisper-cli"),
    )
    monkeypatch.setattr(
        doctor_module,
        "resolve_model_path",
        lambda model_path: Path("/models/ggml-base.bin"),
    )

    result = runner.invoke(cli, ["--config-file", str(config_path), "doctor"])

    assert result.exit_code == 0, result.output
    assert "pi5mic doctor passed" in result.output


def test_install_whispercpp_saves_detected_paths(monkeypatch, tmp_path) -> None:
    runner = CliRunner()
    config_path = tmp_path / "mic.json"
    model_path = tmp_path / "ggml-base.bin"
    model_path.write_text("", encoding="utf-8")

    monkeypatch.setattr(
        install_cmd_module,
        "find_whisper_cpp_command",
        lambda command=None: Path("/usr/local/bin/whisper-cli"),
    )
    monkeypatch.setattr(
        install_cmd_module,
        "resolve_model_path",
        lambda model_path: Path(model_path),
    )

    result = runner.invoke(
        cli,
        [
            "--config-file",
            str(config_path),
            "install",
            "whispercpp",
            "--model-path",
            str(model_path),
        ],
    )

    assert result.exit_code == 0, result.output
    saved = config_path.read_text(encoding="utf-8")
    assert "/usr/local/bin/whisper-cli" in saved
    assert str(model_path) in saved
