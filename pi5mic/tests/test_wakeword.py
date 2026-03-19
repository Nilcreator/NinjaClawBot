"""Tests for optional wake-word backends."""

from __future__ import annotations

import sys
import types

import pytest

from pi5mic.errors import WakeWordError
from pi5mic.wakeword.porcupine import PorcupineWakeWordDetector


class _FakeEngine:
    def __init__(self) -> None:
        self.frame_length = 512
        self.sample_rate = 16_000
        self.deleted = False
        self._results = iter([-1, 0])

    def process(self, pcm_frame):
        del pcm_frame
        return next(self._results)

    def delete(self):
        self.deleted = True


def test_porcupine_from_environment_requires_key(monkeypatch) -> None:
    monkeypatch.delenv("PICOVOICE_ACCESS_KEY", raising=False)

    with pytest.raises(WakeWordError, match="PICOVOICE_ACCESS_KEY"):
        PorcupineWakeWordDetector.from_environment()


def test_porcupine_process_and_close(monkeypatch) -> None:
    created: dict[str, object] = {}
    engine = _FakeEngine()

    def fake_create(**kwargs):
        created.update(kwargs)
        return engine

    fake_module = types.SimpleNamespace(create=fake_create)
    monkeypatch.setitem(sys.modules, "pvporcupine", fake_module)

    detector = PorcupineWakeWordDetector(access_key="demo", keywords=["ninja"])

    miss = detector.process([0] * detector.frame_length)
    hit = detector.process([0] * detector.frame_length)

    assert created["access_key"] == "demo"
    assert created["keywords"] == ["ninja"]
    assert miss.detected is False
    assert hit.detected is True
    assert hit.keyword == "ninja"

    detector.close()
    assert engine.deleted is True
