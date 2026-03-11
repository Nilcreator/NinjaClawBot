"""Root pytest path setup for the NinjaClawBot monorepo."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SRC_PATHS = [
    ROOT / "ninjaclawbot" / "src",
    ROOT / "pi5buzzer" / "src",
    ROOT / "pi5servo" / "src",
    ROOT / "pi5disp" / "src",
    ROOT / "pi5vl53l0x" / "src",
    ROOT / "src",
]

for src_path in reversed(SRC_PATHS):
    src_text = str(src_path)
    if src_text not in sys.path:
        sys.path.insert(0, src_text)
