"""Recognition backend protocol for pi5camera."""

from __future__ import annotations

from pathlib import Path
from typing import Protocol

from pi5camera.models import EncodedFace


class RecognitionBackend(Protocol):
    """Protocol for face-detection and encoding backends."""

    def detect_and_encode(self, image_path: Path) -> list[EncodedFace]:
        """Return all detected faces with embeddings for the given image."""
