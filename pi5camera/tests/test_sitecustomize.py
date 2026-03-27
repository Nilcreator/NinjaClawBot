from __future__ import annotations

import sys

import sitecustomize


def test_prepend_system_paths_moves_paths_ahead_of_existing_entries() -> None:
    fake_path = "/tmp/fake-dist-packages"
    sys.path.append(fake_path)

    sitecustomize._prepend_system_paths([fake_path])

    assert sys.path.index(fake_path) <= 1
    while fake_path in sys.path:
        sys.path.remove(fake_path)


def test_needs_system_paths_detects_broken_module_import(monkeypatch) -> None:
    monkeypatch.setattr(sitecustomize.platform, "system", lambda: "Linux")
    monkeypatch.setattr(sitecustomize, "_is_virtual_environment", lambda: True)

    def fake_import_module(name: str):
        if name == "picamera2":
            raise ModuleNotFoundError("No module named 'libcamera._libcamera'")
        return object()

    monkeypatch.setattr(sitecustomize.importlib, "import_module", fake_import_module)

    assert sitecustomize._needs_system_paths(("picamera2",)) is True


def test_needs_system_paths_returns_false_when_modules_import(monkeypatch) -> None:
    monkeypatch.setattr(sitecustomize.platform, "system", lambda: "Linux")
    monkeypatch.setattr(sitecustomize, "_is_virtual_environment", lambda: True)
    monkeypatch.setattr(sitecustomize.importlib, "import_module", lambda name: object())

    assert sitecustomize._needs_system_paths(("libcamera", "picamera2")) is False
