"""Tests for pi5mic audio-device helpers."""

from __future__ import annotations

import pytest

from pi5mic.core import devices as devices_module
from pi5mic.errors import DeviceError


class _FakeDefault:
    def __init__(self, device):
        self.device = device


class _FakeSoundDevice:
    def __init__(self, devices, default_device=(2, 9)) -> None:
        self._devices = devices
        self.default = _FakeDefault(default_device)

    def query_devices(self):
        return list(self._devices)


def test_list_input_devices_filters_output_only(monkeypatch) -> None:
    fake_devices = [
        {"name": "Speaker", "max_input_channels": 0, "default_samplerate": 48_000.0},
        {"name": "USB Mic", "max_input_channels": 1, "default_samplerate": 16_000.0},
        {"name": "HAT Mic", "max_input_channels": 2, "default_samplerate": 44_100.0},
    ]
    monkeypatch.setattr(
        devices_module,
        "_get_sounddevice",
        lambda: _FakeSoundDevice(fake_devices),
    )

    devices = devices_module.list_input_devices()

    assert [device.name for device in devices] == ["USB Mic", "HAT Mic"]
    assert devices[0].index == 1
    assert devices[1].max_input_channels == 2


def test_get_default_input_device_handles_tuple(monkeypatch) -> None:
    monkeypatch.setattr(
        devices_module,
        "_get_sounddevice",
        lambda: _FakeSoundDevice([], default_device=(4, 8)),
    )

    assert devices_module.get_default_input_device() == 4


def test_resolve_input_device_supports_index_and_name(monkeypatch) -> None:
    fake_devices = [
        {"name": "USB Microphone", "max_input_channels": 1, "default_samplerate": 16_000.0},
        {"name": "Desk Mic", "max_input_channels": 1, "default_samplerate": 48_000.0},
    ]
    monkeypatch.setattr(
        devices_module,
        "_get_sounddevice",
        lambda: _FakeSoundDevice(fake_devices),
    )

    assert devices_module.resolve_input_device(0) == 0
    assert devices_module.resolve_input_device("1") == 1
    assert devices_module.resolve_input_device("Desk Mic") == 1
    assert devices_module.resolve_input_device("USB") == 0


def test_resolve_input_device_rejects_ambiguous_name(monkeypatch) -> None:
    fake_devices = [
        {"name": "USB Mic A", "max_input_channels": 1, "default_samplerate": 16_000.0},
        {"name": "USB Mic B", "max_input_channels": 1, "default_samplerate": 16_000.0},
    ]
    monkeypatch.setattr(
        devices_module,
        "_get_sounddevice",
        lambda: _FakeSoundDevice(fake_devices),
    )

    with pytest.raises(DeviceError, match="Multiple input devices matched"):
        devices_module.resolve_input_device("USB")


def test_resolve_input_device_rejects_missing_device(monkeypatch) -> None:
    monkeypatch.setattr(
        devices_module,
        "_get_sounddevice",
        lambda: _FakeSoundDevice([]),
    )

    with pytest.raises(DeviceError, match="No input device found with index 5"):
        devices_module.resolve_input_device(5)
