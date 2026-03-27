"""face_recognition backend implementation for pi5camera."""

from __future__ import annotations

import importlib
from pathlib import Path
from typing import Any

from pi5camera.environment import (
    describe_face_recognition_environment,
    inject_system_site_packages,
)
from pi5camera.errors import RecognitionError
from pi5camera.models import EncodedFace, FaceBoundingBox


def _import_face_recognition() -> Any:
    try:
        return importlib.import_module("face_recognition")
    except ImportError as exc:  # pragma: no cover - depends on host environment
        if inject_system_site_packages("face_recognition"):
            try:
                return importlib.import_module("face_recognition")
            except ImportError:
                pass

        summary = describe_face_recognition_environment()
        detail = summary.get("diagnostic")
        message = summary.get("help_text") or (
            "The face_recognition Python package is not installed in this environment."
        )
        if detail:
            message = f"{message} Import detail: {detail}."
        raise RecognitionError(message) from exc


class FaceRecognitionBackend:
    """Face-recognition backend using the face_recognition package."""

    def detect_and_encode(self, image_path: Path) -> list[EncodedFace]:
        face_recognition = _import_face_recognition()
        try:
            image = face_recognition.load_image_file(str(image_path))
            locations = face_recognition.face_locations(image)
            encodings = face_recognition.face_encodings(image, locations)
        except Exception as exc:
            raise RecognitionError(f"Face detection failed for '{image_path}': {exc}") from exc

        if len(locations) != len(encodings):
            raise RecognitionError(
                "Face detection returned mismatched location and encoding counts."
            )

        detected: list[EncodedFace] = []
        for location, encoding in zip(locations, encodings, strict=False):
            top, right, bottom, left = location
            detected.append(
                EncodedFace(
                    bounding_box=FaceBoundingBox(
                        top=int(top),
                        right=int(right),
                        bottom=int(bottom),
                        left=int(left),
                    ),
                    encoding=[float(value) for value in encoding.tolist()],
                )
            )
        return detected


def build_recognition_backend(config: dict) -> FaceRecognitionBackend:
    """Build the configured recognition backend."""
    recognition_config = config.get("recognition", {})
    backend_name = str(recognition_config.get("backend", "face_recognition"))
    if backend_name != "face_recognition":
        raise RecognitionError(f"Unsupported recognition backend '{backend_name}'.")
    return FaceRecognitionBackend()
