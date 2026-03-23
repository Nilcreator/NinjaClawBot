"""Face-recognition workflow for pi5camera."""

from __future__ import annotations

import math
from pathlib import Path
from typing import Any

from pi5camera.core.capture import capture_photo
from pi5camera.models import FaceResult
from pi5camera.recognition.face_recognition_backend import build_recognition_backend
from pi5camera.storage.face_store import FaceStore


def _euclidean_distance(left: list[float], right: list[float]) -> float:
    return math.sqrt(sum((lval - rval) ** 2 for lval, rval in zip(left, right, strict=False)))


def _best_known_match(
    encoding: list[float],
    known_entries: list[dict[str, Any]],
    tolerance: float,
) -> tuple[str | None, float | None]:
    best_name: str | None = None
    best_distance: float | None = None
    for entry in known_entries:
        candidate = entry.get("encoding", [])
        if not isinstance(candidate, list):
            continue
        distance = _euclidean_distance(
            [float(value) for value in encoding],
            [float(value) for value in candidate],
        )
        if best_distance is None or distance < best_distance:
            best_distance = distance
            best_name = str(entry.get("name", "")).strip() or None

    if best_distance is None or best_distance > tolerance:
        return None, best_distance
    return best_name, best_distance


def recognize_faces(
    config: dict[str, Any],
    *,
    image_path: Path | None = None,
) -> dict[str, Any]:
    """Recognize faces from a live capture or an existing image file."""
    store = FaceStore(config)
    store.ensure_layout()
    store.purge_expired_pending()

    photo_metadata: dict[str, Any] = {}
    if image_path is None:
        capture_result = capture_photo(config, filename_prefix="recognition")
        source_photo = capture_result.path
        photo_metadata = capture_result.metadata
    else:
        source_photo = image_path.expanduser().resolve()

    backend = build_recognition_backend(config)
    detected = backend.detect_and_encode(source_photo)
    tolerance = float(config.get("recognition", {}).get("tolerance", 0.6))
    known_entries = store.load_known_entries()

    faces: list[FaceResult] = []
    unknown_faces: list[dict[str, Any]] = []
    recognized_names: list[str] = []

    for index, encoded_face in enumerate(detected, start=1):
        face_id = f"face-{index}"
        name, distance = _best_known_match(encoded_face.encoding, known_entries, tolerance)
        status = "known" if name else "unknown"
        if name:
            recognized_names.append(name)
        result = FaceResult(
            face_id=face_id,
            index=index,
            bounding_box=encoded_face.bounding_box,
            status=status,
            name=name,
            match_distance=distance,
        )
        faces.append(result)
        if status == "unknown":
            unknown_faces.append(
                {
                    **result.to_dict(),
                    "encoding": [float(value) for value in encoded_face.encoding],
                }
            )

    recognition_id: str | None = None
    if unknown_faces:
        pending = store.save_pending_recognition(
            photo_path=source_photo,
            photo_metadata=photo_metadata,
            unknown_faces=unknown_faces,
        )
        recognition_id = str(pending["recognition_id"])
        crops_by_face = {
            str(face["face_id"]): face.get("crop_path") for face in pending.get("faces", [])
        }
        for result in faces:
            result.crop_path = crops_by_face.get(result.face_id)

    return {
        "recognition_id": recognition_id,
        "photo_path": str(source_photo),
        "photo_metadata": photo_metadata,
        "face_count": len(faces),
        "unknown_count": len(unknown_faces),
        "recognized_names": recognized_names,
        "needs_enrollment": bool(unknown_faces),
        "requires_disambiguation": len(unknown_faces) > 1,
        "faces": [face.to_dict() for face in faces],
    }
