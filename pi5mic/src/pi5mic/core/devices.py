"""Audio device helpers for pi5mic."""

from __future__ import annotations

from typing import Any, cast

from pi5mic.core.audio_backend import load_sounddevice
from pi5mic.errors import DeviceError
from pi5mic.models import AudioDeviceInfo


def _get_sounddevice():
    return load_sounddevice(
        purpose="microphone discovery and status checks",
        error_factory=DeviceError,
    )


def list_input_devices() -> list[AudioDeviceInfo]:
    """Return all discovered audio devices that support input."""
    sd = _get_sounddevice()
    try:
        raw_devices = cast(list[dict[str, Any]], sd.query_devices())
    except Exception as exc:  # pragma: no cover - backend error path
        raise DeviceError(f"Could not query audio devices: {exc}") from exc

    devices: list[AudioDeviceInfo] = []
    for index, raw in enumerate(raw_devices):
        max_input_channels = int(raw.get("max_input_channels", 0))
        if max_input_channels <= 0:
            continue
        samplerate = raw.get("default_samplerate")
        default_samplerate = float(samplerate) if samplerate is not None else None
        devices.append(
            AudioDeviceInfo(
                index=index,
                name=str(raw.get("name", f"input-{index}")),
                max_input_channels=max_input_channels,
                default_samplerate=default_samplerate,
                hostapi=int(raw["hostapi"]) if "hostapi" in raw else None,
            )
        )
    return devices


def get_default_input_device() -> int | None:
    """Return the default input device index, if available."""
    sd = _get_sounddevice()
    default_device = getattr(sd.default, "device", None)

    if isinstance(default_device, (tuple, list)):
        candidate = default_device[0]
    else:
        candidate = default_device

    if candidate in (None, -1):
        return None
    return int(candidate)


def resolve_input_device(selector: int | str | None) -> int | None:
    """Resolve a device selector into a concrete input-device index."""
    if selector is None or selector == "":
        return None

    devices = list_input_devices()
    if isinstance(selector, int):
        for device in devices:
            if device.index == selector:
                return device.index
        raise DeviceError(f"No input device found with index {selector}.")

    selector_text = str(selector).strip()
    if selector_text.isdigit():
        return resolve_input_device(int(selector_text))

    exact_matches = [
        device for device in devices if device.name.casefold() == selector_text.casefold()
    ]
    if len(exact_matches) == 1:
        return exact_matches[0].index
    if len(exact_matches) > 1:
        raise DeviceError(f"Multiple input devices matched the name '{selector_text}'.")

    fuzzy_matches = [
        device for device in devices if selector_text.casefold() in device.name.casefold()
    ]
    if len(fuzzy_matches) == 1:
        return fuzzy_matches[0].index
    if len(fuzzy_matches) > 1:
        raise DeviceError(
            f"Multiple input devices matched '{selector_text}': "
            + ", ".join(device.name for device in fuzzy_matches)
        )

    raise DeviceError(f"No input device matched '{selector_text}'.")
