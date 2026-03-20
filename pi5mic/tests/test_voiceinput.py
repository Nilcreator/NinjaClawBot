"""Tests for always-on voice input helpers."""

from __future__ import annotations

import copy
import importlib

import pytest

from pi5mic.config.config_manager import DEFAULT_CONFIG
from pi5mic.core.voiceinput import (
    build_voiceinput_runtime_paths,
    normalize_voiceinput_config,
    read_voiceinput_state,
    update_voiceinput_state,
    validate_voiceinput_readiness,
)
from pi5mic.errors import WakeWordError

voiceinput_module = importlib.import_module("pi5mic.core.voiceinput")


def _enabled_voiceinput_config() -> dict:
    config = copy.deepcopy(DEFAULT_CONFIG)
    config["voiceinput"]["enabled"] = True
    config["wakeword"]["enabled"] = True
    config["wakeword"]["keyword"] = "picovoice"
    config["wakeword"]["keyword_path"] = None
    return config


def test_normalize_voiceinput_config_accepts_supported_values() -> None:
    config = _enabled_voiceinput_config()

    normalized = normalize_voiceinput_config(config)

    assert normalized["backend"] == "porcupine"
    assert normalized["keyword"] == "picovoice"
    assert normalized["session_strategy"] == "agent_main"


def test_read_voiceinput_state_marks_stale_process_as_stopped(tmp_path) -> None:
    paths = build_voiceinput_runtime_paths(tmp_path / "mic.json")
    update_voiceinput_state(
        paths,
        running=True,
        pid=999_999,
        mode="running",
        listener_state="listening",
    )

    state = read_voiceinput_state(paths)

    assert state["running"] is False
    assert state["mode"] == "stopped"
    assert state["pid"] is None


def test_validate_voiceinput_readiness_requires_pvporcupine(monkeypatch) -> None:
    config = _enabled_voiceinput_config()
    monkeypatch.setattr(voiceinput_module.importlib.util, "find_spec", lambda name: None)

    with pytest.raises(WakeWordError, match="pvporcupine"):
        validate_voiceinput_readiness(config)


def test_validate_voiceinput_readiness_returns_detector_details(monkeypatch) -> None:
    config = _enabled_voiceinput_config()

    class _FakeDetector:
        frame_length = 512
        sample_rate = 16_000

        def close(self) -> None:
            return None

    monkeypatch.setattr(voiceinput_module.importlib.util, "find_spec", lambda name: object())
    monkeypatch.setattr(
        voiceinput_module, "build_wakeword_detector", lambda config: _FakeDetector()
    )

    readiness = validate_voiceinput_readiness(config)

    assert readiness["detector_frame_length"] == 512
    assert readiness["detector_sample_rate"] == 16_000
    assert readiness["keyword"] == "picovoice"
