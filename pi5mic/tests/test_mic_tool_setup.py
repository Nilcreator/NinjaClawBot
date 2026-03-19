"""Regression tests for mic-tool setup flows."""

from __future__ import annotations

import importlib
from pathlib import Path

from click.testing import CliRunner

from pi5mic.__main__ import cli
from pi5mic.errors import DeviceError

setup_cmd_module = importlib.import_module("pi5mic.cli.setup_cmd")


def test_mic_tool_setup_warns_instead_of_crashing_when_audio_backend_is_unavailable(
    monkeypatch,
    tmp_path,
) -> None:
    runner = CliRunner()
    monkeypatch.setattr(
        setup_cmd_module,
        "list_input_devices",
        lambda: (_ for _ in ()).throw(
            DeviceError("PortAudio library not found\nPortAudio is required for microphone access.")
        ),
    )
    monkeypatch.setattr(
        setup_cmd_module,
        "find_whisper_cpp_command",
        lambda command=None: Path("/usr/local/bin/whisper-cli"),
    )
    monkeypatch.setattr(setup_cmd_module, "build_stt_backend", lambda config: object())

    inputs = "\n".join(
        [
            "1",
            "standalone",
            "default",
            "whisper_cpp",
            "/usr/local/bin/whisper-cli",
            str(tmp_path / "ggml-base.bin"),
            "15",
            "6",
        ]
    )

    result = runner.invoke(
        cli,
        ["--config-file", str(tmp_path / "mic.json"), "mic-tool"],
        input=inputs,
    )

    assert result.exit_code == 0, result.output
    assert "WARNING: Could not list audio devices yet:" in result.output
    assert "Leaving pi5mic mic-tool." in result.output
