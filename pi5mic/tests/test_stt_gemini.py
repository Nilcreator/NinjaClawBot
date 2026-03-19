"""Tests for the Gemini STT backend."""

from __future__ import annotations

import sys
import types

import pytest

from pi5mic.errors import STTError
from pi5mic.stt.gemini import GeminiBackend


def test_gemini_backend_requires_credentials(monkeypatch, tmp_path) -> None:
    audio_path = tmp_path / "clip.wav"
    audio_path.write_bytes(b"RIFF")
    monkeypatch.delenv("GOOGLE_API_KEY", raising=False)
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)

    backend = GeminiBackend()
    with pytest.raises(STTError, match="credentials"):
        backend.transcribe(audio_path)


def test_gemini_backend_transcribes_audio(monkeypatch, tmp_path) -> None:
    audio_path = tmp_path / "clip.wav"
    audio_path.write_bytes(b"RIFF")
    monkeypatch.setenv("GEMINI_API_KEY", "demo-key")

    captured: dict[str, object] = {}

    class _FakePart:
        @staticmethod
        def from_bytes(*, data, mime_type):
            captured["mime_type"] = mime_type
            captured["bytes"] = data
            return {"mime_type": mime_type, "bytes": data}

    class _FakeModels:
        def generate_content(self, *, model, contents):
            captured["model"] = model
            captured["contents"] = contents
            return types.SimpleNamespace(text="こんにちは")

    class _FakeClient:
        def __init__(self):
            self.models = _FakeModels()

    google_module = types.ModuleType("google")
    genai_module = types.ModuleType("google.genai")
    genai_module.Client = _FakeClient
    genai_module.types = types.SimpleNamespace(Part=_FakePart)
    google_module.genai = genai_module

    monkeypatch.setitem(sys.modules, "google", google_module)
    monkeypatch.setitem(sys.modules, "google.genai", genai_module)

    backend = GeminiBackend(model="gemini-3-flash-preview")
    result = backend.transcribe(audio_path)

    assert result.text == "こんにちは"
    assert result.backend == "gemini"
    assert captured["model"] == "gemini-3-flash-preview"
    assert captured["mime_type"] == "audio/wav"
