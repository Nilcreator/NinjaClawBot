from __future__ import annotations

from types import SimpleNamespace

import pytest

from ninjaclawbot.adapters import BuzzerAdapter, DisplayAdapter
from ninjaclawbot.config import NinjaClawbotConfig


class _FakeManager:
    def __init__(self, _path: str) -> None:
        self._config = {"pin": 17, "volume": 128}

    def load(self) -> dict[str, int]:
        return dict(self._config)

    def get_pin(self) -> int:
        return 17

    def get_volume(self) -> int:
        return 128


class _FakeMusicBuzzer:
    def __init__(self, **kwargs) -> None:
        self.kwargs = kwargs
        self.calls: list[tuple[str, object]] = []
        self.is_initialized = False

    def initialize(self) -> None:
        self.is_initialized = True

    def play_emotion(self, emotion: str) -> None:
        self.calls.append(("emotion", emotion))

    def play_sound(self, frequency: int, duration: float) -> None:
        self.calls.append(("tone", (frequency, duration)))

    def off(self) -> None:
        self.calls.append(("off", None))


def test_buzzer_adapter_waits_for_emotion_playback(monkeypatch) -> None:
    fake_buzzer = _FakeMusicBuzzer()
    sleep_calls: list[float] = []

    def fake_import(module_name: str):
        if module_name == "pi5buzzer.config.config_manager":
            return SimpleNamespace(BuzzerConfigManager=_FakeManager)
        if module_name == "pi5buzzer":
            return SimpleNamespace(MusicBuzzer=lambda **kwargs: fake_buzzer)
        if module_name == "pi5buzzer.core.driver":
            return SimpleNamespace(create_default_backend=lambda: object())
        if module_name == "pi5buzzer.notes":
            return SimpleNamespace(EMOTION_SOUNDS={"happy": [("C5", 0.1), ("E5", 0.2)]})
        raise AssertionError(module_name)

    monkeypatch.setattr("ninjaclawbot.adapters._import_or_raise", fake_import)
    monkeypatch.setattr(
        "ninjaclawbot.adapters.time.sleep", lambda seconds: sleep_calls.append(seconds)
    )

    adapter = BuzzerAdapter(NinjaClawbotConfig())
    waited_for = adapter.play(emotion="happy", wait=True)

    assert fake_buzzer.calls == [("emotion", "happy")]
    assert waited_for == pytest.approx(0.35)
    assert len(sleep_calls) == 1
    assert sleep_calls[0] == pytest.approx(0.35)


def test_buzzer_adapter_waits_for_tone_playback(monkeypatch) -> None:
    fake_buzzer = _FakeMusicBuzzer()
    sleep_calls: list[float] = []

    def fake_import(module_name: str):
        if module_name == "pi5buzzer.config.config_manager":
            return SimpleNamespace(BuzzerConfigManager=_FakeManager)
        if module_name == "pi5buzzer":
            return SimpleNamespace(MusicBuzzer=lambda **kwargs: fake_buzzer)
        if module_name == "pi5buzzer.core.driver":
            return SimpleNamespace(create_default_backend=lambda: object())
        if module_name == "pi5buzzer.notes":
            return SimpleNamespace(EMOTION_SOUNDS={})
        raise AssertionError(module_name)

    monkeypatch.setattr("ninjaclawbot.adapters._import_or_raise", fake_import)
    monkeypatch.setattr(
        "ninjaclawbot.adapters.time.sleep", lambda seconds: sleep_calls.append(seconds)
    )

    adapter = BuzzerAdapter(NinjaClawbotConfig())
    waited_for = adapter.play(frequency=440, duration=0.4, wait=True)

    assert fake_buzzer.calls == [("tone", (440, 0.4))]
    assert waited_for == pytest.approx(0.4)
    assert len(sleep_calls) == 1
    assert sleep_calls[0] == pytest.approx(0.4)


def test_display_adapter_uses_root_level_display_config(monkeypatch, tmp_path) -> None:
    captured: dict[str, object] = {}

    class FakeDisplay:
        width = 240
        height = 320

        def __init__(self, **kwargs) -> None:
            captured["driver_kwargs"] = dict(kwargs)

        def set_brightness(self, value: int) -> None:
            captured["brightness"] = value

        def health_check(self) -> bool:
            return True

        def close(self) -> None:
            captured["closed"] = True

    class FakeManager:
        def __init__(self, config_path: str) -> None:
            captured["config_path"] = config_path

        def load(self) -> dict[str, int]:
            return {
                "dc_pin": 21,
                "rst_pin": 22,
                "backlight_pin": 23,
                "width": 240,
                "height": 320,
                "rotation": 180,
                "brightness": 65,
                "spi_speed_mhz": 24,
            }

    def fake_import(module_name: str):
        if module_name == "pi5disp.config.config_manager":
            return SimpleNamespace(ConfigManager=FakeManager)
        if module_name == "pi5disp.core.driver":
            return SimpleNamespace(ST7789V=FakeDisplay)
        raise AssertionError(module_name)

    monkeypatch.setattr("ninjaclawbot.adapters._import_or_raise", fake_import)

    config = NinjaClawbotConfig(root_dir=tmp_path)
    adapter = DisplayAdapter(config)
    health = adapter.health_check()

    assert captured["config_path"] == str(config.display_config_path)
    assert captured["driver_kwargs"] == {
        "dc_pin": 21,
        "rst_pin": 22,
        "backlight_pin": 23,
        "width": 240,
        "height": 320,
        "rotation": 180,
        "speed_hz": 24_000_000,
    }
    assert captured["brightness"] == 65
    assert health.data["config_path"] == str(config.display_config_path)
