from __future__ import annotations

import importlib


def test_integrated_environment_can_import_local_driver_packages() -> None:
    for module_name in ("pi5buzzer", "pi5servo", "pi5disp", "pi5vl53l0x"):
        module = importlib.import_module(module_name)
        assert module is not None
